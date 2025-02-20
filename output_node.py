from io import BytesIO
import json
import os
import re
from pathlib import Path
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
import torch
from comfy import model_management
import requests
import numpy as np
import folder_paths
from nodes import LoadImage
from comfy.utils import ProgressBar
from server import PromptServer
from .rice_def import RiceRoundErrorDef, RiceTaskErrorDef
from .rice_url_config import RiceUrlConfig, user_upload_image, user_upload_imagefile
from .utils import get_machine_id, pil2tensor
from .auth_unit import AuthUnit
from .rice_prompt_info import RicePromptInfo
from .rice_websocket import (
    TaskInfo,
    TaskStatus,
    TaskWebSocket,
    start_and_wait_task_done,
)


class RiceRoundDecryptNode:
    def __init__(self):
        self.auth_unit = AuthUnit()
        self.machine_id = get_machine_id()
        self.url_config = RiceUrlConfig()
        self.pbar = None
        self.last_progress = 0
        self.user_token = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "rice_template_id": ("STRING", {"default": ""}),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "The random seed used for creating the noise.",
                    },
                ),
            },
            "optional": {"input_anything": ("*", {})},
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    @classmethod
    def VALIDATE_INPUTS(s, input_types):
        for key, value in input_types.items():
            if key.startswith("input_anything"):
                if value not in ("STRING", "TEXT", "PROMPT"):
                    return f"{key} must be of string type"
        return True

    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "RiceRound/Output"

    def progress_callback(self, task_uuid, progress_text, progress, preview_refreshed):
        if not self.pbar:
            return
        if preview_refreshed:
            url = self.url_config.workflow_preview_url + "?task_uuid=" + task_uuid
            try:
                headers = {"Authorization": f"Bearer {self.user_token}"}
                response = requests.get(url, stream=True, headers=headers)
                response.raise_for_status()
                preview_image = Image.open(BytesIO(response.content))
                self.pbar.update_absolute(
                    self.last_progress, preview=("PNG", preview_image, None)
                )
            except Exception as e:
                print(f"Failed to load preview image: {str(e)}")
                self.pbar.update_absolute(self.last_progress)
        else:
            self.last_progress = progress
            self.pbar.update_absolute(progress)

    def execute(self, rice_template_id, **kwargs):
        self.pbar = ProgressBar(100)
        self.user_token, error_msg, error_code = self.auth_unit.get_user_token()
        if not self.user_token:
            if (
                error_code == RiceRoundErrorDef.HTTP_UNAUTHORIZED
                or error_code == RiceRoundErrorDef.NO_TOKEN_ERROR
            ):
                AuthUnit().login_dialog("运行云节点需要先完成登录")
            else:
                PromptServer.instance.send_sync(
                    "riceround_toast",
                    {"content": "无法完成鉴权登录，请检查网络或完成登录步骤", "type": "error"},
                )
            raise ValueError(error_msg)
        index_dict = {}
        for k, v in kwargs.items():
            if k.startswith("input_anything"):
                suffix = k[len("input_anything") :]
                suffix = re.sub("\\s*\\([^)]*\\)", "", suffix)
                index = 0 if suffix == "" else int(suffix)
                if index in index_dict:
                    raise ValueError(f"Duplicate input_anything index: {index}")
                if isinstance(v, str):
                    index_dict[str(index)] = v
                else:
                    raise ValueError(f"Invalid input type: {type(v)}")
        if not index_dict:
            return (torch.zeros(1, 1, 1, 3),)
        task_info = self.create_task(index_dict, rice_template_id, self.user_token)
        if not task_info or not task_info.task_uuid:
            raise ValueError("Failed to create task")
        start_and_wait_task_done(
            self.url_config.task_ws_url,
            self.user_token,
            self.machine_id,
            task_info,
            self.progress_callback,
            RicePromptInfo().get_wait_time(),
        )
        model_management.throw_exception_if_processing_interrupted()
        result_data = task_info.result_data
        if not result_data:
            if task_info.progress_text and task_info.state > TaskStatus.FINISHED:
                raise ValueError(task_info.progress_text)
            else:
                raise ValueError("websocket failed")
        image_results = result_data.get("image_results", [])
        if not image_results:
            raise ValueError("Failed to get image results")
        images = []
        for image_url in image_results:
            image = Image.open(requests.get(image_url, stream=True).raw)
            image = ImageOps.exif_transpose(image)
            images.append(pil2tensor(image))
        image_tensor = torch.cat(images, dim=0)
        self.pbar = None
        return (image_tensor,)

    def create_task(self, input_data, template_id, user_token):
        "\n        Create a task and return the task UUID.\n        \n        Args:\n            task_url (str): The URL to send the task request to\n            request_data (dict): The data to send in the request\n            headers (dict): The headers to send with the request\n            \n        Returns:\n            str: The task UUID if successful\n            \n        Raises:\n            ValueError: If the request fails or response is invalid\n"
        task_url = self.url_config.prompt_task_url
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }
        request_data = {
            "taskData": json.dumps(input_data),
            "workData": json.dumps({"template_id": template_id}),
        }
        response = requests.post(task_url, json=request_data, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and "data" in response_data:
                task_info = TaskInfo(response_data.get("data", {}))
                if task_info.task_uuid:
                    return task_info
                else:
                    raise ValueError("No task UUID in response")
            else:
                raise ValueError(
                    f"API error: {response_data.get('message','Unknown error')}"
                )
        elif response.status_code == RiceRoundErrorDef.HTTP_INTERNAL_ERROR:
            response_data = response.json()
            if (
                response_data.get("code")
                == RiceTaskErrorDef.ERROR_INSUFFICIENT_PERMISSION_INSUFFICIENT_BALANCE
            ):
                PromptServer.instance.send_sync(
                    "riceround_show_workflow_payment_dialog",
                    {"template_id": template_id, "title": "余额不足，请充值"},
                )
                raise ValueError(f"余额不足，运行失败，请完成支付后重试！")
            else:
                raise ValueError(
                    f"API error: {response_data.get('message','Unknown error')}"
                )
        else:
            raise ValueError(f"HTTP error {response.status_code}: {response.text}")


class RiceRoundBaseChoiceNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(cls):
        node_name = getattr(cls, "__node_name__", None)
        options = (
            RicePromptInfo().get_choice_node_options(node_name) if node_name else []
        )
        return {
            "required": {
                "name": ("STRING", {"default": "Parameter"}),
                "default": (options,),
            },
            "optional": {},
            "hidden": {},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    FUNCTION = "placeholder"
    CATEGORY = "__hidden__"

    def placeholder(self, default, **kwargs):
        return (default,)


def upload_imagefile(image_path):
    user_token, error_msg, error_code = AuthUnit().get_user_token()
    if not user_token:
        if (
            error_code == RiceRoundErrorDef.HTTP_UNAUTHORIZED
            or error_code == RiceRoundErrorDef.NO_TOKEN_ERROR
        ):
            AuthUnit().login_dialog("运行云节点需要先完成登录")
        else:
            PromptServer.instance.send_sync(
                "riceround_toast", {"content": "无法完成鉴权登录，请检查网络或完成登录步骤", "type": "error"}
            )
        raise ValueError(error_msg)
    return user_upload_imagefile(image_path, user_token)


def upload_image(image):
    user_token, error_msg, error_code = AuthUnit().get_user_token()
    if not user_token:
        if (
            error_code == RiceRoundErrorDef.HTTP_UNAUTHORIZED
            or error_code == RiceRoundErrorDef.NO_TOKEN_ERROR
        ):
            AuthUnit().login_dialog("运行云节点需要先完成登录")
        else:
            PromptServer.instance.send_sync(
                "riceround_toast", {"content": "无法完成鉴权登录，请检查网络或完成登录步骤", "type": "error"}
            )
        raise ValueError(error_msg)
    return user_upload_image(image, user_token)


class RiceRoundImageUrlNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image_url": ("STRING",)}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "RiceRound/Output"

    def load_image(self, image_url, **kwargs):
        return (image_url,)


class RiceRoundUploadImageNode(LoadImage):
    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [
            f
            for f in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, f))
        ]
        return {"required": {"image": (sorted(files), {"image_upload": True})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "RiceRound/Output"

    def load_image(self, image, **kwargs):
        image_path = folder_paths.get_annotated_filepath(image)
        download_url = upload_imagefile(image_path)
        return (download_url,)


class RiceRoundOutputImageBridgeNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"images": ("IMAGE", {"tooltip": "only image."})},
            "optional": {},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Output"

    def bridge(self, images, **kwargs):
        return upload_image(images)


class RiceRoundOutputMaskBridgeNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"mask": ("MASK",)}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Output"

    def bridge(self, mask, **kwargs):
        mask_np = mask.cpu().numpy()
        mask_np = (mask_np * 255).astype(np.uint8)
        mask_image = Image.fromarray(mask_np)
        image_url = upload_image(mask_image)
        return (image_url,)


class RiceRoundMaskUrlNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"mask_url": ("STRING",)}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "RiceRound/Output"

    def load_image(self, mask_url, **kwargs):
        return (mask_url,)


class RiceRoundOutputIntNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "name": ("STRING", {"default": "数值"}),
                "number": ("INT",),
                "min": ("INT", {"default": 0}),
                "max": ("INT", {"default": 1000000}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Output"

    def bridge(self, name, number, min, max, **kwargs):
        return (str(number),)


class RiceRoundOutputFloatNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "name": ("STRING", {"default": "数值"}),
                "number": ("FLOAT",),
                "min": ("FLOAT", {"default": 0.0}),
                "max": ("FLOAT", {"default": 1e6}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Output"

    def bridge(self, name, number, min, max, **kwargs):
        return (str(number),)


class RiceRoundOutputBooleanNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "name": ("STRING", {"default": "开关"}),
                "value": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Output"

    def bridge(self, name, value, **kwargs):
        str_value = "true" if value else "false"
        return (str_value,)


class RiceRoundOutputTextNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"name": ("STRING", {"default": "文本"}), "str": ("STRING",)}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Output"

    def bridge(self, name, str, **kwargs):
        return (str,)

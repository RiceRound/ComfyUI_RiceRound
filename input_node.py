import hashlib
import json
import os
import re
import time
import random
from PIL import Image, ImageOps, ImageSequence
import numpy as np
import torch
import node_helpers
from .rice_prompt_info import RicePromptInfo
from nodes import LoadImage
import requests
from .utils import pil2tensor


class _BasicTypes(str):
    basic_types = ["STRING"]

    def __eq__(self, other):
        return other in self.basic_types or isinstance(other, (list, _BasicTypes))

    def __ne__(self, other):
        return not self.__eq__(other)


BasicTypes = _BasicTypes("BASIC")


class RiceRoundSimpleChoiceNode:
    def __init__(self):
        self.prompt_info = RicePromptInfo()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "Parameter"}),
                "default": ("STRING", {"default": ""}),
            },
            "optional": {},
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = (BasicTypes,)
    RETURN_NAMES = ("value",)
    FUNCTION = "placeholder"
    CATEGORY = "RiceRound/Input"

    def placeholder(self, name, default, **kwargs):
        unique_id = int(kwargs.pop("unique_id", 0))
        prompt = kwargs.pop("prompt", None)
        need_wait = True
        if prompt:
            for _, node in prompt.items():
                if node.get("class_type", "") == "RiceRoundDecryptNode":
                    need_wait = False
                    break
        if need_wait:
            for i in range(10):
                if unique_id in self.prompt_info.choice_node_map:
                    break
                time.sleep(1)
        if unique_id not in self.prompt_info.choice_node_map:
            print(
                f"Warning: RiceRoundSimpleChoiceNode {unique_id} not found in prompt_info.choice_node_map"
            )
        return (default,)


class RiceRoundAdvancedChoiceNode(RiceRoundSimpleChoiceNode):
    def __init__(self):
        super().__init__()

    CATEGORY = "RiceRound/Advanced"


class RiceRoundSimpleImageNode(LoadImage):
    def __init__(self):
        super().__init__()

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    CATEGORY = "RiceRound/Input"
    FUNCTION = "load_image"

    def load_image(self, image):
        output_image, _ = super().load_image(image)
        return (output_image,)


class RiceRoundImageNode(LoadImage):
    def __init__(self):
        super().__init__()

    RETURN_TYPES = "IMAGE", "MASK"
    RETURN_NAMES = "image", "mask"
    OUTPUT_NODE = True
    CATEGORY = "RiceRound/Input"
    FUNCTION = "load_image"

    def load_image(self, image):
        return super().load_image(image)


class RiceRoundDownloadImageNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"image_url": ("STRING", {"default": ""})},
            "optional": {},
            "hidden": {},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "RiceRound/Input"

    def load_image(self, image_url, **kwargs):
        image = Image.open(requests.get(image_url, stream=True).raw)
        image = ImageOps.exif_transpose(image)
        return (pil2tensor(image),)


class RiceRoundDownloadImageAndMaskNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image_url": ("STRING", {"default": ""})}}

    RETURN_TYPES = "IMAGE", "MASK"
    RETURN_NAMES = "image", "mask"
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "RiceRound/Input"

    def load_image(self, image_url, **kwargs):
        img = Image.open(requests.get(image_url, stream=True).raw)
        img = ImageOps.exif_transpose(img)
        output_images = []
        output_masks = []
        w, h = None, None
        excluded_formats = ["MPO"]
        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)
            if i.mode == "I":
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")
            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]
            if image.size[0] != w or image.size[1] != h:
                continue
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            if "A" in i.getbands():
                mask = np.array(i.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))
        if len(output_images) > 1 and img.format not in excluded_formats:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]
        return output_image, output_mask


class RiceRoundImageBridgeNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"images": ("IMAGE", {"tooltip": "only image."})},
            "optional": {},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Input"

    def bridge(self, images, **kwargs):
        return (images,)


class RiceRoundMaskBridgeNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"mask": ("MASK", {"tooltip": "only image."})}}

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "bridge"
    CATEGORY = "RiceRound/Input"

    def bridge(self, mask, **kwargs):
        return (mask,)


class RiceRoundDownloadMaskNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"mask_url": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load_mask"
    CATEGORY = "RiceRound/Input"

    def load_mask(self, mask_url, **kwargs):
        try:
            response = requests.get(mask_url, stream=True, timeout=10)
            response.raise_for_status()
            mask = Image.open(response.raw)
            if mask.mode != "L":
                mask = mask.convert("L")
            return (pil2tensor(mask),)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading mask from {mask_url}: {str(e)}")
            raise
        except Exception as e:
            print(f"Error processing mask: {str(e)}")
            raise


class RiceRoundIntNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "name": ("STRING", {"default": "数值"}),
                "number": ("INT", {"default": 0}),
                "min": ("INT", {"default": 0}),
                "max": ("INT", {"default": 100}),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "RiceRound/Input"

    def load(self, name, number, min, max, **kwargs):
        return (number,)


class RiceRoundStrToIntNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"name": ("STRING", {"default": "数值"}), "str": ("STRING",)}}

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "RiceRound/Input"

    def load(self, name, str, **kwargs):
        return (int(str),)


class RiceRoundFloatNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "name": ("STRING", {"default": "数值"}),
                "number": ("FLOAT", {"default": 0.0}),
                "min": ("FLOAT", {"default": 0.0}),
                "max": ("FLOAT", {"default": 1e2}),
            }
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "RiceRound/Input"

    def load(self, name, number, min, max, **kwargs):
        return (number,)


class RiceRoundStrToFloatNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"name": ("STRING", {"default": "数值"}), "str": ("STRING",)}}

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "RiceRound/Input"

    def load(self, name, str, **kwargs):
        return (float(str),)


class RiceRoundBooleanNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "name": ("STRING", {"default": "开关"}),
                "value": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("value",)
    FUNCTION = "execute"
    CATEGORY = "RiceRound/Input"

    def execute(self, name, value):
        return (value,)


class RiceRoundStrToBooleanNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"name": ("STRING", {"default": "开关"}), "str": ("STRING",)}}

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "RiceRound/Input"

    def load(self, name, str, **kwargs):
        return (str.lower() == "true",)


class RiceRoundInputTextNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_info": (
                    "STRING",
                    {"multiline": True, "tooltip": "The text to be encoded."},
                )
            }
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "RiceRound/Input"

    def load(self, text_info, **kwargs):
        text = ""
        try:
            json_data = json.loads(text_info)
            text = json_data.get("content", "")
        except json.JSONDecodeError:
            text = text_info
        return (text,)


class RiceRoundRandomSeedNode:
    def __init__(self):
        0

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}, "optional": {}, "hidden": {}}

    RETURN_TYPES = ("INT",)
    FUNCTION = "random"
    CATEGORY = "RiceRound/Input"

    @classmethod
    def IS_CHANGED(s):
        return random.randint(0, 999999)

    def random(self):
        r = random.randint(0, 999999)
        print("产生随机数 ", r)
        return (r,)

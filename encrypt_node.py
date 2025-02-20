from collections import defaultdict
import copy
from io import BytesIO
import json
import os
import random
import shutil
import uuid
import numpy as np
import comfy.utils
import time
from PIL import Image
from .rice_def import RiceRoundErrorDef
from .rice_install_client import RiceInstallClient
from .auth_unit import AuthUnit
from .publish import Publish
from .utils import combine_files
from .rice_url_config import machine_upload_image
import folder_paths
from server import PromptServer
from .rice_url_config import RiceUrlConfig
from .rice_prompt_info import RicePromptInfo

output_project_folder = folder_paths.output_directory
INPUT_NODE_TYPES = [
    "RiceRoundSimpleChoiceNode",
    "RiceRoundAdvancedChoiceNode",
    "RiceRoundSimpleImageNode",
    "RiceRoundImageNode",
    "RiceRoundDownloadImageNode",
    "RiceRoundImageBridgeNode",
    "RiceRoundInputTextNode",
    "RiceRoundMaskBridgeNode",
    "RiceRoundDownloadMaskNode",
    "RiceRoundIntNode",
    "RiceRoundFloatNode",
    "RiceRoundStrToIntNode",
    "RiceRoundStrToFloatNode",
    "RiceRoundBooleanNode",
    "RiceRoundStrToBooleanNode",
]


class RiceRoundEncryptNode:
    def __init__(self):
        self.template_id = uuid.uuid4().hex
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + "".join(
            random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5)
        )
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "project_name": ("STRING", {"default": "my_project"}),
                "template_id": ("STRING", {"default": uuid.uuid4().hex}),
                "images": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "encrypt"
    CATEGORY = "RiceRound"

    def encrypt(self, project_name, template_id, images, **kwargs):
        unique_id = kwargs.pop("unique_id", None)
        extra_pnginfo = kwargs.pop("extra_pnginfo", None)
        prompt = kwargs.pop("prompt", None)
        encrypt = Encrypt(extra_pnginfo["workflow"], prompt, project_name, template_id)
        publish_folder = encrypt.do_encrypt()
        filename_prefix = "rice_round"
        filename_prefix += self.prefix_append
        (
            full_output_folder,
            filename,
            counter,
            subfolder,
            filename_prefix,
        ) = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )
        results = list()
        pbar = comfy.utils.ProgressBar(images.shape[0])
        preview_path = None
        for batch_number, image in enumerate(images):
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            if batch_number == 0:
                preview_path = os.path.join(publish_folder, "preview.png")
                img.save(preview_path)
            pbar.update_absolute(batch_number, images.shape[0], ("PNG", img, None))
            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            img.save(
                os.path.join(full_output_folder, file),
                compress_level=self.compress_level,
            )
            results.append(
                {"filename": file, "subfolder": subfolder, "type": self.type}
            )
            counter += 1
        auto_publish = RicePromptInfo().get_auto_publish()
        if auto_publish:
            publish = Publish(publish_folder)
            user_token, error_msg, error_code = AuthUnit().get_user_token()
            if not user_token:
                print(f"riceround get user token failed, {error_msg}")
                if (
                    error_code == RiceRoundErrorDef.HTTP_UNAUTHORIZED
                    or error_code == RiceRoundErrorDef.NO_TOKEN_ERROR
                ):
                    AuthUnit().login_dialog("安装节点需要先完成登录")
                else:
                    PromptServer.instance.send_sync(
                        "riceround_toast",
                        {"content": "无法完成鉴权登录，请检查网络或完成登录步骤", "type": "error"},
                    )
                return {}
            else:
                publish.publish(
                    user_token,
                    template_id,
                    project_name,
                    preview_path,
                    os.path.join(publish_folder, f"{template_id}.bin"),
                )
        if RicePromptInfo().get_run_client():
            error_code, error_msg = RiceInstallClient().run_client()
            if error_code != RiceRoundErrorDef.SUCCESS:
                PromptServer.instance.send_sync(
                    "riceround_toast",
                    {"content": "加密节点发布完成，但无法启动client，建议官网重新安装", "type": "error"},
                )
        return {"ui": {"images": results}}


class RiceRoundOutputImageNode:
    def __init__(self):
        self.url_config = RiceUrlConfig()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"images": ("IMAGE",), "task_id": ("STRING", {"default": ""})},
            "optional": {"template_id": ("STRING", {"default": ""})},
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "load"
    CATEGORY = "__hidden__"

    def load(self, images, task_id, template_id, **kwargs):
        unique_id = kwargs.pop("unique_id", None)
        prompt = kwargs.pop("prompt", None)
        extra_pnginfo = kwargs.pop("extra_pnginfo", None)
        client_id = PromptServer.instance.client_id
        prompt_id = ""
        if (
            hasattr(PromptServer.instance, "last_prompt_id")
            and PromptServer.instance.last_prompt_id
        ):
            prompt_id = PromptServer.instance.last_prompt_id
        if unique_id is None:
            raise Exception("Warning: 'unique_id' is missing.")
        if prompt is None:
            raise Exception("Warning: 'prompt' is missing.")
        if not task_id:
            raise Exception("Warning: 'task_id' is missing.")
        else:
            print(f"RiceRoundOutputImageNode task_id: {task_id}")
            if images.shape[0] > 5:
                raise ValueError("Error: Cannot upload more than 5 images.")
            image_results = []
            for image in images:
                download_url = machine_upload_image(image, task_id)
                if not download_url:
                    raise ValueError("Error: Failed to upload image.")
                image_results.append(download_url)
            result_data = {"image_type": "PNG", "image_results": image_results}
            result_info = {
                "task_id": task_id,
                "unique_id": unique_id,
                "client_id": client_id,
                "prompt_id": prompt_id,
                "timestamp": int(time.time() * 1000),
                "image_type": "PNG",
                "result_data": result_data,
            }
            PromptServer.instance.send_sync(
                "rice_round_done", result_info, sid=client_id
            )
        return {}


class Encrypt:
    def __init__(self, workflow, prompt, project_name, template_id):
        self.original_workflow = workflow
        self.original_prompt = prompt
        self.template_id = template_id
        self.project_name = project_name
        self.project_folder = os.path.join(
            output_project_folder, self.project_name, self.template_id
        )
        if not os.path.exists(self.project_folder):
            os.makedirs(self.project_folder)
        self.output_folder = os.path.join(self.project_folder, "output")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.publish_folder = os.path.join(self.project_folder, "publish")
        if not os.path.exists(self.publish_folder):
            os.makedirs(self.publish_folder)
        self.last_node_id = 0
        self.last_link_id = 0
        self.link_owner_map = defaultdict(dict)
        self.workflow_nodes_dict = {}
        self.node_prompt_map = {}
        self.input_node_map = {}
        self.related_node_ids = set()

    def do_encrypt(self):
        self.load_workflow()
        self.load_prompt()
        self.analyze_input_from_workflow()
        self.assemble_new_workflow()
        self.output_template_json_file()
        self.assemble_new_prompt()
        self.output_file(self.original_workflow, f"original_workflow")
        self.output_file(self.original_prompt, f"original_prompt")
        self.save_rice_zip()
        self.clear()
        return self.publish_folder

    def clear(self):
        self.original_workflow = None
        self.original_prompt = None
        self.template_id = None
        self.project_name = None
        self.project_folder = None
        self.last_node_id = 0
        self.last_link_id = 0
        RicePromptInfo().clear()

    def load_workflow(self):
        simplify_workflow = copy.deepcopy(self.original_workflow)
        self.workflow_nodes_dict = {
            int(node["id"]): node for node in simplify_workflow["nodes"]
        }
        for node in simplify_workflow["nodes"]:
            output_nodes = node.get("outputs", [])
            if not output_nodes:
                continue
            for output in output_nodes:
                links = output.get("links", [])
                if not links:
                    continue
                for link in links:
                    link = int(link)
                    self.link_owner_map[link]["links"] = copy.deepcopy(links)
                    self.link_owner_map[link]["slot_index"] = output.get(
                        "slot_index", 0
                    )
                    self.link_owner_map[link]["owner_id"] = int(node["id"])
                    self.link_owner_map[link]["type"] = output.get("type", "")
        self.last_node_id = int(simplify_workflow["last_node_id"])
        self.last_link_id = int(simplify_workflow["last_link_id"])

    def load_prompt(self):
        simplify_prompt = copy.deepcopy(self.original_prompt)
        self.node_prompt_map = {
            int(node_id): node for (node_id, node) in simplify_prompt.items()
        }

    def analyze_input_from_workflow(self):
        for id, node in self.workflow_nodes_dict.items():
            class_type = node.get("type", "")
            if class_type in INPUT_NODE_TYPES:
                self.input_node_map[id] = copy.deepcopy(node)
                output_nodes = node.get("outputs", [])
                if not output_nodes:
                    continue
                links = output_nodes[0].get("links", [])
                if not links:
                    continue
                link_id = int(links[0])
                self.input_node_map[id]["main_link_id"] = link_id
                self.input_node_map[id]["main_link_type"] = output_nodes[0].get(
                    "type", "STRING"
                )
        self.input_node_map = {
            k: v for (k, v) in sorted(self.input_node_map.items(), key=lambda x: x[0])
        }

    def assemble_new_workflow(self):
        input_node_ids = list(self.input_node_map.keys())
        new_simplify_workflow = copy.deepcopy(self.original_workflow)
        self.related_node_ids = self.find_workflow_related_nodes(
            new_simplify_workflow["links"], input_node_ids
        )
        new_simplify_workflow["nodes"] = [
            node
            for node in new_simplify_workflow["nodes"]
            if int(node["id"]) in self.related_node_ids
        ]
        self.invalid_new_workflow(new_simplify_workflow)
        new_node_ids = self.add_decrypt_node(new_simplify_workflow)
        self.remove_redundant_links(new_simplify_workflow)
        self.remove_unrelated_nodes(
            new_simplify_workflow, self.related_node_ids, new_node_ids
        )
        self.replace_choice_template(new_simplify_workflow)
        self.replace_workflow_node(new_simplify_workflow)
        self.output_file(new_simplify_workflow, f"{self.template_id}_workflow")

    def output_template_json_file(self):
        system_default_title = set()
        try:
            from nodes import NODE_DISPLAY_NAME_MAPPINGS

            for k, v in NODE_DISPLAY_NAME_MAPPINGS.items():
                system_default_title.add(k)
                system_default_title.add(v)
        except ImportError:
            print("Warning: Could not import NODE_DISPLAY_NAME_MAPPINGS")
        rice_prompt_info = RicePromptInfo()
        elements = []
        for node_id, node in self.input_node_map.items():
            input_number = node["input_anything"]
            owner_node_type = self.workflow_nodes_dict[node_id]["type"]
            node_prompt_inputs = self.node_prompt_map[node_id].get("inputs", {})
            label_name = str(node_prompt_inputs.get("name", ""))
            if not label_name:
                label_name = (
                    self.node_prompt_map[node_id].get("_meta", {}).get("title", "")
                )
            item = {
                "id": str(input_number),
                "type": "",
                "describe": "输入组件",
                "node_id": str(node_id),
                "settings": {},
            }
            if owner_node_type in [
                "RiceRoundSimpleImageNode",
                "RiceRoundDownloadImageNode",
                "RiceRoundImageBridgeNode",
            ]:
                item["type"] = "image_upload"
                item["describe"] = "请上传图片"
                item["settings"] = {
                    "accept": "image/*",
                    "max_size": 500000,
                    "tip": "请上传不超过500KB的图片",
                }
            elif owner_node_type == "RiceRoundImageNode":
                item["type"] = "mask_image_upload"
                item["describe"] = "请上传图片并编辑蒙版"
                item["settings"] = {
                    "accept": "image/*",
                    "max_size": 500000,
                    "tip": "请上传不超过500KB的图片",
                    "mask": True,
                }
            elif owner_node_type in [
                "RiceRoundMaskBridgeNode",
                "RiceRoundDownloadMaskNode",
            ]:
                item["type"] = "mask_upload"
                item["describe"] = "请上传蒙版"
                item["settings"] = {
                    "accept": "image/*",
                    "max_size": 50000,
                    "tip": "请上传不超过50KB的图片",
                }
            elif owner_node_type == "RiceRoundInputTextNode":
                item["type"] = "text"
                item["describe"] = "提示词"
                item["settings"] = {"placeholder": "请描述图片内容", "multiline": True}
            elif (
                owner_node_type == "RiceRoundSimpleChoiceNode"
                or owner_node_type == "RiceRoundAdvancedChoiceNode"
            ):
                item["type"] = "choice"
                item["describe"] = "模型选择"
                item["settings"] = {
                    "options": rice_prompt_info.get_choice_value(node_id),
                    "default": node_prompt_inputs.get("default", ""),
                }
                item["addition"] = rice_prompt_info.get_choice_node_addition(node_id)
            elif (
                owner_node_type == "RiceRoundIntNode"
                or owner_node_type == "RiceRoundStrToIntNode"
            ):
                item["type"] = "number_int"
                item["describe"] = "数值"
                item["settings"] = {
                    "min": node_prompt_inputs.get("min", 0),
                    "max": node_prompt_inputs.get("max", 1000),
                    "number": node_prompt_inputs.get("number", 0),
                }
            elif (
                owner_node_type == "RiceRoundFloatNode"
                or owner_node_type == "RiceRoundStrToFloatNode"
            ):
                item["type"] = "number_float"
                item["describe"] = "数值"
                item["settings"] = {
                    "min": node_prompt_inputs.get("min", 0.0),
                    "max": node_prompt_inputs.get("max", 1e3),
                    "number": node_prompt_inputs.get("number", 0.0),
                }
            elif (
                owner_node_type == "RiceRoundBooleanNode"
                or owner_node_type == "RiceRoundStrToBooleanNode"
            ):
                item["type"] = "switch"
                item["describe"] = "开关"
                item["settings"] = {"default": node_prompt_inputs.get("value", False)}
            else:
                raise ValueError(
                    f"Error: The node {node_id} is not a valid RiceRound node."
                )
            if label_name and label_name not in system_default_title:
                item["describe"] = label_name
            elements.append(item)
        json_dict = {"template_id": self.template_id, "elements": elements}
        self.output_file(json_dict, f"{self.template_id}_template")

    def assemble_new_prompt(self):
        "\n        组装新的prompt配置。主要完成:\n        1. 移除不需要的节点\n        2. 转换特定节点的类型和输入\n        3. 保存处理后的prompt配置\n"
        new_prompt = self._create_filtered_prompt()
        self._replace_encrypt_node(new_prompt)
        self._transform_node_types(new_prompt)
        self.output_file(new_prompt, f"{self.template_id}_job")

    def _create_filtered_prompt(self):
        "\n        创建经过过滤的prompt副本，移除不需要的节点\n"
        new_prompt = copy.deepcopy(self.original_prompt)
        exclude_node_ids = self._get_exclude_node_ids(new_prompt)
        for node_id in exclude_node_ids:
            new_prompt.pop(str(node_id), None)
        return new_prompt

    def _replace_encrypt_node(self, new_prompt):
        for node_id, node in new_prompt.items():
            class_type = node.get("class_type", "")
            print(f"class_type: {class_type}")
            if class_type == "RiceRoundEncryptNode":
                node["class_type"] = "RiceRoundOutputImageNode"
                node["inputs"]["task_id"] = ""
                node["inputs"].pop("project_name", None)
                if "_meta" in node and "title" in node["_meta"]:
                    node["_meta"]["title"] = "RiceRoundOutputImageNode"

    def save_rice_zip(self):
        import pyzipper

        try:
            files_to_zip = []
            for i, file in enumerate(
                [
                    f"{self.template_id}_job.json",
                    f"{self.template_id}_template.json",
                    f"{self.template_id}_workflow.json",
                    "original_workflow.json",
                    "original_prompt.json",
                ]
            ):
                src_path = os.path.join(self.output_folder, file)
                files_to_zip.append((src_path, f"{i}.bin"))
            zip_file_path = os.path.join(self.publish_folder, f"{self.template_id}.bin")
            with pyzipper.AESZipFile(
                zip_file_path,
                "w",
                compression=pyzipper.ZIP_DEFLATED,
                encryption=pyzipper.WZ_AES,
            ) as zipf:
                zipf.setpassword(self.template_id.encode())
                for file_path, arcname in files_to_zip:
                    zipf.write(file_path, arcname)
            shutil.copy2(
                os.path.join(self.output_folder, f"{self.template_id}_template.json"),
                os.path.join(self.publish_folder, "template.json"),
            )
            shutil.copy2(
                os.path.join(self.output_folder, f"{self.template_id}_workflow.json"),
                os.path.join(self.project_folder, "workflow.json"),
            )
        except Exception as e:
            print(f"Error creating zip: {str(e)}")
            raise

    def _get_exclude_node_ids(self, prompt):
        "\n        获取需要从prompt中排除的节点ID集合\n"
        EXCLUDE_NODE_TYPES = {"RiceRoundDecryptNode"}
        exclude_ids = self.related_node_ids.difference(set(self.input_node_map.keys()))
        for node_id, node in prompt.items():
            if node.get("class_type", "") in EXCLUDE_NODE_TYPES:
                exclude_ids.add(int(node_id))
        return exclude_ids

    def _transform_node_types(self, prompt):
        "\n        转换节点类型和更新节点输入配置\n"
        NODE_TYPE_MAPPING = {
            "RiceRoundImageBridgeNode": {
                "new_type": "RiceRoundDownloadImageNode",
                "new_inputs": {"image_url": ""},
            },
            "RiceRoundSimpleImageNode": {
                "new_type": "RiceRoundDownloadImageNode",
                "new_inputs": {"image_url": ""},
            },
            "RiceRoundImageNode": {
                "new_type": "RiceRoundDownloadImageAndMaskNode",
                "new_inputs": {"image_url": ""},
            },
            "RiceRoundMaskBridgeNode": {
                "new_type": "RiceRoundDownloadMaskNode",
                "new_inputs": {"mask_url": ""},
            },
            "RiceRoundIntNode": {
                "new_type": "RiceRoundStrToIntNode",
                "new_inputs": {"str": ""},
            },
            "RiceRoundFloatNode": {
                "new_type": "RiceRoundStrToFloatNode",
                "new_inputs": {"str": ""},
            },
            "RiceRoundBooleanNode": {
                "new_type": "RiceRoundStrToBooleanNode",
                "new_inputs": {"str": ""},
            },
        }
        for node_id, node in prompt.items():
            node.pop("is_changed", None)
            node_type = node.get("class_type", "")
            node_inputs = node.get("inputs", {})
            if not node_inputs:
                continue
            label_name = node_inputs.get("name", "")
            if node_type in NODE_TYPE_MAPPING:
                mapping = NODE_TYPE_MAPPING[node_type]
                node["class_type"] = mapping["new_type"]
                node["inputs"] = mapping["new_inputs"].copy()
                if label_name:
                    node["inputs"]["name"] = label_name

    def add_decrypt_node(self, workflow):
        new_node_ids = set()
        self.last_node_id += 1
        encrypt_node = {
            "id": self.last_node_id,
            "type": "RiceRoundDecryptNode",
            "pos": [420, 0],
            "size": [500, 150],
            "flags": {},
            "mode": 0,
            "order": 20,
            "inputs": [],
            "outputs": [
                {
                    "name": "IMAGE",
                    "type": "IMAGE",
                    "links": [],
                    "label": "IMAGE",
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "RiceRoundDecryptNode"},
            "widgets_values": [str(self.template_id), 735127949069071, "randomize"],
        }
        for idx, (owner_id, owner_node) in enumerate(self.input_node_map.items()):
            link_id = owner_node["main_link_id"]
            link_type = owner_node["main_link_type"]
            owner_node["input_anything"] = idx
            input_entry = {
                "name": f"input_anything{idx if idx>0 else''} ({owner_id})",
                "type": "*",
                "link": link_id,
                "label": f"input_anything{idx if idx>0 else''} ({owner_id})",
            }
            if idx == 0:
                input_entry["shape"] = 7
            encrypt_node["inputs"].append(input_entry)
            if link_type not in ["IMAGE", "STRING"]:
                link_type = "STRING"
            links = [link_id, owner_id, 0, self.last_node_id, idx, link_type]
            workflow["links"].append(links)
        new_node_ids.add(self.last_node_id)
        workflow["nodes"].append(encrypt_node)
        workflow["last_node_id"] = self.last_node_id
        return new_node_ids

    def output_file(self, workflow, prefix):
        json_file_path = os.path.join(self.output_folder, f"{prefix}.json")
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(workflow, f, ensure_ascii=False, indent=4)

    def remove_redundant_links(self, workflow):
        delete_links = set()
        for node in workflow["nodes"]:
            node_id = int(node["id"])
            if node_id in self.input_node_map:
                main_link_id = self.input_node_map[node_id]["main_link_id"]
                outputs = node.get("outputs", [])
                if not outputs:
                    continue
                for output in outputs:
                    links = output.get("links", [])
                    if not links:
                        continue
                    for link in links:
                        if link != main_link_id:
                            delete_links.add(link)
                outputs[0]["links"] = [main_link_id]
        workflow["links"] = [
            link
            for link in workflow["links"]
            if isinstance(link, list) and len(link) == 6 and link[0] not in delete_links
        ]

    def replace_choice_template(self, workflow):
        rice_prompt_info = RicePromptInfo()
        for node in workflow["nodes"]:
            node_id = int(node["id"])
            if node.get("type", "") == "RiceRoundAdvancedChoiceNode":
                new_node_type = rice_prompt_info.get_choice_classname(node_id)
                if new_node_type:
                    node["type"] = new_node_type
                else:
                    print(
                        f"Warning: The node {node_id} is not a valid RiceRound Choice node."
                    )
        choice_node_map = {}
        for node_id, node in self.input_node_map.items():
            if node.get("type", "") == "RiceRoundSimpleChoiceNode":
                choice_value = rice_prompt_info.get_choice_value(node_id)
                choice_node_map[node_id] = choice_value
        if "extra" not in workflow:
            workflow["extra"] = {}
        workflow["extra"]["choice_node_map"] = choice_node_map

    def replace_workflow_node(self, workflow):
        NODE_TYPE_MAPPING = {
            "RiceRoundImageBridgeNode": ("RiceRoundOutputImageBridgeNode", ""),
            "RiceRoundSimpleImageNode": ("RiceRoundUploadImageNode", ""),
            "RiceRoundImageNode": ("RiceRoundUploadImageNode", "Image&Mask"),
            "RiceRoundDownloadImageNode": ("RiceRoundImageUrlNode", ""),
            "RiceRoundMaskBridgeNode": ("RiceRoundOutputMaskBridgeNode", ""),
            "RiceRoundDownloadMaskNode": ("RiceRoundMaskUrlNode", ""),
            "RiceRoundIntNode": ("RiceRoundOutputIntNode", ""),
            "RiceRoundFloatNode": ("RiceRoundOutputFloatNode", ""),
            "RiceRoundBooleanNode": ("RiceRoundOutputBooleanNode", ""),
            "RiceRoundStrToBooleanNode": ("RiceRoundOutputTextNode", ""),
            "RiceRoundStrToIntNode": ("RiceRoundOutputTextNode", ""),
            "RiceRoundStrToFloatNode": ("RiceRoundOutputTextNode", ""),
        }
        replace_node_ids = set()
        for node in workflow["nodes"]:
            node_type = node.get("type", "")
            if node_type in NODE_TYPE_MAPPING:
                if "outputs" not in node:
                    raise ValueError(f"Node {node.get('id','unknown')} missing outputs")
                if not node["outputs"] or not isinstance(node["outputs"], list):
                    raise ValueError(
                        f"Invalid outputs format in node {node.get('id','unknown')}"
                    )
                new_type = NODE_TYPE_MAPPING[node_type][0]
                new_name = (
                    new_type
                    if NODE_TYPE_MAPPING[node_type][1] == ""
                    else NODE_TYPE_MAPPING[node_type][1]
                )
                node.update(
                    {
                        "name": new_name,
                        "type": new_type,
                        "outputs": [{"type": "STRING", **node["outputs"][0]}],
                        "properties": {"Node name for S&R": new_name},
                    }
                )
                replace_node_ids.add(int(node["id"]))
        for link in workflow["links"]:
            if len(link) == 6 and link[1] in replace_node_ids:
                link[5] = "STRING"

    def remove_unrelated_nodes(self, workflow, related_node_ids, new_node_ids):
        links = []
        combined_node_ids = related_node_ids.union(new_node_ids)
        for link in workflow["links"]:
            if len(link) == 6:
                if link[1] in combined_node_ids and link[3] in combined_node_ids:
                    links.append(link)
        workflow["links"] = links

    def invalid_new_workflow(self, workflow):
        for node in workflow["nodes"]:
            inputs = node.get("inputs", [])
            for input in inputs:
                link = int(input.get("link", 0))
                owner_id = self.link_owner_map[link]["owner_id"]
                owner_node_type = self.workflow_nodes_dict[owner_id]["type"]
                if owner_node_type in INPUT_NODE_TYPES:
                    raise ValueError(
                        f"Error: The node {node['id']} may have circular references, generation failed."
                    )

    def find_workflow_related_nodes(self, links, input_ids):
        found_ids = set(input_ids)
        stack = list(input_ids)
        while stack:
            current_id = stack.pop()
            for link in links:
                if len(link) == 6 and link[3] == current_id:
                    source_id = link[1]
                    if source_id not in found_ids:
                        if source_id in self.workflow_nodes_dict:
                            found_ids.add(source_id)
                    stack.append(source_id)
        return found_ids

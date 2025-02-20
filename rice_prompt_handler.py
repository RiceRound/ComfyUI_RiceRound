import json
import os
import random
import tempfile
import time
from .rice_def import RiceRoundErrorDef
from server import PromptServer
from .auth_unit import AuthUnit
from .utils import get_local_app_setting_path
from .rice_prompt_info import RicePromptInfo


class RiceRoundPromptHandler:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RiceRoundPromptHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.client_id = ""
            self.task_uuid = ""
            self._initialized = True

    def onprompt_handler(self, json_data):
        "\n        处理传入的 JSON 数据\n        :param json_data: 输入的 JSON 数据，包含各种任务信息\n"
        RicePromptInfo().clear()
        if "prompt" not in json_data:
            return json_data
        has_rice_component = False
        prompt = json_data["prompt"]
        for node in prompt.values():
            class_type = node.get("class_type")
            if class_type in ["RiceRoundEncryptNode", "RiceRoundDecryptNode"]:
                has_rice_component = True
                break
        if has_rice_component:
            user_token, error_msg, error_code = AuthUnit().get_user_token()
            if not user_token:
                if (
                    error_code == RiceRoundErrorDef.HTTP_UNAUTHORIZED
                    or error_code == RiceRoundErrorDef.NO_TOKEN_ERROR
                ):
                    AuthUnit().login_dialog("RiceRound云节点，请先完成登录")
                    json_data["prompt"] = {}
                    return json_data
                else:
                    PromptServer.instance.send_sync(
                        "riceround_toast",
                        {"content": f"无法完成鉴权登录，{error_msg}", "type": "error"},
                    )
                    return json_data
        if "client_id" not in json_data:
            return json_data
        self.client_id = json_data["client_id"]
        if "task_uuid" not in json_data:
            return json_data
        self.task_uuid = json_data["task_uuid"]
        if "template" not in json_data:
            raise Exception("Warning: 'template' is missing.")
        print(
            f"RiceRoundPromptHandler self.client_id={self.client_id!r}{ self.task_uuid=}"
        )
        input_data = json_data["input"] if "input" in json_data else {}
        prompt_data = json_data["prompt"]
        prompt_data = self.replace_output_prompt(prompt_data)
        id_type_map, node_id_map = self.parse_template(json_data["template"])
        prompt_data = self.replace_input_prompt(
            prompt_data, input_data, id_type_map, node_id_map
        )
        print(f"RiceRoundPromptHandler prompt_data={prompt_data!r}")
        json_data["prompt"] = prompt_data
        return json_data

    def parse_template(self, template_data):
        id_type_map = {}
        node_id_map = {}
        elements = template_data["elements"]
        for element in elements:
            id = element["id"]
            node_id_map[id] = element["node_id"]
            id_type_map[id] = element["type"]
        return id_type_map, node_id_map

    def replace_output_prompt(self, prompt_data):
        "\n        替换输出节点中的 task_id\n        :param prompt_data: 任务的 prompt 数据\n        :return: 替换后的 prompt 数据\n"
        for node_id, node in prompt_data.items():
            if node.get("class_type") == "RiceRoundOutputImageNode":
                node["inputs"]["task_id"] = self.task_uuid
            elif node.get("class_type") == "RiceRoundRandomSeedNode":
                node["inputs"]["seed"] = random.randint(0, 999999)
        return prompt_data

    def replace_input_prompt(self, prompt_data, input_data, id_type_map, node_id_map):
        INPUT_TYPE_MAPPING = {
            "text": "text_info",
            "image_upload": "image_url",
            "mask_image_upload": "image_url",
            "mask_upload": "mask_url",
            "number_int": "str",
            "number_float": "str",
            "choice": "default",
            "switch": "str",
        }
        for input_id, value in input_data.items():
            input_type = id_type_map.get(input_id, "")
            input_field = INPUT_TYPE_MAPPING.get(input_type)
            if not input_field:
                print(
                    f"RiceRoundPromptHandler replace_input_prompt unknown input_type {input_type}"
                )
                continue
            node = prompt_data[node_id_map[input_id]]
            node["inputs"][input_field] = str(value)
        if os.environ.get("RICEROUND_DEBUG_SAVE_PROMPT") == "true":
            temp_dir = tempfile.gettempdir()
            with open(f"{temp_dir}//{self.task_uuid}_prompt_data.json", "w") as f:
                json.dump(prompt_data, f, indent=4)
        return prompt_data

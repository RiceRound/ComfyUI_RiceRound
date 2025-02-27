import configparser
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from .auth_unit import AuthUnit
from .rice_url_config import download_template
from server import PromptServer
import re
from .utils import get_local_app_setting_path


class RicePromptInfo:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RicePromptInfo, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if RicePromptInfo._initialized:
            return
        local_app_path = get_local_app_setting_path()
        local_app_path.mkdir(parents=True, exist_ok=True)
        self.config_path = local_app_path / "config.ini"
        self.choice_node_map = {}
        self.auto_overwrite = self._read_config_bool(
            "Settings", "auto_overwrite", False
        )
        self.auto_publish = self._read_config_bool("Settings", "auto_publish", True)
        self.run_client = self._read_config_bool("Settings", "run_client", False)
        self.wait_time = self._read_config_int("Settings", "wait_time", 600)
        self.choice_classname_map = {}
        self.load_choice_node_map()
        RicePromptInfo._initialized = True

    def _read_config_bool(self, section, key, default=False):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding="utf-8")
            return config.getboolean(section, key, fallback=default)
        except Exception as e:
            print(f"Error reading config {section}.{key}: {e}")
            return default

    def _read_config_int(self, section, key, default=0):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding="utf-8")
            return config.getint(section, key, fallback=default)
        except Exception as e:
            print(f"Error reading config {section}.{key}: {e}")
            return default

    def _write_config_bool(self, section, key, value):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding="utf-8")
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, str(value).lower())
            with open(self.config_path, "w", encoding="utf-8") as f:
                config.write(f)
            return True
        except Exception as e:
            print(f"Error writing config {section}.{key}: {e}")
            return False

    def _write_config_int(self, section, key, value):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding="utf-8")
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, str(value))
            with open(self.config_path, "w", encoding="utf-8") as f:
                config.write(f)
            return True
        except Exception as e:
            print(f"Error writing config {section}.{key}: {e}")
            return False

    def set_auto_overwrite(self, auto_overwrite):
        self.auto_overwrite = auto_overwrite
        self._write_config_bool("Settings", "auto_overwrite", auto_overwrite)

    def get_auto_overwrite(self):
        return self.auto_overwrite

    def set_auto_publish(self, auto_publish):
        self.auto_publish = auto_publish
        self._write_config_bool("Settings", "auto_publish", auto_publish)

    def get_auto_publish(self):
        return self.auto_publish

    def set_wait_time(self, wait_time):
        self.wait_time = wait_time
        self._write_config_int("Settings", "wait_time", wait_time)

    def get_wait_time(self):
        return max(self.wait_time, 10)

    def clear(self):
        self.choice_node_map.clear()

    def get_choice_server_folder(self):
        choice_server_folder = get_local_app_setting_path() / "choice_node"
        if not choice_server_folder.exists():
            choice_server_folder.mkdir(parents=True)
        return choice_server_folder

    def load_choice_node_map(self):
        choice_server_folder = self.get_choice_server_folder()
        for file in choice_server_folder.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        print(f"Warning: Invalid JSON structure in file: {file}")
                        continue
                    elements = data.get("elements", [])
                    if not isinstance(elements, list):
                        print(f"Warning: 'elements' is not a list in file: {file}")
                        continue
                    for element in elements:
                        if not isinstance(element, dict):
                            continue
                        if element.get("type") != "choice":
                            continue
                        addition = element.get("addition", {})
                        if not addition or not isinstance(addition, dict):
                            continue
                        if addition.get("node_type") != "RiceRoundAdvancedChoiceNode":
                            continue
                        settings = element.get("settings", {})
                        options = settings.get("options", [])
                        python_class_name = addition.get("python_class_name")
                        if python_class_name and isinstance(options, list):
                            info = copy.deepcopy(addition)
                            info["options_value"] = options
                            self.choice_classname_map[python_class_name] = info
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from file {file}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error processing file {file}: {str(e)}")
                continue

    def install_choice_node(self, template_id):
        user_token, error_msg, error_code = AuthUnit().get_user_token()
        template_file_path = self.get_choice_server_folder() / f"{template_id}.json"
        try:
            download_template(template_id, user_token, template_file_path)
        except Exception as e:
            print(f"failed to download template, {e}")
            return False
        return True

    def get_choice_node_addition(self, node_id):
        info = copy.deepcopy(self.choice_node_map.get(node_id, {}))
        if info and isinstance(info, dict):
            info.pop("options_value", None)
            return info
        return {}

    def get_choice_node_options(self, node_class_name):
        return self.choice_classname_map.get(node_class_name, {}).get(
            "options_value", []
        )

    def get_choice_classname(self, node_id):
        return self.choice_node_map.get(node_id, {}).get("python_class_name", "")

    def get_choice_value(self, node_id):
        return self.choice_node_map.get(node_id, {}).get("options_value", [])

    def set_node_additional_info(self, node_additional_info):
        if node_additional_info and isinstance(node_additional_info, dict):
            self.template_id = node_additional_info.get("template_id", "")
            choice_node_map = node_additional_info.get("choice_node_map", {})
            for node_id, info in choice_node_map.items():
                node_id = int(node_id)
                class_name = info.get("class_name", "")
                info["template_id"] = self.template_id
                info["display_name"] = class_name
                node_type = info.get("node_type", "")
                if node_type == "RiceRoundAdvancedChoiceNode":
                    python_class_name = (
                        f"RiceRoundAdvancedChoiceNode_{self.template_id}_{node_id}"
                    )
                    info["python_class_name"] = python_class_name
                self.choice_node_map[node_id] = info


class RiceEnvConfig:
    def __init__(self):
        0

    def filter_add_cmd(self, add_cmd):
        filtered_add_cmd = []
        skip_next = False
        if not add_cmd:
            return ""
        try:
            for arg in add_cmd.split():
                if skip_next:
                    skip_next = False
                    continue
                if arg in ["--listen", "--port"]:
                    skip_next = True
                    continue
                filtered_add_cmd.append(arg)
        except Exception as e:
            print(f"Error processing add_cmd: {e}")
            return ""
        return " ".join(filtered_add_cmd)

    def _get_python_path(self):
        try:
            return sys.executable.replace("\\", "/").strip("\"'")
        except Exception as e:
            print(f"Error getting Python path: {e}")
            return ""

    def _get_working_directory(self):
        try:
            script_abs_path = os.path.abspath(sys.argv[0]).replace("\\", "/")
            script_dir = os.path.dirname(script_abs_path)
            working_directory = script_dir
            custom_nodes_pattern = re.compile(
                "[/\\\\]custom_nodes[/\\\\]", re.IGNORECASE
            )
            match = custom_nodes_pattern.search(script_dir)
            if match:
                custom_nodes_pos = match.start()
                potential_parent_dir = script_dir[:custom_nodes_pos]
                custom_nodes_dir = os.path.join(potential_parent_dir, "custom_nodes")
                if os.path.isdir(custom_nodes_dir) or os.path.isdir(
                    os.path.join(potential_parent_dir, "Custom_Nodes")
                ):
                    working_directory = potential_parent_dir
            return working_directory.strip("\"'")
        except Exception as e:
            print(f"Error getting working directory: {e}")
            try:
                return os.getcwd().replace("\\", "/").strip("\"'")
            except:
                return ""

    def _get_add_cmd(self):
        try:
            cmd_args = " ".join(sys.argv[1:])
            return self.filter_add_cmd(cmd_args).strip()
        except Exception as e:
            print(f"Error getting command arguments: {e}")
            return ""

    def _get_script_name(self):
        try:
            py_file_pattern = re.compile("[/\\\\]([^/\\\\]+\\.py)", re.IGNORECASE)
            match = py_file_pattern.search(sys.argv[0])
            if match:
                return match.group(1)
            basename = os.path.basename(sys.argv[0]).replace("\\", "/").strip("\"'")
            if re.search("\\.py$", basename, re.IGNORECASE):
                return basename
            else:
                return "main.py"
        except Exception as e:
            print(f"Error getting script name: {e}")
            return "main.py"

    def read_env(self):
        python_path = self._get_python_path()
        working_directory = self._get_working_directory()
        add_cmd = self._get_add_cmd()
        script_name = self._get_script_name()
        return {
            "PythonPath": python_path,
            "WorkingDirectory": working_directory,
            "AddCmd": add_cmd,
            "ScriptName": script_name,
        }

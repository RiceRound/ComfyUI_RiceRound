import os
import sys
import tempfile
import requests
from .rice_def import RiceRoundErrorDef
from .rice_url_config import RiceUrlConfig
from .auth_unit import AuthUnit
from .rice_prompt_info import RiceEnvConfig
from .utils import get_local_app_setting_path


class RiceInstallClient:
    def __init__(self):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.app_path = get_local_app_setting_path()
        (
            self.source_executable_filename,
            self.executable_filename,
        ) = self._get_platform_executables()

    def _get_platform_executables(self):
        "Get platform-specific executable filenames."
        if sys.platform == "win32":
            return "share_client_windows.exe", "share_client.exe"
        elif sys.platform == "darwin":
            return "share_client_mac", "share_client"
        elif sys.platform == "linux":
            return "share_client_linux", "share_client"
        else:
            raise OSError(f"Unsupported platform: {sys.platform}")

    def is_client_running(self):
        if not self.is_client_installed():
            return False
        lock_path = os.path.join(tempfile.gettempdir(), "rice_client.lock")
        if not os.path.exists(lock_path):
            return False
        try:
            import portalocker

            with open(lock_path, "w") as f:
                portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
                portalocker.unlock(f)
                return False
        except portalocker.LockException:
            return True

    def is_client_installed(self):
        if not self.app_path.exists():
            return False
        executable_path = self.app_path / self.executable_filename
        if not executable_path.exists():
            return False
        toml_path = self.app_path / "client.toml"
        if not toml_path.exists():
            return False
        return True

    def repair_client_toml(self, client_toml_path):
        if not client_toml_path.exists():
            return False
        try:
            import tomlkit
            from tomlkit import comment, table, dumps

            env_config = RiceEnvConfig().read_env()
            if not env_config:
                print("Error: Failed to read environment config")
                return False
            if not env_config.get("PythonPath") or not os.path.exists(
                env_config["PythonPath"]
            ):
                print("Error: Invalid Python path in environment config")
                return False
            env_working_dir = env_config.get("WorkingDirectory")
            env_script_name = env_config.get("ScriptName")
            if not env_working_dir or not env_script_name:
                print(
                    "Error: Missing working directory or script name in environment config"
                )
                return False
            if os.path.isabs(env_script_name) and os.path.exists(env_script_name):
                env_script_path = env_script_name
            else:
                env_script_path = os.path.join(env_working_dir, env_script_name)
            if not os.path.exists(env_script_path):
                print("Error: ComfyUI script path does not exist in environment config")
                return False
            with open(client_toml_path, "r", encoding="utf-8") as f:
                toml_data = tomlkit.load(f)
                comfyui_config = toml_data.get("ComfyUI")
                if not comfyui_config or not isinstance(comfyui_config, dict):
                    return False
                script_name = comfyui_config.get("ComfyuiScriptName")
                working_dir = comfyui_config.get("WorkingDirectory")
                if working_dir is None or script_name is None:
                    comfyui_config["WorkingDirectory"] = env_config["WorkingDirectory"]
                    comfyui_config["ComfyuiScriptName"] = env_config["ScriptName"]
                else:
                    if os.path.isabs(script_name) and os.path.exists(script_name):
                        script_path = script_name
                    else:
                        script_path = os.path.join(working_dir, script_name)
                    if not os.path.exists(script_path):
                        comfyui_config["WorkingDirectory"] = env_config[
                            "WorkingDirectory"
                        ]
                        comfyui_config["ComfyuiScriptName"] = env_config["ScriptName"]
                python_path = comfyui_config.get("PythonPath")
                if python_path is None or not os.path.exists(python_path):
                    comfyui_config["PythonPath"] = env_config["PythonPath"]
            with open(client_toml_path, "w", encoding="utf-8") as f:
                f.write(dumps(toml_data))
            return True
        except Exception as e:
            print(f"Error repairing client.toml: {str(e)}")
            return False

    def _generate_toml_config(
        self, secret_token, comfyui_port=6607, local_server_port=6608
    ):
        "Internal function to generate TOML configuration.\n        \n        Args:\n            secret_token: The authentication token\n            comfyui_port: Port for ComfyUI, defaults to 6607\n            local_server_port: Port for local server, defaults to 6608\n            \n        Returns:\n            str: The generated TOML content\n"
        try:
            import tomlkit
            from tomlkit import comment, table, dumps

            env_config = RiceEnvConfig().read_env()
            config = tomlkit.document()
            config.add(comment("日志级别设置"))
            config.add(comment("可选值: 'debug', 'info', 'warn', 'error'"))
            config["LogLevel"] = "info"
            config.add(comment("机器码，非常重要，用于登录鉴权"))
            config.add(comment("在官网可以获取自己的机器码，普通用户也可以由管理员授予"))
            config["SecretToken"] = secret_token
            config.add(comment("本地服务端口"))
            config.add(comment("用于本地服务端口，通常为 6608"))
            config["Port"] = local_server_port
            comfyui_table = table()
            comfyui_table.add(comment("ComfyUI 监听的端口"))
            comfyui_table.add(comment("端口号，默认为 6607"))
            comfyui_table["Port"] = comfyui_port
            comfyui_table.add(comment("Python 解释器路径"))
            comfyui_table.add(comment("这里填写你安装的 Python 解释器路径，确保 Python 环境已经配置好"))
            comfyui_table["PythonPath"] = str(env_config["PythonPath"])
            comfyui_table.add(comment("ComfyUI 脚本的文件名"))
            comfyui_table.add(comment("这里填写 ComfyUI 的启动脚本名，通常是 'main.py'"))
            comfyui_table["ComfyuiScriptName"] = env_config["ScriptName"]
            comfyui_table.add(comment("ComfyUI 工作目录"))
            comfyui_table.add(comment("这里填写 ComfyUI 所在的目录路径"))
            comfyui_table["WorkingDirectory"] = str(env_config["WorkingDirectory"])
            comfyui_table.add(comment("环境命令，用于激活相关环境"))
            comfyui_table.add(comment("例如可以填写 conda 环境的激活命令 conda activate comfyui"))
            comfyui_table["EnvCmd"] = ""
            comfyui_table.add(comment("启动时附加的命令行参数"))
            comfyui_table.add(comment("可根据需要添加，常用的如 '--disable-metadata'"))
            comfyui_table["AddCmd"] = env_config["AddCmd"]
            config["ComfyUI"] = comfyui_table
            return dumps(config)
        except Exception as e:
            print(f"Error generating TOML content: {str(e)}")
            raise e

    def install_client_toml(self, comfyui_port, local_server_port, secret_token):
        try:
            os.makedirs(self.app_path, exist_ok=True)
            toml_content = self._generate_toml_config(
                secret_token, comfyui_port, local_server_port
            )
            client_toml_path = self.app_path / "client.toml"
            with open(client_toml_path, "w", encoding="utf-8") as f:
                f.write(toml_content)
            return True
        except Exception as e:
            print(f"Error writing client.toml: {str(e)}")
            return False

    def export_toml(self, secret_token):
        "Generate and return TOML configuration content."
        return self._generate_toml_config(secret_token)

    def auto_fix_toml(self, comfyui_port=6607, local_server_port=8689):
        toml_path = self.app_path / "client.toml"
        if not toml_path.exists():
            secret_token, error_message, error_code = self.get_secret_token()
            if not secret_token:
                return (
                    error_code
                    if error_code != RiceRoundErrorDef.SUCCESS
                    else RiceRoundErrorDef.ERROR_SECRET_TOKEN,
                    error_message,
                )
            if not self.install_client_toml(
                comfyui_port, local_server_port, secret_token
            ):
                return RiceRoundErrorDef.ERROR_INSTALL_CLIENT_TOML, "安装client.toml失败"
        else:
            self.repair_client_toml(toml_path)

    def get_secret_token(self):
        token, error_message, error_code = AuthUnit().get_user_token()
        if not token:
            return None, error_message, error_code
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        try:
            response = requests.get(
                RiceUrlConfig().machine_bind_key_url, headers=headers, timeout=10
            )
            if response.status_code != 200:
                error_code = response.status_code
                return (
                    None,
                    "获取密钥失败",
                    RiceRoundErrorDef.calc_error_code(
                        RiceRoundErrorDef.ERROR_MACHINE_CODE_BASE, error_code
                    ),
                )
            response_data = response.json()
            if response_data.get("code") != 0:
                return None, "获取密钥失败: 响应码不为0", RiceRoundErrorDef.ERROR_SECRET_TOKEN
            secret_token = response_data.get("data", {}).get("key")
            if not secret_token:
                return None, "获取密钥失败: 密钥为空", RiceRoundErrorDef.ERROR_SECRET_TOKEN
            return secret_token, "", 0
        except Exception as e:
            return None, "获取密钥失败" + str(e), RiceRoundErrorDef.ERROR_SECRET_TOKEN

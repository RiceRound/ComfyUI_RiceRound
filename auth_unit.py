import logging
import os
import time
import requests
import configparser
from .rice_def import RiceRoundErrorDef
from .utils import get_local_app_setting_path, get_machine_id, generate_random_string
from .rice_url_config import RiceUrlConfig
from server import PromptServer


class AuthUnit:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AuthUnit, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.machine_id = get_machine_id()
            local_app_path = get_local_app_setting_path()
            local_app_path.mkdir(parents=True, exist_ok=True)
            self.config_path = local_app_path / "config.ini"
            self.last_check_time = 0
            self.initialized = True
            self.user_id = 0

    def empty_token(self, need_clear=False):
        self.token = ""
        self.last_check_time = 0
        if need_clear:
            self.clear_user_token()

    def get_user_token(self):
        self.token = self.read_user_token()
        if (
            time.time() - self.last_check_time > 120
            and self.token
            and len(self.token) > 50
        ):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",
                }
                response = requests.get(
                    RiceUrlConfig().get_info_url, headers=headers, timeout=10
                )
                if response.status_code == 200:
                    user_info = response.json()
                    try:
                        self.user_id = int(user_info.get("user_id", 0) or 0)
                    except (ValueError, TypeError):
                        self.user_id = 0
                    self.last_check_time = time.time()
                    return self.token, "", RiceRoundErrorDef.SUCCESS
                else:
                    logging.warn(
                        f"get_user_token failed, {response.status_code} {response.text}"
                    )
                    error_message = "登录结果错误"
                    error_code = RiceRoundErrorDef.UNKNOWN_ERROR
                    try:
                        response_data = response.json()
                        if "message" in response_data:
                            error_message = response_data["message"]
                    except ValueError:
                        pass
                    if response.status_code == 401:
                        error_message = "登录已过期，请重新登录"
                        error_code = RiceRoundErrorDef.HTTP_UNAUTHORIZED
                    elif response.status_code == 500:
                        error_message = "服务器内部错误，请稍后重试"
                        error_code = RiceRoundErrorDef.HTTP_INTERNAL_ERROR
                    elif response.status_code == 503:
                        error_message = "服务不可用，请稍后重试"
                        error_code = RiceRoundErrorDef.HTTP_SERVICE_UNAVAILABLE
                    self.empty_token(response.status_code == 401)
                    return None, error_message, error_code
            except requests.exceptions.Timeout:
                self.empty_token()
                return None, "请求超时，请检查网络连接", RiceRoundErrorDef.HTTP_TIMEOUT
            except requests.exceptions.ConnectionError:
                self.empty_token()
                return None, "网络连接失败，请检查网络", RiceRoundErrorDef.NETWORK_ERROR
            except requests.exceptions.RequestException as e:
                self.empty_token()
                return None, f"请求失败: {str(e)}", RiceRoundErrorDef.REQUEST_ERROR
        if self.token and len(self.token) > 50:
            return self.token, "", RiceRoundErrorDef.SUCCESS
        return None, "未读取到有效的token，请重新登录", RiceRoundErrorDef.NO_TOKEN_ERROR

    def get_user_info(self):
        _, error_message, error_code = self.get_user_token()
        if error_code == RiceRoundErrorDef.SUCCESS and self.user_id:
            return error_code, self.user_id
        else:
            return error_code, error_message

    def login_dialog(self, title=""):
        self.client_key = generate_random_string(8)
        PromptServer.instance.send_sync(
            "riceround_login_dialog",
            {
                "machine_id": self.machine_id,
                "client_key": self.client_key,
                "title": title,
            },
        )

    def read_user_token(self):
        if not os.path.exists(self.config_path):
            return ""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding="utf-8")
            return config.get("Auth", "user_token", fallback="")
        except Exception as e:
            print(f"Error reading token: {e}")
            return ""

    def set_user_token(self, user_token, client_key):
        if not client_key or self.client_key != client_key:
            logging.warn(f"client_key is not match, {self.client_key} != {client_key}")
            return
        if not user_token:
            user_token = ""
            print("user_token is empty")
        self.save_user_token(user_token)

    def save_user_token(self, user_token):
        try:
            config = configparser.ConfigParser()
            try:
                if os.path.exists(self.config_path):
                    config.read(self.config_path, encoding="utf-8")
            except Exception as read_error:
                print(f"Warning: Error reading existing config: {read_error}")
            if "Auth" not in config:
                config.add_section("Auth")
            config["Auth"]["user_token"] = user_token
            with open(self.config_path, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving token: {e}")
            raise RuntimeError(f"Failed to save token: {e}")

    def set_long_token(self, long_token):
        if not long_token:
            return
        self.save_user_token(long_token)
        self.client_key = ""

    def clear_user_token(self):
        PromptServer.instance.send_sync(
            "riceround_clear_user_info", {"clear_key": "all"}
        )
        if os.path.exists(self.config_path):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_path, encoding="utf-8")
                if "Auth" not in config:
                    return
                if "user_token" not in config["Auth"]:
                    return
                config["Auth"]["user_token"] = ""
                with open(self.config_path, "w", encoding="utf-8") as f:
                    config.write(f)
            except Exception as e:
                print(f"Error clearing token: {e}")
                raise RuntimeError(f"Failed to clear token: {e}")

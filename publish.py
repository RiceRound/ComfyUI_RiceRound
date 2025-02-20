import json
import os
import requests
from .rice_prompt_info import RicePromptInfo
from .rice_url_config import RiceUrlConfig, user_upload_imagefile
from server import PromptServer
from aiohttp import web
import time
from .message_holder import MessageHolder


class Publish:
    def __init__(self, publish_folder):
        self.publish_folder = publish_folder

    def publish(
        self, user_token, template_id, project_name, preview_path, publish_file
    ):
        if not os.path.exists(publish_file):
            raise ValueError(f"Publish file not found: {publish_file}")
        overwrite = False
        error_code, error_msg = self._check_workflow(user_token, template_id)
        if error_code == 1:
            overwrite = True
            auto_overwrite = RicePromptInfo().get_auto_overwrite()
            if not auto_overwrite:
                json_content = {
                    "title": "已经存在相同template_id的数据，是否覆盖？注意，如果接口做了调整，覆盖后老用户将无法使用！",
                    "icon": "info",
                    "confirmButtonText": "覆盖",
                    "cancelButtonText": "取消",
                    "showCancelButton": True,
                    "timer": 50000,
                }
                PromptServer.instance.send_sync(
                    "riceround_dialog",
                    {"json_content": json.dumps(json_content), "id": template_id},
                )
                msg_result = MessageHolder.waitForMessage(template_id, timeout=60000)
                try:
                    result_code = int(msg_result)
                except ValueError:
                    print("riceround upload cancel: Invalid response format")
                    return False
                if result_code != 1:
                    print("riceround upload cancel: User rejected overwrite")
                    return False
        elif error_code != 0:
            print(f"riceround upload failed: {error_msg}")
            PromptServer.instance.send_sync(
                "riceround_toast", {"content": f"异常情况，{error_msg}", "type": "error"}
            )
            return False
        preview_image_url = None
        if not overwrite:
            if os.path.exists(preview_path):
                preview_image_url = user_upload_imagefile(preview_path, user_token)
        success, message = self._upload_workflow(
            user_token, template_id, project_name, preview_image_url, publish_file
        )
        if success:
            PromptServer.instance.send_sync(
                "riceround_toast", {"content": "上传成功", "type": "info", "duration": 5000}
            )
        else:
            PromptServer.instance.send_sync(
                "riceround_toast",
                {"content": f"上传失败: {message}", "type": "error", "duration": 5000},
            )
        return success

    def _check_workflow(self, user_token, template_id):
        headers = {"Authorization": f"Bearer {user_token}"}
        params = {"id": template_id, "action": "check"}
        try:
            response = requests.get(
                RiceUrlConfig().publisher_workflow_url, params=params, headers=headers
            )
            if response.status_code == 200:
                response_data = response.json()
                error_code = response_data.get("code")
                error_msg = response_data.get("message")
                return error_code, error_msg
            else:
                return -1, ""
        except Exception as e:
            return -1, str(e)

    def _upload_workflow(
        self, user_token, template_id, project_name, preview_image_url, publish_file
    ):
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            json_data = {
                "template_id": template_id,
                "title": project_name,
                "main_image_url": preview_image_url or "",
            }
            with open(publish_file, "rb") as f:
                files = {"workflow_file": ("workflow", f, "application/octet-stream")}
                form_data = {"data": json.dumps(json_data), "source": "comfyui"}
                response = requests.put(
                    RiceUrlConfig().publisher_workflow_url,
                    headers=headers,
                    files=files,
                    data=form_data,
                )
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code") == 0:
                    return True, "Success"
                else:
                    return False, response_data.get("message", "Unknown error")
            else:
                return False, f"Server returned status code: {response.status_code}"
        except Exception as e:
            return False, str(e)

from enum import IntEnum
import json
import os
from PIL import Image
from io import BytesIO
import numpy as np
import requests
from urllib.parse import urljoin
from .utils import get_local_app_setting_path

DEFAULT_SUBDOMAIN = "api" if os.getenv("RICE_ROUND_DEBUG") != "true" else "test"
_URL_PREFIX = os.getenv("RICE_ROUND_URL_PREFIX", "")
DEFAULT_URL_PREFIX = (
    _URL_PREFIX
    if _URL_PREFIX and len(_URL_PREFIX) > 10
    else f"https://{DEFAULT_SUBDOMAIN}.riceround.online"
)
DEFAULT_WS_PREFIX = f"wss://{DEFAULT_SUBDOMAIN}.riceround.online"


class UploadType(IntEnum):
    TEMPLATE_PUBLISH_IMAGE = 1
    USER_UPLOAD_TASK_IMAGE = 2
    MACHINE_TASK_RESULT = 1000


class RiceUrlConfig:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RiceUrlConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True

    def get_server_url(self, url_path):
        return urljoin(DEFAULT_URL_PREFIX, url_path)

    def get_ws_url(self, url_path):
        return urljoin(DEFAULT_WS_PREFIX, url_path)

    @property
    def machine_upload_sign_url(self):
        return self.get_server_url("/api/machine_client/upload_image_sign_url")

    @property
    def user_upload_sign_url(self):
        return self.get_server_url("/api/user/upload_sign_url")

    @property
    def prompt_task_url(self):
        return self.get_server_url("/api/workflow/add_task")

    @property
    def preview_refresh_url(self):
        return self.get_server_url("/api/workflow/refresh_preview")

    @property
    def task_ws_url(self):
        return self.get_ws_url("/api/workflow/task_websocket")

    @property
    def workflow_preview_url(self):
        return self.get_server_url("/api/workflow/refresh_preview")

    @property
    def get_info_url(self):
        return self.get_server_url("/api/workflow/get_info")

    @property
    def machine_bind_key_url(self):
        return self.get_server_url("/api/machine_bind/key")

    @property
    def workflow_template_url(self):
        return self.get_server_url("/api/workflow/get_template")

    @property
    def publisher_workflow_url(self):
        return self.get_server_url("/api/publisher/workflow")


def user_upload_imagefile(image_file_path, user_token):
    if not os.path.exists(image_file_path):
        raise ValueError(f"Image file not found: {image_file_path}")
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    file_extension = os.path.splitext(image_file_path)[1].lower()
    if file_extension not in content_types:
        raise ValueError(
            f"Unsupported image format: {file_extension}. Supported formats: {', '.join(content_types.keys())}"
        )
    content_type = content_types[file_extension]
    upload_sign_url = RiceUrlConfig().user_upload_sign_url
    headers = {"Authorization": f"Bearer {user_token}"}
    params = {
        "upload_type": UploadType.USER_UPLOAD_TASK_IMAGE.value,
        "file_type": content_type,
    }
    response = requests.get(upload_sign_url, headers=headers, params=params)
    upload_url = ""
    download_url = ""
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("code") == 0:
            upload_url = response_data.get("data", {}).get("upload_sign_url", "")
            download_url = response_data.get("data", {}).get("download_url", "")
    else:
        raise ValueError(
            f"Failed to get upload URL. Status code: {response.status_code}"
        )
    if not upload_url or not download_url:
        raise ValueError("Failed to get upload URL. Upload sign URL is empty")
    try:
        with open(image_file_path, "rb") as f:
            image_data = f.read()
        response = requests.put(
            upload_url, data=image_data, headers={"Content-Type": content_type}
        )
        if response.status_code == 200:
            return download_url
        else:
            raise ValueError(
                f"Failed to upload image. Status code: {response.status_code}"
            )
    except IOError as e:
        raise ValueError(f"Failed to read image file: {str(e)}")


def user_upload_image(image, user_token):
    upload_sign_url = RiceUrlConfig().user_upload_sign_url
    headers = {"Authorization": f"Bearer {user_token}"}
    params = {
        "upload_type": UploadType.USER_UPLOAD_TASK_IMAGE.value,
        "file_type": "image/png",
    }
    response = requests.get(upload_sign_url, headers=headers, params=params)
    upload_url = ""
    download_url = ""
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("code") == 0:
            upload_url = response_data.get("data", {}).get("upload_sign_url", "")
            download_url = response_data.get("data", {}).get("download_url", "")
    else:
        raise ValueError(f"failed to upload image. Status code: {response.status_code}")
    if not upload_url or not download_url:
        raise ValueError(f"failed to upload image. upload_sign_url is empty")
    i = 255.0 * image.cpu().numpy()
    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
    bytesIO = BytesIO()
    img.save(bytesIO, format="PNG", quality=95, compress_level=1)
    send_bytes = bytesIO.getvalue()
    response = requests.put(
        upload_sign_url, data=send_bytes, headers={"Content-Type": "image/png"}
    )
    if response.status_code == 200:
        return download_url
    else:
        print(f"failed to upload image. Status code: {response.status_code}")
        raise ValueError(f"failed to upload image. Status code: {response.status_code}")


def machine_upload_image(image, task_id):
    upload_image_sign_url = RiceUrlConfig().machine_upload_sign_url
    print(f"upload_image_sign_url: {upload_image_sign_url}")
    i = 255.0 * image.cpu().numpy()
    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
    bytesIO = BytesIO()
    img.save(bytesIO, format="PNG", quality=95, compress_level=1)
    send_bytes = bytesIO.getvalue()
    upload_url = ""
    download_url = ""
    params = {
        "upload_type": UploadType.MACHINE_TASK_RESULT.value,
        "file_type": "image/png",
        "task_id": task_id,
    }
    response = requests.get(upload_image_sign_url, params=params)
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("code") == 0:
            upload_url = response_data.get("data", {}).get("upload_sign_url", "")
            download_url = response_data.get("data", {}).get("download_url", "")
    else:
        print(
            f"failed to upload image. Status code: {response.status_code}, Response: {response.text}"
        )
        raise ValueError(f"failed to upload image. Status code: {response.status_code}")
    if not upload_url or not download_url:
        raise ValueError(f"failed to upload image. upload_sign_url is empty")
    response = requests.put(
        upload_url, data=send_bytes, headers={"Content-Type": "image/png"}
    )
    if response.status_code == 200:
        return download_url
    else:
        print(
            f"failed to upload image. Status code: {response.status_code}, Response: {response.text}"
        )
        raise ValueError(f"failed to upload image. Status code: {response.status_code}")


def download_template(template_id, user_token, save_path):
    workflow_template_url = RiceUrlConfig().workflow_template_url
    headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
    params = {"template_id": template_id}
    response = requests.get(workflow_template_url, headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(f"Failed to get template. Status code: {response.status_code}")
    response_data = response.json()
    if response_data.get("code") != 0:
        raise ValueError(f"Failed to get template. Error: {response_data.get('msg')}")
    download_url = response_data.get("data", {}).get("download_url")
    if not download_url:
        raise ValueError("Template download URL is empty")
    template_response = requests.get(download_url)
    if template_response.status_code != 200:
        raise ValueError(
            f"Failed to download template. Status code: {template_response.status_code}"
        )
    try:
        template_data = template_response.json()
        if template_data.get("template_id") != template_id:
            raise ValueError(
                f"Template ID mismatch. Expected: {template_id}, Got: {template_data.get('template_id')}"
            )
        with open(save_path, "wb") as file:
            file.write(template_response.content)
        return template_data
    except json.JSONDecodeError:
        raise ValueError("Failed to parse template JSON data")

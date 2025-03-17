import logging
import platform
import random
import sys
from urllib.parse import unquote
import asyncio
import aiohttp
from .utils import get_local_app_setting_path, restart_comfyui
from server import PromptServer
from .input_node import *
from .output_node import *
from .encrypt_node import *
from .auth_unit import AuthUnit
from aiohttp import web
from functools import partial
from .rice_prompt_handler import RiceRoundPromptHandler
from .rice_url_config import RiceUrlConfig
from .rice_prompt_info import RiceEnvConfig, RicePromptInfo


def create_dynamic_nodes(base_class):
    rice_prompt_info = RicePromptInfo()
    dynamic_classes = {}
    for node_name, info in rice_prompt_info.choice_classname_map.items():
        class_name = node_name
        category = "RiceRound/Advanced/Choice"
        dynamic_class = type(
            class_name,
            (base_class,),
            {"__node_name__": node_name, "CATEGORY": category},
        )
        dynamic_classes[class_name] = {
            "dynamic_class": dynamic_class,
            "display_name": info.get("display_name", class_name),
        }
    return dynamic_classes


dynamic_choice_nodes = create_dynamic_nodes(RiceRoundBaseChoiceNode)
NODE_CLASS_MAPPINGS = {
    "RiceRoundSimpleChoiceNode": RiceRoundSimpleChoiceNode,
    "RiceRoundAdvancedChoiceNode": RiceRoundAdvancedChoiceNode,
    "RiceRoundImageBridgeNode": RiceRoundImageBridgeNode,
    "RiceRoundSimpleImageNode": RiceRoundSimpleImageNode,
    "RiceRoundImageNode": RiceRoundImageNode,
    "RiceRoundDownloadImageAndMaskNode": RiceRoundDownloadImageAndMaskNode,
    "RiceRoundDownloadImageNode": RiceRoundDownloadImageNode,
    "RiceRoundRandomSeedNode": RiceRoundRandomSeedNode,
    "RiceRoundInputTextNode": RiceRoundInputTextNode,
    "RiceRoundMaskBridgeNode": RiceRoundMaskBridgeNode,
    "RiceRoundDownloadMaskNode": RiceRoundDownloadMaskNode,
    "RiceRoundIntNode": RiceRoundIntNode,
    "RiceRoundFloatNode": RiceRoundFloatNode,
    "RiceRoundBooleanNode": RiceRoundBooleanNode,
    "RiceRoundStrToIntNode": RiceRoundStrToIntNode,
    "RiceRoundStrToFloatNode": RiceRoundStrToFloatNode,
    "RiceRoundStrToBooleanNode": RiceRoundStrToBooleanNode,
    "RiceRoundDecryptNode": RiceRoundDecryptNode,
    "RiceRoundOutputImageBridgeNode": RiceRoundOutputImageBridgeNode,
    "RiceRoundImageUrlNode": RiceRoundImageUrlNode,
    "RiceRoundUploadImageNode": RiceRoundUploadImageNode,
    "RiceRoundOutputMaskBridgeNode": RiceRoundOutputMaskBridgeNode,
    "RiceRoundOutputIntNode": RiceRoundOutputIntNode,
    "RiceRoundOutputFloatNode": RiceRoundOutputFloatNode,
    "RiceRoundOutputBooleanNode": RiceRoundOutputBooleanNode,
    "RiceRoundOutputTextNode": RiceRoundOutputTextNode,
    "RiceRoundEncryptNode": RiceRoundEncryptNode,
    "RiceRoundOutputImageNode": RiceRoundOutputImageNode,
    **{name: cls["dynamic_class"] for (name, cls) in dynamic_choice_nodes.items()},
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RiceRoundSimpleChoiceNode": "Simple Choice",
    "RiceRoundAdvancedChoiceNode": "Advanced Choice",
    "RiceRoundImageBridgeNode": "Image Bridge",
    "RiceRoundSimpleImageNode": "Simple Image",
    "RiceRoundImageNode": "Image & Mask",
    "RiceRoundDownloadImageAndMaskNode": "Download Image&Mask",
    "RiceRoundDownloadImageNode": "Download Image",
    "RiceRoundRandomSeedNode": "Random Seed",
    "RiceRoundInputTextNode": "Input Text",
    "RiceRoundMaskBridgeNode": "Mask Bridge",
    "RiceRoundDownloadMaskNode": "Download Mask",
    "RiceRoundIntNode": "RiceRound Int",
    "RiceRoundFloatNode": "RiceRound Float",
    "RiceRoundBooleanNode": "RiceRound Boolean",
    "RiceRoundStrToIntNode": "RiceRound Str To Int",
    "RiceRoundStrToFloatNode": "RiceRound Str To Float",
    "RiceRoundStrToBooleanNode": "RiceRound Str To Boolean",
    "RiceRoundDecryptNode": "RiceRound Cloud",
    "RiceRoundOutputImageBridgeNode": "Output Image Bridge",
    "RiceRoundImageUrlNode": "Image URL",
    "RiceRoundUploadImageNode": "Upload Image",
    "RiceRoundOutputMaskBridgeNode": "Output Mask Bridge",
    "RiceRoundOutputIntNode": "Output Int",
    "RiceRoundOutputFloatNode": "Output Float",
    "RiceRoundOutputBooleanNode": "Output Boolean",
    "RiceRoundOutputTextNode": "Output Text",
    "RiceRoundEncryptNode": "RiceRound Publish",
    "RiceRoundOutputImageNode": "Output Image",
    **{name: cls["display_name"] for (name, cls) in dynamic_choice_nodes.items()},
}
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAMES_MAPPINGS", "WEB_DIRECTORY"]
handler_instance = RiceRoundPromptHandler()
onprompt_callback = partial(handler_instance.onprompt_handler)
PromptServer.instance.add_on_prompt_handler(onprompt_callback)
routes = PromptServer.instance.routes
url_config = RiceUrlConfig()
workspace_path = os.path.join(os.path.dirname(__file__))
dist_path = os.path.join(workspace_path, "static")
if os.path.exists(dist_path):
    PromptServer.instance.app.add_routes(
        [aiohttp.web.static("/riceround/static", dist_path)]
    )


@routes.post("/riceround/auth_callback")
async def auth_callback(request):
    auth_query = await request.json()
    token = auth_query.get("token", "")
    client_key = auth_query.get("client_key", "")
    logging.info(f"### auth_callback: {token} {client_key}")
    if token and client_key:
        token = unquote(token)
        client_key = unquote(client_key)
        AuthUnit().set_user_token(token, client_key)
    return aiohttp.web.json_response({"status": "success"}, status=200)


@routes.post("/riceround/set_long_token")
async def set_long_token(request):
    data = await request.json()
    long_token = data.get("long_token", "")
    if long_token:
        AuthUnit().save_user_token(long_token)
    return aiohttp.web.json_response({"status": "success"}, status=200)


@routes.post("/riceround/set_node_additional_info")
async def set_node_additional_info(request):
    additional_info = await request.json()
    RicePromptInfo().set_node_additional_info(additional_info)
    return web.json_response({}, status=200)


@routes.get("/riceround/open_folder")
async def open_folder(request):
    if request.remote not in ("127.0.0.1", "::1"):
        return web.json_response({"error": "Unauthorized access"}, status=403)
    id = request.query.get("id", "")
    folder = None
    if id == "1":
        folder = get_local_app_setting_path()
        if not folder.exists():
            return web.json_response({"error": "Folder does not exist"}, status=404)
    elif id == "2":
        folder = RicePromptInfo().get_choice_server_folder()
        if not folder.exists():
            return web.json_response({"error": "Folder does not exist"}, status=404)
    if folder:
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(folder)
            return web.json_response({"status": "success"}, status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)


@routes.get("/riceround/get_current_env_config")
async def save_current_env_config(request):
    if request.remote not in ("127.0.0.1", "::1"):
        return web.json_response({"error": "Unauthorized access"}, status=403)
    env_info = RiceEnvConfig().read_env()
    return web.json_response(env_info, status=200)


@routes.get("/riceround/logout")
async def logout(request):
    AuthUnit().clear_user_token()
    return aiohttp.web.json_response({"status": "success"}, status=200)


@routes.post("/riceround/set_auto_overwrite")
async def set_auto_overwrite(request):
    data = await request.json()
    auto_overwrite = data.get("auto_overwrite")
    RicePromptInfo().set_auto_overwrite(auto_overwrite)
    return web.json_response({"status": "success"}, status=200)


@routes.post("/riceround/set_auto_publish")
async def set_auto_publish(request):
    data = await request.json()
    auto_publish = data.get("auto_publish")
    RicePromptInfo().set_auto_publish(auto_publish)
    return web.json_response({"status": "success"}, status=200)


@routes.post("/riceround/set_wait_time")
async def set_wait_time(request):
    data = await request.json()
    wait_time = data.get("wait_time")
    RicePromptInfo().set_wait_time(wait_time)
    return web.json_response({"status": "success"}, status=200)


@routes.post("/riceround/install_choice_node")
async def install_choice_node(request):
    async def delayed_restart():
        await asyncio.sleep(3)
        restart_comfyui()

    data = await request.json()
    template_id = data.get("template_id")
    need_reboot = data.get("need_reboot", False)
    if not template_id:
        return aiohttp.web.json_response(
            {"status": "failed", "message": "template_id is required"}, status=400
        )
    if RicePromptInfo().install_choice_node(template_id):
        if need_reboot:
            asyncio.create_task(delayed_restart())
        return aiohttp.web.json_response(
            {
                "status": "success",
                "message": "Installation successful, server will restart in 3 seconds",
            },
            status=200,
        )
    return aiohttp.web.json_response(
        {"status": "failed", "message": "Installation failed"}, status=400
    )


@routes.post("/riceround/export_toml")
async def export_toml(request):
    data = await request.json()
    secret_token = data.get("secret_token")
    if not secret_token:
        return aiohttp.web.json_response(
            {"status": "failed", "message": "secret_token is required"}, status=400
        )
    try:
        from .rice_install_client import RiceInstallClient

        toml_content = RiceInstallClient().export_toml(secret_token)
        return aiohttp.web.Response(
            body=toml_content.encode("utf-8"),
            headers={
                "Content-Type": "application/toml",
                "Content-Disposition": 'attachment; filename="client.toml"',
            },
        )
    except Exception as e:
        return aiohttp.web.json_response(
            {"status": "failed", "message": str(e)}, status=400
        )


@routes.get("/riceround/fix_toml")
async def fix_toml(request):
    try:
        from .rice_install_client import RiceInstallClient

        RiceInstallClient().auto_fix_toml()
        return aiohttp.web.json_response({"status": "success"}, status=200)
    except Exception as e:
        return aiohttp.web.json_response(
            {"status": "failed", "message": str(e)}, status=400
        )


is_on_riceround = False
client_random = None
if os.getenv("RICE_ROUND_SERVER") == "true":
    is_on_riceround = True
if is_on_riceround:
    client_random = os.getenv("RICE_ROUND_CLIENT_RANDOM")


@web.middleware
async def check_login_status(request, handler):
    if is_on_riceround:
        if request.path.startswith("/internal/"):
            return await handler(request)
        if (
            request.headers.get("owner") == "share_client"
            and request.headers.get("client_random") == client_random
        ):
            return await handler(request)
        else:
            try:
                headers = dict(request.headers)
                logging.warn(f"### check_login_status failed - Headers: {headers}")
            except Exception as e:
                logging.warn(
                    f"### check_login_status failed - Error parsing request: {str(e)}"
                )
        return web.json_response({"error": "Access denied"}, status=403)
    return await handler(request)


if is_on_riceround == True:
    PromptServer.instance.app.middlewares.append(check_login_status)

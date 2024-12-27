_d='RiceRoundTempTokenNode'
_c='RiceRoundOutputImageNode'
_b='RiceRoundEncryptNode'
_a='RiceRoundOutputTextNode'
_Z='RiceRoundOutputBooleanNode'
_Y='RiceRoundOutputFloatNode'
_X='RiceRoundOutputIntNode'
_W='RiceRoundOutputMaskBridgeNode'
_V='RiceRoundUploadImageNode'
_U='RiceRoundImageUrlNode'
_T='RiceRoundOutputImageBridgeNode'
_S='RiceRoundDecryptNode'
_R='RiceRoundStrToBooleanNode'
_Q='RiceRoundStrToFloatNode'
_P='RiceRoundStrToIntNode'
_O='RiceRoundBooleanNode'
_N='RiceRoundFloatNode'
_M='RiceRoundIntNode'
_L='RiceRoundDownloadMaskNode'
_K='RiceRoundMaskBridgeNode'
_J='RiceRoundInputTextNode'
_I='RiceRoundRandomSeedNode'
_H='RiceRoundDownloadImageNode'
_G='RiceRoundSimpleImageNode'
_F='RiceRoundImageBridgeNode'
_E='RiceRoundDebugNode'
_D='RiceRoundAdvancedChoiceNode'
_C='RiceRoundSimpleChoiceNode'
_B='dynamic_class'
_A='display_name'
import platform,random
from urllib.parse import unquote
import subprocess
from server import PromptServer
from.input_node import*
from.output_node import*
from.encrypt_node import*
from.auth_unit import AuthUnit
from aiohttp import web
from functools import partial
from.rice_prompt_handler import RiceRoundPromptHandler
from.rice_url_config import RiceUrlConfig
from.rice_prompt_info import RiceEnvConfig,RicePromptInfo
def create_dynamic_nodes(base_class):
	rice_prompt_info=RicePromptInfo();dynamic_classes={}
	for(node_name,info)in rice_prompt_info.choice_classname_map.items():class_name=node_name;category='RiceRound/Advanced/Choice';dynamic_class=type(class_name,(base_class,),{'__node_name__':node_name,'CATEGORY':category});dynamic_classes[class_name]={_B:dynamic_class,_A:info.get(_A,class_name)}
	return dynamic_classes
dynamic_choice_nodes=create_dynamic_nodes(RiceRoundBaseChoiceNode)
NODE_CLASS_MAPPINGS={_C:RiceRoundSimpleChoiceNode,_D:RiceRoundAdvancedChoiceNode,_E:RiceRoundDebugNode,_F:RiceRoundImageBridgeNode,_G:RiceRoundSimpleImageNode,_H:RiceRoundDownloadImageNode,_I:RiceRoundRandomSeedNode,_J:RiceRoundInputTextNode,_K:RiceRoundMaskBridgeNode,_L:RiceRoundDownloadMaskNode,_M:RiceRoundIntNode,_N:RiceRoundFloatNode,_O:RiceRoundBooleanNode,_P:RiceRoundStrToIntNode,_Q:RiceRoundStrToFloatNode,_R:RiceRoundStrToBooleanNode,_S:RiceRoundDecryptNode,_T:RiceRoundOutputImageBridgeNode,_U:RiceRoundImageUrlNode,_V:RiceRoundUploadImageNode,_W:RiceRoundOutputMaskBridgeNode,_X:RiceRoundOutputIntNode,_Y:RiceRoundOutputFloatNode,_Z:RiceRoundOutputBooleanNode,_a:RiceRoundOutputTextNode,_b:RiceRoundEncryptNode,_c:RiceRoundOutputImageNode,_d:RiceRoundTempTokenNode,**{name:cls[_B]for(name,cls)in dynamic_choice_nodes.items()}}
NODE_DISPLAY_NAME_MAPPINGS={_C:'Simple Choice',_D:'Advanced Choice',_E:'Debug',_F:'Image Bridge',_G:'Simple Image',_H:'Download Image',_I:'Random Seed',_J:'Input Text',_K:'Mask Bridge',_L:'Download Mask',_M:'RiceRound Int',_N:'RiceRound Float',_O:'RiceRound Boolean',_P:'RiceRound Str To Int',_Q:'RiceRound Str To Float',_R:'RiceRound Str To Boolean',_S:'Decrypt',_T:'Output Image Bridge',_U:'Image URL',_V:'Upload Image',_W:'Output Mask Bridge',_X:'Output Int',_Y:'Output Float',_Z:'Output Boolean',_a:'Output Text',_b:'Encrypt',_c:'Output Image',_d:'Temp Token',**{name:cls[_A]for(name,cls)in dynamic_choice_nodes.items()}}
WEB_DIRECTORY='./js'
__all__=['NODE_CLASS_MAPPINGS','NODE_DISPLAY_NAMES_MAPPINGS','WEB_DIRECTORY']
handler_instance=RiceRoundPromptHandler()
onprompt_callback=partial(handler_instance.onprompt_handler)
PromptServer.instance.add_on_prompt_handler(onprompt_callback)
routes=PromptServer.instance.routes
url_config=RiceUrlConfig()
@routes.post('/riceround/set_comfyui_web_server_info')
async def set_comfyui_web_server_info(request):server_info=await request.json();url_config.set_comfyui_local_web_server_info(server_info);return web.json_response({},status=200)
@routes.get('/riceround/auth_callback')
async def auth_callback(request):
	auth_query=request.query;token=auth_query.get('token','')
	if token:token=unquote(token);AuthUnit().save_user_token(token)
	raise web.HTTPFound('/')
@routes.post('/riceround/set_node_additional_info')
async def set_node_additional_info(request):additional_info=await request.json();RicePromptInfo().set_node_additional_info(additional_info);return web.json_response({},status=200)
@routes.get('/riceround/open_selector_list_folder')
async def open_selector_list_folder(request):
	A='error'
	if request.remote not in('127.0.0.1','::1'):return web.json_response({A:'Unauthorized access'},status=403)
	choice_server_folder=RicePromptInfo().get_choice_server_folder()
	if not choice_server_folder.exists():return web.json_response({A:'Folder does not exist'},status=404)
	system=platform.system()
	try:
		if system=='Windows':os.startfile(choice_server_folder)
		elif system=='Darwin':subprocess.run(['open',choice_server_folder])
		else:subprocess.run(['xdg-open',choice_server_folder])
		return web.json_response({'status':'success'},status=200)
	except Exception as e:return web.json_response({A:str(e)},status=500)
@routes.get('/riceround/save_current_env_config')
async def save_current_env_config(request):RiceEnvConfig().save_env_config();return web.json_response({},status=200)
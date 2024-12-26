_e='RiceRoundTempTokenNode'
_d='RiceRoundOutputImageNode'
_c='RiceRoundEncryptNode'
_b='RiceRoundOutputTextNode'
_a='RiceRoundOutputBooleanNode'
_Z='RiceRoundOutputFloatNode'
_Y='RiceRoundOutputIntNode'
_X='RiceRoundOutputMaskBridgeNode'
_W='RiceRoundUploadImageNode'
_V='RiceRoundImageUrlNode'
_U='RiceRoundOutputImageBridgeNode'
_T='RiceRoundDecryptNode'
_S='RiceRoundStrToBooleanNode'
_R='RiceRoundStrToFloatNode'
_Q='RiceRoundStrToIntNode'
_P='RiceRoundBooleanNode'
_O='RiceRoundFloatNode'
_N='RiceRoundIntNode'
_M='RiceRoundDownloadMaskNode'
_L='RiceRoundMaskBridgeNode'
_K='RiceRoundInputTextNode'
_J='RiceRoundRandomSeedNode'
_I='RiceRoundDownloadImageNode'
_H='RiceRoundSimpleImageNode'
_G='RiceRoundImageBridgeNode'
_F='RiceRoundDebugNode'
_E='RiceRoundAdvancedChoiceNode'
_D='RiceRoundSimpleChoiceNode'
_C='dynamic_class'
_B='error'
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
from.rice_prompt_info import RicePromptInfo
def create_dynamic_nodes(base_class):
	rice_prompt_info=RicePromptInfo();dynamic_classes={}
	for(node_name,info)in rice_prompt_info.choice_classname_map.items():class_name=node_name;category='RiceRound/Advanced/Choice';dynamic_class=type(class_name,(base_class,),{'__node_name__':node_name,'CATEGORY':category});dynamic_classes[class_name]={_C:dynamic_class,_A:info.get(_A,class_name)}
	return dynamic_classes
dynamic_choice_nodes=create_dynamic_nodes(RiceRoundBaseChoiceNode)
NODE_CLASS_MAPPINGS={_D:RiceRoundSimpleChoiceNode,_E:RiceRoundAdvancedChoiceNode,_F:RiceRoundDebugNode,_G:RiceRoundImageBridgeNode,_H:RiceRoundSimpleImageNode,_I:RiceRoundDownloadImageNode,_J:RiceRoundRandomSeedNode,_K:RiceRoundInputTextNode,_L:RiceRoundMaskBridgeNode,_M:RiceRoundDownloadMaskNode,_N:RiceRoundIntNode,_O:RiceRoundFloatNode,_P:RiceRoundBooleanNode,_Q:RiceRoundStrToIntNode,_R:RiceRoundStrToFloatNode,_S:RiceRoundStrToBooleanNode,_T:RiceRoundDecryptNode,_U:RiceRoundOutputImageBridgeNode,_V:RiceRoundImageUrlNode,_W:RiceRoundUploadImageNode,_X:RiceRoundOutputMaskBridgeNode,_Y:RiceRoundOutputIntNode,_Z:RiceRoundOutputFloatNode,_a:RiceRoundOutputBooleanNode,_b:RiceRoundOutputTextNode,_c:RiceRoundEncryptNode,_d:RiceRoundOutputImageNode,_e:RiceRoundTempTokenNode,**{name:cls[_C]for(name,cls)in dynamic_choice_nodes.items()}}
NODE_DISPLAY_NAME_MAPPINGS={_D:'Simple Choice',_E:'Advanced Choice',_F:'Debug',_G:'Image Bridge',_H:'Simple Image',_I:'Download Image',_J:'Random Seed',_K:'Input Text',_L:'Mask Bridge',_M:'Download Mask',_N:'RiceRound Int',_O:'RiceRound Float',_P:'RiceRound Boolean',_Q:'RiceRound Str To Int',_R:'RiceRound Str To Float',_S:'RiceRound Str To Boolean',_T:'Decrypt',_U:'Output Image Bridge',_V:'Image URL',_W:'Upload Image',_X:'Output Mask Bridge',_Y:'Output Int',_Z:'Output Float',_a:'Output Boolean',_b:'Output Text',_c:'Encrypt',_d:'Output Image',_e:'Temp Token',**{name:cls[_A]for(name,cls)in dynamic_choice_nodes.items()}}
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
	choice_server_folder=RicePromptInfo().get_choice_server_folder()
	if not choice_server_folder.exists():return web.json_response({_B:'Folder does not exist'},status=404)
	system=platform.system()
	try:
		if system=='Windows':os.startfile(choice_server_folder)
		elif system=='Darwin':subprocess.run(['open',choice_server_folder])
		else:subprocess.run(['xdg-open',choice_server_folder])
		return web.json_response({'status':'success'},status=200)
	except Exception as e:return web.json_response({_B:str(e)},status=500)
@routes.post('/riceround/set_long_token')
async def set_long_token(request):
	try:request_data=await request.json();long_token=request_data.get('long_token','');AuthUnit().set_user_long_token(long_token);return web.json_response({},status=200)
	except Exception as e:return web.json_response({_B:str(e)},status=500)
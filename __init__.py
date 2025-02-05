_i='Unauthorized access'
_h='127.0.0.1'
_g='RiceRoundOutputImageNode'
_f='RiceRoundEncryptNode'
_e='RiceRoundOutputTextNode'
_d='RiceRoundOutputBooleanNode'
_c='RiceRoundOutputFloatNode'
_b='RiceRoundOutputIntNode'
_a='RiceRoundOutputMaskBridgeNode'
_Z='RiceRoundUploadImageNode'
_Y='RiceRoundImageUrlNode'
_X='RiceRoundOutputImageBridgeNode'
_W='RiceRoundDecryptNode'
_V='RiceRoundStrToBooleanNode'
_U='RiceRoundStrToFloatNode'
_T='RiceRoundStrToIntNode'
_S='RiceRoundBooleanNode'
_R='RiceRoundFloatNode'
_Q='RiceRoundIntNode'
_P='RiceRoundDownloadMaskNode'
_O='RiceRoundMaskBridgeNode'
_N='RiceRoundInputTextNode'
_M='RiceRoundRandomSeedNode'
_L='RiceRoundDownloadImageNode'
_K='RiceRoundDownloadImageAndMaskNode'
_J='RiceRoundImageNode'
_I='RiceRoundSimpleImageNode'
_H='RiceRoundImageBridgeNode'
_G='RiceRoundAdvancedChoiceNode'
_F='RiceRoundSimpleChoiceNode'
_E='dynamic_class'
_D='display_name'
_C='error'
_B='success'
_A='status'
import platform,random,sys
from urllib.parse import unquote
import subprocess,asyncio,aiohttp
from.utils import restart
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
	for(node_name,info)in rice_prompt_info.choice_classname_map.items():class_name=node_name;category='RiceRound/Advanced/Choice';dynamic_class=type(class_name,(base_class,),{'__node_name__':node_name,'CATEGORY':category});dynamic_classes[class_name]={_E:dynamic_class,_D:info.get(_D,class_name)}
	return dynamic_classes
dynamic_choice_nodes=create_dynamic_nodes(RiceRoundBaseChoiceNode)
NODE_CLASS_MAPPINGS={_F:RiceRoundSimpleChoiceNode,_G:RiceRoundAdvancedChoiceNode,_H:RiceRoundImageBridgeNode,_I:RiceRoundSimpleImageNode,_J:RiceRoundImageNode,_K:RiceRoundDownloadImageAndMaskNode,_L:RiceRoundDownloadImageNode,_M:RiceRoundRandomSeedNode,_N:RiceRoundInputTextNode,_O:RiceRoundMaskBridgeNode,_P:RiceRoundDownloadMaskNode,_Q:RiceRoundIntNode,_R:RiceRoundFloatNode,_S:RiceRoundBooleanNode,_T:RiceRoundStrToIntNode,_U:RiceRoundStrToFloatNode,_V:RiceRoundStrToBooleanNode,_W:RiceRoundDecryptNode,_X:RiceRoundOutputImageBridgeNode,_Y:RiceRoundImageUrlNode,_Z:RiceRoundUploadImageNode,_a:RiceRoundOutputMaskBridgeNode,_b:RiceRoundOutputIntNode,_c:RiceRoundOutputFloatNode,_d:RiceRoundOutputBooleanNode,_e:RiceRoundOutputTextNode,_f:RiceRoundEncryptNode,_g:RiceRoundOutputImageNode,**{name:cls[_E]for(name,cls)in dynamic_choice_nodes.items()}}
NODE_DISPLAY_NAME_MAPPINGS={_F:'Simple Choice',_G:'Advanced Choice',_H:'Image Bridge',_I:'Simple Image',_J:'Image',_K:'Download Image&Mask',_L:'Download Image',_M:'Random Seed',_N:'Input Text',_O:'Mask Bridge',_P:'Download Mask',_Q:'RiceRound Int',_R:'RiceRound Float',_S:'RiceRound Boolean',_T:'RiceRound Str To Int',_U:'RiceRound Str To Float',_V:'RiceRound Str To Boolean',_W:'Decrypt',_X:'Output Image Bridge',_Y:'Image URL',_Z:'Upload Image',_a:'Output Mask Bridge',_b:'Output Int',_c:'Output Float',_d:'Output Boolean',_e:'Output Text',_f:'Encrypt',_g:'Output Image',**{name:cls[_D]for(name,cls)in dynamic_choice_nodes.items()}}
WEB_DIRECTORY='./js'
__all__=['NODE_CLASS_MAPPINGS','NODE_DISPLAY_NAMES_MAPPINGS','WEB_DIRECTORY']
handler_instance=RiceRoundPromptHandler()
onprompt_callback=partial(handler_instance.onprompt_handler)
PromptServer.instance.add_on_prompt_handler(onprompt_callback)
routes=PromptServer.instance.routes
url_config=RiceUrlConfig()
workspace_path=os.path.join(os.path.dirname(__file__))
dist_path=os.path.join(workspace_path,'static')
if os.path.exists(dist_path):PromptServer.instance.app.add_routes([aiohttp.web.static('/riceround/static',dist_path)])
@routes.post('/riceround/auth_callback')
async def auth_callback(request):
	auth_query=await request.json();token=auth_query.get('token','');client_key=auth_query.get('client_key','')
	if token and client_key:token=unquote(token);client_key=unquote(client_key);AuthUnit().set_user_token(token,client_key)
	return aiohttp.web.json_response({_A:_B},status=200)
@routes.post('/riceround/set_long_token')
async def set_long_token(request):
	data=await request.json();long_token=data.get('long_token','')
	if long_token:AuthUnit().save_user_token(long_token)
	return aiohttp.web.json_response({_A:_B},status=200)
@routes.post('/riceround/set_node_additional_info')
async def set_node_additional_info(request):additional_info=await request.json();RicePromptInfo().set_node_additional_info(additional_info);return web.json_response({},status=200)
@routes.get('/riceround/open_selector_list_folder')
async def open_selector_list_folder(request):
	if request.remote not in(_h,'::1'):return web.json_response({_C:_i},status=403)
	choice_server_folder=RicePromptInfo().get_choice_server_folder()
	if not choice_server_folder.exists():return web.json_response({_C:'Folder does not exist'},status=404)
	system=platform.system()
	try:
		if system=='Windows':os.startfile(choice_server_folder)
		elif system=='Darwin':subprocess.run(['open',choice_server_folder])
		else:subprocess.run(['xdg-open',choice_server_folder])
		return web.json_response({_A:_B},status=200)
	except Exception as e:return web.json_response({_C:str(e)},status=500)
@routes.get('/riceround/get_current_env_config')
async def save_current_env_config(request):
	if request.remote not in(_h,'::1'):return web.json_response({_C:_i},status=403)
	env_info=RiceEnvConfig().read_env();return web.json_response(env_info,status=200)
@routes.get('/riceround/logout')
async def logout(request):AuthUnit().clear_user_token();return aiohttp.web.json_response({_A:_B},status=200)
@routes.post('/riceround/set_auto_overwrite')
async def set_auto_overwrite(request):data=await request.json();auto_overwrite=data.get('auto_overwrite');RicePromptInfo().set_auto_overwrite(auto_overwrite);return web.json_response({_A:_B},status=200)
@routes.post('/riceround/set_run_client')
async def set_run_client(request):data=await request.json();run_client=data.get('run_client');RicePromptInfo().set_run_client(run_client);return web.json_response({_A:_B},status=200)
@routes.post('/riceround/set_auto_publish')
async def set_auto_publish(request):data=await request.json();auto_publish=data.get('auto_publish');RicePromptInfo().set_auto_publish(auto_publish);return web.json_response({_A:_B},status=200)
@routes.post('/riceround/set_wait_time')
async def set_wait_time(request):data=await request.json();wait_time=data.get('wait_time');RicePromptInfo().set_wait_time(wait_time);return web.json_response({_A:_B},status=200)
@routes.post('/riceround/install_choice_node')
async def install_choice_node(request):
	B='failed';A='message'
	async def delayed_restart():await asyncio.sleep(3);restart()
	data=await request.json();template_id=data.get('template_id');need_reboot=data.get('need_reboot',False)
	if not template_id:return aiohttp.web.json_response({_A:B,A:'template_id is required'},status=400)
	if RicePromptInfo().install_choice_node(template_id):
		if need_reboot:asyncio.create_task(delayed_restart())
		return aiohttp.web.json_response({_A:_B,A:'Installation successful, server will restart in 3 seconds'},status=200)
	return aiohttp.web.json_response({_A:B,A:'Installation failed'},status=400)
is_on_riceround=False
if os.getenv('RICE_ROUND_SERVER')=='true':is_on_riceround=True
@web.middleware
async def check_login_status(request,handler):
	if is_on_riceround:
		if request.headers.get('owner')=='share_client':return await handler(request)
		return web.json_response({_C:'Access denied'},status=403)
	return await handler(request)
if not is_on_riceround:
	try:
		from.rice_install_client import RiceInstallClient
		if RicePromptInfo().get_run_client():RiceInstallClient().run_client()
	except Exception as e:print(f"Error running client: {e}")
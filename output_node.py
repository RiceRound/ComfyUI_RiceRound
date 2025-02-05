_Z='number'
_Y='Authorization'
_X='PROMPT'
_W='tooltip'
_V='hidden'
_U='load_image'
_T='error'
_S='无法完成鉴权登录，请检查网络或完成登录步骤'
_R='type'
_Q='content'
_P='riceround_toast'
_O='运行云节点需要先完成登录'
_N='max'
_M='min'
_L='optional'
_K='input_anything'
_J='INT'
_I='name'
_H=None
_G='bridge'
_F='RiceRound/Output'
_E='value'
_D='required'
_C='default'
_B=True
_A='STRING'
from io import BytesIO
import json,os,re
from pathlib import Path
from PIL import Image,ImageOps
from PIL.PngImagePlugin import PngInfo
import torch
from comfy import model_management
import requests,numpy as np,folder_paths
from nodes import LoadImage
from comfy.utils import ProgressBar
from server import PromptServer
from.rice_def import RiceRoundErrorDef
from.rice_url_config import RiceUrlConfig,user_upload_image,user_upload_imagefile
from.utils import get_machine_id,pil2tensor
from.auth_unit import AuthUnit
from.rice_prompt_info import RicePromptInfo
from.rice_websocket import TaskInfo,TaskStatus,TaskWebSocket,start_and_wait_task_done
class RiceRoundDecryptNode:
	def __init__(A):A.auth_unit=AuthUnit();A.machine_id=get_machine_id();A.url_config=RiceUrlConfig();A.pbar=_H;A.last_progress=0;A.user_token=_H
	@classmethod
	def INPUT_TYPES(A):return{_D:{'rice_template_id':(_A,{_C:''}),'seed':(_J,{_C:0,_M:0,_N:0xffffffffffffffff,_W:'The random seed used for creating the noise.'})},_L:{_K:('*',{})},_V:{'unique_id':'UNIQUE_ID','prompt':_X,'extra_pnginfo':'EXTRA_PNGINFO'}}
	@classmethod
	def VALIDATE_INPUTS(C,input_types):
		for(A,B)in input_types.items():
			if A.startswith(_K):
				if B not in(_A,'TEXT',_X):return f"{A} must be of string type"
		return _B
	RETURN_TYPES='IMAGE',;OUTPUT_NODE=_B;FUNCTION='execute';CATEGORY=_F
	def progress_callback(A,task_uuid,progress_text,progress,preview_refreshed):
		B=progress
		if not A.pbar:return
		if preview_refreshed:
			D=A.url_config.workflow_preview_url+'?task_uuid='+task_uuid
			try:E={_Y:f"Bearer {A.user_token}"};C=requests.get(D,stream=_B,headers=E);C.raise_for_status();F=Image.open(BytesIO(C.content));A.pbar.update_absolute(A.last_progress,preview=('PNG',F,_H))
			except Exception as G:print(f"Failed to load preview image: {str(G)}");A.pbar.update_absolute(A.last_progress)
		else:A.last_progress=B;A.pbar.update_absolute(B)
	def execute(A,rice_template_id,**M):
		A.pbar=ProgressBar(100);A.user_token,N,H=A.auth_unit.get_user_token()
		if not A.user_token:
			if H==RiceRoundErrorDef.HTTP_UNAUTHORIZED or H==RiceRoundErrorDef.NO_TOKEN_ERROR:AuthUnit().login_dialog(_O)
			else:PromptServer.instance.send_sync(_P,{_Q:_S,_R:_T})
			raise ValueError(N)
		C={}
		for(I,E)in M.items():
			if I.startswith(_K):
				D=I[len(_K):];D=re.sub('\\s*\\([^)]*\\)','',D);F=0 if D==''else int(D)
				if F in C:raise ValueError(f"Duplicate input_anything index: {F}")
				if isinstance(E,str):C[str(F)]=E
				else:raise ValueError(f"Invalid input type: {type(E)}")
		if not C:return torch.zeros(1,1,1,3),
		B=A.create_task(C,rice_template_id,A.user_token)
		if not B or not B.task_uuid:raise ValueError('Failed to create task')
		start_and_wait_task_done(A.url_config.task_ws_url,A.user_token,A.machine_id,B,A.progress_callback,RicePromptInfo().get_wait_time());model_management.throw_exception_if_processing_interrupted();J=B.result_data
		if not J:
			if B.progress_text and B.state>TaskStatus.FINISHED:raise ValueError(B.progress_text)
			else:raise ValueError('websocket failed')
		K=J.get('image_results',[])
		if not K:raise ValueError('Failed to get image results')
		L=[]
		for O in K:G=Image.open(requests.get(O,stream=_B).raw);G=ImageOps.exif_transpose(G);L.append(pil2tensor(G))
		P=torch.cat(L,dim=0);A.pbar=_H;return P,
	def create_task(E,input_data,template_id,user_token):
		'\n        Create a task and return the task UUID.\n        \n        Args:\n            task_url (str): The URL to send the task request to\n            request_data (dict): The data to send in the request\n            headers (dict): The headers to send with the request\n            \n        Returns:\n            str: The task UUID if successful\n            \n        Raises:\n            ValueError: If the request fails or response is invalid\n        ';D='data';F=E.url_config.prompt_task_url;G={_Y:f"Bearer {user_token}",'Content-Type':'application/json'};H={'taskData':json.dumps(input_data),'workData':json.dumps({'template_id':template_id})};A=requests.post(F,json=H,headers=G)
		if A.status_code==200:
			B=A.json()
			if B.get('code')==0 and D in B:
				C=TaskInfo(B.get(D,{}))
				if C.task_uuid:return C
				else:raise ValueError('No task UUID in response')
			else:raise ValueError(f"API error: {B.get('message','Unknown error')}")
		else:raise ValueError(f"HTTP error {A.status_code}: {A.text}")
class RiceRoundBaseChoiceNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(B):A=getattr(B,'__node_name__',_H);C=RicePromptInfo().get_choice_node_options(A)if A else[];return{_D:{_I:(_A,{_C:'Parameter'}),_C:(C,)},_L:{},_V:{}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;FUNCTION='placeholder';CATEGORY='__hidden__'
	def placeholder(A,default,**B):return default,
def upload_imagefile(image_path):
	A,C,B=AuthUnit().get_user_token()
	if not A:
		if B==RiceRoundErrorDef.HTTP_UNAUTHORIZED or B==RiceRoundErrorDef.NO_TOKEN_ERROR:AuthUnit().login_dialog(_O)
		else:PromptServer.instance.send_sync(_P,{_Q:_S,_R:_T})
		raise ValueError(C)
	return user_upload_imagefile(image_path,A)
def upload_image(image):
	A,C,B=AuthUnit().get_user_token()
	if not A:
		if B==RiceRoundErrorDef.HTTP_UNAUTHORIZED or B==RiceRoundErrorDef.NO_TOKEN_ERROR:AuthUnit().login_dialog(_O)
		else:PromptServer.instance.send_sync(_P,{_Q:_S,_R:_T})
		raise ValueError(C)
	return user_upload_image(image,A)
class RiceRoundImageUrlNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'image_url':(_A,)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_U;CATEGORY=_F
	def load_image(A,image_url,**B):return image_url,
class RiceRoundUploadImageNode(LoadImage):
	def __init__(A):super().__init__()
	@classmethod
	def INPUT_TYPES(C):A=folder_paths.get_input_directory();B=[B for B in os.listdir(A)if os.path.isfile(os.path.join(A,B))];return{_D:{'image':(sorted(B),{'image_upload':_B})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_U;CATEGORY=_F
	def load_image(C,image,**D):A=folder_paths.get_annotated_filepath(image);B=upload_imagefile(A);return B,
class RiceRoundOutputImageBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'images':('IMAGE',{_W:'only image.'})},_L:{}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_G;CATEGORY=_F
	def bridge(A,images,**B):return upload_image(images)
class RiceRoundOutputMaskBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'mask':('MASK',)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_G;CATEGORY=_F
	def bridge(D,mask,**E):A=mask.cpu().numpy();A=(A*255).astype(np.uint8);B=Image.fromarray(A);C=upload_image(B);return C,
class RiceRoundMaskUrlNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'mask_url':(_A,)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_U;CATEGORY=_F
	def load_image(A,mask_url,**B):return mask_url,
class RiceRoundOutputIntNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{_I:(_A,{_C:'数值'}),_Z:(_J,),_M:(_J,{_C:0}),_N:(_J,{_C:1000000})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_G;CATEGORY=_F
	def bridge(A,name,number,min,max,**B):return str(number),
class RiceRoundOutputFloatNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(B):A='FLOAT';return{_D:{_I:(_A,{_C:'数值'}),_Z:(A,),_M:(A,{_C:.0}),_N:(A,{_C:1e6})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_G;CATEGORY=_F
	def bridge(A,name,number,min,max,**B):return str(number),
class RiceRoundOutputBooleanNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{_I:(_A,{_C:'开关'}),_E:('BOOLEAN',{_C:False})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_G;CATEGORY=_F
	def bridge(B,name,value,**C):A='true'if value else'false';return A,
class RiceRoundOutputTextNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{_I:(_A,{_C:'文本'}),'str':(_A,)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_E,;OUTPUT_NODE=_B;FUNCTION=_G;CATEGORY=_F
	def bridge(A,name,str,**B):return str,
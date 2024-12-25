_S='number'
_R='PROMPT'
_Q='tooltip'
_P='load_image'
_O='Failed to get user token'
_N='max'
_M='min'
_L='hidden'
_K='input_anything'
_J='INT'
_I='optional'
_H='name'
_G='bridge'
_F='value'
_E='RiceRound/Output'
_D='required'
_C=True
_B='default'
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
from.rice_url_config import RiceUrlConfig,user_upload_image
from.utils import get_machine_id,pil2tensor
from.auth_unit import AuthUnit
from.rice_prompt_info import RicePromptInfo
from.rice_websocket import TaskInfo,TaskStatus,TaskWebSocket,start_and_wait_task_done
RICE_ROUND_IMAGE_TAG='RICE_ROUND_IMAGE'
RICE_ROUND_MASK_TAG='RICE_ROUND_MASK'
class RiceRoundDecryptNode:
	def __init__(A):A.auth_unit=AuthUnit();A.machine_id=get_machine_id();A.url_config=RiceUrlConfig();A.pbar=None
	@classmethod
	def INPUT_TYPES(A):return{_D:{'rice_template_id':(_A,{_B:''}),'seed':(_J,{_B:0,_M:0,_N:0xffffffffffffffff,_Q:'The random seed used for creating the noise.'})},_I:{_K:('*',{})},_L:{'unique_id':'UNIQUE_ID','prompt':_R,'extra_pnginfo':'EXTRA_PNGINFO'}}
	@classmethod
	def VALIDATE_INPUTS(C,input_types):
		for(A,B)in input_types.items():
			if A.startswith(_K):
				if B not in(_A,'TEXT',_R):return f"{A} must be of string type"
		return _C
	RETURN_TYPES='IMAGE',;OUTPUT_NODE=_C;FUNCTION='execute';CATEGORY=_E
	def progress_callback(A,task_uuid,progress_text,progress,preview_refreshed):
		if not A.pbar:return
		if preview_refreshed:print(f"RiceRoundDecryptNode progress_callback preview_refreshed")
		else:A.pbar.update_absolute(progress)
	def execute(A,rice_template_id,**L):
		A.pbar=ProgressBar(100);G=A.auth_unit.get_user_token()
		if not G:raise ValueError(_O)
		D={}
		for(I,B)in L.items():
			if I.startswith(_K):
				F=I[len(_K):];F=re.sub('\\s*\\([^)]*\\)','',F);E=0 if F==''else int(F)
				if E in D:raise ValueError(f"Duplicate input_anything index: {E}")
				if isinstance(B,str):
					if B.startswith(RICE_ROUND_IMAGE_TAG):D[str(E)]=B[len(RICE_ROUND_IMAGE_TAG):]
					elif B.startswith(RICE_ROUND_MASK_TAG):D[str(E)]=B[len(RICE_ROUND_MASK_TAG):]
					else:D[str(E)]=B
				else:raise ValueError(f"Invalid input type: {type(B)}")
		if not D:return torch.zeros(1,1,1,3),
		C=A.create_task(D,rice_template_id,G)
		if not C or not C.task_uuid:raise ValueError('Failed to create task')
		start_and_wait_task_done(A.url_config.task_ws_url,G,A.machine_id,C,A.progress_callback);model_management.throw_exception_if_processing_interrupted();J=C.result_data
		if not J:
			if C.progress_text and C.state>TaskStatus.FINISHED:raise ValueError(C.progress_text)
			else:raise ValueError('websocket failed')
		K=J.get('image_results',[])
		if not K:raise ValueError('Failed to get image results')
		M=K[0];H=Image.open(requests.get(M,stream=_C).raw);H=ImageOps.exif_transpose(H);A.pbar=None;return pil2tensor(H),
	def create_task(E,input_data,template_id,user_token):
		'\n        Create a task and return the task UUID.\n        \n        Args:\n            task_url (str): The URL to send the task request to\n            request_data (dict): The data to send in the request\n            headers (dict): The headers to send with the request\n            \n        Returns:\n            str: The task UUID if successful\n            \n        Raises:\n            ValueError: If the request fails or response is invalid\n        ';D='data';F=E.url_config.prompt_task_url;G={'Authorization':f"Bearer {user_token}",'Content-Type':'application/json'};H={'taskData':json.dumps(input_data),'workData':json.dumps({'template_id':template_id})};A=requests.post(F,json=H,headers=G)
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
	def INPUT_TYPES(B):A=getattr(B,'__node_name__',None);C=RicePromptInfo().get_choice_node_options(A)if A else[];return{_D:{_H:(_A,{_B:'Parameter'}),_B:(C,)},_I:{},_L:{}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;FUNCTION='placeholder';CATEGORY=_E
	def placeholder(A,default,**B):return default,
def upload_images(images):
	C=AuthUnit().get_user_token()
	if not C:raise ValueError(_O)
	A=[]
	for D in images:E=user_upload_image(D,C);A.append(E)
	B=''
	if len(A)==1:B=A[0]
	elif len(A)>1:B=','.join(A)
	return RICE_ROUND_IMAGE_TAG+B,
class RiceRoundImageUrlNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'image_url':(_A,)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_P;CATEGORY=_E
	def load_image(A,image_url,**B):return RICE_ROUND_IMAGE_TAG+image_url,
class RiceRoundUploadImageNode(LoadImage):
	def __init__(A):super().__init__()
	@classmethod
	def INPUT_TYPES(C):A=folder_paths.get_input_directory();B=[B for B in os.listdir(A)if os.path.isfile(os.path.join(A,B))];return{_D:{'image':(sorted(B),{'image_upload':_C})},_I:{},_L:{}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_P;CATEGORY=_E
	def load_image(B,image,**C):A,D=super().load_image(image);return upload_images(A[:1])
class RiceRoundOutputImageBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'images':('IMAGE',{_Q:'only image.'})},_I:{}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_G;CATEGORY=_E
	def bridge(A,images,**B):return upload_images(images)
class RiceRoundOutputMaskBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'mask':('MASK',)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_G;CATEGORY=_E
	def bridge(E,mask,**F):
		A=mask.cpu().numpy();A=(A*255).astype(np.uint8);C=Image.fromarray(A);B=AuthUnit().get_user_token()
		if not B:raise ValueError(_O)
		D=user_upload_image(C,B);return RICE_ROUND_MASK_TAG+D,
class RiceRoundMaskUrlNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{'mask_url':(_A,)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_P;CATEGORY=_E
	def load_image(A,mask_url,**B):return RICE_ROUND_MASK_TAG+mask_url,
class RiceRoundOutputIntNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{_H:(_A,{_B:'数值'}),_S:(_J,),_M:(_J,{_B:0}),_N:(_J,{_B:1000000})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_G;CATEGORY=_E
	def bridge(A,name,number,min,max,**B):return str(number),
class RiceRoundOutputFloatNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(B):A='FLOAT';return{_D:{_H:(_A,{_B:'数值'}),_S:(A,),_M:(A,{_B:.0}),_N:(A,{_B:1e6})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_G;CATEGORY=_E
	def bridge(A,name,number,min,max,**B):return str(number),
class RiceRoundOutputBooleanNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{_H:(_A,{_B:'开关'}),_F:('BOOLEAN',{_B:False})}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_G;CATEGORY=_E
	def bridge(B,name,value,**C):A='true'if value else'false';return A,
class RiceRoundOutputTextNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_D:{_H:(_A,{_B:'文本'}),'str':(_A,)}}
	RETURN_TYPES=_A,;RETURN_NAMES=_F,;OUTPUT_NODE=_C;FUNCTION=_G;CATEGORY=_E
	def bridge(A,name,str,**B):return str,
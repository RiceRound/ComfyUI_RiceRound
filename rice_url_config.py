_I='Content-Type'
_H='download_url'
_G='upload_sign_url'
_F='file_type'
_E='upload_type'
_D='server_info.json'
_C='comfyui_local_web_server_info.json'
_B='image/png'
_A='data'
from enum import IntEnum
import json,os
from PIL import Image
from io import BytesIO
import numpy as np,requests
from urllib.parse import urljoin
from.utils import get_local_app_setting_path
DEFAULT_SUBDOMAIN='api'if os.getenv('DEBUG')!='true'else'test'
DEFAULT_URL_PREFIX=f"https://{DEFAULT_SUBDOMAIN}.riceround.online"
DEFAULT_WS_PREFIX=f"wss://{DEFAULT_SUBDOMAIN}.riceround.online"
DEFAULT_WEB_URL_PREFIX=f"https://www.riceround.online"if os.getenv('DEBUG')!='true'else'http://localhost:5173/'
DEFAULT_LOCAL_BASE_URL='http://127.0.0.1:8188'
class UploadType(IntEnum):TEMPLATE_PUBLISH_IMAGE=1;USER_UPLOAD_TASK_IMAGE=2;MACHINE_TASK_RESULT=1000
class RiceUrlConfig:
	_instance=None;_initialized=False
	def __new__(A,*B,**C):
		if A._instance is None:A._instance=super(RiceUrlConfig,A).__new__(A)
		return A._instance
	def __init__(A):
		if not A._initialized:A.comfyui_local_web_server_info={};A.load_comfyui_local_web_server_info();A.server_info={};A.load_server_info();A._initialized=True
	def set_comfyui_local_web_server_info(B,local_server_info):
		A=local_server_info;B.comfyui_local_web_server_info=A;C=get_local_app_setting_path();D=C/_C
		with open(D,'w')as E:json.dump(A,E)
	def load_comfyui_local_web_server_info(A):
		C=get_local_app_setting_path();B=C/_C
		if B.exists():
			with open(B,'r')as D:A.comfyui_local_web_server_info=json.load(D)
		else:A.comfyui_local_web_server_info={}
	@property
	def comfyui_local_base_url(self):
		if self.comfyui_local_web_server_info:return self.comfyui_local_web_server_info.get('local_base_url','')
		return DEFAULT_LOCAL_BASE_URL
	def set_server_info(C,server_info):
		B=server_info
		if B and isinstance(B,dict):
			A=B.get(_A)
			if A and isinstance(A,dict):
				C.server_info=A;D=get_local_app_setting_path()
				with open(D/_D,'w')as E:json.dump(A,E)
	def load_server_info(B):
		C=get_local_app_setting_path();A=C/_D
		if A.exists():
			with open(A,'r')as D:B.server_info=json.load(D)
	def get_server_url(A,url_path):return urljoin(A.url_prefix,url_path)
	def get_ws_url(A,url_path):return urljoin(A.ws_prefix,url_path)
	def get_web_url(A,url_path):return urljoin(A.web_url_prefix,url_path)
	@property
	def ws_prefix(self):
		A=DEFAULT_WS_PREFIX
		if self.server_info:A=self.server_info.get('ws_prefix')
		if A:return A
		return DEFAULT_WS_PREFIX
	@property
	def url_prefix(self):
		A=DEFAULT_URL_PREFIX
		if self.server_info:A=self.server_info.get('url_prefix')
		if A:return A
		return DEFAULT_URL_PREFIX
	@property
	def web_url_prefix(self):
		A=DEFAULT_WEB_URL_PREFIX
		if self.server_info:A=self.server_info.get('web_url_prefix')
		if A:return A
		return DEFAULT_WEB_URL_PREFIX
	@property
	def machine_upload_sign_url(self):return self.get_server_url('/api/machine_client/upload_image_sign_url')
	@property
	def user_upload_sign_url(self):return self.get_server_url('/api/user/upload_sign_url')
	@property
	def prompt_task_url(self):return self.get_server_url('/api/workflow/add_task')
	@property
	def preview_refresh_url(self):return self.get_server_url('/api/workflow/refresh_preview')
	@property
	def task_ws_url(self):return self.get_ws_url('/api/workflow/task_websocket')
	@property
	def login_api_url(self):return self.get_server_url('/api/workflow/get_info')
	@property
	def auth_web_url(self):return self.get_web_url('/auth/login')
def user_upload_image(image,user_token):
	D=RiceUrlConfig().user_upload_sign_url;G={'Authorization':f"Bearer {user_token}"};H={_E:UploadType.USER_UPLOAD_TASK_IMAGE.value,_F:_B};A=requests.get(D,headers=G,params=H);E='';B=''
	if A.status_code==200:
		C=A.json()
		if C.get('code')==0:E=C.get(_A,{}).get(_G,'');B=C.get(_A,{}).get(_H,'')
	else:raise ValueError(f"failed to upload image. Status code: {A.status_code}")
	if not E or not B:raise ValueError(f"failed to upload image. upload_sign_url is empty")
	I=255.*image.cpu().numpy();J=Image.fromarray(np.clip(I,0,255).astype(np.uint8));F=BytesIO();J.save(F,format='PNG',quality=95,compress_level=1);K=F.getvalue();A=requests.put(D,data=K,headers={_I:_B})
	if A.status_code==200:return B
	else:print(f"failed to upload image. Status code: {A.status_code}");raise ValueError(f"failed to upload image. Status code: {A.status_code}")
def machine_upload_image(image,task_id):
	F=RiceUrlConfig().machine_upload_sign_url;G=255.*image.cpu().numpy();H=Image.fromarray(np.clip(G,0,255).astype(np.uint8));E=BytesIO();H.save(E,format='PNG',quality=95,compress_level=1);I=E.getvalue();B='';C='';J={_E:UploadType.MACHINE_TASK_RESULT.value,_F:_B,'task_id':task_id};A=requests.get(F,params=J)
	if A.status_code==200:
		D=A.json()
		if D.get('code')==0:B=D.get(_A,{}).get(_G,'');C=D.get(_A,{}).get(_H,'')
	else:print(f"failed to upload image. Status code: {A.status_code}, Response: {A.text}");raise ValueError(f"failed to upload image. Status code: {A.status_code}")
	if not B or not C:raise ValueError(f"failed to upload image. upload_sign_url is empty")
	A=requests.put(B,data=I,headers={_I:_B})
	if A.status_code==200:return C
	else:print(f"failed to upload image. Status code: {A.status_code}, Response: {A.text}");raise ValueError(f"failed to upload image. Status code: {A.status_code}")
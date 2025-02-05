_J='/api/workflow/refresh_preview'
_I='Content-Type'
_H='upload_sign_url'
_G='file_type'
_F='upload_type'
_E='Authorization'
_D='download_url'
_C='code'
_B='image/png'
_A='data'
from enum import IntEnum
import json,os
from PIL import Image
from io import BytesIO
import numpy as np,requests
from urllib.parse import urljoin
from.utils import get_local_app_setting_path
DEFAULT_SUBDOMAIN='api'if os.getenv('RICE_ROUND_DEBUG')!='true'else'test'
DEFAULT_URL_PREFIX=f"https://{DEFAULT_SUBDOMAIN}.riceround.online"
DEFAULT_WS_PREFIX=f"wss://{DEFAULT_SUBDOMAIN}.riceround.online"
class UploadType(IntEnum):TEMPLATE_PUBLISH_IMAGE=1;USER_UPLOAD_TASK_IMAGE=2;MACHINE_TASK_RESULT=1000
class RiceUrlConfig:
	_instance=None;_initialized=False
	def __new__(A,*B,**C):
		if A._instance is None:A._instance=super(RiceUrlConfig,A).__new__(A)
		return A._instance
	def __init__(A):
		if not A._initialized:A._initialized=True
	def get_server_url(A,url_path):return urljoin(DEFAULT_URL_PREFIX,url_path)
	def get_ws_url(A,url_path):return urljoin(DEFAULT_WS_PREFIX,url_path)
	@property
	def machine_upload_sign_url(self):return self.get_server_url('/api/machine_client/upload_image_sign_url')
	@property
	def user_upload_sign_url(self):return self.get_server_url('/api/user/upload_sign_url')
	@property
	def prompt_task_url(self):return self.get_server_url('/api/workflow/add_task')
	@property
	def preview_refresh_url(self):return self.get_server_url(_J)
	@property
	def task_ws_url(self):return self.get_ws_url('/api/workflow/task_websocket')
	@property
	def workflow_preview_url(self):return self.get_server_url(_J)
	@property
	def get_info_url(self):return self.get_server_url('/api/workflow/get_info')
	@property
	def machine_bind_key_url(self):return self.get_server_url('/api/machine_bind/key')
	@property
	def workflow_template_url(self):return self.get_server_url('/api/workflow/get_template')
	@property
	def publisher_workflow_url(self):return self.get_server_url('/api/publisher/workflow')
def user_upload_imagefile(image_file_path,user_token):
	I='image/jpeg';B=image_file_path
	if not os.path.exists(B):raise ValueError(f"Image file not found: {B}")
	C={'.png':_B,'.jpg':I,'.jpeg':I,'.webp':'image/webp','.bmp':'image/bmp'};D=os.path.splitext(B)[1].lower()
	if D not in C:raise ValueError(f"Unsupported image format: {D}. Supported formats: {', '.join(C.keys())}")
	H=C[D];J=RiceUrlConfig().user_upload_sign_url;K={_E:f"Bearer {user_token}"};L={_F:UploadType.USER_UPLOAD_TASK_IMAGE.value,_G:H};A=requests.get(J,headers=K,params=L);E='';F=''
	if A.status_code==200:
		G=A.json()
		if G.get(_C)==0:E=G.get(_A,{}).get(_H,'');F=G.get(_A,{}).get(_D,'')
	else:raise ValueError(f"Failed to get upload URL. Status code: {A.status_code}")
	if not E or not F:raise ValueError('Failed to get upload URL. Upload sign URL is empty')
	try:
		with open(B,'rb')as M:N=M.read()
		A=requests.put(E,data=N,headers={_I:H})
		if A.status_code==200:return F
		else:raise ValueError(f"Failed to upload image. Status code: {A.status_code}")
	except IOError as O:raise ValueError(f"Failed to read image file: {str(O)}")
def user_upload_image(image,user_token):
	D=RiceUrlConfig().user_upload_sign_url;G={_E:f"Bearer {user_token}"};H={_F:UploadType.USER_UPLOAD_TASK_IMAGE.value,_G:_B};A=requests.get(D,headers=G,params=H);E='';B=''
	if A.status_code==200:
		C=A.json()
		if C.get(_C)==0:E=C.get(_A,{}).get(_H,'');B=C.get(_A,{}).get(_D,'')
	else:raise ValueError(f"failed to upload image. Status code: {A.status_code}")
	if not E or not B:raise ValueError(f"failed to upload image. upload_sign_url is empty")
	I=255.*image.cpu().numpy();J=Image.fromarray(np.clip(I,0,255).astype(np.uint8));F=BytesIO();J.save(F,format='PNG',quality=95,compress_level=1);K=F.getvalue();A=requests.put(D,data=K,headers={_I:_B})
	if A.status_code==200:return B
	else:print(f"failed to upload image. Status code: {A.status_code}");raise ValueError(f"failed to upload image. Status code: {A.status_code}")
def machine_upload_image(image,task_id):
	F=RiceUrlConfig().machine_upload_sign_url;G=255.*image.cpu().numpy();H=Image.fromarray(np.clip(G,0,255).astype(np.uint8));E=BytesIO();H.save(E,format='PNG',quality=95,compress_level=1);I=E.getvalue();B='';C='';J={_F:UploadType.MACHINE_TASK_RESULT.value,_G:_B,'task_id':task_id};A=requests.get(F,params=J)
	if A.status_code==200:
		D=A.json()
		if D.get(_C)==0:B=D.get(_A,{}).get(_H,'');C=D.get(_A,{}).get(_D,'')
	else:print(f"failed to upload image. Status code: {A.status_code}, Response: {A.text}");raise ValueError(f"failed to upload image. Status code: {A.status_code}")
	if not B or not C:raise ValueError(f"failed to upload image. upload_sign_url is empty")
	A=requests.put(B,data=I,headers={_I:_B})
	if A.status_code==200:return C
	else:print(f"failed to upload image. Status code: {A.status_code}, Response: {A.text}");raise ValueError(f"failed to upload image. Status code: {A.status_code}")
def download_template(template_id,user_token,save_path):
	F='template_id';B=template_id;H=RiceUrlConfig().workflow_template_url;I={_E:f"Bearer {user_token}"};J={F:B};C=requests.get(H,headers=I,params=J)
	if C.status_code!=200:raise ValueError(f"Failed to get template. Status code: {C.status_code}")
	D=C.json()
	if D.get(_C)!=0:raise ValueError(f"Failed to get template. Error: {D.get('msg')}")
	G=D.get(_A,{}).get(_D)
	if not G:raise ValueError('Template download URL is empty')
	A=requests.get(G)
	if A.status_code!=200:raise ValueError(f"Failed to download template. Status code: {A.status_code}")
	try:
		E=A.json()
		if E.get(F)!=B:raise ValueError(f"Template ID mismatch. Expected: {B}, Got: {E.get(F)}")
		with open(save_path,'wb')as K:K.write(A.content)
		return E
	except json.JSONDecodeError:raise ValueError('Failed to parse template JSON data')
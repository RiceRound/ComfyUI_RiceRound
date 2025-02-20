_C='message'
_B='Authorization'
_A=False
import json,os,requests
from.rice_prompt_info import RicePromptInfo
from.rice_url_config import RiceUrlConfig,user_upload_imagefile
from server import PromptServer
from aiohttp import web
import time
from.message_holder import MessageHolder
class Publish:
	def __init__(A,publish_folder):A.publish_folder=publish_folder
	def publish(G,user_token,template_id,project_name,preview_path,publish_file):
		P='duration';O='error';N='info';H=preview_path;F='type';E='content';D='riceround_toast';C=publish_file;B=user_token;A=template_id
		if not os.path.exists(C):raise ValueError(f"Publish file not found: {C}")
		I=_A;J,K=G._check_workflow(B,A)
		if J==1:
			I=True;Q=RicePromptInfo().get_auto_overwrite()
			if not Q:
				R={'title':'已经存在相同template_id的数据，是否覆盖？注意，如果接口做了调整，覆盖后老用户将无法使用！','icon':N,'confirmButtonText':'覆盖','cancelButtonText':'取消','showCancelButton':True,'timer':50000};PromptServer.instance.send_sync('riceround_dialog',{'json_content':json.dumps(R),'id':A});S=MessageHolder.waitForMessage(A,timeout=60000)
				try:T=int(S)
				except ValueError:print('riceround upload cancel: Invalid response format');return _A
				if T!=1:print('riceround upload cancel: User rejected overwrite');return _A
		elif J!=0:print(f"riceround upload failed: {K}");PromptServer.instance.send_sync(D,{E:f"异常情况，{K}",F:O});return _A
		L=None
		if not I:
			if os.path.exists(H):L=user_upload_imagefile(H,B)
		M,U=G._upload_workflow(B,A,project_name,L,C)
		if M:PromptServer.instance.send_sync(D,{E:'上传成功',F:N,P:5000})
		else:PromptServer.instance.send_sync(D,{E:f"上传失败: {U}",F:O,P:5000})
		return M
	def _check_workflow(H,user_token,template_id):
		C={_B:f"Bearer {user_token}"};D={'id':template_id,'action':'check'}
		try:
			A=requests.get(RiceUrlConfig().publisher_workflow_url,params=D,headers=C)
			if A.status_code==200:B=A.json();E=B.get('code');F=B.get(_C);return E,F
			else:return-1,''
		except Exception as G:return-1,str(G)
	def _upload_workflow(I,user_token,template_id,project_name,preview_image_url,publish_file):
		try:
			C={_B:f"Bearer {user_token}"};D={'template_id':template_id,'title':project_name,'main_image_url':preview_image_url or''}
			with open(publish_file,'rb')as E:F={'workflow_file':('workflow',E,'application/octet-stream')};G={'data':json.dumps(D),'source':'comfyui'};A=requests.put(RiceUrlConfig().publisher_workflow_url,headers=C,files=F,data=G)
			if A.status_code==200:
				B=A.json()
				if B.get('code')==0:return True,'Success'
				else:return _A,B.get(_C,'Unknown error')
			else:return _A,f"Server returned status code: {A.status_code}"
		except Exception as H:return _A,str(H)
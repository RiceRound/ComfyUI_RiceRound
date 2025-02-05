_B='inputs'
_A='class_type'
import json,os,random,tempfile,time
from.rice_def import RiceRoundErrorDef
from server import PromptServer
from.auth_unit import AuthUnit
from.utils import get_local_app_setting_path
from.rice_prompt_info import RicePromptInfo
class RiceRoundPromptHandler:
	_instance=None;_initialized=False
	def __new__(A,*B,**C):
		if A._instance is None:A._instance=super(RiceRoundPromptHandler,A).__new__(A)
		return A._instance
	def __init__(A):
		if not A._initialized:A.client_id='';A.task_uuid='';A._initialized=True
	def onprompt_handler(B,json_data):
		'\n        处理传入的 JSON 数据\n        :param json_data: 输入的 JSON 数据，包含各种任务信息\n        ';J='input';I='template';H='task_uuid';G='client_id';D='prompt';A=json_data;RicePromptInfo().clear()
		if D not in A:return A
		E=False;K=A[D]
		for L in K.values():
			M=L.get(_A)
			if M in['RiceRoundEncryptNode','RiceRoundDecryptNode']:E=True;break
		if E:
			N,O,F=AuthUnit().get_user_token()
			if not N:
				if F==RiceRoundErrorDef.HTTP_UNAUTHORIZED or F==RiceRoundErrorDef.NO_TOKEN_ERROR:AuthUnit().login_dialog('RiceRound云节点，请先完成登录');A[D]={};return A
				else:PromptServer.instance.send_sync('riceround_toast',{'content':f"无法完成鉴权登录，{O}",'type':'error'});return A
		if G not in A:return A
		B.client_id=A[G]
		if H not in A:return A
		B.task_uuid=A[H]
		if I not in A:raise Exception("Warning: 'template' is missing.")
		print(f"RiceRoundPromptHandler self.client_id={B.client_id!r} self.task_uuid={B.task_uuid!r}");P=A[J]if J in A else{};C=A[D];C=B.replace_output_prompt(C);Q,R=B.parse_template(A[I]);C=B.replace_input_prompt(C,P,Q,R);print(f"RiceRoundPromptHandler prompt_data={C!r}");A[D]=C;return A
	def parse_template(E,template_data):
		B={};C={};D=template_data['elements']
		for A in D:id=A['id'];C[id]=A['node_id'];B[id]=A['type']
		return B,C
	def replace_output_prompt(C,prompt_data):
		'\n        替换输出节点中的 task_id\n        :param prompt_data: 任务的 prompt 数据\n        :return: 替换后的 prompt 数据\n        ';B=prompt_data
		for(D,A)in B.items():
			if A.get(_A)=='RiceRoundOutputImageNode':A[_B]['task_id']=C.task_uuid
			elif A.get(_A)=='RiceRoundRandomSeedNode':A[_B]['seed']=random.randint(0,999999)
		return B
	def replace_input_prompt(G,prompt_data,input_data,id_type_map,node_id_map):
		F='image_url';B='str';A=prompt_data;H={'text':'text_info','image_upload':F,'mask_image_upload':F,'mask_upload':'mask_url','number_int':B,'number_float':B,'choice':'default','switch':B}
		for(C,I)in input_data.items():
			D=id_type_map.get(C,'');E=H.get(D)
			if not E:print(f"RiceRoundPromptHandler replace_input_prompt unknown input_type {D}");continue
			J=A[node_id_map[C]];J[_B][E]=str(I)
		if os.environ.get('RICEROUND_DEBUG_SAVE_PROMPT')=='true':
			K=tempfile.gettempdir()
			with open(f"{K}//{G.task_uuid}_prompt_data.json",'w')as L:json.dump(A,L,indent=4)
		return A
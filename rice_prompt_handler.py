_C='inputs'
_B='class_type'
_A='prompt'
import json,os,random,tempfile,time
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
		'\n        处理传入的 JSON 数据\n        :param json_data: 输入的 JSON 数据，包含各种任务信息\n        ';G='input';F='template';E='task_uuid';D='client_id';A=json_data;RicePromptInfo().clear();B.search_and_set_temp_token(A)
		if D not in A:return A
		B.client_id=A[D]
		if E not in A:return A
		B.task_uuid=A[E]
		if _A not in A:raise Exception("Warning: 'prompt' is missing.")
		if F not in A:raise Exception("Warning: 'template' is missing.")
		print(f"RiceRoundPromptHandler self.client_id={B.client_id!r} self.task_uuid={B.task_uuid!r}");H=A[G]if G in A else{};C=A[_A];C=B.replace_output_prompt(C);I,J=B.parse_template(A[F]);C=B.replace_input_prompt(C,H,I,J);print(f"RiceRoundPromptHandler prompt_data={C!r}");A[_A]=C;return A
	def search_and_set_temp_token(E,json_data):
		D=json_data.get(_A,{});B='';C=None
		for(F,A)in D.items():
			if A.get(_B)=='RiceRoundTempTokenNode':B=A.get(_C,{}).get('text','')
			if A.get(_B)=='RiceRoundDecryptNode':C=A
		if B and C:AuthUnit().set_temp_token(B)
		else:AuthUnit().set_temp_token('')
	def parse_template(E,template_data):
		B={};C={};D=template_data['elements']
		for A in D:id=A['id'];C[id]=A['node_id'];B[id]=A['type']
		return B,C
	def replace_output_prompt(C,prompt_data):
		'\n        替换输出节点中的 task_id\n        :param prompt_data: 任务的 prompt 数据\n        :return: 替换后的 prompt 数据\n        ';B=prompt_data
		for(D,A)in B.items():
			if A.get(_B)=='RiceRoundOutputImageNode':A[_C]['task_id']=C.task_uuid
			elif A.get(_B)=='RiceRoundRandomSeedNode':A[_C]['seed']=random.randint(0,999999)
		return B
	def replace_input_prompt(F,prompt_data,input_data,id_type_map,node_id_map):
		B='str';A=prompt_data;G={'text':'text_info','image_upload':'image_url','mask_upload':'mask_url','number_int':B,'number_float':B,'choice':'default','switch':B}
		for(C,H)in input_data.items():
			D=id_type_map.get(C,'');E=G.get(D)
			if not E:print(f"RiceRoundPromptHandler replace_input_prompt unknown input_type {D}");continue
			I=A[node_id_map[C]];I[_C][E]=str(H)
		if os.environ.get('DEBUG')=='true':
			J=tempfile.gettempdir()
			with open(f"{J}//{F.task_uuid}_prompt_data.json",'w')as K:json.dump(A,K,indent=4)
		return A
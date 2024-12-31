_G='file_name'
_F='options_value'
_E='choice_node'
_D='python_class_name'
_C='utf-8'
_B=False
_A=True
import configparser,hashlib,json,os
from pathlib import Path
import sys
from server import PromptServer
import re
from.utils import get_local_app_setting_path
class RicePromptInfo:
	_instance=None;_initialized=_B
	def __new__(A):
		if A._instance is None:A._instance=super(RicePromptInfo,A).__new__(A)
		return A._instance
	def __init__(A):
		if RicePromptInfo._initialized:return
		A.task_info_folder=get_local_app_setting_path()/'tasks'
		if not A.task_info_folder.exists():A.task_info_folder.mkdir(parents=_A)
		A.choice_node_map={};A.new_choice_file_map={};A.choice_classname_map={};A.load_choice_node_map();RicePromptInfo._initialized=_A
	def clear(A):A.choice_node_map.clear();A.new_choice_file_map.clear()
	def get_choice_server_folder(B):
		A=B.task_info_folder/_E
		if not A.exists():A.mkdir(parents=_A)
		return A
	def load_choice_node_map(A):
		E=A.get_choice_server_folder()
		for B in E.glob('*.json'):
			try:
				with open(B,'r',encoding=_C)as F:
					C=json.load(F);D=C.get(_D)
					if D:A.choice_classname_map[D]=C
			except json.JSONDecodeError:print(f"Error parsing JSON from server file: {B}");continue
	def get_choice_node_options(A,node_class_name):return A.choice_classname_map.get(node_class_name,{}).get(_F,[])
	def get_choice_classname(A,node_id):return A.choice_node_map.get(node_id,{}).get(_D,'')
	def get_choice_value(A,node_id):return A.choice_node_map.get(node_id,{}).get(_F,[])
	def save_choice_classname(D,save_folder):
		A=Path(save_folder)/_E
		if not A.exists():A.mkdir(parents=_A)
		for(F,B)in D.new_choice_file_map.items():
			C=B.get(_G,'')
			if C:
				with open(A/f"{C}.json",'w',encoding=_C)as E:json.dump(B,E,ensure_ascii=_B,indent=4)
	def set_node_additional_info(B,node_additional_info):
		H='template_id';C=node_additional_info
		if C and isinstance(C,dict):
			B.template_id=C.get(H,'');I=C.get('choice_node_map',{})
			for(D,A)in I.items():
				D=int(D);G=A.get('class_name','');A[H]=B.template_id;A['display_name']=G;J=A.get('node_type','')
				if J=='RiceRoundAdvancedChoiceNode':
					E=re.sub('[<>:"/\\\\|?*]','',G);F='RiceRoundAdvancedChoiceNode_'+hashlib.md5(E.lower().encode()).hexdigest()
					if F in B.choice_classname_map:print(f"Error RicePromptInfo set_node_additional_info python_class_name {F} already exists");PromptServer.instance.send_sync('rice_round_toast',{'content':'选择名称重复，如果本身是同一类型的节点，可以忽略提示','type':'info','duration':5000})
					A[_D]=F;A[_G]=E;B.new_choice_file_map[E]=A
				B.choice_node_map[D]=A
class RiceEnvConfig:
	def __init__(A):A.local_app_path=get_local_app_setting_path();A.config_path=A.local_app_path/'config.ini'
	def filter_add_cmd(F,add_cmd):
		B=add_cmd;C=[];A=_B
		if not B:return''
		try:
			for D in B.split():
				if A:A=_B;continue
				if D in['--listen','--port']:A=_A;continue
				C.append(D)
		except Exception as E:print(f"Error processing add_cmd: {E}");return''
		return' '.join(C)
	def read_env(A):B=sys.executable;C=os.getcwd();D=' '.join(sys.argv[1:]);E=A.filter_add_cmd(D).strip();return{'PythonPath':B,'WorkingDirectory':C,'AddCmd':E}
	def save_env_config(A):
		C='ComfyUI';D=A.read_env();A.local_app_path.mkdir(parents=_A,exist_ok=_A);B=configparser.ConfigParser()
		if A.config_path.exists():B.read(A.config_path,encoding=_C)
		if not B.has_section(C):B.add_section(C)
		for(E,F)in D.items():B.set(C,E,F)
		with open(A.config_path,'w',encoding=_C)as G:B.write(G)
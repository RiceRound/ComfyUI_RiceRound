_L='RiceRoundAdvancedChoiceNode'
_K='node_type'
_J='wait_time'
_I='run_client'
_H='auto_publish'
_G='auto_overwrite'
_F='python_class_name'
_E='options_value'
_D='utf-8'
_C='Settings'
_B=False
_A=True
import configparser,copy,hashlib,json,os
from pathlib import Path
import sys
from.auth_unit import AuthUnit
from.rice_url_config import download_template
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
		B=get_local_app_setting_path();B.mkdir(parents=_A,exist_ok=_A);A.config_path=B/'config.ini';A.choice_node_map={};A.auto_overwrite=A._read_config_bool(_C,_G,_B);A.auto_publish=A._read_config_bool(_C,_H,_A);A.run_client=A._read_config_bool(_C,_I,_A);A.wait_time=A._read_config_int(_C,_J,600);A.choice_classname_map={};A.load_choice_node_map();RicePromptInfo._initialized=_A
	def _read_config_bool(D,section,key,default=_B):
		'读取配置文件中的布尔值';B=default;A=section
		try:C=configparser.ConfigParser();C.read(D.config_path,encoding=_D);return C.getboolean(A,key,fallback=B)
		except Exception as E:print(f"Error reading config {A}.{key}: {E}");return B
	def _read_config_int(D,section,key,default=0):
		'读取配置文件中的整数';B=default;A=section
		try:C=configparser.ConfigParser();C.read(D.config_path,encoding=_D);return C.getint(A,key,fallback=B)
		except Exception as E:print(f"Error reading config {A}.{key}: {E}");return B
	def _write_config_bool(C,section,key,value):
		'写入布尔值到配置文件';B=section
		try:
			A=configparser.ConfigParser();A.read(C.config_path,encoding=_D)
			if not A.has_section(B):A.add_section(B)
			A.set(B,key,str(value).lower())
			with open(C.config_path,'w',encoding=_D)as D:A.write(D)
			return _A
		except Exception as E:print(f"Error writing config {B}.{key}: {E}");return _B
	def _write_config_int(C,section,key,value):
		'写入整数到配置文件';B=section
		try:
			A=configparser.ConfigParser();A.read(C.config_path,encoding=_D)
			if not A.has_section(B):A.add_section(B)
			A.set(B,key,str(value))
			with open(C.config_path,'w',encoding=_D)as D:A.write(D)
			return _A
		except Exception as E:print(f"Error writing config {B}.{key}: {E}");return _B
	def set_auto_overwrite(A,auto_overwrite):B=auto_overwrite;A.auto_overwrite=B;A._write_config_bool(_C,_G,B)
	def get_auto_overwrite(A):return A.auto_overwrite
	def set_auto_publish(A,auto_publish):B=auto_publish;A.auto_publish=B;A._write_config_bool(_C,_H,B)
	def get_auto_publish(A):return A.auto_publish
	def set_run_client(A,run_client):B=run_client;A.run_client=B;A._write_config_bool(_C,_I,B)
	def get_run_client(A):return A.run_client
	def set_wait_time(A,wait_time):B=wait_time;A.wait_time=B;A._write_config_int(_C,_J,B)
	def get_wait_time(A):return max(A.wait_time,10)
	def clear(A):A.choice_node_map.clear()
	def get_choice_server_folder(B):
		A=get_local_app_setting_path()/'choice_node'
		if not A.exists():A.mkdir(parents=_A)
		return A
	def load_choice_node_map(E):
		"\n        Load and parse choice node options from JSON files in the choice_server_folder.\n        Each JSON file should contain an 'elements' array with choice node configurations.\n        ";K=E.get_choice_server_folder()
		for A in K.glob('*.json'):
			try:
				with open(A,'r',encoding=_D)as L:
					F=json.load(L)
					if not isinstance(F,dict):print(f"Warning: Invalid JSON structure in file: {A}");continue
					G=F.get('elements',[])
					if not isinstance(G,list):print(f"Warning: 'elements' is not a list in file: {A}");continue
					for C in G:
						if not isinstance(C,dict):continue
						if C.get('type')!='choice':continue
						B=C.get('addition',{})
						if not B or not isinstance(B,dict):continue
						if B.get(_K)!=_L:continue
						M=C.get('settings',{});H=M.get('options',[]);I=B.get(_F)
						if I and isinstance(H,list):J=copy.deepcopy(B);J[_E]=H;E.choice_classname_map[I]=J
			except json.JSONDecodeError as D:print(f"Error parsing JSON from file {A}: {str(D)}")
			except Exception as D:print(f"Unexpected error processing file {A}: {str(D)}");continue
	def install_choice_node(D,template_id):
		A=template_id;B,E,C=AuthUnit().get_user_token()
		if not B:
			print(f"riceround get user token failed, {E}")
			if C==401 or C==-3:AuthUnit().login_dialog('安装节点需要先完成登录')
			else:PromptServer.instance.send_sync('riceround_toast',{'content':'无法完成鉴权登录，请检查网络或完成登录步骤','type':'error'})
			return _B
		F=D.get_choice_server_folder()/f"{A}.json"
		try:download_template(A,B,F)
		except Exception as G:print(f"failed to download template, {G}");return _B
		return _A
	def get_choice_node_addition(B,node_id):
		A=copy.deepcopy(B.choice_node_map.get(node_id,{}))
		if A and isinstance(A,dict):A.pop(_E,None);return A
		return{}
	def get_choice_node_options(A,node_class_name):return A.choice_classname_map.get(node_class_name,{}).get(_E,[])
	def get_choice_classname(A,node_id):return A.choice_node_map.get(node_id,{}).get(_F,'')
	def get_choice_value(A,node_id):return A.choice_node_map.get(node_id,{}).get(_E,[])
	def set_node_additional_info(B,node_additional_info):
		E='template_id';C=node_additional_info
		if C and isinstance(C,dict):
			B.template_id=C.get(E,'');F=C.get('choice_node_map',{})
			for(D,A)in F.items():
				D=int(D);G=A.get('class_name','');A[E]=B.template_id;A['display_name']=G;H=A.get(_K,'')
				if H==_L:I=f"RiceRoundAdvancedChoiceNode_{B.template_id}_{D}";A[_F]=I
				B.choice_node_map[D]=A
class RiceEnvConfig:
	def __init__(A):0
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
	def read_env(K):
		J='ScriptName';I='AddCmd';H='WorkingDirectory';G='PythonPath';F='"\'';E='\\';C='/'
		try:
			D=sys.executable.replace(E,C);B=os.getcwd().replace(E,C);L=' '.join(sys.argv[1:]);M=K.filter_add_cmd(L).strip();A=sys.argv[0].replace(E,C)
			if B in A:A=A.replace(B,'').lstrip(C)
			D=D.strip(F);B=B.strip(F);A=A.strip(F);return{G:D,H:B,I:M,J:A}
		except Exception as N:print(f"Error reading environment: {str(N)}");return{G:'',H:'',I:'',J:''}
_D='user_token'
_C=None
_B='Auth'
_A='utf-8'
import base64,json,os
from pathlib import Path
import time
from urllib.parse import urljoin
from.utils import get_local_app_path,get_machine_id
from.rice_url_config import RiceUrlConfig
from server import PromptServer
import urllib.request,urllib.error,configparser
class AuthUnit:
	_instance=_C
	def __new__(A,*B,**C):
		if A._instance is _C:A._instance=super(AuthUnit,A).__new__(A)
		return A._instance
	def __init__(A):
		B=True
		if not hasattr(A,'initialized'):A.machine_id=get_machine_id();A.url_config=RiceUrlConfig();A.callback_path='/riceround/auth_callback';A.shift_key=sum(ord(A)for A in A.machine_id[:8])%20+1;C=get_local_app_path();C.mkdir(parents=B,exist_ok=B);A.config_path=C/'config.ini';A.auto_login=False;A.load_config();A.last_check_time=0;A.temp_token='';A.long_token='';A.initialized=B
	def load_config(A):B=configparser.ConfigParser();B.read(A.config_path,encoding=_A);A.auto_login=B.get(_B,'auto_login',fallback=False)
	def set_temp_token(A,temp_token):A.temp_token=temp_token
	def set_user_long_token(B,long_token):
		A=long_token
		if not A:B.long_token=''
		elif len(A)==64:B.long_token=A
	def get_user_token(B):
		A=''
		if B.long_token:A=B.long_token
		else:A=B.read_user_token()
		if not A and B.temp_token:A=B.temp_token
		if A and time.time()-B.last_check_time>120:
			try:
				D=urllib.request.Request(B.url_config.login_api_url,headers={'Content-Type':'application/json','Authorization':f"Bearer {A}"},method='GET')
				with urllib.request.urlopen(D)as C:
					if C.status!=200:A=_C;print(f"Auth failed, token: {A}")
					else:E=json.loads(C.read().decode(_A));B.url_config.set_server_info(E);B.last_check_time=time.time();return A
			except urllib.error.URLError:A=_C
		if not A:B.login_in()
		return A
	def login_in(A):
		PromptServer.instance.send_sync('rice_round_login',{'machine_id':A.machine_id,'url_prefix':A.url_config.web_url_prefix})
		if A.auto_login:import webbrowser as C;B='';D=urljoin(A.url_config.comfyui_local_base_url,A.callback_path);E=base64.b64encode(D.encode(_A)).decode(_A);B='&callback_url='+E;F=A.url_config.auth_web_url+'?machine_id='+A.machine_id+B;C.open(F)
	@staticmethod
	def _encrypt(text,shift_key):
		'Encrypt text using a simple character shift and base64 encoding.'
		try:A=''.join(chr((ord(A)+shift_key)%65536)for A in text);return base64.b64encode(A.encode(_A)).decode(_A)
		except Exception as B:print(f"Encryption error: {B}");return text
	@staticmethod
	def _decrypt(encoded_text,shift_key):
		'Decrypt text that was encrypted with the _encrypt method.';A=encoded_text
		try:B=base64.b64decode(A.encode(_A)).decode(_A);return''.join(chr((ord(A)-shift_key)%65536)for A in B)
		except Exception as C:print(f"Decryption error: {C}");return A
	def read_user_token(A):
		'Retrieve and decrypt the user token.'
		if not os.path.exists(A.config_path):return''
		try:
			B=configparser.ConfigParser();B.read(A.config_path,encoding=_A);C=B.get(_B,'test_user_token',fallback='')
			if C:return C
			D=B.get(_B,_D,fallback='')
			if not D:return''
			return AuthUnit._decrypt(D,A.shift_key)
		except Exception as E:print(f"Error reading token: {E}");return''
	def save_user_token(A,user_token):
		'Encrypt and save the user token.';C=user_token
		if not C:return
		if C==A.temp_token:return
		try:
			B=configparser.ConfigParser()
			if os.path.exists(A.config_path):B.read(A.config_path,encoding=_A)
			if _B not in B:B.add_section(_B)
			E=AuthUnit._encrypt(C,A.shift_key);B[_B][_D]=E
			with open(A.config_path,'w',encoding=_A)as F:B.write(F)
		except Exception as D:print(f"Error saving token: {D}");raise RuntimeError(f"Failed to save token: {D}")
	def clear_user_token(A):A.save_user_token('')
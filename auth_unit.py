_D='user_token'
_C='utf-8'
_B='Auth'
_A=None
import os,time,requests,configparser
from.rice_def import RiceRoundErrorDef
from.utils import get_local_app_setting_path,get_machine_id,generate_random_string
from.rice_url_config import RiceUrlConfig
from server import PromptServer
class AuthUnit:
	_instance=_A
	def __new__(A,*B,**C):
		if A._instance is _A:A._instance=super(AuthUnit,A).__new__(A)
		return A._instance
	def __init__(A):
		B=True
		if not hasattr(A,'initialized'):A.machine_id=get_machine_id();C=get_local_app_setting_path();C.mkdir(parents=B,exist_ok=B);A.config_path=C/'config.ini';A.last_check_time=0;A.initialized=B;A.user_id=0
	def empty_token(A,need_clear=False):
		A.token='';A.last_check_time=0
		if need_clear:A.clear_user_token()
	def get_user_token(A):
		F='message';A.token=A.read_user_token()
		if time.time()-A.last_check_time>120 and A.token and len(A.token)>50:
			try:
				G={'Content-Type':'application/json','Authorization':f"Bearer {A.token}"};B=requests.get(RiceUrlConfig().get_info_url,headers=G,timeout=10)
				if B.status_code==200:
					H=B.json()
					try:A.user_id=int(H.get('user_id',0)or 0)
					except(ValueError,TypeError):A.user_id=0
					A.last_check_time=time.time();return A.token,'',RiceRoundErrorDef.SUCCESS
				else:
					C='登录结果错误';D=RiceRoundErrorDef.UNKNOWN_ERROR
					try:
						E=B.json()
						if F in E:C=E[F]
					except ValueError:pass
					if B.status_code==401:C='登录已过期，请重新登录';D=RiceRoundErrorDef.HTTP_UNAUTHORIZED
					elif B.status_code==500:C='服务器内部错误，请稍后重试';D=RiceRoundErrorDef.HTTP_INTERNAL_ERROR
					elif B.status_code==503:C='服务不可用，请稍后重试';D=RiceRoundErrorDef.HTTP_SERVICE_UNAVAILABLE
					A.empty_token(B.status_code==401);return _A,C,D
			except requests.exceptions.Timeout:A.empty_token();return _A,'请求超时，请检查网络连接',RiceRoundErrorDef.HTTP_TIMEOUT
			except requests.exceptions.ConnectionError:A.empty_token();return _A,'网络连接失败，请检查网络',RiceRoundErrorDef.NETWORK_ERROR
			except requests.exceptions.RequestException as I:A.empty_token();return _A,f"请求失败: {str(I)}",RiceRoundErrorDef.REQUEST_ERROR
		if A.token and len(A.token)>50:return A.token,'',RiceRoundErrorDef.SUCCESS
		return _A,'未读取到有效的token，请重新登录',RiceRoundErrorDef.NO_TOKEN_ERROR
	def get_user_info(A):
		D,C,B=A.get_user_token()
		if B==RiceRoundErrorDef.SUCCESS and A.user_id:return B,A.user_id
		else:return B,C
	def login_dialog(A,title=''):A.client_key=generate_random_string(8);PromptServer.instance.send_sync('riceround_login_dialog',{'machine_id':A.machine_id,'client_key':A.client_key,'title':title})
	def read_user_token(A):
		if not os.path.exists(A.config_path):return''
		try:B=configparser.ConfigParser();B.read(A.config_path,encoding=_C);return B.get(_B,_D,fallback='')
		except Exception as C:print(f"Error reading token: {C}");return''
	def set_user_token(B,user_token,client_key):
		C=client_key;A=user_token
		if not C or B.client_key!=C:return
		if not A:A='';print('user_token is empty')
		B.save_user_token(A)
	def save_user_token(B,user_token):
		try:
			A=configparser.ConfigParser()
			try:
				if os.path.exists(B.config_path):A.read(B.config_path,encoding=_C)
			except Exception as D:print(f"Warning: Error reading existing config: {D}")
			if _B not in A:A.add_section(_B)
			A[_B][_D]=user_token
			with open(B.config_path,'w',encoding=_C)as E:A.write(E)
		except Exception as C:print(f"Error saving token: {C}");raise RuntimeError(f"Failed to save token: {C}")
	def set_long_token(A,long_token):
		B=long_token
		if not B:return
		A.save_user_token(B);A.client_key=''
	def clear_user_token(B):
		PromptServer.instance.send_sync('riceround_clear_user_info',{'clear_key':'all'})
		if os.path.exists(B.config_path):
			try:
				A=configparser.ConfigParser();A.read(B.config_path,encoding=_C)
				if _B not in A:return
				if _D not in A[_B]:return
				A[_B][_D]=''
				with open(B.config_path,'w',encoding=_C)as D:A.write(D)
			except Exception as C:print(f"Error clearing token: {C}");raise RuntimeError(f"Failed to clear token: {C}")
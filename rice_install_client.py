_L='找不到可执行文件'
_K='ComfyUI'
_J='utf-8'
_I='client.toml'
_H='win32'
_G='ComfyuiScriptName'
_F='ScriptName'
_E=None
_D='PythonPath'
_C='WorkingDirectory'
_B=True
_A=False
import os,shutil,sys,tempfile,time,portalocker,requests,tomlkit
from tomlkit import comment,table,dumps
import subprocess
from.rice_def import RiceRoundErrorDef
from.rice_url_config import RiceUrlConfig
from.auth_unit import AuthUnit
from.rice_prompt_info import RiceEnvConfig
from.utils import get_local_app_setting_path
class RiceInstallClient:
	def __init__(A):A.current_path=os.path.dirname(os.path.abspath(__file__));A.app_path=get_local_app_setting_path();A.source_executable_filename,A.executable_filename=A._get_platform_executables()
	def _get_platform_executables(B):
		'Get platform-specific executable filenames.';A='share_client'
		if sys.platform==_H:return'share_client_windows.exe','share_client.exe'
		elif sys.platform=='darwin':return'share_client_mac',A
		elif sys.platform=='linux':return'share_client_linux',A
		else:raise OSError(f"Unsupported platform: {sys.platform}")
	def is_client_running(C):
		if not C.is_client_installed():return _A
		A=os.path.join(tempfile.gettempdir(),'rice_client.lock')
		if not os.path.exists(A):return _A
		try:
			with open(A,'w')as B:portalocker.lock(B,portalocker.LOCK_EX|portalocker.LOCK_NB);portalocker.unlock(B);return _A
		except portalocker.LockException:return _B
	def is_client_installed(A):
		if not A.app_path.exists():return _A
		B=A.app_path/A.executable_filename
		if not B.exists():return _A
		C=A.app_path/_I
		if not C.exists():return _A
		return _B
	def repair_client_toml(N,client_toml_path):
		E=client_toml_path
		if not E.exists():return _A
		try:
			A=RiceEnvConfig().read_env()
			if not A:print('Error: Failed to read environment config');return _A
			if not A.get(_D)or not os.path.exists(A[_D]):print('Error: Invalid Python path in environment config');return _A
			G=A.get(_C);C=A.get(_F)
			if not G or not C:print('Error: Missing working directory or script name in environment config');return _A
			if os.path.isabs(C)and os.path.exists(C):H=C
			else:H=os.path.join(G,C)
			if not os.path.exists(H):print('Error: ComfyUI script path does not exist in environment config');return _A
			with open(E,'r',encoding=_J)as F:
				I=tomlkit.load(F);B=I.get(_K)
				if not B or not isinstance(B,dict):return _A
				D=B.get(_G);J=B.get(_C)
				if J is _E or D is _E:B[_C]=A[_C];B[_G]=A[_F]
				else:
					if os.path.isabs(D)and os.path.exists(D):K=D
					else:K=os.path.join(J,D)
					if not os.path.exists(K):B[_C]=A[_C];B[_G]=A[_F]
				L=B.get(_D)
				if L is _E or not os.path.exists(L):B[_D]=A[_D]
			with open(E,'w',encoding=_J)as F:F.write(dumps(I))
			return _B
		except Exception as M:print(f"Error repairing client.toml: {str(M)}");return _A
	def install_client_toml(D,comfyui_port,local_server_port,secret_token):
		F='AddCmd';E='Port';C=RiceEnvConfig().read_env();os.makedirs(D.app_path,exist_ok=_B);B=tomlkit.document();B.add(comment('日志级别设置'));B.add(comment("可选值: 'debug', 'info', 'warn', 'error'"));B['LogLevel']='info';B.add(comment('机器码，非常重要，用于登录鉴权'));B.add(comment('在官网可以获取自己的机器码，普通用户也可以由管理员授予'));B['SecretToken']=secret_token;B.add(comment('本地服务端口'));B.add(comment('用于本地服务端口，通常为 6608'));B[E]=local_server_port;A=table();A.add(comment('ComfyUI 监听的端口'));A.add(comment('端口号，默认为 6607'));A[E]=comfyui_port;A.add(comment('Python 解释器路径'));A.add(comment('这里填写你安装的 Python 解释器路径，确保 Python 环境已经配置好'));A[_D]=str(C[_D]);A.add(comment('ComfyUI 脚本的文件名'));A.add(comment("这里填写 ComfyUI 的启动脚本名，通常是 'main.py'"));A[_G]=C[_F];A.add(comment('ComfyUI 工作目录'));A.add(comment('这里填写 ComfyUI 所在的目录路径'));A[_C]=str(C[_C]);A.add(comment('环境命令，用于激活相关环境'));A.add(comment('例如可以填写 conda 环境的激活命令 conda activate comfyui'));A['EnvCmd']='';A.add(comment('启动时附加的命令行参数'));A.add(comment("可根据需要添加，常用的如 '--disable-metadata'"));A[F]=C[F];B[_K]=A
		try:
			G=D.app_path/_I
			with open(G,'w',encoding=_J)as H:H.write(dumps(B))
			return _B
		except Exception as I:print(f"Error writing client.toml: {str(I)}");return _A
	def install_client_executable(A):
		try:
			B=os.path.join(A.current_path,A.source_executable_filename);C=os.path.join(A.app_path,A.executable_filename)
			if os.path.exists(C):return _B
			if not os.path.exists(B):raise FileNotFoundError(f"Executable file not found: {B}")
			shutil.copyfile(B,C)
			if sys.platform=='linux':os.chmod(C,493)
			return _B
		except Exception as D:print(f"Error installing client executable: {str(D)}");return _A
	def run_client(A,comfyui_port=6607,local_server_port=6608):
		if A.is_client_running():return RiceRoundErrorDef.SUCCESS,''
		F=A.app_path/A.executable_filename
		if not F.exists():A.install_client_executable()
		D=A.app_path/_I
		if not D.exists():
			E,C,B=A.get_secret_token()
			if not E:return B if B!=RiceRoundErrorDef.SUCCESS else RiceRoundErrorDef.ERROR_SECRET_TOKEN,C
			if not A.install_client_toml(comfyui_port,local_server_port,E):return RiceRoundErrorDef.ERROR_INSTALL_CLIENT_TOML,'安装client.toml失败'
		else:A.repair_client_toml(D)
		B,C=A.start_client();return B,C
	def start_client(B):
		A=B.app_path/B.executable_filename
		if not A.exists():return RiceRoundErrorDef.ERROR_EXECUTABLE_NOT_FOUND,_L
		try:
			if sys.platform==_H:E=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_BREAKAWAY_FROM_JOB;C=subprocess.Popen(str(A),shell=_B,start_new_session=_B,creationflags=E,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=_B)
			else:C=subprocess.Popen(str(A),shell=_A,start_new_session=_B,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=_B)
			time.sleep(10)
			if C.poll()is not _E:return RiceRoundErrorDef.ERROR_PROCESS_EXIT,'程序启动后异常退出'
			else:return RiceRoundErrorDef.SUCCESS,''
		except Exception as D:print(f"程序启动异常: {str(D)}");return RiceRoundErrorDef.ERROR_START_EXCEPTION,str(D)
	def get_secret_token(I):
		D='获取密钥失败';C,E,A=AuthUnit().get_user_token()
		if not C:return _E,E,A
		F={'Content-Type':'application/json','Authorization':f"Bearer {C}"}
		try:
			B=requests.get(RiceUrlConfig().machine_bind_key_url,headers=F,timeout=10)
			if B.status_code!=200:A=B.status_code;return _E,D,RiceRoundErrorDef.calc_error_code(RiceRoundErrorDef.ERROR_MACHINE_CODE_BASE,A)
			G=B.json()['key'];return G,'',0
		except Exception as H:return _E,D+str(H),RiceRoundErrorDef.ERROR_SECRET_TOKEN
	def restart_client(C):
		E='--reload';B=C.app_path/C.executable_filename
		if not B.exists():return RiceRoundErrorDef.ERROR_EXECUTABLE_NOT_FOUND,_L
		try:
			import subprocess as A
			if sys.platform==_H:F=A.DETACHED_PROCESS|A.CREATE_NO_WINDOW;G=A.Popen([str(B),E],shell=_A,creationflags=F,start_new_session=_B,stdin=A.DEVNULL,stdout=A.DEVNULL,stderr=A.DEVNULL,close_fds=_B)
			else:G=A.Popen([str(B),E],shell=_A,start_new_session=_B,stdin=A.DEVNULL,stdout=A.DEVNULL,stderr=A.DEVNULL,close_fds=_B)
			return RiceRoundErrorDef.SUCCESS,''
		except Exception as D:print(f"重启程序异常: {str(D)}");return RiceRoundErrorDef.ERROR_RESTART_EXCEPTION,str(D)
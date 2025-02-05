_C='RiceRound'
_B=True
_A='utf-8'
import configparser,hashlib
from io import BytesIO
import os
from pathlib import Path
import random,string,sys,uuid,torch,numpy as np
from PIL import Image
import platform,subprocess
def pil2tensor(images):
	'Converts a PIL Image or a list of PIL Images to a tensor.';A=images
	def B(image):
		A=np.array(image).astype(np.float32)/255.
		if A.ndim==2:return torch.from_numpy(A).unsqueeze(0)
		else:return torch.from_numpy(A).unsqueeze(0)
	if isinstance(A,Image.Image):return B(A)
	else:return torch.cat([B(A)for A in A],dim=0)
def calculate_machine_id():
	'\n    获取跨平台的机器唯一标识符，类似于 gopsutil 的 HostID\n    ';A=platform.system()
	if A=='Linux':
		try:
			with open('/etc/machine-id','r')as B:return B.read().strip()
		except FileNotFoundError:
			try:
				with open('/var/lib/dbus/machine-id','r')as B:return B.read().strip()
			except FileNotFoundError:pass
		try:C=subprocess.check_output(['cat','/sys/class/dmi/id/product_uuid']);return C.decode().strip()
		except Exception:pass
	elif A=='Windows':
		try:
			import winreg as D;F='SOFTWARE\\Microsoft\\Cryptography'
			with D.OpenKey(D.HKEY_LOCAL_MACHINE,F)as G:H,I=D.QueryValueEx(G,'MachineGuid');return H
		except Exception:pass
	elif A=='Darwin':
		try:
			C=subprocess.check_output(['ioreg','-rd1','-c','IOPlatformExpertDevice'])
			for E in C.decode().splitlines():
				if'IOPlatformUUID'in E:return E.split('=')[-1].strip().strip('"')
		except Exception:pass
	return str(uuid.getnode())
def normalize_machine_id(machine_id):'\n    接受一个机器标识符，并返回经过 MD5 哈希处理的规范化标识符\n    ';A=_C;B=machine_id.strip();C=B.lower();D=C+A;E=hashlib.md5(D.encode(_A));return E.hexdigest()
def get_local_app_setting_path():A=Path.home();B=A/_C;return B
def get_machine_id():
	'\n    返回机器ID，为了兼容各个平台，各个语言，需要统一读写这个值\n    ';F='machine_id';B='Machine';D=get_local_app_setting_path();C=D/'machine.ini'
	try:D.mkdir(parents=_B,exist_ok=_B)
	except Exception as E:print(f"Error creating directory '{D}': {E}");return''
	A=configparser.ConfigParser()
	try:
		if C.exists():
			A.read(C,encoding=_A)
			if B in A and F in A[B]:return A[B][F]
		H=calculate_machine_id();G=normalize_machine_id(H)
		if B not in A:A.add_section(B)
		A.set(B,F,G)
		with open(C,'w',encoding=_A)as I:A.write(I)
		return G
	except Exception as E:print(f"Error handling machine ID in '{C}': {E}");return''
def restart():
	D='--windows-standalone-build';C='__COMFY_CLI_SESSION__'
	try:sys.stdout.close_log()
	except Exception:pass
	if C in os.environ:
		with open(os.path.join(os.environ[C]+'.reboot'),'w'):0
		print('Restarting...\n\n');exit(0)
	A=sys.argv.copy()
	if D in A:A.remove(D)
	if sys.platform.startswith('win32'):B=['"'+sys.executable+'"','"'+A[0]+'"']+A[1:]
	else:B=[sys.executable]+A
	print(f"Command: {B}",flush=_B);return os.execv(sys.executable,B)
def combine_files(files,password,zip_file_path):
	D=files;A=password;import pyzipper as C
	for B in D:
		if not os.path.exists(B):raise FileNotFoundError(f"file not found: {B}")
	try:
		with C.AESZipFile(zip_file_path,'w',compression=C.ZIP_DEFLATED,encryption=C.WZ_AES)as E:
			if isinstance(A,str):A=A.encode(_A)
			E.setpassword(A)
			for(F,B)in enumerate(D,start=1):G=f"{F}.bin";E.write(B,G)
		return _B
	except Exception as H:print(f"Error creating zip: {str(H)}");return False
def generate_random_string(length):'\n    Generate a random string of specified length using uppercase and lowercase letters.\n    \n    Args:\n        length (int): The desired length of the random string\n        \n    Returns:\n        str: A random string of the specified length\n    ';A=string.ascii_letters;return''.join(random.choice(A)for B in range(length))
_P='Message'
_O='CommandType'
_N='resultData'
_M='templateName'
_L='templateDescription'
_K='templateId'
_J='updateTime'
_I='createTime'
_H='prompt'
_G='thumbnail'
_F='progressText'
_E='progress'
_D='state'
_C='taskUuid'
_B=False
_A=None
import datetime
from enum import Enum
import json,time,threading
from typing import Any,Callable,Optional
import asyncio,websockets
from websockets.exceptions import ConnectionClosedError
import comfy.model_management as model_management
COMMAND_TYPE_USER_SERVER_TASK_PROGRESS=5004
COMMAND_TYPE_USER_CLIENT_WEB_COMMAND_CANCEL_TASK=4002
class TaskStatus(Enum):
	CREATED=0;PENDING=1;IN_PROGRESS=2;FINISHED=3;FAILED=4;CANCELLED=5
	def __lt__(A,other):
		B=other
		if A.__class__ is B.__class__:return A.value<B.value
		return NotImplemented
	def __le__(A,other):
		B=other
		if A.__class__ is B.__class__:return A.value<=B.value
		return NotImplemented
	def __gt__(A,other):
		B=other
		if A.__class__ is B.__class__:return A.value>B.value
		return NotImplemented
	def __ge__(A,other):
		B=other
		if A.__class__ is B.__class__:return A.value>=B.value
		return NotImplemented
class TaskInfo:
	def __init__(A,json_data):'\n        Initialize TaskInfo from JSON data\n        \n        Args:\n            json_data (dict): JSON data containing task information\n        ';B=json_data;A.task_uuid=B.get(_C,'');A.state=TaskStatus(B.get(_D,0));A.progress=B.get(_E,0);A.progress_text=B.get(_F,'');A.thumbnail=B.get(_G,'');A.prompt=B.get(_H,'');A.create_time=B.get(_I,'');A.update_time=B.get(_J,'');A.template_id=B.get(_K,'');A.template_description=B.get(_L,'');A.template_name=B.get(_M,'');A.result_data=B.get(_N,_A);A.lock=threading.Lock();A.preview_refreshed=_B
	def to_dict(A):'\n        Convert TaskInfo to a dictionary\n        \n        Returns:\n            dict: The dictionary representation of the TaskInfo object\n        ';return{_C:A.task_uuid,_D:A.state.value,_E:A.progress,_F:A.progress_text,_G:A.thumbnail,_H:A.prompt,_I:A.create_time,_J:A.update_time,_K:A.template_id,_L:A.template_description,_M:A.template_name}
	def update_progress(A,json_data):
		C=json_data
		with A.lock:
			if C.get(_C,'')!=A.task_uuid:return _B
			D=TaskStatus(C.get(_D,0))
			if D<A.state:return _B
			A.state=D;E=C.get(_E,0);B=C.get(_F,'')
			if E==0 and B=='preview_refreshed':print(f"Task {A.task_uuid} preview_refreshed");A.preview_refreshed=True
			else:
				A.preview_refreshed=_B
				if E>A.progress:A.progress=E;A.progress_text=B
				elif D==TaskStatus.FAILED:A.progress_text=B if B else'task failed'
				elif D==TaskStatus.CANCELLED:A.progress_text=B if B else'task cancelled'
				else:return _B
			F=C.get(_N,_A)
			if F:A.result_data=F
			elif A.state==TaskStatus.IN_PROGRESS:A.result_data=_A
			return True
	def is_task_done(A):
		with A.lock:return A.state>=TaskStatus.FINISHED
	def __str__(A):'\n        Get a string representation of the task\n        \n        Returns:\n            str: A human-readable string describing the task status\n        ';return f"Task {A.task_uuid}: {A.state.name} ({A.progress}%) - {A.progress_text}"
class PackageMessage:
	def __init__(A,CommandType,Message):A.CommandType=CommandType;A.Message=Message
	def to_json(A):return json.dumps({_O:A.CommandType,_P:A.Message})
	@classmethod
	def from_json(B,data):A=json.loads(data);return B(A[_O],A[_P])
class TaskWebSocket:
	def __init__(A,url,token,machine_id,task_info,progress_callback,timeout=600):B=timeout;A.url=f"{url}?machine_id={machine_id}";A.token=token;A.task_info=task_info;A.stop_event=asyncio.Event();A.timeout=B;A.progress_callback=progress_callback;A.last_progress_time=_A;A.message_timeout=B-3 if B<600 else 600;A.websocket=_A;A.task=_A
	async def connect(A):
		try:
			B=f"{A.url}&token={A.token}"
			async with websockets.connect(B)as C:A.websocket=C;await A.on_connection_open();await A.run_tasks()
		except Exception as D:print(f"Connection error: {D}")
	async def run_tasks(A):
		try:
			C=asyncio.create_task(A.on_receive());D=asyncio.create_task(A.monitor_progress_timeout());F,E=await asyncio.wait([C,D],timeout=A.timeout,return_when=asyncio.FIRST_COMPLETED);A.stop_event.set()
			for B in E:
				print(f"cancel task {B}");B.cancel()
				try:await B
				except asyncio.CancelledError:pass
		finally:A.stop_event.set()
	async def on_receive(A):
		try:
			if not A.websocket or A.stop_event.is_set():return
			async for B in A.websocket:
				if A.stop_event.is_set():break
				await A.on_message(B)
		except Exception as C:print(f"Error while listening to messages: {C}")
	async def monitor_progress_timeout(A):
		while not A.stop_event.is_set():
			await asyncio.sleep(5)
			try:model_management.throw_exception_if_processing_interrupted()
			except Exception as B:
				print(f"Processing interrupted during progress monitoring: {B}");A.stop_event.set();C=PackageMessage(CommandType=COMMAND_TYPE_USER_CLIENT_WEB_COMMAND_CANCEL_TASK,Message={'task_uuid':A.task_info.task_uuid})
				try:await A.send_message(C)
				except Exception as D:print(f"Failed to send cancel notification: {D}")
				break
			E=asyncio.get_event_loop().time()
			if A.last_progress_time and E-A.last_progress_time>A.message_timeout:print(f"No task progress received within {A.message_timeout} seconds, disconnecting...");A.stop_event.set();break
	async def on_message(B,message):
		try:
			A=PackageMessage.from_json(message)
			if A.CommandType==COMMAND_TYPE_USER_SERVER_TASK_PROGRESS:await B.handle_task_progress(A)
			else:print(f"Unknown message type: {A.CommandType}")
		except Exception as C:print(f"Message unpacking error: {C}")
	async def on_connection_open(A):print('WebSocket connection connected')
	async def send_message(A,message):
		try:
			if A.websocket:await A.websocket.send(message.to_json())
		except Exception as B:print(f"Error sending message: {B}")
	async def handle_task_progress(A,package):
		if not A.task_info or A.stop_event.is_set():return
		B=asyncio.get_event_loop();A.last_progress_time=B.time()
		if A.task_info.update_progress(package.Message):
			print(f"Task progress updated: {A.task_info}")
			if A.progress_callback:A.progress_callback(A.task_info.task_uuid,A.task_info.progress_text,A.task_info.progress,A.task_info.preview_refreshed)
		if A.task_info.is_task_done():print('task is done');A.stop_event.set()
	async def shutdown(A):
		print('shutdown websocket');A.stop_event.set();A.progress_callback=_A
		if A.websocket:
			try:await A.websocket.close()
			except websockets.ConnectionClosed:pass
			finally:A.websocket=_A
def start_and_wait_task_done(task_ws_url,user_token,machine_id,task_info,progress_callback,timeout=7200):
	async def A():
		A=TaskWebSocket(task_ws_url,user_token,machine_id,task_info,progress_callback,timeout)
		try:await A.connect()
		except asyncio.CancelledError:print('Task cancelled')
		finally:await A.shutdown()
	asyncio.run(A())
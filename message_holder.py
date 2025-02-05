_A=False
import json,os,time,requests
from server import PromptServer
from aiohttp import web
class Cancelled(Exception):0
class MessageHolder:
	stash={};messages={};cancelled=_A
	@classmethod
	def addMessage(A,id,message):
		B=message
		if B=='__cancel__':A.messages={};A.cancelled=True
		elif B=='__start__':A.messages={};A.stash={};A.cancelled=_A
		else:A.messages[str(id)]=B
	@classmethod
	def waitForMessage(A,id,period=.1,timeout=60):
		B=str(id);A.messages.clear();C=time.time()
		while not B in A.messages and not'-1'in A.messages:
			if A.cancelled:A.cancelled=_A;raise Cancelled()
			if time.time()-C>timeout:raise Cancelled('Operation timed out')
			time.sleep(period)
		if A.cancelled:A.cancelled=_A;raise Cancelled()
		D=A.messages.pop(str(id),None)or A.messages.pop('-1');return D.strip()
routes=PromptServer.instance.routes
@routes.post('/riceround/message')
async def message_handler(request):A=await request.post();MessageHolder.addMessage(A.get('id'),A.get('message'));return web.json_response({})
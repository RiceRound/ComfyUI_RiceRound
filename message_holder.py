import json
import os
import time
import requests
from server import PromptServer
from aiohttp import web


class Cancelled(Exception):
    0


class MessageHolder:
    messages = {}
    cancelled = False

    @classmethod
    def addMessage(cls, id, message):
        if message == "__cancel__":
            cls.messages = {}
            cls.cancelled = True
        elif message == "__start__":
            cls.messages = {}
            cls.cancelled = False
        else:
            cls.messages[str(id)] = message

    @classmethod
    def waitForMessage(cls, id, period=0.1, timeout=60):
        sid = str(id)
        cls.messages.clear()
        cls.cancelled = False
        start_time = time.time()
        while sid not in cls.messages:
            if cls.cancelled:
                cls.cancelled = False
                raise Cancelled()
            if time.time() - start_time > timeout:
                raise Cancelled("Operation timed out")
            time.sleep(period)
        if cls.cancelled:
            cls.cancelled = False
            raise Cancelled()
        return cls.messages.pop(sid)


routes = PromptServer.instance.routes


@routes.post("/riceround/message")
async def message_handler(request):
    data = await request.json()
    MessageHolder.addMessage(data["id"], data["message"])
    return web.json_response({})

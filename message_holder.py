import json
import os
import time
import requests
from server import PromptServer
from aiohttp import web


class Cancelled(Exception):
    0


class MessageHolder:
    stash = {}
    messages = {}
    cancelled = False

    @classmethod
    def addMessage(cls, id, message):
        if message == "__cancel__":
            cls.messages = {}
            cls.cancelled = True
        elif message == "__start__":
            cls.messages = {}
            cls.stash = {}
            cls.cancelled = False
        else:
            cls.messages[str(id)] = message

    @classmethod
    def waitForMessage(cls, id, period=0.1, timeout=60):
        sid = str(id)
        cls.messages.clear()
        start_time = time.time()
        while not sid in cls.messages and not "-1" in cls.messages:
            if cls.cancelled:
                cls.cancelled = False
                raise Cancelled()
            if time.time() - start_time > timeout:
                raise Cancelled("Operation timed out")
            time.sleep(period)
        if cls.cancelled:
            cls.cancelled = False
            raise Cancelled()
        message = cls.messages.pop(str(id), None) or cls.messages.pop("-1")
        return message.strip()


routes = PromptServer.instance.routes


@routes.post("/riceround/message")
async def message_handler(request):
    post = await request.post()
    MessageHolder.addMessage(post.get("id"), post.get("message"))
    return web.json_response({})

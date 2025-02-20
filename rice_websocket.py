import datetime
from enum import Enum
import json
import time
import threading
from typing import Any, Callable, Optional
import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError
import comfy.model_management as model_management

COMMAND_TYPE_USER_SERVER_TASK_PROGRESS = 5004
COMMAND_TYPE_USER_CLIENT_WEB_COMMAND_CANCEL_TASK = 4002


class TaskStatus(Enum):
    CREATED = 0
    PENDING = 1
    IN_PROGRESS = 2
    FINISHED = 3
    FAILED = 4
    CANCELLED = 5

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class TaskInfo:
    def __init__(self, json_data):
        "\n        Initialize TaskInfo from JSON data\n        \n        Args:\n            json_data (dict): JSON data containing task information\n"
        self.task_uuid = json_data.get("task_uuid", "")
        self.state = TaskStatus(json_data.get("state", 0))
        self.progress = json_data.get("progress", 0)
        self.progress_text = json_data.get("progress_text", "")
        self.thumbnail = json_data.get("thumbnail", "")
        self.prompt = json_data.get("prompt", "")
        self.create_time = json_data.get("create_time", "")
        self.update_time = json_data.get("update_time", "")
        self.template_id = json_data.get("template_id", "")
        self.template_description = json_data.get("template_description", "")
        self.template_name = json_data.get("template_name", "")
        self.result_data = json_data.get("result_data", None)
        self.lock = threading.Lock()
        self.preview_refreshed = False

    def to_dict(self):
        "\n        Convert TaskInfo to a dictionary\n        \n        Returns:\n            dict: The dictionary representation of the TaskInfo object\n"
        return {
            "task_uuid": self.task_uuid,
            "state": self.state.value,
            "progress": self.progress,
            "progress_text": self.progress_text,
            "thumbnail": self.thumbnail,
            "prompt": self.prompt,
            "create_time": self.create_time,
            "update_time": self.update_time,
            "template_id": self.template_id,
            "template_description": self.template_description,
            "template_name": self.template_name,
        }

    def update_progress(self, json_data):
        with self.lock:
            if json_data.get("task_uuid", "") != self.task_uuid:
                return False
            state = TaskStatus(json_data.get("state", 0))
            if state < self.state:
                return False
            self.state = state
            progress = json_data.get("progress", 0)
            progress_text = json_data.get("progress_text", "")
            if progress == 0 and progress_text == "preview_refreshed":
                print(f"Task {self.task_uuid} preview_refreshed")
                self.preview_refreshed = True
            else:
                self.preview_refreshed = False
                if progress > self.progress:
                    self.progress = progress
                    self.progress_text = progress_text
                elif state == TaskStatus.FAILED:
                    self.progress_text = (
                        progress_text if progress_text else "task failed"
                    )
                elif state == TaskStatus.CANCELLED:
                    self.progress_text = (
                        progress_text if progress_text else "task cancelled"
                    )
                else:
                    return False
            result_data = json_data.get("result_data", None)
            if result_data:
                self.result_data = result_data
            elif self.state == TaskStatus.IN_PROGRESS:
                self.result_data = None
            return True

    def is_task_done(self):
        with self.lock:
            return self.state >= TaskStatus.FINISHED

    def __str__(self):
        "\n        Get a string representation of the task\n        \n        Returns:\n            str: A human-readable string describing the task status\n"
        return f"Task {self.task_uuid}: {self.state.name} ({self.progress}%) - {self.progress_text}"


class PackageMessage:
    def __init__(self, CommandType, Message):
        self.CommandType = CommandType
        self.Message = Message

    def to_json(self):
        return json.dumps({"CommandType": self.CommandType, "Message": self.Message})

    @classmethod
    def from_json(cls, data):
        parsed = json.loads(data)
        return cls(parsed["CommandType"], parsed["Message"])


class TaskWebSocket:
    def __init__(
        self, url, token, machine_id, task_info, progress_callback, timeout=600
    ):
        self.url = f"{url}?machine_id={machine_id}"
        self.token = token
        self.task_info = task_info
        self.stop_event = asyncio.Event()
        self.timeout = timeout
        self.progress_callback = progress_callback
        self.last_progress_time = None
        self.message_timeout = timeout - 3 if timeout < 600 else 600
        self.websocket = None
        self.task = None

    async def connect(self):
        try:
            ws_url = f"{self.url}&token={self.token}"
            async with websockets.connect(ws_url) as websocket:
                self.websocket = websocket
                await self.on_connection_open()
                await self.run_tasks()
        except Exception as e:
            print(f"Connection error: {e}")

    async def run_tasks(self):
        try:
            receive_task = asyncio.create_task(self.on_receive())
            monitor_task = asyncio.create_task(self.monitor_progress_timeout())
            done, pending = await asyncio.wait(
                [receive_task, monitor_task],
                timeout=self.timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )
            self.stop_event.set()
            for task in pending:
                print(f"cancel task {task}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        finally:
            self.stop_event.set()

    async def on_receive(self):
        try:
            if not self.websocket or self.stop_event.is_set():
                return
            async for message in self.websocket:
                if self.stop_event.is_set():
                    break
                await self.on_message(message)
        except Exception as e:
            print(f"Error while listening to messages: {e}")

    async def monitor_progress_timeout(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(5)
            try:
                model_management.throw_exception_if_processing_interrupted()
            except Exception as e:
                print(f"Processing interrupted during progress monitoring: {e}")
                self.stop_event.set()
                cancel_message = PackageMessage(
                    CommandType=COMMAND_TYPE_USER_CLIENT_WEB_COMMAND_CANCEL_TASK,
                    Message={"task_uuid": self.task_info.task_uuid},
                )
                try:
                    await self.send_message(cancel_message)
                except Exception as send_err:
                    print(f"Failed to send cancel notification: {send_err}")
                break
            current_time = asyncio.get_event_loop().time()
            if (
                self.last_progress_time
                and current_time - self.last_progress_time > self.message_timeout
            ):
                print(
                    f"No task progress received within {self.message_timeout} seconds, disconnecting..."
                )
                self.stop_event.set()
                break

    async def on_message(self, message):
        try:
            package = PackageMessage.from_json(message)
            if package.CommandType == COMMAND_TYPE_USER_SERVER_TASK_PROGRESS:
                await self.handle_task_progress(package)
            else:
                print(f"Unknown message type: {package.CommandType}")
        except Exception as e:
            print(f"Message unpacking error: {e}")

    async def on_connection_open(self):
        print("WebSocket connection connected")

    async def send_message(self, message):
        try:
            if self.websocket:
                await self.websocket.send(message.to_json())
        except Exception as e:
            print(f"Error sending message: {e}")

    async def handle_task_progress(self, package):
        if not self.task_info or self.stop_event.is_set():
            return
        loop = asyncio.get_event_loop()
        self.last_progress_time = loop.time()
        if self.task_info.update_progress(package.Message):
            print(f"Task progress updated: {self.task_info}")
            if self.progress_callback:
                self.progress_callback(
                    self.task_info.task_uuid,
                    self.task_info.progress_text,
                    self.task_info.progress,
                    self.task_info.preview_refreshed,
                )
        if self.task_info.is_task_done():
            print("task is done")
            self.stop_event.set()

    async def shutdown(self):
        print("shutdown websocket")
        self.stop_event.set()
        self.progress_callback = None
        if self.websocket:
            try:
                await self.websocket.close()
            except websockets.ConnectionClosed:
                pass
            finally:
                self.websocket = None


def start_and_wait_task_done(
    task_ws_url, user_token, machine_id, task_info, progress_callback, timeout=7200
):
    async def main():
        task_ws = TaskWebSocket(
            task_ws_url, user_token, machine_id, task_info, progress_callback, timeout
        )
        try:
            await task_ws.connect()
        except asyncio.CancelledError:
            print("Task cancelled")
        finally:
            await task_ws.shutdown()

    asyncio.run(main())

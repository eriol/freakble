import asyncio
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from .ble import BLE_interface
from .ble import connect as ble_connect


class TimedBuffer:
    def __init__(self):
        self._buffer = []

    def append(self, data):
        self._buffer.append(f"[{datetime.now()}] {data}")

    def content(self):
        return "\n".join(self._buffer)


class App:
    def config(self, adapter, device, ble_connection_timeout):
        self.adapter = adapter
        self.device = device
        self.ble_connection_timeout = ble_connection_timeout

    async def run(self):
        self.window = Window(self, asyncio.get_event_loop())
        await self.window.show()


class Window(tk.Tk):
    def __init__(self, app, loop):
        self.app = app
        self.loop = loop
        self.root = tk.Tk()
        self.root.title("freakble")
        self.root.geometry("640x480")

        self.buffer = TimedBuffer()
        self.make_ui()

        self.task1 = self.loop.create_task(self.ble_loop())

        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def make_ui(self):
        self.frame = ttk.Frame(self.root, borderwidth=5, relief="ridge", height=100)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.message = tk.Message(
            self.frame, bg="white", justify="left", anchor="nw", width=640
        )
        self.message.pack(fill=tk.BOTH, expand=True)
        self.entry = ttk.Entry(self.root)
        self.entry.pack(fill=tk.X)

    async def ble_loop(self):
        self.ble = BLE_interface(self.app.adapter, None)
        self.ble.set_receiver(self._on_ble_data_received)
        await ble_connect(self.ble, self.app.device, self.app.ble_connection_timeout)
        await asyncio.gather(self.ble.send_loop(), self.send())

    async def send(self):
        while True:
            # self.ble.queue_send(bytes("Hello!", "utf-8"))
            await asyncio.sleep(10)

    def _on_ble_data_received(self, data):
        data = data.decode("utf-8").rstrip()
        print(f"Rx: {data}")
        self.buffer.append(data)

    def quit(self):
        self.root.destroy()
        # TODO: properly close using an asyncio.Event: using click is hard to
        # pass it from main. One possible solution is to stop using click.
        self.loop.stop()

    async def show(self):
        while True:
            self.message["text"] = self.buffer.content()
            self.root.update()
            await asyncio.sleep(0.1)

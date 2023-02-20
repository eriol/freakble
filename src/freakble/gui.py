# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""This module contains a simple GUI for freakble."""

import asyncio
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from ttkthemes import ThemedTk

from .ble import BLE_interface
from .ble import connect as ble_connect

WINDOW_SIZE = "800x600"


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
        self.root = ThemedTk(theme="breeze")
        self.root.title("freakble")
        self.root.geometry(WINDOW_SIZE)
        self.root.option_add("*Font", "12")

        self.make_ui()

        self.task = self.loop.create_task(self.ble_loop())

        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def make_ui(self):
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.frame_text = ttk.Frame(self.frame, relief="ridge", width=100, height=100)
        self.frame_text.grid(row=0, column=0, sticky="news")
        self.frame_text.rowconfigure(0, weight=1)
        self.frame_text.columnconfigure(0, weight=1)
        self.v_scrollbar = ttk.Scrollbar(self.frame_text)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(
            self.frame_text,
            bg="white",
            width=100,
            height=100,
            yscrollcommand=self.v_scrollbar.set,
            state=tk.DISABLED,
        )
        self.text.pack(side=tk.TOP, fill=tk.X)
        self.v_scrollbar.config(command=self.text.yview)

        self.entry = ttk.Entry(self.frame, width=100)
        self.entry.grid(row=1, column=0, sticky="news")
        self.entry.rowconfigure(0, weight=1)
        self.entry.columnconfigure(0, weight=1)
        self.entry.focus_set()
        self.entry.bind("<Return>", self.on_entry_return)
        self.button = ttk.Button(self.entry, text="⮕")
        self.button.pack(side=tk.RIGHT)
        self.button.rowconfigure(1, weight=1)
        self.button.columnconfigure(1, weight=1)
        self.button.bind("<Button-1>", self.on_entry_return)

    async def ble_loop(self):
        self.ble = BLE_interface(self.app.adapter, "")
        self.ble.set_receiver(self.on_ble_data_received)
        await ble_connect(self.ble, self.app.device, self.app.ble_connection_timeout)
        await self.ble.send_loop()

    def send_over_ble(self, data):
        self.ble.queue_send(bytes(data, "utf-8"))

    def on_ble_data_received(self, data):
        data = data.decode("utf-8")
        self.insert_text(data)

    def insert_text(self, text):
        now = datetime.now().strftime("%y/%m/%d %H:%M:%S")
        self.text["state"] = tk.NORMAL
        self.text.insert(tk.END, f"[{now}] {text}")
        self.text["state"] = tk.DISABLED

    def on_entry_return(self, e):
        text = self.entry.get()
        self.send_over_ble(text)
        self.insert_text(f"{text}\n")
        self.entry.delete(0, len(text))

    def quit(self):
        self.root.destroy()
        # TODO: properly close using an asyncio.Event: using click is hard to
        # pass it from main. One possible solution is to stop using click.
        self.loop.stop()

    async def show(self):
        while True:
            self.root.update()
            await asyncio.sleep(0.1)

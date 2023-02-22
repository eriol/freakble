# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""This module contains a simple GUI for freakble."""

import asyncio
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

from ttkthemes import ThemedTk

from .ble import BLE_interface
from .ble import connect as ble_connect

WINDOW_SIZE = "800x600"


class App:
    def config(self, adapter, device, ble_connection_timeout):
        self.adapter = adapter
        self.device = device
        self.ble_connection_timeout = ble_connection_timeout
        self.loop = asyncio.get_event_loop()

    async def run(self):
        self.window = MainWindow(self, theme="breeze")
        await self.window.show()


class MainWindow(ThemedTk):
    def __init__(self, app, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.app = app
        self.title("freakble")
        self.geometry(WINDOW_SIZE)
        self.option_add("*Font", "12")

        self.protocol("WM_DELETE_WINDOW", self.quit)

        self.make_ui()

        self.windows = {}

        for window in (ScanWindow, DeviceWindow):
            w = window(self.container, self)
            self.windows[window] = w
            w.grid(row=0, column=0, sticky="news")

        self.show_window(DeviceWindow)

    def make_ui(self):
        self.container = ttk.Frame(self)
        self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

    def quit(self):
        self.destroy()
        # TODO: properly close using an asyncio.Event: using click is hard to
        # pass it from main. One possible solution is to stop using click.
        self.app.loop.stop()

    async def show(self):
        while True:
            self.update()
            await asyncio.sleep(0.1)

    def show_window(self, window):
        for w in self.windows:
            w.grid_forget(self)

        frame = self.windows[window]
        frame.tkraise()


class ScanWindow(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)

        self.parent = parent
        self.main_window = main_window

        self.make_ui()

    def make_ui(self):
        self.button = ttk.Button(self, text="Scan")
        self.button.grid(row=1, column=1, sticky="nesw")


class DeviceWindow(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)

        self.main_window = main_window

        self.make_ui()

        self.task = self.main_window.app.loop.create_task(self.ble_loop())

    def make_ui(self):
        # Make the frame expand to the whole window.
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.text = scrolledtext.ScrolledText(
            self,
            bg="white",
            state=tk.DISABLED,
        )
        self.text.grid(row=0, column=0, sticky="news")

        self.frame_send = ttk.Frame(self, width=100)
        self.frame_send.grid(row=1, column=0, sticky="news")
        self.frame_send.rowconfigure(1, weight=1)
        self.frame_send.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(self.frame_send, width=100)
        self.entry.grid(row=1, column=0, sticky="news")
        self.entry.rowconfigure(0, weight=1)
        self.entry.columnconfigure(0, weight=1)
        self.entry.focus_set()
        self.entry.bind("<Return>", self.on_entry_return)
        self.button = ttk.Button(self.frame_send, text="⮞")
        self.button.grid(row=1, column=1, sticky="nesw")
        self.button.rowconfigure(1, weight=1)
        self.button.columnconfigure(1, weight=1)
        self.button.bind("<Button-1>", self.on_entry_return)

    async def ble_loop(self):
        self.ble = BLE_interface(self.main_window.app.adapter, "")
        self.ble.set_receiver(self.on_ble_data_received)
        await ble_connect(
            self.ble,
            self.main_window.app.device,
            self.main_window.app.ble_connection_timeout,
        )
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
        # Scroll to the end.
        self.text.see(tk.END)

    def on_entry_return(self, _):
        text = self.entry.get()
        self.send_over_ble(text)
        self.insert_text(f"{text}\n")
        self.entry.delete(0, len(text))

import asyncio
import tkinter as tk


class App:
    async def run(self):
        self.window = Window(asyncio.get_event_loop())
        await self.window.show()


class Window(tk.Tk):
    def __init__(self, loop):
        self.loop = loop
        self.root = tk.Tk()
        self.root.title("freakble")
        self.root.geometry("640x480")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def quit(self):
        self.root.destroy()
        # TODO: properly close.
        # self.loop.stop()

    async def show(self):
        while True:
            self.root.update()
            await asyncio.sleep(0.1)

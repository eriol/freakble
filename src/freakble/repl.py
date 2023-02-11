# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""This module contains a simple interactive shell for FreakWAN nodes."""

import asyncio

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

PROMPT_MESSAGE = "Φ] "

command_completer = WordCompleter(["!automsg off", "!automsg on", "!bat"])


class REPL:
    """Simple interactive shell able to send data over BLE."""

    def __init__(self, ble) -> None:  # noqa: D107
        # We consider the BLE interface already connected and we use it to
        # send and receive data. The ownership remains outside of this class.
        self.ble = ble
        self.ble.set_receiver(self._on_ble_data_received)

    async def shell(self):
        """Display a prompt and handle user interaction."""
        session = PromptSession(PROMPT_MESSAGE, completer=command_completer)
        while True:
            try:
                with patch_stdout():
                    text = await session.prompt_async()
                    self._send_over_ble(text)
            except (EOFError, KeyboardInterrupt):
                raise asyncio.CancelledError

    def _on_ble_data_received(self, data):
        """Print data received from ble."""
        data = data.decode("utf-8")
        print(f"{data}")

    def _send_over_ble(self, data):
        """Send data over BLE."""
        self.ble.queue_send(bytes(data, "utf-8"))

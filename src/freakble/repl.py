# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""This module contains a simple interactive shell for FreakWAN nodes."""

import asyncio
from itertools import cycle

from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

PROMPT_MESSAGE = "Φ] "

# These bandwidth values are for LYLIGO TTGO LoRa (TM) v2 1.6 and similar, the
# boards we use for FreakWAN.
BW_VALUES = [
    7800,
    10400,
    15600,
    20800,
    31250,
    41700,
    62500,
    62500,
    125000,
    250000,
    500000,
]

command_completer = NestedCompleter.from_nested_dict(
    {
        "!automsg": {"on": None, "off": None},
        "!bat": None,
        "!bw": dict(zip(map(str, BW_VALUES), cycle([None]))),
        "!cr": dict(zip(map(str, range(5, 9)), cycle([None]))),
        "!help": None,
        "!sp": dict(zip(map(str, range(6, 13)), cycle([None]))),
    }
)


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

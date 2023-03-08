# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""This module contains a simple interactive shell for freakble."""

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
CR_VALUES = range(5, 9)
PW_VALUES = range(2, 21)
SP_VALUES = range(6, 13)

command_completer = NestedCompleter.from_nested_dict(
    {
        "!automsg": {"on": None, "off": None},
        "!bat": None,
        "!bw": dict(zip(map(str, BW_VALUES), cycle([None]))),
        "!config": {"save": None, "reset": None},
        "!cr": dict(zip(map(str, CR_VALUES), cycle([None]))),
        "!font": {"big": None, "small": None},
        "!help": None,
        "!irc": {"start": None, "stop": None},
        "!last": None,
        "!ls": None,
        "!pw": dict(zip(map(str, PW_VALUES), cycle([None]))),
        "!quiet": {"yes": None, "no": None},
        "!sp": dict(zip(map(str, SP_VALUES), cycle([None]))),
    }
)


class REPL:
    """Simple interactive shell able to send data over Bluetooth LE."""

    def __init__(self, client) -> None:
        # We use the client to set the callback and to send and receive data.
        # The ownership remains outside of this class.
        self._client = client
        self._client.set_receive_callback(self._on_ble_data_received)

    async def shell(self):
        """Display a prompt and handle user interaction."""
        session = PromptSession(PROMPT_MESSAGE, completer=command_completer)
        while True:
            try:
                with patch_stdout():
                    text = await session.prompt_async()
                    await self._client.send(bytes(text, "utf-8"))
            except (EOFError, KeyboardInterrupt):
                raise asyncio.CancelledError

    def _on_ble_data_received(self, data):
        """Print data received from Bluetooth LE."""
        print(f"{data}")

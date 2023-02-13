# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""BLE related stuff for freakble."""

import asyncio

from ble_serial.bluetooth.ble_interface import BLE_interface

# We use this module as a facade for ble_serial scanner.
from ble_serial.scan import main as scanner

from .repl import REPL

__all__ = [
    "connect",
    "repl_loop",
    "scanner",
    "send_text",
]


async def connect(ble: BLE_interface, device: str, timeout: float = 10.0):
    """Connect to the specified device."""
    await ble.connect(device, "public", timeout)
    # TODO: Handle WRITE_UUID and READ_UUID.
    await ble.setup_chars(None, None, "rw")


async def send(ble: BLE_interface, data: bytes, loop: bool, sleep_time: float):
    """Send data over BLE.

    Raise asyncio.CancelledError if loop == False after data is sent once.
    """
    while True:
        ble.queue_send(data)
        if not loop:
            raise asyncio.CancelledError
        await asyncio.sleep(sleep_time)


async def send_text(
    adapter: str,
    text: str,
    device: str,
    loop: bool,
    sleep_time: float,
    ble_connection_timeout: float,
    callback=None,
):
    """Send text over BLE.

    This is a facade that handle also connection/disconnection.
    """
    ble = BLE_interface(adapter, None)
    if callback is not None:
        ble.set_receiver(callback)

    try:
        await connect(ble, device, ble_connection_timeout)
        await asyncio.gather(
            ble.send_loop(),
            send(ble, bytes(text, "utf-8"), loop, sleep_time),
        )
    except asyncio.CancelledError:
        pass
    except AssertionError:
        raise
    finally:
        await ble.disconnect()


async def repl_loop(
    adapter: str,
    device: str,
    ble_connection_timeout: float,
):
    """Run a REPL over BLE.

    This is a facade that handle also connection/disconnection.
    """
    ble = BLE_interface(adapter, None)
    repl = REPL(ble)
    try:
        await connect(ble, device, ble_connection_timeout)
        await asyncio.gather(ble.send_loop(), repl.shell())
    except asyncio.CancelledError:
        pass
    except AssertionError:
        raise
    finally:
        await ble.disconnect()

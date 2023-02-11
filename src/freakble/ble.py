# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

import asyncio

from ble_serial.bluetooth.ble_interface import BLE_interface
from ble_serial.scan import main as scanner


async def connect(ble: BLE_interface, device):
    await ble.connect(device, "public", 10.0)
    # TODO: Handle WRITE_UUID and READ_UUID.
    await ble.setup_chars(None, None, "rw")


async def send_conditionally(
    ble: BLE_interface, data: bytes, loop: bool, sleep_time: float
):
    """Send specified data.

    Raise asyncio.CancelledError if loop == False after data is sent once.
    """
    ble.queue_send(data)
    if not loop:
        raise asyncio.CancelledError
    await asyncio.sleep(sleep_time)


async def send_forever(ble: BLE_interface, data: bytes, loop: bool, sleep_time: float):
    """Send data forever."""
    while True:
        await send_conditionally(ble, data, loop, sleep_time)
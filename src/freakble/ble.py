# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""BLE related stuff for freakble."""

import asyncio
import logging
from typing import Any, Callable

from bleak import BleakClient, BleakScanner

from .repl import REPL

__all__ = [
    "Client",
    "repl_loop",
    "scan",
    "send_text",
]

DEFAULT_TIMEOUT = 5.0
NORDIC_UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"


async def scan(adapter: str, timeout: float = DEFAULT_TIMEOUT):
    """Scan for Bluetooth LE devices."""
    return await BleakScanner.discover(adapter=adapter, timeout=timeout)


class Client:
    """Simple client for UART devices."""

    def __init__(self, adapter: str, address: str) -> None:
        self.adapter = adapter
        self.address = address

        self._receive_callback = None
        self.disconnect_event = asyncio.Event()
        self._client = None
        self.uart_rx_char = None
        self.uart_tx_char = None

    async def connect(self, timeout: float = DEFAULT_TIMEOUT):
        device = await BleakScanner.find_device_by_address(
            self.address, adapter=self.adapter, timeout=timeout
        )
        if device is None:
            raise RuntimeError(f"device with address {self.address} not found")
        self._client = BleakClient(device, disconnected_callback=self.on_disconnect)
        await self._client.__aenter__()
        for service in self._client.services:
            for char in service.characteristics:
                if "write" in char.properties:
                    self.uart_tx_char = char
                elif "notify" in char.properties:
                    self.uart_rx_char = char

    async def disconnect(self):
        if self._client is not None:
            await self.stop()
            await self._client.disconnect()

    async def start(self):
        if self._client is not None:
            await self._client.start_notify(self.uart_rx_char, self.on_rx)

    async def stop(self):
        if self._client is not None:
            await self._client.stop_notify(self.uart_rx_char)

    def set_receive_callback(self, callback: Callable[[Any], None]):
        self._receive_callback = callback

    def on_rx(self, characteristic, data):
        logging.debug(characteristic, data)
        data = data.decode("utf-8").rstrip()

        if self._receive_callback is not None:
            self._receive_callback(data)

    async def wait_until_disconnect(self):
        await self.disconnect_event.wait()

    def on_disconnect(self, client: BleakClient):
        logging.debug("Disconnect...")
        self.disconnect_event.set()

    async def send(self, data):
        if self._client is not None:
            await self._client.write_gatt_char(self.uart_tx_char, data)

    async def send_forever(self, data: bytes, sleep_time: float):
        while True:
            await self.send(data)
            await asyncio.sleep(sleep_time)


async def send_text(
    adapter: str,
    text: str,
    device: str,
    loop: bool,
    sleep_time: float,
    timeout: float,
    callback=None,
):
    """Send text over Bluetooth LE.

    This is a facade that handle also connection/disconnection.
    """
    client = Client(adapter, device)
    if callback is not None:
        client.set_receive_callback(callback)
    try:
        await client.connect(timeout)
        await client.start()
        if loop:
            await asyncio.gather(
                client.wait_until_disconnect(),
                client.send_forever(bytes(text, "utf-8"), sleep_time),
            )
        else:
            await client.send(bytes(text, "utf-8"))
    finally:
        await client.disconnect()


async def repl_loop(
    adapter: str,
    device: str,
    timeout: float,
):
    """Run a REPL over BLE.

    This is a facade that handle also connection/disconnection.
    """
    client = Client(adapter, device)
    try:
        repl = REPL(client)
        await client.connect(timeout)
        await client.start()
        await asyncio.gather(client.wait_until_disconnect(), repl.shell())
    except asyncio.CancelledError:
        pass
    except AssertionError:
        raise
    finally:
        await client.disconnect()

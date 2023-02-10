# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

import asyncio
import logging
from functools import wraps

import click
from ble_serial.bluetooth.ble_interface import BLE_interface


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


async def send_conditionally(ble: BLE_interface, data: bytes, loop: bool):
    """Send specified data.

    Raise asyncio.CancelledError if loop == True after data is sent once.
    """
    ble.queue_send(data)
    # TODO: Make the user able to specify sleep duration.
    await asyncio.sleep(0.1)
    if not loop:
        raise asyncio.CancelledError


async def send_forever(ble: BLE_interface, data: bytes, loop: bool):
    """Send data forever."""
    while True:
        await send_conditionally(ble, data, loop)


def _receive_callback(data: bytes):
    logging.debug("Received:", data)


@click.group()
@click.option("--adapter", default="hci0", type=str, help="ble adapter [default: hci0]")
@click.pass_context
def cli(ctx, adapter):
    """A simple tool to send messages into FreakWAN."""
    ctx.ensure_object(dict)
    ctx.obj["ADAPTER"] = adapter
    ctx.obj["BLE"] = BLE_interface(ctx.obj["ADAPTER"], None)


@cli.command()
@click.option("--loop", is_flag=True, default=False, help="send forever the messages")
@click.option("--device", required=True, type=str, help="ble device address")
@click.argument("messages", type=str, nargs=-1)
@click.pass_context
@coro
async def send(ctx, messages, device, loop):
    """Send one or more messages over BLE to a specific device."""
    msg = " ".join(messages)
    ble = ctx.obj["BLE"]
    ble.set_receiver(_receive_callback)
    try:
        logging.info(f"Connecting to {device}...")
        await ble.connect(device, "public", 10.0)
        # TODO: Handle WRITE_UUID and READ_UUID.
        await ble.setup_chars(None, None, "rw")

        await asyncio.gather(
            ble.send_loop(),
            send_forever(ble, bytes(msg, "utf-8"), loop),
        )
    except asyncio.CancelledError:
        pass
    finally:
        await ble.disconnect()


def run():
    """CLI entrypoint."""
    # ble-serial fire a warning on disconnect, but our main use case is to just
    # send a message and disconnect, so we disable logging here.
    # TODO: Make configurable by the user.
    logging.disable()

    asyncio.run(cli())

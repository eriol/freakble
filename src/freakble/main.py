# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause
"""A simple tool to send messages into FreakWAN over Bluetooth low energy."""

import asyncio
import logging
import warnings
from functools import wraps

import click
from ble_serial.bluetooth.ble_interface import BLE_interface
from ble_serial.scan import main as scanner


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


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


def _receive_callback(data: bytes):
    logging.debug("Received:", data)


@click.group()
@click.option(
    "--adapter", default="hci0", show_default="hci0", type=str, help="ble adapter"
)
@click.pass_context
def cli(ctx, adapter):
    """A simple tool to send messages into FreakWAN."""  # noqa: D401
    ctx.ensure_object(dict)
    ctx.obj["ADAPTER"] = adapter
    ctx.obj["BLE"] = BLE_interface(ctx.obj["ADAPTER"], None)


@cli.command()
@click.option("--loop", is_flag=True, default=False, help="send forever the messages")
@click.option("--device", required=True, type=str, help="ble device address")
@click.option(
    "--sleep-time",
    default=1,
    show_default="1 sec",
    type=float,
    help="sleep between messages sent with --loop",
)
@click.argument("messages", type=str, nargs=-1)
@click.pass_context
@coro
async def send(ctx, messages, device, loop, sleep_time):
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
            send_forever(ble, bytes(msg, "utf-8"), loop, sleep_time),
        )
    except asyncio.CancelledError:
        pass
    except AssertionError as e:
        click.echo(click.style(e, fg="red"))
    finally:
        await ble.disconnect()


@cli.command()
@click.option(
    "--scan-time", default=5, show_default="5 secs", type=float, help="scan duration"
)
@click.option(
    "--service-uuid",
    default=None,
    show_default="None",
    type=str,
    help="service UUID used to filter",
)
@click.pass_context
@coro
async def scan(ctx, scan_time, service_uuid):
    """Scan to find BLE devices."""
    devices = await scanner.scan(ctx.obj["ADAPTER"], scan_time, service_uuid)
    scanner.print_list(devices)


@cli.command()
@click.option("--device", required=True, type=str, help="ble device address")
@click.option(
    "--scan-time", default=5, show_default="5 secs", type=float, help="scan duration"
)
@click.pass_context
@coro
async def deep_scan(ctx, device, scan_time):
    """Scan to find services of a specific device."""
    devices = await scanner.scan(ctx.obj["ADAPTER"], scan_time, None)
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        services = await scanner.deep_scan(device, devices)
    scanner.print_details(services)


@cli.command()
@coro
async def version():
    """Scan to find services of a specific device."""
    # Import here to don't pollute main namespace.
    from . import __version__

    click.echo(f"freakble {__version__}")


def run():
    """CLI entrypoint."""
    # ble-serial fire a warning on disconnect, but our main use case is to just
    # send a message and disconnect, so we disable logging here.
    # TODO: Make configurable by the user.
    logging.disable()

    asyncio.run(cli())

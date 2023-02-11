# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause
"""A simple tool to send messages into FreakWAN over Bluetooth low energy."""

import asyncio
import logging
import sys
import warnings
from functools import wraps

import click

from . import __version__
from .ble import BLE_interface, scanner, send_conditionally, send_forever, connect
from .repl import REPL


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def ble_receive_callback(data: bytes):
    """Print data received from BLE."""
    click.echo(data)


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
@click.option("--loop", is_flag=True, default=False, help="send forever the message")
@click.option(
    "--device",
    required=True,
    type=str,
    envvar="FREAKBLE_DEVICE",
    help="ble device address",
)
@click.option(
    "--sleep-time",
    default=1,
    show_default="1 sec",
    type=float,
    help="sleep between messages sent with --loop",
)
@click.option(
    "--ble-connection-timeout",
    default=10,
    show_default="10 secs",
    type=float,
    help="BLE connection timeout",
)
@click.argument("words", type=str, nargs=-1)
@click.pass_context
@coro
async def send(ctx, words, device, loop, sleep_time, ble_connection_timeout):
    """Send one or more words over BLE to a specific device."""
    msg = " ".join(words)
    ble = ctx.obj["BLE"]
    ble.set_receiver(ble_receive_callback)
    logging.info(f"Connecting to {device}...")
    try:
        await connect(ble, device, ble_connection_timeout)
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
@click.option(
    "--device",
    required=True,
    type=str,
    envvar="FREAKBLE_DEVICE",
    help="ble device address",
)
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
@click.option(
    "--device",
    required=True,
    type=str,
    envvar="FREAKBLE_DEVICE",
    help="ble device address",
)
@click.option(
    "--ble-connection-timeout",
    default=10,
    show_default="10 secs",
    type=float,
    help="BLE connection timeout",
)
@click.pass_context
@coro
async def repl(ctx, device, ble_connection_timeout):
    """Start a REPL with the device."""
    ble = ctx.obj["BLE"]
    repl = REPL(ble)
    click.echo(f"freakble {__version__} on {sys.platform}")
    click.echo(f"Connecting to {device}...")
    try:
        await connect(ble, device, ble_connection_timeout)
        await asyncio.gather(ble.send_loop(), repl.shell())
    except asyncio.CancelledError:
        pass
    except AssertionError as e:
        click.echo(click.style(e, fg="red"))
    finally:
        await ble.disconnect()


@cli.command()
@coro
async def version():
    """Return freakble version."""
    click.echo(f"freakble {__version__}")


def run():
    """CLI entrypoint."""
    # ble-serial fire a warning on disconnect, but our main use case is to just
    # send a message and disconnect, so we disable logging here.
    # TODO: Make configurable by the user.
    logging.disable()

    asyncio.run(cli(auto_envvar_prefix="FREAKBLE"))

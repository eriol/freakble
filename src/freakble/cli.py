# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""CLI related stuff for freakble."""

import logging
import sys

import asyncclick as click

from . import __version__, ble
from .gui import App


def ble_receive_callback(data: bytes):
    """Print data received from BLE."""
    click.echo(data)


@click.group()
@click.option(
    "--adapter", default="hci0", show_default="hci0", type=str, help="ble adapter"
)
@click.pass_context
def cli(ctx, adapter):
    """A simple tool to send messages into FreakWAN."""
    ctx.ensure_object(dict)
    ctx.obj["ADAPTER"] = adapter


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
async def send(ctx, words, device, loop, sleep_time, ble_connection_timeout):
    """Send one or more words over BLE to a specific device."""
    msg = " ".join(words)
    logging.info(f"Connecting to {device}...")
    try:
        await ble.send_text(
            ctx.obj["ADAPTER"],
            msg,
            device,
            loop,
            sleep_time,
            ble_connection_timeout,
            ble_receive_callback,
        )
    except AssertionError as e:
        click.echo(click.style(e, fg="red"))


@cli.command()
@click.option(
    "--scan-time", default=5, show_default="5 secs", type=float, help="scan duration"
)
@click.pass_context
async def scan(ctx, scan_time):
    """Scan to find BLE devices."""
    devices = await ble.scan(ctx.obj["ADAPTER"], scan_time)
    for device in devices:
        print(f"{device.address} (rssi:{device.rssi}) {device.name}")


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
async def repl(ctx, device, ble_connection_timeout):
    """Start a REPL with the device."""
    click.echo(f"freakble {__version__} on {sys.platform}")
    click.echo(f"Connecting to {device}...")
    try:
        await ble.repl_loop(ctx.obj["ADAPTER"], device, ble_connection_timeout)
    except AssertionError as e:
        click.echo(click.style(e, fg="red"))


@cli.command()
@click.option(
    "--device",
    default=None,
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
async def gui(ctx, device, ble_connection_timeout):
    """Start freakble GUI."""

    with App() as app:
        app.config(ctx.obj["ADAPTER"], device, ble_connection_timeout)
        await app.run()


@cli.command()
async def version():
    """Return freakble version."""
    click.echo(f"freakble {__version__}")


def get_cli():
    """Return the CLI entrypoint."""
    return cli(auto_envvar_prefix="FREAKBLE", _anyio_backend="asyncio")

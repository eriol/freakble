# Copyright © 2023 Daniele Tricoli <eriol@mornie.org>
# SPDX-License-Identifier: BSD-3-Clause

"""A simple tool to send messages into FreakWAN over Bluetooth low energy."""

import asyncio
import sys

from .cli import get_cli


def run() -> None:
    """Main entrypoint."""
    try:
        asyncio.run(get_cli())
    except RuntimeError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()

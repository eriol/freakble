# freakble

A simple tool to send messages into [FreakWAN](https://github.com/antirez/sx1276-micropython-driver/)
over Bluetooth low energy.

**This is still a work in progress and it's not complete.**

## Installation

### Using pipx

The best way to install freakble is using [pipx](https://pypa.github.io/pipx/):
```console
$ pipx install freakble
```

### Using pip

```console
$ python -m pip install freakble
```

### From source

freakble uses [Poetry](https://python-poetry.org) as dependency management and
packaging tool, you need to install it first.

Then:

1. Clone this repository.
2. From the root of the repository run:
   ```console
   $ poetry build
   ```
3. Install using pipx or pip (it's better to use pipx):
   ```console
   $ pipx install dist/freakble-0.1.0-py3-none-any.whl
   ```

## Usage

At the moment only the command `send` used to send a message to the board is
implemented. You need to already know the address of the device.

For example:

```console
$ freakble send --device AA:AA:AA:AA:AA:AA Hello, there!
```

where you have to substitute `AA:AA:AA:AA:AA:AA` with your device's address.

# Changelog

## 0.3.2 (2023-02-14)

- Remove newline in BLE replies.
- Refactor to move all the BLE stuff in BLE module.

## 0.3.1 (2023-02-11)

- Expose BLE connection timeout on CLI.
- Switch to asyncclick: this fix "got Future <Future pending> attached to a
  different loop" on Python 3.9.

## 0.3.0 (2023-02-11)

BREAKING CHAGES:
- Rename the environment variable to set the device address in FREAKBLE_DEVICE.

- Add repl command to interact with the device from terminal.
- Move BLE stuff in a separate module.

## 0.2.0 (2023-02-10)

- Add scan, and deep-scan commands.
- Enable environment variables for options.
- Add --sleep-time flag (with 1 sec of default) to the send command to set
  sleep time between messages send.

## 0.1.1 (2023-02-10)

Relax minimum Python required version to 3.9.

## 0.1.0 (2023-02-10)

Initial public release.

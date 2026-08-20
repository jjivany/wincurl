# SteamController Haptics

A lightweight, zero-dependency Python library for driving haptic feedback on Steam Controllers natively on Linux.

**Major Feature**: This library works *without* needing to detach the kernel driver or claim the USB interface using `libusb`. This means you can continue to use your Steam Controller as a mouse (Lizard Mode) or gamepad while simultaneously sending haptic commands from Python! 

It achieves this by interfacing directly with `/dev/hidraw*` and sending the correct HID feature/output reports.

## Supported Devices

- **Original Steam Controller (Wired)** - PID `0x1102`
- **Original Steam Controller (Wireless Dongle)** - PID `0x1142`
- **2026 Steam Controller (IBEX/USB-C BLE Puck)** - PID `0x1304`

*Note: The new 2026 controller uses a completely different HID report structure (`0x81` output reports) which is fully handled by this library!*

## Installation

```bash
pip install steamcontroller-haptics
```

### IMPORTANT: udev Rules

To write to `/dev/hidraw*` without running your scripts as `root`, you must install a `udev` rule to grant your user permission.

Create a file named `/etc/udev/rules.d/99-steam-controller.rules` with the following content:

```udev
# Original Steam Controller - Wired
KERNEL=="hidraw*", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1102", MODE="0666"
# Original Steam Controller - Wireless Dongle
KERNEL=="hidraw*", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1142", MODE="0666"
# 2026 Steam Controller - USB-C BLE Puck
KERNEL=="hidraw*", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1304", MODE="0666"
```

Then reload the udev rules and replug your controller:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Usage

```python
import time
from steamcontroller_haptics import SteamControllerHaptics, STEAM_PAD_LEFT, STEAM_PAD_RIGHT, STEAM_PAD_BOTH

# Initialize the controller (spawns a daemon thread for non-blocking IO)
haptics = SteamControllerHaptics()

# Send a simple pulse to the right pad
# pulse(pad, duration_us, interval_us, count, gain=0)
haptics.pulse(STEAM_PAD_RIGHT, 15000, 0, 1, 0)
time.sleep(0.5)

# Built-in sound effects (originally designed for curling games!)
haptics.sweep(intensity=1.0)
time.sleep(0.5)
haptics.takeout(mass=1.0)
time.sleep(0.5)

# Play text phonetically through the actuators!
haptics.play_english("Hello")

# Play morse code
haptics.play_morse("SOS")

# Cleanup
haptics.close()
```

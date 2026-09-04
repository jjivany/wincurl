import os
import fcntl
import struct
import glob

# Steam Controller Vendor/Product IDs
VALVE_VID = 0x28de
SC_WIRED_PID = 0x1102
SC_WIRELESS_PID = 0x1142
SC_BLE_PID = 0x1304

STEAM_PAD_LEFT = 0
STEAM_PAD_RIGHT = 1
STEAM_PAD_BOTH = 2

# HID ioctl macros
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2

def _IOC(dir, type, nr, size):
    return (dir << _IOC_DIRSHIFT) | (type << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)

def _IOR(type, nr, size):
    return _IOC(_IOC_READ, type, nr, size)

def _IOW(type, nr, size):
    return _IOC(_IOC_WRITE, type, nr, size)

HIDIOCGRAWINFO = _IOR(ord('H'), 0x03, 8) 

def HIDIOCSFEATURE(length):
    return _IOW(ord('H'), 0x06, length)

import threading
import queue

class SteamControllerHaptics:
    def __init__(self):
        self.fds = [] # list of (fd, product_id)
        self._find_steam_controller()
        self.queue = queue.Queue(maxsize=100)
        self.thread = threading.Thread(target=self._haptic_worker, daemon=True)
        if self.fds:
            self.thread.start()

    def _find_steam_controller(self):
        try:
            for dev in glob.glob("/dev/hidraw*"):
                try:
                    fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
                    info = fcntl.ioctl(fd, HIDIOCGRAWINFO, struct.pack('Ihh', 0, 0, 0))
                    bustype, vendor, product = struct.unpack('Ihh', info)
                    vendor &= 0xffff
                    product &= 0xffff
                    if vendor == VALVE_VID and product in (SC_WIRED_PID, SC_WIRELESS_PID, SC_BLE_PID):
                        self.fds.append((fd, product))
                    else:
                        os.close(fd)
                except Exception:
                    pass
        except Exception:
            pass

    def close(self):
        for fd, _ in self.fds:
            try:
                os.close(fd)
            except:
                pass
        self.fds = []

    def _haptic_worker(self):
        import time
        while self.fds:
            try:
                item = self.queue.get(timeout=1.0)
                if isinstance(item, (float, int)):
                    time.sleep(item)
                    self.queue.task_done()
                    continue
                
                # item is (pad, duration_us, interval_us, count, gain)
                pad, duration_us, interval_us, count, gain = item
                
                for fd, product in self.fds:
                    try:
                        if product == SC_BLE_PID:
                            # 2026 IBEX Controller over BLE uses an output report 0x81
                            report = bytearray([
                                0x81, pad,
                                (duration_us & 0xFF), ((duration_us >> 8) & 0xFF),
                                (interval_us & 0xFF), ((interval_us >> 8) & 0xFF),
                                (count & 0xFF), ((count >> 8) & 0xFF)
                            ])
                            buf = bytearray(65)
                            buf[0:len(report)] = report
                            os.write(fd, buf)
                        else:
                            # Original Steam Controller
                            report = bytearray([
                                0x00, 0x8F, 8, pad,
                                (duration_us & 0xFF), ((duration_us >> 8) & 0xFF),
                                (interval_us & 0xFF), ((interval_us >> 8) & 0xFF),
                                (count & 0xFF), ((count >> 8) & 0xFF),
                                gain & 0xFF
                            ])
                            buf = bytearray(65)
                            buf[0:len(report)] = report
                            try:
                                os.write(fd, buf)
                            except:
                                try:
                                    fcntl.ioctl(fd, HIDIOCSFEATURE(65), buf)
                                except:
                                    pass
                    except Exception:
                        pass
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def pulse(self, pad, duration_us, interval_us, count, gain=0):
        if not self.fds: return
        try:
            self.queue.put_nowait((pad, duration_us, interval_us, count, gain))
        except queue.Full:
            pass

    def sweep(self, intensity=1.0):
        # Scale duration, count, and gain based on intensity
        dur = int(10000 + 15000 * intensity)
        dur = min(65000, dur) # Prevent 16-bit overflow!
        gain = min(255, int(100 + 155 * intensity))
        count = max(1, int(intensity * 3))
        interval = 5000 if count > 1 else 0
        self.pulse(STEAM_PAD_RIGHT, dur, interval, count, gain)
        
    def takeout(self, mass=1.0):
        # Scale duration, count, and gain based on mass
        dur = int(40000 + 25000 * mass)
        dur = min(65000, dur) # Prevent 16-bit overflow!
        gain = min(255, int(150 + 105 * mass))
        # Increase count significantly for stronger collisions
        count = max(2, int(mass * 8))
        interval = 10000 if count > 1 else 0
        self.pulse(STEAM_PAD_BOTH, dur, interval, count, gain)

    def click(self):
        # Short sharp pulse
        self.pulse(STEAM_PAD_BOTH, 10000, 0, 1, 0)
        
    def hover(self):
        # Very short light pulse
        self.pulse(STEAM_PAD_BOTH, 5000, 0, 1, 0)

    def play_english(self, text):
        # Approximates speech formants using haptic pulses!
        # Very rough phoneme-to-frequency mapping
        phonemes = {
            'w': (2000, 20), 'i': (1200, 30), 'n': (2500, 25), 
            'c': (4000, 15), 'u': (1800, 30), 'r': (3000, 25), 'l': (2200, 25)
        }
        for char in text.lower():
            if char in phonemes:
                period_us, count = phonemes[char]
                # Play the note
                self.pulse(STEAM_PAD_BOTH, period_us//2, period_us//2, count, 0)
                try: self.queue.put_nowait(0.05) # short gap
                except queue.Full: pass

    def play_morse(self, text):
        morse_dict = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
            'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
            'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
            '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----', ' ': ' '
        }
        text = text.upper()
        for char in text:
            if char in morse_dict:
                code = morse_dict[char]
                if code == ' ':
                    try: self.queue.put_nowait(0.2)
                    except queue.Full: pass
                    continue
                for symbol in code:
                    if symbol == '.':
                        self.pulse(STEAM_PAD_BOTH, 50000, 0, 1, 0)
                        try: self.queue.put_nowait(0.1)
                        except queue.Full: pass
                    elif symbol == '-':
                        self.pulse(STEAM_PAD_BOTH, 150000, 0, 1, 0)
                        try: self.queue.put_nowait(0.15)
                        except queue.Full: pass
                try: self.queue.put_nowait(0.2)
                except queue.Full: pass

_haptics = None

def get_haptics():
    global _haptics
    if _haptics is None:
        _haptics = SteamControllerHaptics()
    return _haptics

def trigger_sweep(intensity=1.0):
    try:
        h = get_haptics()
        if h.fds:
            h.sweep(intensity)
    except:
        pass

def trigger_collision(mass=1.0):
    try:
        h = get_haptics()
        if h.fds:
            h.takeout(mass)
    except:
        pass
def trigger_click():
    try:
        h = get_haptics()
        if h.fds:
            h.click()
    except:
        pass

def trigger_hover():
    try:
        h = get_haptics()
        if h.fds:
            h.hover()
    except:
        pass

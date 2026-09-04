import os
import pygame
import threading
try:
    import evdev
    import steamcontroller_haptics
except Exception as e:
    print("[SC] Could not import steamcontroller_haptics:", e)
    evdev = None
    steamcontroller_haptics = None

class SteamControllerEvdevDriver:
    def __init__(self):
        self.device = None
        self.running = False
        self.thread = None
        self.sens = 1.0
        self.start()

    def start(self):
        if self.running or evdev is None: return
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            sc_devices = [d for d in devices if 'Steam Controller' in d.name or 'Valve' in d.name]
            for d in sc_devices:
                caps = d.capabilities()
                if evdev.ecodes.EV_REL in caps and evdev.ecodes.REL_X in caps[evdev.ecodes.EV_REL]:
                    self.device = d
                    break
            if not self.device: return
            self.device.grab()
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
        except Exception: pass

    def _run_loop(self):
        try:
            for event in self.device.read_loop():
                if not self.running: break
                if event.type == evdev.ecodes.EV_REL:
                    dx, dy = 0, 0
                    if event.code == evdev.ecodes.REL_X:
                        dx = int(event.value * self.sens)
                    elif event.code == evdev.ecodes.REL_Y:
                        dy = int(event.value * self.sens)
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT + 1, rel_x=dx, rel_y=dy))
                elif event.type == evdev.ecodes.EV_KEY:
                    if event.code == evdev.ecodes.BTN_LEFT:
                        is_down = True if event.value == 1 else False if event.value == 0 else None
                        if is_down is not None:
                            pygame.event.post(pygame.event.Event(pygame.USEREVENT + 1, btn_down=is_down))
        except Exception: pass

    def close(self):
        self.running = False
        if self.device:
            try: self.device.ungrab()
            except: pass

_driver = None

def get_haptics():
    global _driver
    if _driver is None:
        _driver = SteamControllerEvdevDriver()
    return _driver

def trigger_sweep(intensity=1.0):
    if steamcontroller_haptics: steamcontroller_haptics.trigger_sweep(intensity)

def trigger_collision(mass=1.0):
    if steamcontroller_haptics: steamcontroller_haptics.trigger_collision(mass)

def trigger_click():
    if steamcontroller_haptics: steamcontroller_haptics.trigger_click()

def trigger_hover():
    if steamcontroller_haptics: steamcontroller_haptics.trigger_hover()

def play_wincurl():
    if steamcontroller_haptics:
        h = steamcontroller_haptics.get_haptics()
        def _wincurl_thread():
            h.play_english("WINCURL")
        threading.Thread(target=_wincurl_thread, daemon=True).start()

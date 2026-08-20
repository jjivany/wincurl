import os
import pygame
import threading
import evdev
import steamcontroller_haptics

class SteamControllerEvdevDriver:
    def __init__(self):
        self.device = None
        self.running = False
        self.thread = None
        
        self.virtual_x = 1280 // 2
        self.virtual_y = 720 // 2
        self.width = 1280
        self.height = 720
        self.sens = 1.0  # Mouse sensitivity
        
        self.left_down = False
        
        self.start()

    def start(self):
        if self.running: return
        try:
            # Find Steam Controller evdev node with REL_X
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            sc_devices = [d for d in devices if 'Steam Controller' in d.name or 'Valve' in d.name]
            
            for d in sc_devices:
                caps = d.capabilities()
                if evdev.ecodes.EV_REL in caps and evdev.ecodes.REL_X in caps[evdev.ecodes.EV_REL]:
                    self.device = d
                    break
                    
            if not self.device:
                print("[SC] No Steam Controller evdev found.")
                return
                
            self.device.grab()
            print(f"[SC] Grabbed {self.device.name} via evdev. OS mouse is now locked out.")
            
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            print("[SC] Error initializing evdev:", e)

    def _run_loop(self):
        try:
            for event in self.device.read_loop():
                if not self.running:
                    break
                    
                if event.type == evdev.ecodes.EV_REL:
                    try:
                        di = pygame.display.Info()
                        self.width, self.height = di.current_w, di.current_h
                    except: pass
                    
                    if event.code == evdev.ecodes.REL_X:
                        dx = event.value * self.sens
                        self.virtual_x += dx
                        self.virtual_x = max(0, min(self.width, self.virtual_x))
                        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, 
                            pos=(int(self.virtual_x), int(self.virtual_y)), 
                            rel=(int(dx), 0),
                            buttons=(1 if self.left_down else 0, 0, 0)))
                            
                    elif event.code == evdev.ecodes.REL_Y:
                        dy = event.value * self.sens
                        self.virtual_y += dy
                        self.virtual_y = max(0, min(self.height, self.virtual_y))
                        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, 
                            pos=(int(self.virtual_x), int(self.virtual_y)), 
                            rel=(0, int(dy)),
                            buttons=(1 if self.left_down else 0, 0, 0)))
                            
                elif event.type == evdev.ecodes.EV_KEY:
                    if event.code == evdev.ecodes.BTN_LEFT:
                        if event.value == 1 and not self.left_down:
                            self.left_down = True
                            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, 
                                pos=(int(self.virtual_x), int(self.virtual_y)), button=1))
                        elif event.value == 0 and self.left_down:
                            self.left_down = False
                            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, 
                                pos=(int(self.virtual_x), int(self.virtual_y)), button=1))
        except Exception as e:
            print("[SC] Evdev read loop died:", e)
            
    def close(self):
        self.running = False
        if self.device:
            try:
                self.device.ungrab()
            except: pass

_driver = None

def get_haptics():
    global _driver
    if _driver is None:
        _driver = SteamControllerEvdevDriver()
    return _driver

def trigger_sweep(intensity=1.0):
    steamcontroller_haptics.trigger_sweep(intensity)

def trigger_collision(mass=1.0):
    steamcontroller_haptics.trigger_collision(mass)

def trigger_click():
    steamcontroller_haptics.trigger_click()

def trigger_hover():
    steamcontroller_haptics.trigger_hover()

def play_wincurl():
    h = steamcontroller_haptics.get_haptics()
    def _wincurl_thread():
        h.play_english("WINCURL")
    threading.Thread(target=_wincurl_thread, daemon=True).start()

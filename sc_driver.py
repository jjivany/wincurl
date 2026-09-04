import os
import pygame
import threading
try:
    import steamcontroller_haptics
except Exception as e:
    print("[SC] Could not import steamcontroller_haptics:", e)
    steamcontroller_haptics = None

def get_haptics():
    pass

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

import sys, os
sys.path.append("/home/jason/wincurl/wincurl_android")
import pygame
pygame.mixer.init()
from main import WinCurlAudioEngine

class DummyAudio(WinCurlAudioEngine):
    def __init__(self):
        super().__init__()

def generate():
    import main
    main.IS_ANDROID = True
    a = WinCurlAudioEngine()
    import time
    time.sleep(2) # wait for bg_worker to finish
    import io
    for attr in ['snd_speech', 'snd_cheer', 'snd_end_match', 'snd_hurry', 'snd_hard', 'snd_you_win', 'snd_chal_comp', 'snd_red_wins', 'snd_ylw_wins',
                 'snd_slide', 'snd_sweep', 'snd_throw', 'snd_clack', 'snd_hover', 'snd_click']:
        val = getattr(a, attr, None)
        if isinstance(val, pygame.mixer.Sound):
            print(f"Skipping {attr}, already Sound")
        elif isinstance(val, io.BytesIO):
            with open(f"/home/jason/wincurl/wincurl_android/snd_{attr}.wav", "wb") as f:
                f.write(val.getvalue())
            print(f"Generated snd_{attr}.wav")
        else:
            print(f"Unknown {attr}: {type(val)}")
        
generate()

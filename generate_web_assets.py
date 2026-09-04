import sys, os, io
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
pygame.init()
pygame.mixer.init()
from main import WinCurlAudioEngine
import subprocess

def generate():
    a = WinCurlAudioEngine()
    
    os.makedirs("wincurl_web", exist_ok=True)
    
    # Theme is special, returns file path
    theme_wav = a._synthesize_theme_song(return_path=True)
    subprocess.run(["ffmpeg", "-y", "-i", theme_wav, "wincurl_web/theme.ogg"])

    pending_tasks = [
        ("snd_speech", a._synthesize_sega_speech),
        ("snd_cheer", a._synthesize_cheer),
        ("snd_end_match", a._synthesize_end_of_match),
        ("snd_hurry", lambda return_bytes=False: a._synthesize_vosim_phrase("HURRY", 0.7, return_bytes=return_bytes)),
        ("snd_hard", lambda return_bytes=False: a._synthesize_vosim_phrase("HARD", 0.65, return_bytes=return_bytes)),
        ("snd_chal_comp", lambda return_bytes=False: a._synthesize_vosim_phrase("CHALLENGE_COMPLETE", 1.2, return_bytes=return_bytes)),
        ("snd_red_wins", lambda return_bytes=False: a._synthesize_vosim_phrase("RED_TEAM_WINS", 1.2, return_bytes=return_bytes)),
        ("snd_ylw_wins", lambda return_bytes=False: a._synthesize_vosim_phrase("YELLOW_TEAM_WINS", 1.2, return_bytes=return_bytes)),
        ("snd_you_win", lambda return_bytes=False: a._synthesize_vosim_phrase("YOU_WIN", 1.2, return_bytes=return_bytes)),
        ("snd_slide", a._synthesize_rumble),
        ("snd_sweep", a._synthesize_sweep),
        ("snd_throw", a._synthesize_throw),
        ("snd_clack", a._synthesize_clack),
        ("snd_hover", lambda return_bytes=False: a._synthesize_ui_sound(440, 0.05, "sine", return_bytes=return_bytes)),
        ("snd_click", lambda return_bytes=False: a._synthesize_ui_sound(587, 0.12, "square", return_bytes=return_bytes))
    ]
    
    for name, func in pending_tasks:
        val = func(return_bytes=True)
        if isinstance(val, io.BytesIO):
            wav_path = f"/tmp/{name}.wav"
            with open(wav_path, "wb") as f:
                f.write(val.getvalue())
            ogg_path = f"wincurl_web/{name}.ogg"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, ogg_path])
            print(f"Generated {ogg_path}")
        else:
            print(f"{name} returned {type(val)}")

if __name__ == "__main__":
    generate()

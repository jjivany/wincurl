import os, sys
if hasattr(os, 'name') and os.name == 'posix' and not hasattr(sys, 'getandroidapilevel') and 'ANDROID_ARGUMENT' not in os.environ:
    os.environ['SDL_VIDEO_WAYLAND_WMCLASS'] = 'wincurl3'
    os.environ['SDL_VIDEO_X11_WMCLASS'] = 'wincurl3'
import pygame
import math, random, time, json, socket, threading, queue, base64, zlib
import struct
import io
import collections

VERSION = "27"


class CachedFont:
    def __init__(self, font):
        self.font = font
        self.cache = {}
    def render(self, text, antialias, color, background=None):
        key = (text, antialias, str(color), str(background))
        if key not in self.cache:
            if len(self.cache) > 256: self.cache.clear()
            if background:
                self.cache[key] = self.font.render(text, antialias, color, background)
            else:
                self.cache[key] = self.font.render(text, antialias, color)
        return self.cache[key]

class ChatFont:
    def __init__(self, size):
        self.target_size = size
        self.text_font = pygame.font.Font(None, size)
        self.emoji_font = None
        self.cache = {}
        
        try:
            ef = pygame.font.SysFont("segoeuiemoji,applecoloremoji,notocoloremoji,symbola", size)
            if ef: self.emoji_font = ef
        except: pass
        
        if not self.emoji_font:
            import os
            android_emoji = "/system/fonts/NotoColorEmoji.ttf"
            if os.path.exists(android_emoji):
                try: self.emoji_font = pygame.font.Font(android_emoji, size)
                except: pass

    def render(self, text, antialias, color, background=None):
        key = (text, antialias, str(color), str(background))
        if key in self.cache: return self.cache[key]
        if len(self.cache) > 256: self.cache.clear()

        if not self.emoji_font:
            if background: surf = self.text_font.render(text, antialias, color, background)
            else: surf = self.text_font.render(text, antialias, color)
            self.cache[key] = surf
            return surf
            
        chunks = []
        current_chunk = ""
        current_font_is_text = True
        
        for char in text:
            m = self.text_font.metrics(char)
            is_text = (m is not None and len(m) > 0 and m[0] is not None)
            
            if is_text == current_font_is_text:
                current_chunk += char
            else:
                if current_chunk:
                    chunks.append((current_chunk, current_font_is_text))
                current_chunk = char
                current_font_is_text = is_text
                
        if current_chunk:
            chunks.append((current_chunk, current_font_is_text))
            
        surfaces = []
        total_width = 0
        max_height = 0
        
        for chunk_text, is_text in chunks:
            font = self.text_font if is_text else self.emoji_font
            try:
                if background: s = font.render(chunk_text, antialias, color, background)
                else: s = font.render(chunk_text, antialias, color)
                
                if not is_text and s.get_height() > self.target_size + 15:
                    scale = self.target_size / float(s.get_height())
                    new_w = max(1, int(s.get_width() * scale))
                    s = pygame.transform.smoothscale(s, (new_w, self.target_size))
                    
                surfaces.append(s)
                total_width += s.get_width()
                max_height = max(max_height, s.get_height())
            except:
                pass
                
        if not surfaces:
            self.cache[key] = pygame.Surface((1, self.target_size), pygame.SRCALPHA)
            return self.cache[key]
            
        final_surf = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        if background: final_surf.fill(background)
        
        x = 0
        for s in surfaces:
            final_surf.blit(s, (x, max_height//2 - s.get_height()//2))
            x += s.get_width()
            
        self.cache[key] = final_surf
        return final_surf

# --- Global Constants & Configurations ---
from pygame.locals import *

import wave
import os

VIBRATE_ENABLED = True

def vibrate_android(ms):
    global VIBRATE_ENABLED
    if not VIBRATE_ENABLED: return
    try:
        from plyer import vibrator
        vibrator.vibrate(time=ms/1000.0)
        return
    except Exception as e:
        print("Plyer vibration failed:", e)

    try:
        from jnius import autoclass
        Context = autoclass('android.content.Context')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        vibrator = PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
        if vibrator and vibrator.hasVibrator():
            VERSION = autoclass('android.os.Build$VERSION')
            if VERSION.SDK_INT >= 26:
                VibrationEffect = autoclass('android.os.VibrationEffect')
                vibrator.vibrate(VibrationEffect.createOneShot(int(ms), VibrationEffect.DEFAULT_AMPLITUDE))
            else:
                vibrator.vibrate(int(ms))
            return
    except Exception as e:
        print("Pyjnius vibration failed:", e)
        
    try:
        if pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            if not joy.get_init(): joy.init()
            joy.rumble(0.5, 0.5, int(ms))
    except: pass

# Define this immediately after imports
IS_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_BOOTLOGO' in os.environ
if IS_ANDROID:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- Immediate Environment Verification ---
print("\n" + "="*80)
print(f"     [SYSTEM] WINCURL 3 BUILD {VERSION}")
print("     (IMPROVED NETPLAY | NET CHAT | MULTI-SYLLABLE AUDIO | REALISM | VIBRATION)")
print("="*80 + "\n")



# --- Configuration & Canvas Setup ---
BASE_WIDTH, BASE_HEIGHT = 1200, 1800 
FPS = 60
FRICTION_BASE = 0.022 

# Premium Vector Palette
ICE_COLOR = (242, 247, 254)
ICE_SHADOW = (212, 226, 246)
HOG_LINE_COLOR = (225, 45, 45)
TEE_LINE_COLOR = (45, 115, 235)
HOUSE_BLUE = (35, 85, 195)
HOUSE_RED = (215, 45, 55)
TEAM_YELLOW = (245, 195, 25)
WHITE = (255, 255, 255)
BLACK = (25, 25, 30)

# 90s Tracksuit Palette
PURPLE_SUIT = (106, 13, 173) 
PURPLE_SHADOW = (60, 10, 100)
CYAN_ACCENT = (0, 255, 255)

HIGHLIGHT_COLOR = (255, 255, 255, 120)

def lerp_color(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t), int(c1[2] + (c2[2] - c1[2]) * t))

def draw_maple_leaf(surface, cx, cy, scale, color):
    pts = [(-0.45, 10.0), (-0.22, 5.72), (-0.77, 5.23), (-5.04, 5.98), (-4.46, 4.39), (-4.56, 4.03), (-9.23, 0.25), (-8.18, -0.24), (-8.01, -0.64), (-8.93, -3.47), (-6.24, -2.9), (-5.88, -3.09), (-5.36, -4.32), (-3.26, -2.06), (-2.71, -2.35), (-3.72, -7.57), (-2.1, -6.63), (-1.65, -6.76), (0.0, -10.0), (1.65, -6.76), (2.1, -6.63), (3.72, -7.57), (2.71, -2.35), (3.26, -2.06), (5.36, -4.32), (5.88, -3.09), (6.24, -2.9), (8.93, -3.47), (8.01, -0.64), (8.18, -0.24), (9.23, 0.25), (4.56, 4.03), (4.46, 4.39), (5.04, 5.98), (0.77, 5.23), (0.22, 5.72), (0.45, 10.0)]
    polygon = []
    for x, y in pts:
        wrap_y = y + (x*x + y*y) * 0.015
        polygon.append((cx + x * scale * 2.5, cy + wrap_y * scale * 2.5))
    pygame.draw.polygon(surface, color, polygon)

def draw_hammer_icon(surface, x, y, color):
    pygame.draw.rect(surface, color, (x, y, 16, 8), border_radius=2)
    pygame.draw.rect(surface, color, (x+6, y+8, 4, 12))

# OPTIMIZATION: Cache glass buttons
class UICache:
    glass_surfs = {}
    
    @classmethod
    def get_glass(cls, w, h, base_color, radius, hovered):
        key = (w, h, tuple(base_color), radius, hovered)
        if key not in cls.glass_surfs:
            # 1. Shadow (No need for 2x, just draw and scale? Actually, 1x is fine for shadow)
            shadow = pygame.Surface((w+10, h+10), pygame.SRCALPHA).convert_alpha()
            shadow.fill((0, 0, 0, 0))
            pygame.draw.rect(shadow, (0, 0, 0, 50), (5, 5, w, h), border_radius=radius)
            
            # 2. Button Surface via 2x Supersampling (SSAA) and Masking
            tw, th = w * 2, h * 2
            tr = radius * 2
            
            # Create clipping mask
            mask = pygame.Surface((tw, th), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, tw, th), border_radius=tr)
            
            # Create content
            content = pygame.Surface((tw, th), pygame.SRCALPHA)
            content.fill((0, 0, 0, 0))
            
            a = base_color[3] if len(base_color) > 3 else 150
            c = pygame.Color(*base_color[:3], a)
            pygame.draw.rect(content, c, (0, 0, tw, th))
            pygame.draw.rect(content, (255, 255, 255, 60), (0, 0, tw, th//2))
            pygame.draw.ellipse(content, (255, 255, 255, 90), (tw*0.05, -th*0.2, tw*0.9, th*0.7))
            pygame.draw.rect(content, (0, 0, 0, 40), (0, th//2, tw, th//2))
            
            if hovered:
                pygame.draw.rect(content, (255, 255, 255, 60), (0, 0, tw, th))
                
            # Apply mask to clip overflowing gradients
            content.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Draw borders on top
            if hovered:
                pygame.draw.rect(content, (255, 255, 255, 240), (0, 0, tw, th), 6, border_radius=tr)
            else:
                pygame.draw.rect(content, (255, 255, 255, 120), (0, 0, tw, th), 4, border_radius=tr)
                
            # Downscale for perfectly smooth edges
            btn_surf = pygame.transform.smoothscale(content, (w, h))
            
            cls.glass_surfs[key] = (shadow, btn_surf)
        return cls.glass_surfs[key]

def draw_speaker_icon(surface, x, y, is_muted):
    color = (255, 255, 255)
    pygame.draw.rect(surface, color, (x, y + 8, 8, 10))
    pygame.draw.polygon(surface, color, [(x + 8, y + 8), (x + 20, y), (x + 20, y + 26), (x + 8, y + 18)])
    if is_muted:
        pygame.draw.line(surface, (255, 50, 50), (x + 24, y + 6), (x + 34, y + 20), 4)
        pygame.draw.line(surface, (255, 50, 50), (x + 34, y + 6), (x + 24, y + 20), 4)
    else:
        pygame.draw.line(surface, color, (x + 24, y + 8), (x + 28, y + 13), 3)
        pygame.draw.line(surface, color, (x + 28, y + 13), (x + 24, y + 18), 3)
        pygame.draw.line(surface, color, (x + 28, y + 4), (x + 34, y + 13), 3)
        pygame.draw.line(surface, color, (x + 34, y + 13), (x + 28, y + 22), 3)

def draw_glass_rect(surface, rect, base_color, border_radius=16, is_hovered=False):
    shadow, btn_surf = UICache.get_glass(rect.w, rect.h, base_color, border_radius, is_hovered)
    if not IS_ANDROID:
        surface.blit(shadow, (rect.x-5, rect.y-5))
    surface.blit(btn_surf, rect.topleft)

# --- Audio Synthesis Engine ---
class WinCurlAudioEngine:
    def __init__(self):
        if IS_ANDROID: pygame.mixer.pre_init(44100, -16, 2, 4096)
        else: pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.mixer.init()
        self.ch_slide = pygame.mixer.Channel(0); self.ch_sweep = pygame.mixer.Channel(1)
        self.ch_sfx = pygame.mixer.Channel(2); self.ch_ui = pygame.mixer.Channel(3)
        self.ch_music = pygame.mixer.Channel(4); self.ch_crowd = pygame.mixer.Channel(5)
        self.ch_voice = pygame.mixer.Channel(6)
        pygame.mixer.set_num_channels(16)
        
        self.sfx_on = True
        
        self.snd_music = None; self.snd_speech = None; self.snd_cheer = None
        self.snd_end_match = None; self.snd_hurry = None; self.snd_hard = None
        self.snd_chal_comp = None; self.snd_red_wins = None; self.snd_ylw_wins = None
        self.snd_slide = None; self.snd_sweep = None
        self.snd_throw = None; self.snd_clack = None
        self.snd_hover = None; self.snd_click = None
        
        self._synthesize_heavy_bg()
        self.last_call = 0

    def _synthesize_heavy_bg(self):
        import os, io, pygame, threading
        asset_dir = os.path.dirname(os.path.abspath(__file__))
        
        pending_tasks = []
        
        def load_sound(attr_name, filename, fallback):
            try:
                setattr(self, attr_name, pygame.mixer.Sound(filename))
            except:
                try:
                    setattr(self, attr_name, pygame.mixer.Sound(os.path.join(asset_dir, filename)))
                except:
                    pending_tasks.append((attr_name, fallback))

        self.snd_music = ["theme.wav", os.path.join(asset_dir, "theme.wav")]

        load_sound("snd_speech", "sega_speech.wav", self._synthesize_sega_speech)
        load_sound("snd_cheer", "cheer.wav", self._synthesize_cheer)
        load_sound("snd_end_match", "end_match.wav", self._synthesize_end_of_match)
        load_sound("snd_hurry", "vosim_HURRY.wav", lambda return_bytes=False: self._synthesize_vosim_phrase("HURRY", 0.7, return_bytes=return_bytes))
        load_sound("snd_hard", "vosim_HARD.wav", lambda return_bytes=False: self._synthesize_vosim_phrase("HARD", 0.65, return_bytes=return_bytes))
        load_sound("snd_chal_comp", "vosim_CHALLENGE_COMPLETE.wav", lambda return_bytes=False: self._synthesize_vosim_phrase("CHALLENGE_COMPLETE", 2.5, return_bytes=return_bytes))
        load_sound("snd_red_wins", "vosim_RED_TEAM_WINS.wav", lambda return_bytes=False: self._synthesize_vosim_phrase("RED_TEAM_WINS", 2.2, return_bytes=return_bytes))
        load_sound("snd_ylw_wins", "vosim_YELLOW_TEAM_WINS.wav", lambda return_bytes=False: self._synthesize_vosim_phrase("YELLOW_TEAM_WINS", 2.4, return_bytes=return_bytes))
        
        pending_tasks.extend([
            ("snd_slide", self._synthesize_rumble),
            ("snd_sweep", self._synthesize_sweep),
            ("snd_throw", self._synthesize_throw),
            ("snd_clack", self._synthesize_clack),
            ("snd_hover", lambda return_bytes=False: self._synthesize_ui_sound(440, 0.05, "sine", return_bytes=return_bytes)),
            ("snd_click", lambda return_bytes=False: self._synthesize_ui_sound(587, 0.12, "square", return_bytes=return_bytes))
        ])

        def bg_worker():
            for attr_name, fallback in pending_tasks:
                try:
                    setattr(self, attr_name, fallback(return_bytes=True))
                except Exception as e: pass
                    
        threading.Thread(target=bg_worker, daemon=True).start()
        
    def process_pending_sounds(self):
        import io, pygame
        for attr in ['snd_speech', 'snd_cheer', 'snd_end_match', 'snd_hurry', 'snd_hard', 'snd_chal_comp', 'snd_red_wins', 'snd_ylw_wins',
                     'snd_slide', 'snd_sweep', 'snd_throw', 'snd_clack', 'snd_hover', 'snd_click']:
            val = getattr(self, attr, None)
            if isinstance(val, io.BytesIO):
                try: 
                    snd = pygame.mixer.Sound(file=val)
                    setattr(self, attr, snd)
                    if attr == 'snd_slide': self.ch_slide.play(snd, loops=-1); self.ch_slide.set_volume(0.0)
                    elif attr == 'snd_sweep': self.ch_sweep.play(snd, loops=-1); self.ch_sweep.set_volume(0.0)
                except Exception as e: print("Sound load error:", e); setattr(self, attr, None)
            elif isinstance(val, str):
                try: setattr(self, attr, pygame.mixer.Sound(file=val))
                except Exception as e: print("Sound file load error:", e); setattr(self, attr, None)

    def play_clack(self, intensity):
        if not self.sfx_on: return
        vol = max(0.1, min(1.0, intensity / 20.0))
        self.snd_clack.set_volume(vol)
        self.ch_sfx.play(self.snd_clack)
        if IS_ANDROID and vol > 0.3:
            vibrate_android(int(vol * 150))

    def _get_cache_dir(self):
        import os, tempfile
        if IS_ANDROID:
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                cache_dir = os.path.join(PythonActivity.mActivity.getCacheDir().getAbsolutePath(), "wincurl_cache")
                os.makedirs(cache_dir, exist_ok=True)
                return cache_dir
            except: pass
            
        try:
            cache_dir = os.path.join(tempfile.gettempdir(), "wincurl_cache")
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        except: pass
        
        try:
            base_dir = pygame.system.get_pref_path("jason", "wincurl3")
            cache_dir = os.path.join(base_dir, "wincurl_cache")
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        except: pass
        
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "wincurl_cache")

    def _get_cached_sound(self, cache_key, return_bytes=False):
        import os, io, threading, pygame
        cache_file = os.path.join(self._get_cache_dir(), f"{cache_key}.wav")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    data = f.read()
                    if return_bytes: return io.BytesIO(data)
                    return pygame.mixer.Sound(file=io.BytesIO(data))
            except: pass
        return None

    def _create_wav_sound(self, byte_buffer, sample_rate=44100, cache_key=None, return_path=False, channels=2, return_bytes=False):
        import os, struct, io, threading
        data_size = len(byte_buffer)
        bits = 16
        wav = b'RIFF'
        wav += struct.pack('<I', 36 + data_size)
        wav += b'WAVE'
        wav += b'fmt '
        wav += struct.pack('<IHHIIHH', 16, 1, channels, sample_rate, sample_rate * channels * (bits//8), channels * (bits//8), bits)
        wav += b'data'
        wav += struct.pack('<I', data_size)
        wav += byte_buffer
        
        if cache_key:
            cache_dir = self._get_cache_dir()
            path = os.path.join(cache_dir, f"{cache_key}.wav")
            try:
                os.makedirs(cache_dir, exist_ok=True)
                with open(path, "wb") as f: f.write(wav)
                if return_path: return path
            except: pass
            
        if return_path: return None
        if return_bytes: return io.BytesIO(wav)
        
        import io, threading, pygame
        return pygame.mixer.Sound(file=io.BytesIO(wav))

    def _synthesize_sega_speech(self, return_bytes=False):
        cached = self._get_cached_sound("sega_speech", return_bytes=return_bytes)
        if cached: return cached
        steps = int(44100 * 3.0); buf = bytearray(steps * 4)
        w_f1, w_f2, w_f3 = [(0.0,300),(0.9,400),(1.4,250)], [(0.0,600),(0.9,1900),(1.4,1200)], [(0.0,2200),(0.9,2400),(1.4,2600)]
        c_f1, c_f2, c_f3 = [(1.4,500),(2.3,350),(2.8,300)], [(1.4,1450),(2.3,1000),(2.8,900)], [(1.4,2450),(1.8,1400),(2.8,2300)]
        
        def get_val(t, pts):
            for i in range(len(pts)-1):
                if pts[i][0] <= t <= pts[i+1][0]: return pts[i][1] + (pts[i+1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i+1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            t = i / 44100; val = 0.0
            if t < 1.4: 
                env = min(1.0, t/0.1) * max(0.0, min(1.0, (1.4-t)/0.2))
                chord = [155.56, 196.00, 233.08] 
                for f0 in chord:
                    phase = (t * f0) % 1.0; decay = math.exp(-phase * 5.0)
                    val += (math.sin(2*math.pi*get_val(t,w_f1)*phase/f0) + math.sin(2*math.pi*get_val(t,w_f2)*phase/f0)*0.6 + math.sin(2*math.pi*get_val(t,w_f3)*phase/f0)*0.3) * decay
                val = (val / 3.0) * env * 1.8
            elif t < 2.8: 
                tc = t - 1.4; env = min(1.0, tc/0.1) * max(0.0, min(1.0, (2.8-t)/0.3))
                if tc < 0.1: val += random.uniform(-1, 1) * max(0.0, 1.0-tc/0.1) * 0.35
                chord = [130.81, 164.81, 196.00] 
                for f0 in chord:
                    phase = (t * f0) % 1.0; decay = math.exp(-phase * 5.0)
                    val += (math.sin(2*math.pi*get_val(t,c_f1)*phase/f0) + math.sin(2*math.pi*get_val(t,c_f2)*phase/f0)*0.6 + math.sin(2*math.pi*get_val(t,c_f3)*phase/f0)*0.3) * decay
                val = (val / 3.0) * env * 1.8
            sample = int(max(-1.0, min(1.0, val)) * 24000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100, cache_key="sega_speech", return_bytes=return_bytes)

    def _synthesize_vosim_phrase(self, phrase, duration, return_bytes=False):
        cached = self._get_cached_sound(f"vosim_{phrase}", return_bytes=return_bytes)
        if cached: return cached
        SR = 44100
        steps = int(SR * duration); buf = bytearray(steps * 4)
        if phrase == "HURRY":
            f1_env, f2_env, f3_env = [(0.0,400),(0.5,450),(1.0,300)], [(0.0,1000),(0.5,1400),(1.0,2400)], [(0.0,2600),(0.5,1600),(1.0,2800)]
            chord = [261.63, 329.63]
        elif phrase == "RED_TEAM_WINS":
            # Three dips in the frequency envelope simulate three words
            f1_env = [(0.0,500), (0.2,530), (0.3,300), (0.5,550), (0.7,400), (0.8,600), (1.0,300)]
            f2_env = [(0.0,1800), (0.3,1840), (0.5,1200), (0.8,1600), (1.0,1500)]
            f3_env = [(0.0,2600), (0.5,2400), (1.0,2600)]
            chord = [220.00, 277.18]
        elif phrase == "YELLOW_TEAM_WINS":
            f1_env = [(0.0,530), (0.2,500), (0.3,300), (0.5,550), (0.7,400), (0.8,600), (1.0,300)]
            f2_env = [(0.0,1840), (0.3,1200), (0.5,1200), (0.8,1600), (1.0,1500)]
            f3_env = [(0.0,2600), (0.3,2000), (0.5,2400), (1.0,2600)]
            chord = [233.08, 293.66]
        elif phrase == "CHALLENGE_COMPLETE":
            f1_env = [(0.0,600), (0.2,500), (0.3,300), (0.5,600), (0.7,300), (0.9,400), (1.0,200)]
            f2_env = [(0.0,1700), (0.3,1200), (0.5,1800), (0.7,1100), (1.0,1400)]
            f3_env = [(0.0,2400), (0.5,2200), (0.8,2500), (1.0,2000)]
            chord = [261.63, 311.13]
        else: # "HARD" and fallback
            f1_env, f2_env, f3_env = [(0.0,400),(0.3,750),(1.0,200)], [(0.0,1000),(0.8,1400),(1.0,1600)], [(0.0,2600),(0.8,1800),(1.0,2400)]
            chord = [246.94, 311.13] 

        def get_val(t, pts):
            for i in range(len(pts)-1):
                if pts[i][0] <= t <= pts[i+1][0]: return pts[i][1] + (pts[i+1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i+1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            t_norm = i / steps; env = min(1.0, t_norm/0.1) * max(0.0, min(1.0, (1.0-t_norm)/0.2))
            if t_norm < 0.1: env += random.uniform(-0.5, 0.5) * (0.1 - t_norm)*15 
            val = 0.0
            for f0 in chord:
                phase = ((i/SR) * f0) % 1.0; decay = math.exp(-phase * 2.2)
                val += (math.sin(2*math.pi*get_val(t_norm,f1_env)*phase/f0) + math.sin(2*math.pi*get_val(t_norm,f2_env)*phase/f0)*0.6 + math.sin(2*math.pi*get_val(t_norm,f3_env)*phase/f0)*0.3) * decay
            sample = int(max(-1.0, min(1.0, (val / len(chord)) * env * 2.0)) * 24000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, SR, cache_key=f"vosim_{phrase}")

    def _synthesize_end_of_match(self):
        cached = self._get_cached_sound("end_match")
        if cached: return cached
        SR = 11025
        steps = int(SR * 2.0); buf = bytearray(steps * 4)
        f1_env = [(0,400),(0.3,500),(0.6,300),(1.0,400),(1.4,700),(1.8,300),(2.0,200)]
        f2_env = [(0,1800),(0.3,1200),(0.6,1000),(1.0,900),(1.4,1200),(1.8,1800),(2.0,2400)]
        f3_env = [(0,2600),(0.5,2400),(1.0,2400),(1.5,2600),(2.0,2800)]
        
        def get_val(t, pts):
            for i in range(len(pts)-1):
                if pts[i][0] <= t <= pts[i+1][0]: return pts[i][1] + (pts[i+1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i+1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            t = i / SR; env = math.sin((t / 2.0) * math.pi)
            f0 = 120.0 - t*15.0; phase = (t * f0) % 1.0; decay = math.exp(-phase * 4.0)
            noise = random.uniform(-1, 1) * max(0, (t-1.6)/0.4) * 0.5
            val = (math.sin(2*math.pi*get_val(t,f1_env)*phase/f0) + math.sin(2*math.pi*get_val(t,f2_env)*phase/f0)*0.6 + math.sin(2*math.pi*get_val(t,f3_env)*phase/f0)*0.3) * decay
            sample = int(max(-1.0, min(1.0, (val*0.6 + noise) * env)) * 24000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, SR, cache_key="end_match", return_bytes=return_bytes)

    def _synthesize_cheer(self, return_bytes=False):
        cached = self._get_cached_sound("cheer", return_bytes=return_bytes)
        if cached: return cached
        SR = 11025
        duration = 3.5; steps = int(SR * duration); buf = bytearray(steps * 4); val = 0.0
        for i in range(steps):
            t = i / SR; val += (random.uniform(-1.0, 1.0) - val) * 0.02 
            sample = int(val * math.sin(t * math.pi / duration) * 18000 * (1.0 + 0.3 * math.sin(t*12))) 
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, SR, cache_key="cheer", return_bytes=return_bytes)

    def _synthesize_rumble(self, return_bytes=False):
        cached = self._get_cached_sound("whoosh", return_bytes=return_bytes)
        if cached: return cached
        buf = bytearray(44100 * 4); v = 0.0
        for i in range(44100):
            v = max(-0.4, min(0.4, (v + random.uniform(-0.08, 0.08)) * 0.98))
            struct.pack_into('<hh', buf, i * 4, int(v * 32767), int(v * 32767))
        return self._create_wav_sound(buf, 44100, cache_key="whoosh", return_bytes=return_bytes)

    def _synthesize_sweep(self, return_bytes=False):
        cached = self._get_cached_sound("sweep", return_bytes=return_bytes)
        if cached: return cached
        buf = bytearray(22050 * 4)
        for i in range(22050): struct.pack_into('<hh', buf, i*4, int(random.uniform(-0.15, 0.15)*32767), int(random.uniform(-0.15, 0.15)*32767))
        return self._create_wav_sound(buf, 22050, cache_key="sweep", return_bytes=return_bytes)

    def _synthesize_throw(self, return_bytes=False):
        cached = self._get_cached_sound("throw", return_bytes=return_bytes)
        if cached: return cached
        duration = 0.5; steps = int(44100 * duration); buf = bytearray(steps * 4)
        for i in range(steps):
            t = i / 44100; val = math.sin(2 * math.pi * (180 - (t * 100)) * t) * (math.sin(t * math.pi / duration) * math.exp(-t * 2))
            sample = int(max(-1.0, min(1.0, val * 0.5)) * 32767)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100, cache_key="throw", return_bytes=return_bytes)

    def _synthesize_clack(self, return_bytes=False):
        cached = self._get_cached_sound("clack", return_bytes=return_bytes)
        if cached: return cached
        buf = bytearray(11025 * 4)
        for i in range(11025):
            t = i / 11025; sample = int(math.sin(2 * math.pi * (220 + random.uniform(-20, 20)) * t) * math.exp(-t * 25) * 32767)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 11025, cache_key="clack", return_bytes=return_bytes)

    def _synthesize_ui_sound(self, frequency, duration, type="sine", return_bytes=False):
        cached = self._get_cached_sound(f"ui_{frequency}_{duration}_{type}", return_bytes=return_bytes)
        if cached: return cached
        steps = int(44100 * duration); buf = bytearray(steps * 4)
        for i in range(steps):
            t = i / 44100; val = math.sin(2 * math.pi * frequency * t) if type == "sine" else (1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0)
            struct.pack_into('<hh', buf, i * 4, int(val * math.exp(-t * (1.0 / duration * 3)) * 12000), int(val * math.exp(-t * (1.0 / duration * 3)) * 12000))
        return self._create_wav_sound(buf, 44100, cache_key=f"ui_{frequency}_{duration}_{type}", return_bytes=return_bytes)

    def _synthesize_theme_song(self, return_path=False):
        import os
        if return_path:
            cache_file = os.path.join(self._get_cache_dir(), "theme_v2.wav")
            if os.path.exists(cache_file): return cache_file
        else:
            cached = self._get_cached_sound("theme_v2")
            if cached: return cached
        bpm = 125.0
        step_len = 60.0 / bpm / 4.0 # 16th notes
        total_steps = 512
        duration = step_len * total_steps
        steps = int(22050 * duration)
        buf = bytearray(steps * 2)
        
        # Phonk Melody (E Minor) extended
        cb_base = [
            329.6, 0, 392.0, 0, 329.6, 0, 369.9, 0,
            329.6, 0, 311.1, 0, 246.9, 0, 329.6, 0,
            329.6, 0, 392.0, 392.0, 329.6, 0, 369.9, 0,
            329.6, 0, 493.9, 0, 392.0, 369.9, 329.6, 0,
            329.6, 0, 392.0, 0, 329.6, 0, 369.9, 0,
            329.6, 0, 311.1, 0, 246.9, 0, 329.6, 0,
            329.6, 0, 392.0, 392.0, 329.6, 0, 369.9, 0,
            329.6, 0, 493.9, 0, 392.0, 369.9, 329.6, 0,
            329.6, 0, 392.0, 0, 329.6, 0, 369.9, 0,
            329.6, 0, 311.1, 0, 246.9, 0, 329.6, 0,
            329.6, 0, 587.3, 587.3, 329.6, 0, 493.9, 0,
            329.6, 0, 659.3, 0, 587.3, 493.9, 329.6, 0,
            329.6, 0, 392.0, 0, 329.6, 0, 369.9, 0,
            329.6, 0, 311.1, 0, 246.9, 0, 329.6, 0,
            329.6, 0, 587.3, 587.3, 329.6, 0, 493.9, 0,
            329.6, 0, 659.3, 0, 587.3, 493.9, 329.6, 0,
            329.6, 0, 392.0, 392.0, 329.6, 0, 440.0, 0,
            329.6, 0, 392.0, 0, 369.9, 369.9, 329.6, 0,
            329.6, 0, 493.9, 0, 329.6, 0, 587.3, 0,
            329.6, 0, 659.3, 0, 587.3, 493.9, 329.6, 0,
            329.6, 0, 392.0, 392.0, 329.6, 0, 440.0, 0,
            329.6, 0, 392.0, 0, 369.9, 369.9, 329.6, 0,
            329.6, 0, 493.9, 0, 329.6, 0, 587.3, 0,
            329.6, 0, 659.3, 0, 587.3, 493.9, 329.6, 0,
            329.6, 0, 392.0, 0, 329.6, 0, 369.9, 0,
            329.6, 0, 311.1, 0, 246.9, 0, 329.6, 0,
            329.6, 0, 392.0, 392.0, 329.6, 0, 369.9, 0,
            329.6, 0, 493.9, 0, 392.0, 369.9, 329.6, 0,
            329.6, 0, 659.3, 659.3, 329.6, 0, 587.3, 0,
            329.6, 0, 493.9, 0, 392.0, 0, 329.6, 0,
            329.6, 0, 783.9, 783.9, 329.6, 0, 659.3, 0,
            329.6, 0, 587.3, 0, 493.9, 392.0, 329.6, 0,
            329.6, 0, 392.0, 0, 329.6, 0, 369.9, 0,
            329.6, 0, 311.1, 0, 246.9, 0, 329.6, 0,
            329.6, 0, 587.3, 587.3, 329.6, 0, 493.9, 0,
            329.6, 0, 659.3, 0, 587.3, 493.9, 329.6, 0,
        ]
        
        # Evolving variations: pitched up, then arpeggiated
        cb_notes = cb_base + [n * 1.5 if n > 0 else 0 for n in cb_base] + [n * 2.0 if n > 0 else 0 for n in cb_base] + [n * 0.75 if n > 0 else 0 for n in cb_base]
        
        # 808 Bass Pattern (much longer and more complex)
        bass_pitches = [
            41.2, 0, 0, 41.2, 0, 0, 41.2, 0, 
            0, 41.2, 41.2, 0, 0, 0, 0, 0,
            49.0, 0, 0, 49.0, 0, 0, 49.0, 0, 
            0, 49.0, 49.0, 0, 0, 0, 0, 0,
            36.7, 0, 0, 36.7, 0, 0, 36.7, 0, 
            0, 36.7, 36.7, 0, 0, 0, 0, 0,
            41.2, 0, 0, 41.2, 0, 0, 41.2, 0, 
            0, 41.2, 41.2, 0, 41.2, 0, 41.2, 0
        ] * 4 # Repeat 4 times for the full progression
        
        # Add high-end distortion noise for the hat and snare layers
        noise = [random.uniform(-1, 1) for _ in range(22050)]
        
        for i in range(steps):
            t = i / 22050.0
            step = int((t / duration) * total_steps) % total_steps
            step_t = t - (step * step_len)
            
            # --- 808 BASS (Distorted Sine with Pitch Drop) ---
            bass = 0.0
            last_bass_step = step
            while last_bass_step >= 0 and bass_pitches[last_bass_step % len(bass_pitches)] == 0: last_bass_step -= 1
            if last_bass_step >= 0:
                b_t = t - (last_bass_step * step_len)
                if b_t < 1.0:
                    b_freq = bass_pitches[last_bass_step % len(bass_pitches)]
                    if step >= 512: b_freq *= 1.0 + math.sin(b_t * math.pi * 8) * 0.03 # Wobbly bass in second half
                    # Correct integral of frequency envelope for phase
                    integral_env = (1.0 - math.exp(-b_t * 12.0)) / 12.0
                    phase = (b_freq * b_t + b_freq * 0.5 * integral_env) % 1.0
                    wave = math.sin(phase * 2 * math.pi)
                    # Hard overdrive distortion
                    wave = max(-0.95, min(0.95, wave * 12.0))
                    bass = wave * math.exp(-b_t * 1.5) * 0.75
                
            # --- DRIFT PHONK COWBELL & SYNTH LEAD ---
            cowbell = 0.0
            last_cb_step = step
            while last_cb_step >= 0 and cb_notes[last_cb_step % len(cb_notes)] == 0: last_cb_step -= 1
            if last_cb_step >= 0:
                cb_t = t - (last_cb_step * step_len)
                if cb_t < 0.5:
                    cb_freq = cb_notes[last_cb_step % len(cb_notes)]
                    v1 = 1.0 if ((cb_t * cb_freq) % 1.0) < 0.5 else -1.0
                    v2 = 1.0 if ((cb_t * cb_freq * 1.48) % 1.0) < 0.5 else -1.0
                    # Add a sawtooth lead for the second half
                    synth = 0.0
                    if step >= 256:
                        mod = 1.0 + math.sin(t * 15) * 0.05
                        synth = (2.0 * ((cb_t * cb_freq * 2.0 * mod) % 1.0) - 1.0) * math.exp(-cb_t * 5.0) * 0.5
                    if step >= 768:
                        synth += (2.0 * ((cb_t * cb_freq * 3.0) % 1.0) - 1.0) * math.exp(-cb_t * 8.0) * 0.3 # Higher octave layer
                    cowbell = (v1 + v2) * 0.5 * math.exp(-cb_t * 15.0) * 0.35 + synth
                    
            # --- TRAP PERCUSSION (Hats and Snare) ---
            hat = 0.0
            # Hi-hat ratchets (32nd notes) on specific steps
            is_ratchet = step % 16 in [14, 15] or (step >= 256 and step % 16 in [6, 7])
            hh_t = (step_t % (step_len / 2.0)) if is_ratchet else step_t
            if hh_t < 0.1:
                hat = noise[i % 22050] * math.exp(-hh_t * 45.0) * 0.3
                
            snare = 0.0
            if step % 16 == 8: # Half-time snare on beat 3
                if step_t < 0.3:
                    sn_phase = 250 * step_t + (250 / 30.0) * (1.0 - math.exp(-step_t * 30.0))
                    sn_body = math.sin(sn_phase * 2 * math.pi) * math.exp(-step_t * 25.0)
                    sn_noise = noise[(i + 1000) % 22050] * math.exp(-step_t * 15.0)
                    snare = (sn_body + sn_noise * 1.5) * 0.55
            
            # --- MASTERING (Soft Clipping / Saturation) ---
            mixed = bass + cowbell + hat + snare
            mixed = math.tanh(mixed * 2.8) * 0.7 # Analog warmth & limiting
            
            sample = int(max(-32768, min(32767, mixed * 32767)))
            struct.pack_into('<h', buf, i * 2, sample)
            
        return self._create_wav_sound(buf, 22050, cache_key="theme_v2", return_path=return_path, channels=1)

    def play_curler_call(self, intensity):
        now = pygame.time.get_ticks()
        if intensity > 8.0 and (now - self.last_call) > 2500:
            self.last_call = now
            if self.snd_hurry and self.snd_hard:
                if not self.ch_voice.get_busy():
                    if random.random() > 0.5: self.ch_voice.play(self.snd_hurry)
                    else: self.ch_voice.play(self.snd_hard)

    def stop_all_match_sounds(self):
        self.ch_slide.set_volume(0.0); self.ch_sweep.set_volume(0.0); self.ch_sfx.stop(); self.ch_crowd.stop()

    def play_cheer(self): 
        if not self.ch_crowd.get_busy() and getattr(self, 'snd_cheer', None): self.ch_crowd.play(self.snd_cheer)
    def update_slide(self, speed): self.ch_slide.set_volume(min(0.15, speed * 0.04) if speed > 0.05 else 0.0)
    def update_sweep(self, intensity):
        self.ch_sweep.set_volume(min(0.5, intensity * 0.06))
        if IS_ANDROID and intensity > 0.1:
            now = pygame.time.get_ticks()
            if not hasattr(self, 'last_sweep_vib') or now - getattr(self, 'last_sweep_vib', 0) > 100:
                self.last_sweep_vib = now
                vibrate_android(15)
    def play_throw(self): 
        if getattr(self, 'snd_throw', None): self.ch_sfx.play(self.snd_throw)
    
    def play_clack(self, force): 
        now = pygame.time.get_ticks()
        if hasattr(self, 'last_clack') and now - self.last_clack < 150: return
        self.last_clack = now
        ch = pygame.mixer.find_channel()
        if ch and getattr(self, 'snd_clack', None):
            ch.play(self.snd_clack)
            ch.set_volume(min(0.4, force * 0.05))

    def play_hover(self): 
        if getattr(self, 'snd_hover', None): self.ch_ui.play(self.snd_hover)
    def play_click(self): 
        if getattr(self, 'snd_click', None): self.ch_ui.play(self.snd_click)
        if IS_ANDROID: vibrate_android(15)
    def play_music(self):
        if not getattr(self, 'sfx_on', True) or not getattr(self, 'snd_music', None): return
        if not pygame.mixer.music.get_busy():
            loaded = False
            if isinstance(self.snd_music, list):
                for p in self.snd_music:
                    try:
                        pygame.mixer.music.load(p)
                        loaded = True; break
                    except: pass
                if not loaded:
                    try:
                        fallback = self._synthesize_theme_song(return_path=True)
                        pygame.mixer.music.load(fallback)
                        loaded = True
                    except: pass
            elif isinstance(self.snd_music, str):
                try:
                    pygame.mixer.music.load(self.snd_music); loaded = True
                except: pass
            if loaded:
                pygame.mixer.music.set_volume(0.25)
                pygame.mixer.music.play(-1)
    def stop_music(self):
        pygame.mixer.music.stop()

# --- Visual Effects & Geometry ---
class Starfield:
    def __init__(self, count=150, max_w=None, max_h=None):
        self.max_h = max_h or BASE_HEIGHT
        self.stars = [(random.randint(0, max_w or BASE_WIDTH), random.randint(0, self.max_h), random.uniform(0.5, 3.0)) for _ in range(count)]
        self.colors = {s: (int(min(255, 30 + s*60)),)*3 for _, _, s in self.stars}
        
    def draw(self, surface, speed_mult=1.0):
        for i in range(len(self.stars)):
            x, y, s = self.stars[i]; y = (y + s * speed_mult) % self.max_h
            self.stars[i] = (x, y, s)
            size = max(1, int(s))
            surface.fill(self.colors[s], (int(x), int(y), size, size))

# OPTIMIZATION: Pre-rendered 3D stone for Menu to save drawing calls
class ThreeDStone:
    cached_surf = None

    @classmethod
    def render_cache(cls):
        if cls.cached_surf is not None: return
        r_max = 280
        surf = pygame.Surface((r_max*2+80, r_max*2+80), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        bx, by = r_max + 20, r_max + 30
        
        pygame.draw.ellipse(surf, (10, 15, 20, 100), (bx - r_max + 20, by - r_max + 30, r_max*2, r_max*2-40))
        for r in range(r_max, 150, -2):
            t = (r_max - r) / (r_max - 150)
            shade = int(70 + 80 * (1.0 - (1.0 - t)**3))
            pygame.draw.circle(surf, (shade, shade+2, shade+5), (int(bx), int(by)), r)
            
        pygame.draw.circle(surf, (60, 65, 70), (int(bx), int(by)), 160)
        for r in range(150, 80, -2):
            t = (150 - r) / 70.0
            col = lerp_color(HOUSE_RED, (140, 20, 30), t)
            pygame.draw.circle(surf, col, (int(bx), int(by)), r)
            
        draw_maple_leaf(surf, bx, by + 12, 2.5, WHITE)
        hx_start, hy_start, hx_end, hy_end = bx - 130, by + 70, bx + 130, by - 70
        for i in range(240):
            p = i / 240.0; px, py = hx_start + (hx_end - hx_start)*p, hy_start + (hy_end - hy_start)*p
            h_col = lerp_color(BLACK, (70, 75, 80), 1.0 - abs(p - 0.5)*2)
            pygame.draw.circle(surf, h_col, (int(px), int(py - math.sin(p*math.pi)*90)), 32) 
            pygame.draw.circle(surf, HOUSE_RED, (int(px), int(py - math.sin(p*math.pi)*90)), 24) 
        
        for x, y in [(hx_start, hy_start), (hx_end, hy_end)]:
            pygame.draw.circle(surf, BLACK, (int(x), int(y)), 36); pygame.draw.circle(surf, HOUSE_RED, (int(x), int(y)), 28)
        pygame.draw.circle(surf, BLACK, (int(hx_start), int(hy_start)), 10); pygame.draw.circle(surf, WHITE, (int(hx_start), int(hy_start)), 4)
        
        # PROPER 3D CRESCENT GLARE REFLECTION
        glare = pygame.Surface((r_max*2, r_max*2), pygame.SRCALPHA)
        glare.fill((0, 0, 0, 0))
        pygame.draw.circle(glare, (255, 255, 255, 80), (r_max, r_max), r_max - 10)
        inner_mask = pygame.Surface((r_max*2, r_max*2), pygame.SRCALPHA)
        inner_mask.fill((0, 0, 0, 0))
        pygame.draw.circle(inner_mask, (255, 255, 255, 255), (r_max, r_max + 24), r_max - 10)
        glare.blit(inner_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        surf.blit(glare, (bx - r_max, by - r_max))
        cls.cached_surf = surf

    def draw(self, surface, center_x, center_y, mouse_pos):
        bx, by = center_x + (mouse_pos[0] - center_x)*0.03, center_y + (mouse_pos[1] - center_y)*0.03
        if self.cached_surf: surface.blit(self.cached_surf, (bx - 300, by - 310))

# --- Game Entities ---
class Stone:
    # OPTIMIZATION: Cache full un-rotated bases to save 6000 Pygame calls per second.
    cached_red_base = None
    cached_ylw_base = None
    cached_hl = None

    next_id = 1
    def __init__(self, x, y, team, sid=None):
        self.id = sid if sid is not None else random.randint(1000, 9999999)
        self.pos = pygame.math.Vector2(x, y); self.vel = pygame.math.Vector2(0, 0)
        self.team, self.radius, self.mass, self.is_moving, self.curl, self.rotation = team, 32, 1.0, False, 0.0, 0.0
        
        if Stone.cached_red_base is None:
            Stone.cached_hl = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA).convert_alpha()
            pygame.draw.ellipse(Stone.cached_hl, HIGHLIGHT_COLOR, (self.radius*0.6, self.radius*0.2, self.radius*0.8, self.radius*0.4))
            Stone.cached_red_base = self._render_base(HOUSE_RED)
            Stone.cached_ylw_base = self._render_base(TEAM_YELLOW)

    def _render_base(self, color):
        # BUILD 14 PREVIEW 2: Advanced 3D Geometry
        s = pygame.Surface((self.radius*2+15, self.radius*2+15), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(s, (0, 0, 0, 80), (self.radius+8, self.radius+8), self.radius)
        
        for r in range(self.radius, 0, -1):
            t = (self.radius - r) / self.radius
            shade = 70 + int(80 * (1.0 - (1.0 - t)**3))
            pygame.draw.circle(s, (shade, shade+2, shade+5), (self.radius+5, self.radius+5), r)
            
        pygame.draw.circle(s, color, (self.radius+5, self.radius+5), self.radius-4, 6)
        # Highlight ring for 3D depth
        pygame.draw.circle(s, (min(255, color[0]+60), min(255, color[1]+60), min(255, color[2]+60)), (self.radius+5, self.radius+5), self.radius-4, 1)
        
        glare = pygame.Surface((self.radius*2+15, self.radius*2+15), pygame.SRCALPHA).convert_alpha()
        pygame.draw.ellipse(glare, (255, 255, 255, 70), (self.radius-3, self.radius-9, self.radius*1.2, self.radius*0.6))
        s.blit(glare, (0, 0))
        
        return s

    def get_state(self, offset_y=0): return [round(self.pos.x, 1), round(self.pos.y - offset_y, 1), round(self.vel.x, 2), round(self.vel.y, 2), self.team, round(self.curl, 2), round(self.rotation, 1), self.is_moving, getattr(self, 'id', -1)]
    def set_state(self, s, offset_y=0):
        nx, ny, nvx, nvy, self.team, self.curl, self.rotation, self.is_moving = s[0], s[1] + offset_y, s[2], s[3], s[4], s[5], s[6], s[7]
        if len(s) > 8: self.id = s[8]
        now = pygame.time.get_ticks()
        if hasattr(self, 'last_collision_time') and now - self.last_collision_time < 400: return
        new_pos = pygame.math.Vector2(nx, ny); new_vel = pygame.math.Vector2(nvx, nvy)
        dist = (self.pos - new_pos).length()
        if dist > 80.0:
            self.pos.x, self.pos.y, self.vel.x, self.vel.y = nx, ny, nvx, nvy
        else:
            if dist > 1.0: self.pos = self.pos.lerp(new_pos, 0.4)
            if (self.vel - new_vel).length() > 1.0: self.vel = self.vel.lerp(new_vel, 0.4)

    def update(self, sweep_intensity, base_friction):
        if not self.is_moving: return
        speed = self.vel.length(); current_friction = max(0.008, base_friction - (sweep_intensity * 0.0012))
        if speed <= current_friction: self.vel.update(0, 0); self.is_moving = False
        else:
            self.vel.scale_to_length(speed - current_friction)
            if speed > 0.4: self.vel.rotate_ip((1.4 / speed) * self.curl * 0.05 * (1.0 - (sweep_intensity * 0.04)))
            self.rotation += speed * (self.curl * 2.8 if abs(self.curl * 2.8) >= 0.6 else (0.6 if self.curl>=0 else -0.6))
            self.pos += self.vel

    def draw(self, surface):
        surface.blit(Stone.cached_red_base if self.team == 0 else Stone.cached_ylw_base, (self.pos.x - self.radius - 5, self.pos.y - self.radius - 5))
        color = HOUSE_RED if self.team == 0 else TEAM_YELLOW
        
        angle = math.radians(self.rotation)
        hx_s, hy_s = self.pos.x - math.cos(angle)*18, self.pos.y - math.sin(angle)*18
        hx_e, hy_e = self.pos.x + math.cos(angle)*22, self.pos.y + math.sin(angle)*22
        
        # 3D Handle
        pygame.draw.line(surface, (40, 40, 40), (hx_s, hy_s), (hx_e, hy_e), 14)
        for x,y in [(hx_s,hy_s), (hx_e,hy_e)]: pygame.draw.circle(surface, (40, 40, 40), (int(x), int(y)), 7)
        pygame.draw.line(surface, color, (hx_s, hy_s), (hx_e, hy_e), 8)
        for x,y in [(hx_s,hy_s), (hx_e,hy_e)]: pygame.draw.circle(surface, color, (int(x), int(y)), 4)
        
        hl_s, hl_e = self.pos.x - math.cos(angle)*10 - math.sin(angle)*2, self.pos.y - math.sin(angle)*10 + math.cos(angle)*2
        pygame.draw.circle(surface, WHITE, (int(hl_s), int(hl_e)), 2)
        
        surface.blit(Stone.cached_hl, (self.pos.x - self.radius, self.pos.y - self.radius))

class AnimatedCurler:
    _head_cache = {}

    def __init__(self, hack_pos):
        self.hack_pos = pygame.math.Vector2(hack_pos); self.delivery_progress = 0.0; self.state = "IDLE"
        
    def update(self, state, drag_vector=None):
        self.state = state
        if self.state == "LUNGING":
            self.delivery_progress = min(1.0, self.delivery_progress + 0.04)
            if self.delivery_progress >= 1.0: self.state = "IDLE"; self.delivery_progress = 0.0
        elif self.state == "BACKSWING" and drag_vector: self.delivery_progress = min(1.0, drag_vector.length() / 250.0)
        else: self.delivery_progress = 0.0

    def _draw_char_geometry(self, surface, hx, hy, offset_y, lunge_dist, override_color=None):
        def c(col): return override_color or col

        def draw_cylinder_line(surf, color, start, end, width):
            if override_color:
                pygame.draw.line(surf, override_color, start, end, width)
                return
            shadow_col = (max(0, color[0]-50), max(0, color[1]-50), max(0, color[2]-50))
            pygame.draw.line(surf, shadow_col, start, end, width)
            pygame.draw.line(surf, color, start, end, max(2, width - 4))
            hl_col = (min(255, color[0]+60), min(255, color[1]+60), min(255, color[2]+60))
            pygame.draw.line(surf, hl_col, (start[0]-2, start[1]), (end[0]-2, end[1]), max(1, width - 8))

        def head(ix, iy):
            cache_key = (self.tc, override_color)
            if cache_key not in AnimatedCurler._head_cache:
                surf = pygame.Surface((60, 80), pygame.SRCALPHA)
                cx, cy = 30, 40
                
                head_rw, head_rh = 15, 12
                # Base skin tone
                pygame.draw.ellipse(surf, c((240, 200, 180)), (cx-head_rw, cy-head_rh, head_rw*2, head_rh*2))

                if not override_color:
                    import math
                    import random
                    rng = random.Random(self.tc[0] + self.tc[1])  # Deterministic seed based on team color
                    hair_poly = []
                    shade = max(0, self.tc[0]-100)
                    hair_color = (shade, int(shade*0.75), int(shade*0.55))
                    
                    # Draw spiky procedural hair
                    for angle in range(0, 361, 15):
                        rad = math.radians(angle)
                        base_r = head_rw * 1.1
                        # Hair is longer at the bottom/back of the head
                        if 0 <= angle <= 180:
                            spike = rng.uniform(0, 8)
                            r = base_r + spike
                        else:
                            r = base_r
                        hair_poly.append((cx + math.cos(rad)*r, cy + math.sin(rad)*r))
                    
                    pygame.draw.polygon(surf, hair_color, hair_poly)
                else:
                    pygame.draw.ellipse(surf, c((80, 50, 30)), (cx-head_rw, cy-head_rh, head_rw*2, head_rh*2))

                # Beanie Base
                hat_rw, hat_rh = 19, 14
                hat_shade = (max(0, self.tc[0]-80), max(0, self.tc[1]-80), max(0, self.tc[2]-80))
                
                # The beanie pulled down over the back of the head
                pygame.draw.ellipse(surf, c(hat_shade), (cx-hat_rw-1, cy-head_rh-6, hat_rw*2+2, hat_rh*2+2))
                pygame.draw.ellipse(surf, c(self.tc), (cx-hat_rw, cy-head_rh-5, hat_rw*2, hat_rh*2))

                if not override_color:
                    pygame.draw.ellipse(surf, (min(255, self.tc[0]+40), min(255, self.tc[1]+40), min(255, self.tc[2]+40)), (cx-hat_rw+4, cy-head_rh-3, hat_rw*2-8, 6))

                # Beanie Brim (Curves across the back of the head)
                pygame.draw.rect(surf, c(hat_shade), (cx-hat_rw-2, cy-head_rh+4, hat_rw*2+4, 10), border_radius=4)
                pygame.draw.rect(surf, c(self.tc), (cx-hat_rw-1, cy-head_rh+5, hat_rw*2+2, 8), border_radius=3)
                pygame.draw.rect(surf, c(CYAN_ACCENT), (cx-hat_rw-1, cy-head_rh+7, hat_rw*2+2, 3), border_radius=1)

                # Pom-pom (Slightly shifted up for back perspective)
                if not override_color:
                    for r in range(9, 0, -1):
                        s = 140 + r*11
                        pygame.draw.circle(surf, (s,s,s), (cx, cy-head_rh-9), r)
                else:
                    pygame.draw.circle(surf, c((180,180,180)), (cx, cy-head_rh-9), 9)
                    
                AnimatedCurler._head_cache[cache_key] = surf
            
            surface.blit(AnimatedCurler._head_cache[cache_key], (ix - 30, iy - 40))

        if self.state == "BACKSWING":
            # 3D Legs
            draw_cylinder_line(surface, (30,30,35), (hx-15, hy+90+offset_y), (hx-20, hy+140+offset_y), 16)
            draw_cylinder_line(surface, (30,30,35), (hx+15, hy+90+offset_y), (hx+20, hy+140+offset_y), 16)
            
            # SHOES
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx-28, hy+135+offset_y, 20, 30))
            pygame.draw.ellipse(surface, c((240, 240, 240)), (hx-26, hy+137+offset_y, 16, 26))
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx+12, hy+135+offset_y, 20, 30))
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx+14, hy+137+offset_y, 16, 26))
            
            # Back of Neck
            if override_color:
                pygame.draw.rect(surface, c((240,200,180)), (int(hx-8), int(hy+offset_y), 16, 20))
            else:
                pygame.draw.rect(surface, (200, 150, 130), (int(hx-8), int(hy+offset_y), 16, 20))
                # Hair shadow cast onto the back of the neck
                pygame.draw.rect(surface, (160, 110, 90), (int(hx-8), int(hy+offset_y), 16, 6))

            # 90s Tracksuit Body (Back View)
            if override_color:
                pygame.draw.rect(surface, c(PURPLE_SUIT), (hx-35, hy+20+offset_y, 70, 80), border_radius=16)
            else:
                pygame.draw.rect(surface, PURPLE_SHADOW, (hx-36, hy+18+offset_y, 72, 84), border_radius=16)
                pygame.draw.rect(surface, PURPLE_SUIT, (hx-32, hy+20+offset_y, 64, 76), border_radius=14)
                pygame.draw.rect(surface, (150, 55, 210), (hx-22, hy+24+offset_y, 30, 68), border_radius=10)

            # Tracksuit accent lines (Center zipper removed for back view)
            pygame.draw.line(surface, c(CYAN_ACCENT), (hx-20, hy+30+offset_y), (hx-20, hy+92+offset_y), 4)
            pygame.draw.line(surface, c(CYAN_ACCENT), (hx+20, hy+30+offset_y), (hx+20, hy+92+offset_y), 4)

            # Tracksuit Collar (Wraps fully around the back of the neck)
            if override_color:
                pygame.draw.rect(surface, c(PURPLE_SUIT), (hx-16, hy+10+offset_y, 32, 14), border_radius=4)
            else:
                pygame.draw.rect(surface, PURPLE_SHADOW, (hx-17, hy+9+offset_y, 34, 16), border_radius=4)
                pygame.draw.rect(surface, PURPLE_SUIT, (hx-15, hy+11+offset_y, 30, 12), border_radius=3)

            # Full Head Overlap
            head(hx, hy - 8 + offset_y)
            
            # 3D Forward Arm
            draw_cylinder_line(surface, (210,180,50), (hx-55, hy+10+offset_y), (hx-15, hy+45+offset_y), 10)
            
            # Hand & Hack Foot Shadows
            pygame.draw.ellipse(surface, c((90, 10, 15)), (hx-71, hy-1+offset_y, 28, 20))
            if not override_color: pygame.draw.ellipse(surface, HOUSE_RED, (hx-69, hy+1+offset_y, 24, 16))
            
            pygame.draw.ellipse(surface, c(PURPLE_SHADOW), (hx-48, hy+28+offset_y, 31, 56))
            pygame.draw.ellipse(surface, c(PURPLE_SUIT), (hx-45, hy+30+offset_y, 25, 50))
            pygame.draw.ellipse(surface, c(PURPLE_SHADOW), (hx+17, hy+28+offset_y, 31, 56))
            pygame.draw.ellipse(surface, c(PURPLE_SUIT), (hx+20, hy+30+offset_y, 25, 50))
            
            if not override_color:
                pygame.draw.ellipse(surface, (150, 55, 210), (hx-42, hy+32+offset_y, 10, 40))
                pygame.draw.ellipse(surface, (150, 55, 210), (hx+22, hy+32+offset_y, 10, 40))
        
        elif self.state == "LUNGING":
            ly = hy + lunge_dist
            
            # 3D Forward Leg
            draw_cylinder_line(surface, (30,30,35), (hx-12, ly+60), (hx-15, hy+110), 18)
            # SHOE (Forward)
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx-25, hy+105, 24, 34)) 
            pygame.draw.ellipse(surface, c((240, 240, 240)), (hx-23, hy+107, 20, 30))
            
            # Trailing Leg
            pygame.draw.polygon(surface, c((15,15,20)), [(hx+6, ly+48), (hx+34, ly+99), (hx+10, ly+104)])
            if not override_color: 
                pygame.draw.polygon(surface, (50,50,55), [(hx+10, ly+52), (hx+30, ly+94), (hx+14, ly+97)])
            # SHOE (Trailing)
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx+22, ly+94, 20, 30))

            # Back of Neck
            if override_color:
                pygame.draw.rect(surface, c((240,200,180)), (int(hx-8), int(ly-48), 16, 20))
            else:
                pygame.draw.rect(surface, (200, 150, 130), (int(hx-8), int(ly-48), 16, 20))
                # Hair shadow
                pygame.draw.rect(surface, (160, 110, 90), (int(hx-8), int(ly-48), 16, 6))

            # 90s Tracksuit Body (Back View)
            if override_color:
                pygame.draw.rect(surface, c(PURPLE_SUIT), (hx-30, ly-30, 60, 90), border_radius=15)
            else:
                pygame.draw.rect(surface, PURPLE_SHADOW, (hx-32, ly-32, 64, 94), border_radius=15)
                pygame.draw.rect(surface, PURPLE_SUIT, (hx-28, ly-30, 56, 86), border_radius=12)
                pygame.draw.rect(surface, (150, 55, 210), (hx-18, ly-26, 26, 76), border_radius=10)

            # Tracksuit accent lines (Center zipper removed for back view)
            pygame.draw.line(surface, c(CYAN_ACCENT), (hx-15, ly-15), (hx-15, ly+50), 4)
            pygame.draw.line(surface, c(CYAN_ACCENT), (hx+15, ly-15), (hx+15, ly+50), 4)

            # Tracksuit Collar
            if override_color:
                pygame.draw.rect(surface, c(PURPLE_SUIT), (hx-16, ly-39, 32, 14), border_radius=4)
            else:
                pygame.draw.rect(surface, PURPLE_SHADOW, (hx-17, ly-40, 34, 16), border_radius=4)
                pygame.draw.rect(surface, PURPLE_SUIT, (hx-15, ly-38, 30, 12), border_radius=3)

            # Full Head Overlap
            head(hx, ly-45)
            
            # 3D Lunging Arm
            draw_cylinder_line(surface, (210,180,50), (hx-75, ly-10), (hx-20, ly+20), 10)
            
            # Slider Hand
            pygame.draw.ellipse(surface, c((90, 10, 15)), (hx-92, ly-19, 32, 20))
            if not override_color: pygame.draw.ellipse(surface, HOUSE_RED, (hx-90, ly-17, 28, 16))
            
            # Broom Arm
            draw_cylinder_line(surface, PURPLE_SUIT, (hx-25, ly-10), (hx-10, ly-60), 16)

    def draw(self, surface, team_color):
        if self.state == "IDLE" and self.delivery_progress == 0.0: return
        self.tc = team_color; oy = self.delivery_progress*70 if self.state == "BACKSWING" else 0; ld = (1.0 - self.delivery_progress)*-190 if self.state == "LUNGING" else 0
        
        if not hasattr(self, 'shadow_surf'):
            self.shadow_surf = pygame.Surface((250, 350), pygame.SRCALPHA).convert_alpha()
        self.shadow_surf.fill((0,0,0,0))
        self._draw_char_geometry(self.shadow_surf, 125+18, 150+18, oy, ld, (0,0,0,100))
        surface.blit(self.shadow_surf, (self.hack_pos.x - 125, self.hack_pos.y - 150))
        
        self._draw_char_geometry(surface, self.hack_pos.x, self.hack_pos.y, oy, ld)
# --- Main Engine ---
class WinCurl3:
    def __init__(self):
        self.screen = None
        self.canvas = None
        self.current_mapped_pos = pygame.math.Vector2(BASE_WIDTH//2, BASE_HEIGHT//2)
        self.is_pointer_pressed = False
        
        # BUILD 14 PREVIEW 2: Advanced Chat State
        self.chat_messages = []
        self.typing_chat = False
        self.chat_input = ""
        self.frames_elapsed = 0

    def get_pointer_pos(self):
        return self.current_mapped_pos

    def get_pointer_pressed(self):
        return self.is_pointer_pressed

    def scale_mouse(self, pos):
        if IS_ANDROID:
            if isinstance(pos, pygame.math.Vector2): return pos
            return pygame.math.Vector2(pos[0], pos[1])
            
        ww, wh = self.screen.get_size()
        scale = min(ww / BASE_WIDTH, wh / BASE_HEIGHT)
        sw, sh = int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale)
        ox, oy = (ww - sw) // 2, (wh - sh) // 2
        
        mx = (pos[0] - ox) / scale if scale > 0 else pos[0]
        my = (pos[1] - oy) / scale if scale > 0 else pos[1]
        return pygame.math.Vector2(mx, my)

    def preload_assets(self):
        self.font = CachedFont(pygame.font.Font(None, 45))
        self.score_font = CachedFont(pygame.font.Font(None, 36))
        self.small_font = CachedFont(pygame.font.Font(None, 31))
        self.chat_font = ChatFont(31)
        self.title_font = pygame.font.Font(None, 120)
        self.large_sym_font = CachedFont(pygame.font.Font(None, 95))
        self.font_62 = CachedFont(pygame.font.Font(None, 60))
        self.font_72 = CachedFont(pygame.font.Font(None, 70))
        self.font_85 = CachedFont(pygame.font.Font(None, 82))
        
        # Pre-allocate dark overlays used in UI
        self.dark_overlay_150 = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha(); self.dark_overlay_150.fill((0, 0, 0, 150))
        self.dark_overlay_200 = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha(); self.dark_overlay_200.fill((0, 0, 0, 200))
        
        self.BOT_LOGIC_CACHE = {
            "easy": {"error_multiplier": 2.5, "takeout_chance": 0.1, "guard_chance": 0.3},
            "medium": {"error_multiplier": 1.0, "takeout_chance": 0.4, "guard_chance": 0.5},
            "hard": {"error_multiplier": 0.2, "takeout_chance": 0.8, "guard_chance": 0.7}
        }
        
        t_text = 'WinCurl 3'
        
        # Use standard Pygame font for the original heavy bold look.
        # Render at exactly 2x scale (210) to bypass SDL_ttf hinting clipping bugs on the top edge of letters like "C".
        ss_font = pygame.font.Font(None, 240)
        ss_white = ss_font.render(t_text, True, WHITE)
        ss_purple = ss_font.render(t_text, True, (80, 20, 140))
        
        # Smoothscale down by exactly half to get a pristine, unclipped 105-point title
        target_size = (ss_white.get_width() // 2, ss_white.get_height() // 2)
        self.title_base = pygame.transform.smoothscale(ss_white, target_size)
        self.title_shadow = pygame.transform.smoothscale(ss_purple, target_size)
        
        # Pre-render the thick 36-sample rounded outline so we don't kill the FPS doing 36 blits per frame!
        outline_size = 7
        pad = outline_size + 2
        self.title_outline = pygame.Surface((self.title_shadow.get_width() + pad*2, self.title_shadow.get_height() + pad*2), pygame.SRCALPHA)
        self.title_outline.fill((0, 0, 0, 0)) # Explicitly clear to transparent to fix backend black-rectangle bug
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            dx, dy = math.cos(rad) * outline_size, math.sin(rad) * outline_size
            self.title_outline.blit(self.title_shadow, (pad + dx, pad + dy))
        
        # Pre-render hypnotic rainbow text background (tighter period for trippier effect)
        rw = self.title_base.get_width() + 600
        self.rainbow_grad = pygame.Surface((rw, 200)).convert()
        for x in range(rw):
            c = pygame.Color(0); c.hsva = ((x / 150.0) * 360 % 360, 90, 100, 100)
            pygame.draw.line(self.rainbow_grad, c, (x, 0), (x, 200))
        
        # Live-rendered rainbow text avoids a 50-frame pre-generation delay (fixes Android load time)
        self.title_rainbow_frame = pygame.Surface(self.title_base.get_size(), pygame.SRCALPHA).convert_alpha()
            
        # Realistic Olympic Push Broom Rendering
        self.broom_surf = pygame.Surface((80, 260), pygame.SRCALPHA)
        pygame.draw.rect(self.broom_surf, (215, 215, 30), (35, 0, 10, 220), border_radius=4)
        pygame.draw.rect(self.broom_surf, (40, 40, 45), (20, 220, 40, 20), border_radius=4)
        pygame.draw.rect(self.broom_surf, (225, 225, 225), (10, 240, 60, 18), border_radius=6)
        pygame.draw.line(self.broom_surf, (150, 150, 150), (12, 248), (68, 248), 2)
            
        # Pre-render coins for butter-smooth Android coin flip
        self.coin_red_surf = self._render_coin_surface(True)
        self.coin_yellow_surf = self._render_coin_surface(False)
        ThreeDStone.render_cache()
        
        # Pre-cache all UI buttons to eliminate Android boot-lag
        for c in [(40, 120, 200), (60, 60, 65), TEAM_YELLOW, HOUSE_RED, (40, 150, 80), (150, 40, 80), HOUSE_BLUE]:
            UICache.get_glass(600, 100, c, 50, False)
        for c in [(50, 60, 80), (50, 55, 65)]: UICache.get_glass(80, 80, c, 40, False)
        UICache.get_glass(200, 90, (255, 180, 180), 16, False)
        UICache.get_glass(200, 90, (180, 255, 180), 16, False)
        
    def _render_coin_surface(self, is_red):
        surf = pygame.Surface((280, 280), pygame.SRCALPHA).convert_alpha()
        cx, cy, r_w, r_h = 140, 140, 120, 120
        for i in range(15): pygame.draw.ellipse(surf, (150, 110, 10), (cx - r_w, cy - r_h//2 + 15 - i, r_w * 2, r_h))
        pygame.draw.ellipse(surf, (255, 215, 0), (cx - r_w, cy - r_h//2, r_w * 2, r_h))
        pygame.draw.ellipse(surf, (220, 170, 20), (cx - int(r_w*0.85), cy - int(r_h*0.85)//2, int(r_w*0.85)*2, int(r_h*0.85)))
        pygame.draw.ellipse(surf, (255, 215, 0), (cx - int(r_w*0.75), cy - int(r_h*0.75)//2, int(r_w*0.75)*2, int(r_h*0.75)))
        if is_red: draw_maple_leaf(surf, cx, cy, 2.0, HOUSE_RED)
        else:
            rw = 55
            pygame.draw.ellipse(surf, (90, 95, 100), (cx - rw, cy - 10, rw*2, 30))
            pygame.draw.ellipse(surf, (150, 155, 160), (cx - rw, cy - 25, rw*2, 35))
            pygame.draw.ellipse(surf, HOUSE_BLUE, (cx - rw, cy - 15, rw*2, 18))
            pygame.draw.ellipse(surf, (170, 175, 180), (cx - rw*0.75, cy - 32, rw*1.5, 25))
            pygame.draw.ellipse(surf, HOUSE_BLUE, (cx - rw*0.25, cy - 35, rw*0.5, 12))
            pygame.draw.lines(surf, HOUSE_BLUE, False, [(cx - rw*0.4, cy - 25), (cx - rw*0.4, cy - 48), (cx + rw*0.2, cy - 48), (cx + rw*0.4, cy - 25)], 8)
            
        glare = pygame.Surface((r_w * 2, r_h), pygame.SRCALPHA).convert_alpha()
        pygame.draw.ellipse(glare, (255, 255, 255, 60), (int(r_w*0.2), int(r_h*0.1), int(r_w*1.6), int(r_h*0.4)))
        surf.blit(glare, (cx - r_w, cy - r_h//2))
        return surf

    def setup_display(self):
        import sys
        if sys.platform == 'win32':
            import ctypes
            try: ctypes.windll.user32.SetProcessDPIAware()
            except: pass
        import os
        os.environ['SDL_RENDER_SCALE_QUALITY'] = '1'
            
        pygame.display.init()
        gm = getattr(self, 'game_mode', 'MENU')
        pygame.display.set_caption(f"WinCurl 3.0 - Build {VERSION}{'' if gm == 'MENU' else ' - ' + gm}")

        info = pygame.display.Info()
        
        global BASE_HEIGHT
        if IS_ANDROID and info.current_w > 0 and info.current_h > 0:
            aspect = info.current_h / info.current_w
            BASE_HEIGHT = int(BASE_WIDTH * aspect)
        
        if IS_ANDROID:
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.SCALED)
        else:
            desk_h = info.current_h
            if desk_h > 0 and 1800 > desk_h * 0.85:
                target_h = int(desk_h * 0.85)
                target_w = int(target_h * (BASE_WIDTH / BASE_HEIGHT))
                self.screen = pygame.display.set_mode((target_w, target_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
            else:
                self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
                
        try:
            if not IS_ANDROID:
                ThreeDStone.render_cache()
                try: pygame.image.save(ThreeDStone.cached_surf, "icon.png")
                except: pass
                try: pygame.image.save(ThreeDStone.cached_surf, "icon.png")
                except: pass
                try:
                    import shutil
                    for target_dir in ["wincurl_android", "wincurl_android/wincurl_build_clean", "wincurl/wincurl_android", "wincurl/wincurl_android/wincurl_build_clean"]:
                        if os.path.exists(target_dir):
                            pygame.image.save(ThreeDStone.cached_surf, os.path.join(target_dir, "icon.png"))
                except: pass
            
            if not IS_ANDROID:
                try: pygame.display.set_icon(pygame.image.load("icon.png"))
                except: pass
                
                if hasattr(os, 'name') and os.name == 'posix':
                    desk_dir = os.path.expanduser("~/.local/share/applications")
                    os.makedirs(desk_dir, exist_ok=True)
                    desk_path = os.path.join(desk_dir, "wincurl3.desktop")
                    if not os.path.exists(desk_path):
                        icon_path = os.path.abspath("icon.png")
                        exec_path = os.path.abspath(sys.argv[0])
                        with open(desk_path, "w") as f:
                            f.write(f"[Desktop Entry]\nName=WinCurl 3\nExec=python3 {exec_path}\nIcon={icon_path}\nType=Application\nTerminal=false\nCategories=Game;\nStartupWMClass=wincurl3\n")
                        os.system(f"update-desktop-database {desk_dir} >/dev/null 2>&1")
        except:
            pass
        
        self.is_4k = (info.current_w >= 1920 or info.current_h >= 1080)
        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT)).convert()
        self.clock = pygame.time.Clock()
        
        pygame.font.init()
        self.preload_assets()
        
        self.app_state = "MENU"        
        self.game_mode = "LOCAL"
        self.audio = WinCurlAudioEngine()
        self.net = IRCNetworkManager()
        self.is_fullscreen = False
        self.dragging_slider = False
        self.drag_start_pos = None
        
        try:
            base_dir = pygame.system.get_pref_path("jason", "wincurl3")
        except:
            if IS_ANDROID:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.environ.get('ANDROID_PRIVATE', os.path.abspath(os.path.join(app_dir, '..')))
            else:
                base_dir = os.path.expanduser("~")
        self.save_file = os.path.join(base_dir, ".wincurl3_save.json")
        self.load_progress()
        
        self.house_pos = pygame.math.Vector2(BASE_WIDTH // 2, (BASE_HEIGHT // 2) + 100 - 650)
        self.hack_pos = pygame.math.Vector2(BASE_WIDTH // 2, (BASE_HEIGHT // 2) + 100 + 650)
        self.curler_anim = AnimatedCurler(self.hack_pos)
        self.starfield = Starfield(count=50 if IS_ANDROID else 150)
        if self.is_4k:
            self.border_starfield = Starfield(count=400, max_w=4000, max_h=4000)
        
        self.game_mode = "LOCAL"
        self.stones_per_team = 8
        self.challenge_level = 1
        self.challenge_attempts = 0
        self.is_sweeping_now = False
        
        self.menu_stone = ThreeDStone()
        self.particles = []
        self.shake_amount = 0.0
        self.pause_anim = 0.0
        self.typing_target = None; self.net_action = None
        self.prompt_rect = pygame.Rect(BASE_WIDTH//2 - 350, BASE_HEIGHT//2 - 50, 700, 120)
        
        self.btn_curl_l, self.btn_curl_r = pygame.Rect(120, BASE_HEIGHT-260, 200, 90), pygame.Rect(BASE_WIDTH-320, BASE_HEIGHT-260, 200, 90)
        
        self.btn_next_end = pygame.Rect(BASE_WIDTH//2-200, BASE_HEIGHT//2+120, 400, 95)
        self.btn_pause, self.btn_resume = pygame.Rect(BASE_WIDTH - 280, 140, 240, 60), pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2-100, 500, 100)
        self.btn_chat = pygame.Rect(BASE_WIDTH - 500, 140, 180, 60)
        self.btn_quit_main, self.btn_return_menu = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2+40, 500, 100), pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT-250, 500, 100)
        self.btn_mute = pygame.Rect(40, 30, 80, 60)
        self.is_music_muted = False
        
        self.btn_fs = pygame.Rect(BASE_WIDTH - 280, 30, 250, 60)

        self.menu_buttons = [
            {"id": "local", "y": 480, "text": "Local 1v1", "color": HOUSE_RED, "scale": 1.0},
            {"id": "bot", "y": 600, "text": "Local vs Bot", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "chal", "y": 720, "text": "Challenge Mode", "color": PURPLE_SUIT, "scale": 1.0},
            {"id": "options", "y": 840, "text": "Options", "color": HOUSE_RED, "scale": 1.0},
            {"id": "host", "y": 960, "text": "Host IRC", "color": HOUSE_BLUE, "scale": 1.0},
            {"id": "join", "y": 1080, "text": "Join IRC", "color": HOUSE_BLUE, "scale": 1.0},
            {"id": "exit", "y": 1200, "text": "Exit Game", "color": HOUSE_RED, "scale": 1.0}
        ]
        
        self.options_buttons = [
            {"id": "name", "y": 480, "text": "Name:", "color": (130, 140, 155), "scale": 1.0},
            {"id": "color", "y": 600, "text": "My Team:", "color": HOUSE_RED, "scale": 1.0},
            {"id": "vibrate", "y": 720, "text": "Vibration:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "bilinear", "y": 840, "text": "Bilinear Filtering:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "fxaa", "y": 720, "text": "FXAA:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "light_filter", "y": 840, "text": "Lower Spec Filtering:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "back", "y": 1200, "text": "Back", "color": HOUSE_RED, "scale": 1.0}
        ]
        self.last_hovered = None

        self.bg_pebble_layer = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.fg_pebble_layer = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        
        tile_size = 256
        bg_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        fg_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        
        for _ in range(600):
            px, py = random.randint(0, tile_size), random.randint(0, tile_size)
            pygame.draw.circle(bg_tile, (0, 0, 0, 50), (px+1, py+1), 1)
            pygame.draw.circle(bg_tile, (255, 255, 255, 100), (px, py), 1)
        
        for _ in range(400): 
            pygame.draw.circle(fg_tile, (255, 255, 255, random.randint(30, 90)), (random.randint(0, tile_size), random.randint(0, tile_size)), 1)
            
        for tx in range(0, BASE_WIDTH, tile_size):
            for ty in range(0, BASE_HEIGHT, tile_size):
                self.bg_pebble_layer.blit(bg_tile, (tx, ty))
                self.fg_pebble_layer.blit(fg_tile, (tx, ty))
        
        self.ice_env_map = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        pygame.draw.polygon(self.ice_env_map, (255, 255, 255, 18), [(300, 0), (800, 0), (200, BASE_HEIGHT), (-300, BASE_HEIGHT)])
        pygame.draw.polygon(self.ice_env_map, (255, 255, 255, 12), [(900, 0), (1300, 0), (700, BASE_HEIGHT), (300, BASE_HEIGHT)])
        pygame.draw.rect(self.ice_env_map, (0, 0, 0, 30), (0, 0, 100, BASE_HEIGHT))
        pygame.draw.rect(self.ice_env_map, (0, 0, 0, 30), (BASE_WIDTH-100, 0, 100, BASE_HEIGHT))
        
        for x in range(0, BASE_WIDTH, 15):
            dist_from_center = abs(x - BASE_WIDTH//2)
            alpha = max(0, 45 - int((dist_from_center / (BASE_WIDTH//2)) * 45))
            pygame.draw.rect(self.ice_env_map, (255, 255, 255, alpha), (x, 0, 15, BASE_HEIGHT))

        self.static_ice_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT)).convert()
        for y in range(0, BASE_HEIGHT, 45): pygame.draw.rect(self.static_ice_surface, (max(0, ICE_COLOR[0]-int((y/BASE_HEIGHT)*18)),)*3, (0, y, BASE_WIDTH, 45))
        self.static_ice_surface.blit(self.bg_pebble_layer, (0, 0))
        for y in range(0, BASE_HEIGHT, 80): pygame.draw.line(self.static_ice_surface, ICE_SHADOW, (0, y), (BASE_WIDTH, y), 2)
        pygame.draw.line(self.static_ice_surface, TEE_LINE_COLOR, (0, self.house_pos.y), (BASE_WIDTH, self.house_pos.y), 6)
        pygame.draw.line(self.static_ice_surface, (200, 212, 226), (self.house_pos.x, 0), (self.house_pos.x, BASE_HEIGHT), 3)
        pygame.draw.line(self.static_ice_surface, HOG_LINE_COLOR, (0, self.house_pos.y + 400), (BASE_WIDTH, self.house_pos.y + 400), 10)
        pygame.draw.line(self.static_ice_surface, (10, 10, 10), (0, self.house_pos.y - 220), (BASE_WIDTH, self.house_pos.y - 220), 4)
        
        house_layer = pygame.Surface((440, 440))
        house_layer.fill((255, 0, 255))
        house_layer.set_colorkey((255, 0, 255))
        house_layer.set_alpha(80)
        for r, c, w in [(210, HOUSE_BLUE, 0), (140, WHITE, 0), (70, HOUSE_RED, 0), (20, WHITE, 0), (20, BLACK, 2), (6, BLACK, 0), (2, WHITE, 0)]:
            pygame.draw.circle(house_layer, c, (220, 220), r, w)
        self.static_ice_surface.blit(house_layer, (int(self.house_pos.x - 220), int(self.house_pos.y - 220)))
        
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        overlay.fill((235, 245, 255, 15))
        self.static_ice_surface.blit(overlay, (0, 0))
        
        self.static_ice_surface.blit(self.ice_env_map, (0, 0))
        

        self.static_ice_surface.blit(self.fg_pebble_layer, (0, 0))

        self.reset_match()

    def set_typing_target(self, target):
        if getattr(self, 'typing_target', None) == target: return
        was_typing = getattr(self, 'typing_target', None) is not None
        if was_typing: self.save_progress()
        self.typing_target = target
        if IS_ANDROID:
            try:
                if target is not None: pygame.key.start_text_input()
                else: pygame.key.stop_text_input()
            except: pass

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if IS_ANDROID:
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.SCALED)
        else:
            if self.is_fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            else:
                info = pygame.display.Info()
                desk_h = info.current_h
                if desk_h > 0 and 1800 > desk_h * 0.85:
                    target_h = int(desk_h * 0.85)
                    target_w = int(target_h * (BASE_WIDTH / BASE_HEIGHT))
                    self.screen = pygame.display.set_mode((target_w, target_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                else:
                    self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
            ww, wh = self.screen.get_size()
            self.border_starfield = Starfield(count=400, max_w=ww, max_h=wh)
        
    def load_progress(self):
        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)
                self.challenge_progress = data.get("challenge", [False] * 25)
                self.username = data.get("username", "")
                self.preferred_color = data.get("color", 0)
                self.room_text = data.get("room", "")
                self.ai_difficulty = data.get("bot_skill", 5)
                self.challenge_completed_seen = data.get("challenge_completed_seen", False)
                self.is_music_muted = data.get("is_music_muted", False)
                self.vibrate_on = data.get("vibrate_enabled", True)
                self.fxaa_on = data.get("fxaa_on", False)
                self.bilinear_on = data.get("bilinear_on", False)
                self.lighter_filter = data.get("lighter_filter", False)
        except:
            self.challenge_progress = [False] * 25; self.username = ""; self.preferred_color = 0; self.room_text = ""; self.ai_difficulty = 5; self.challenge_completed_seen = False; self.is_music_muted = False
            self.vibrate_on = True; self.fxaa_on = False; self.bilinear_on = False; self.lighter_filter = False

        global VIBRATE_ENABLED
        VIBRATE_ENABLED = self.vibrate_on

        if not self.username:
            firsts = ["John", "Sarah", "Mike", "Emily", "Dave", "Lisa", "Chris", "Anna", "Tom", "Jessica"]
            lasts = ["Sweeps", "McPebble", "Hackman", "Slider", "Broomfield", "Skip", "Hammer", "Hogline", "Iceburn", "Von Curl", "Rocksley", "Stoned", "Freezeman"]
            self.username = f"{random.choice(firsts)} {random.choice(lasts)}"[:15]
            self.save_progress()

    def save_progress(self):
        try:
            data = {"challenge": self.challenge_progress[:25], "username": self.username, "color": self.preferred_color, "room": self.room_text, "bot_skill": self.ai_difficulty, "challenge_completed_seen": getattr(self, 'challenge_completed_seen', False), "is_music_muted": getattr(self, 'is_music_muted', False), "vibrate_enabled": getattr(self, 'vibrate_on', False), "fxaa_on": getattr(self, 'fxaa_on', False), "bilinear_on": getattr(self, 'bilinear_on', False), "lighter_filter": getattr(self, 'lighter_filter', False)}
            with open(self.save_file, "w") as f: json.dump(data, f)
        except Exception as e: 
            print(f"Game Progress Save Failed: {e}")

    def reset_turn_vars(self):
        pygame.event.set_grab(False); pygame.mouse.set_visible(True)
        self.turn_state = "AIMING"
        self.is_dragging = False; self.virtual_pull = pygame.math.Vector2(0, 0)
        self.selected_curl = 0.0; self.sweep_power = 0.0; self.is_sweeping_now = False
        self.last_mouse_pos = pygame.math.Vector2(0, 0)
        self.dragging_slider = False
        self.drag_start_pos = None
        self.drag_finger_id = None
        self.pull_history = []
        self.spawn_next_stone()

    def return_to_menu(self):
        self.audio.stop_all_match_sounds(); self.sweep_power = 0.0; self.particles = []
        pygame.event.set_grab(False); pygame.mouse.set_visible(True)
        if self.game_mode in ["HOST", "JOIN"]: self.net.close(); self.net = IRCNetworkManager()
        self.app_state = "MENU"; self.turn_state = "MENU"

    def reset_match(self):
        self.score = {0: [0]*8, 1: [0]*8}
        self.current_end = 1; self.total_stones_played = 0
        self.stones_per_team = 8
        self.stones = []; self.stones_thrown = {0: 0, 1: 0}
        
    def start_match(self):
        self.reset_match()
        if self.game_mode == "CHALLENGE":
            self.app_state = "PLAY"; self.challenge_attempts = 0; self.load_challenge(self.challenge_level)
            self.challenge_announced = False
        else:
            self.app_state = "COIN_TOSS"; self.coin_timer = 30; self.coin_flip_result = random.choice([0, 1])
            self.audio.play_cheer()

    def load_challenge(self, level):
        self.stones = []; self.stones_thrown = {0: 0, 1: 0}
        self.stones_per_team = 1; self.current_team = 0 
        self.challenge_success = False; cx, cy = self.house_pos.x, self.house_pos.y
        self.challenge_target = None; self.challenge_takeout_target = None

        if level <= 5: 
            self.c_type = "DRAW"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] THE DRAW", "Land inside the highlighted target."
            self.challenge_target = (cx + (level%2)*30, cy + (5-level)*40, max(20, 80 - level*10))
        elif level <= 10: 
            self.c_type = "GUARD"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] THE GUARD", "Place a rock in the target zone (Guard)."
            self.challenge_target = (cx, cy + 300 - (level-6)*20, 40)
        elif level <= 15: 
            self.c_type = "TAKEOUT"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] TAKEOUT", "Remove the yellow rock. Stay in play."
            s = Stone(cx + (level-12)*15, cy + (level-13)*20, 1); self.stones.append(s); self.challenge_takeout_target = s
            if level > 13: self.stones.append(Stone(cx - 30, cy + 180, 0)) 
        elif level == 16: 
            self.c_type = "DRAW" 
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] HIT AND ROLL", "Hit the rock and roll into the target."
            self.stones.append(Stone(cx + 40, cy + 50, 1)); self.challenge_target = (cx - 40, cy, 45)
        elif level <= 21: 
            self.c_type = "DOUBLE"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] DOUBLE TAKEOUT", "Clear ALL yellow rocks from the house."
            self.stones.extend([Stone(cx - 25, cy + 15, 1), Stone(cx + 25, cy - 15, 1)])
            if level > 19: self.stones.append(Stone(cx, cy + 60, 1)) 
        else: 
            self.c_type = "TAKEOUT"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] ANGLE RAISE", "Raise the red guard into the yellow rock."
            self.stones.append(Stone(cx, cy + 150, 0)) 
            s = Stone(cx - 10, cy + 10, 1); self.stones.append(s); self.challenge_takeout_target = s
            if level == 25: self.stones.append(Stone(cx + 60, cy + 120, 1)) 

        self.reset_turn_vars()

    def reset_end(self):
        self.stones = []; self.stones_thrown = {0: 0, 1: 0}
        self.current_team = 1 if getattr(self, 'hammer_team', 0) == 0 else 0
        self.reset_turn_vars()

    def spawn_next_stone(self): self.active_stone = Stone(self.hack_pos.x, self.hack_pos.y, self.current_team); self.stones.append(self.active_stone)

    def handle_collisions(self):
        for i in range(len(self.stones)):
            for j in range(i + 1, len(self.stones)):
                s1, s2 = self.stones[i], self.stones[j]; dist_vec = s2.pos - s1.pos; dist = dist_vec.length(); min_dist = s1.radius + s2.radius
                if 0 < dist < min_dist:
                    overlap = min_dist - dist; normal = dist_vec.normalize()
                    s1.pos -= normal * (overlap / 2); s2.pos += normal * (overlap / 2)
                    v_normal = (s1.vel - s2.vel).dot(normal)
                    if v_normal > 0:
                        impulse = (1.94) * v_normal / (s1.mass + s2.mass)
                        s1.vel -= normal * (impulse * s2.mass); s2.vel += normal * (impulse * s1.mass)
                        s1.is_moving, s2.is_moving = True, True
                        if impulse * 12 > 0.8: 
                            s1.last_collision_time = pygame.time.get_ticks(); s2.last_collision_time = pygame.time.get_ticks()
                            self.audio.play_clack(impulse * 12); self.shake_amount = min(25.0, impulse * 4.0)
                            if IS_ANDROID:
                                try:
                                    vibrate_android(50)
                                except: pass
                            mid_x, mid_y = (s1.pos.x + s2.pos.x) / 2, (s1.pos.y + s2.pos.y) / 2
                            for _ in range(int(impulse * 5)): self.particles.append({'pos': pygame.math.Vector2(mid_x, mid_y), 'vel': normal.rotate(random.uniform(-45, 45)) * random.uniform(2, 10), 'life': 1.0, 'decay': random.uniform(0.02, 0.05), 'type': 'spark'})

    def execute_ai(self):
        bot_level = "easy" if self.ai_difficulty < 4 else "medium" if self.ai_difficulty < 8 else "hard"
        params = self.BOT_LOGIC_CACHE[bot_level]
        
        if not hasattr(self, 'ai_wait_start'):
            self.ai_wait_start = pygame.time.get_ticks()
            return
            
        if pygame.time.get_ticks() - self.ai_wait_start < 1000:
            return
            
        delattr(self, 'ai_wait_start')

        err = (11 - self.ai_difficulty) * params["error_multiplier"]
        target = self.house_pos + pygame.math.Vector2(random.uniform(-7, 7)*err, random.uniform(-6, 6)*err)
        
        p_stones = sorted([s for s in self.stones if s.team == 0 and s != self.active_stone], key=lambda s: (s.pos - self.house_pos).length())
        if p_stones and (p_stones[0].pos - self.house_pos).length() < 170 and random.random() < params["takeout_chance"]: 
            target = p_stones[0].pos + pygame.math.Vector2(random.uniform(-2, 2)*err, 12) 
            
        req_spd = max(2.5, min(35.0, math.sqrt(2 * FRICTION_BASE * (target - self.hack_pos).length()) + random.uniform(-0.05, 0.05)*err))
        
        self.curler_anim.update("LUNGING"); self.audio.play_throw()
        self.active_stone.vel = (target - self.hack_pos).normalize() * req_spd; self.active_stone.curl = random.choice([-0.55, 0.55]); self.active_stone.is_moving = True
        self.stones_thrown[self.current_team] += 1; self.total_stones_played += 1; self.turn_state = "SLIDING"

    def fire_stone(self):
        if getattr(self, 'pull_history', []):
            avg_x = sum(p.x for p in self.pull_history) / len(self.pull_history)
            avg_y = sum(p.y for p in self.pull_history) / len(self.pull_history)
            self.virtual_pull = pygame.math.Vector2(avg_x, avg_y)

        pull = pygame.math.Vector2(-self.virtual_pull.x / 4.0, -self.virtual_pull.y)
        if abs(pull.x) < 2.0: 
            pull.x = 0
            
        if pull.length() > 20:
            self.active_stone.vel = pull.normalize() * min(16.0, pull.length() / 14.0) 
            self.active_stone.curl = self.selected_curl; self.active_stone.is_moving = True
            self.stones_thrown[self.current_team] += 1; self.total_stones_played += 1; self.turn_state = "SLIDING"
            self.curler_anim.update("LUNGING"); self.audio.play_throw()
            if self.game_mode in ["HOST", "JOIN"]: self.net.send_action({'cmd': 'shoot', 'vx': self.active_stone.vel.x, 'vy': self.active_stone.vel.y, 'c': self.selected_curl, 'sid': getattr(self.active_stone, 'id', -1)})
        else: self.curler_anim.update("IDLE")
        self.is_dragging = False; self.virtual_pull = pygame.math.Vector2(0, 0)
        self.drag_start_pos = None
        self.drag_finger_id = None
        self.pull_history = []

    def advance_end_logic(self):
        if self.game_mode == "CHALLENGE":
            if getattr(self, 'challenge_success', False) or self.challenge_attempts >= 3: 
                if getattr(self, 'challenge_success', False): self.challenge_progress[self.challenge_level-1] = True; self.save_progress()
                
                if all(self.challenge_progress[:25]):
                    if getattr(self, 'challenge_success', False) and not getattr(self, 'challenge_completed_seen', False):
                        if self.app_state != "MATCH_OVER":
                            self.app_state = "MATCH_OVER"
                            self.audio.play_cheer()
                            if not getattr(self, 'challenge_announced', False) and getattr(self.audio, 'snd_chal_comp', None):
                                self.audio.ch_voice.play(self.audio.snd_chal_comp)
                                self.challenge_announced = True
                            self.challenge_completed_seen = True
                            self.save_progress()
                        return
                    else:
                        self.return_to_menu()
                        return
                
                start_lvl = self.challenge_level
                while True:
                    self.challenge_level = (self.challenge_level % 25) + 1
                    if not self.challenge_progress[self.challenge_level-1] or self.challenge_level == start_lvl:
                        break
                self.challenge_attempts = 0
            self.load_challenge(self.challenge_level)
            return

        self.current_end += 1
        if self.current_end > 8: 
            self.app_state = "MATCH_OVER"
            self.audio.play_cheer()
            
            r_tot, y_tot = sum(self.score[0]), sum(self.score[1])
            if getattr(self, 'game_mode', None) in ["HOST", "JOIN"]:
                my_score = r_tot if getattr(self, 'preferred_color', 0) == 0 else y_tot
                self.post_score(getattr(self, 'username', 'Player'), my_score)
                
            if not getattr(self, 'match_winner_announced', False):
                self.match_winner_announced = True
                if r_tot > y_tot and getattr(self.audio, 'snd_red_wins', None): self.audio.ch_voice.play(self.audio.snd_red_wins)
                elif y_tot > r_tot and getattr(self.audio, 'snd_ylw_wins', None): self.audio.ch_voice.play(self.audio.snd_ylw_wins)
                elif getattr(self.audio, 'snd_end_match', None): self.audio.ch_voice.play(self.audio.snd_end_match)
        else: self.reset_end()

    def handle_menu_events(self, event):
        mouse_pos = getattr(event, 'pos', self.get_pointer_pos())
        mx, my = mouse_pos[0] if isinstance(mouse_pos, tuple) else mouse_pos.x, mouse_pos[1] if isinstance(mouse_pos, tuple) else mouse_pos.y
        menu_my = my - getattr(self, 'menu_dy', 0)
        curr_hov = next((b["id"] for b in self.menu_buttons if 300<mx<900 and b["y"]<menu_my<b["y"]+110*b["scale"]), None)
        if curr_hov != self.last_hovered:
            if curr_hov: self.audio.play_hover()
            self.last_hovered = curr_hov

        if event.type == MOUSEBUTTONUP and getattr(event, 'button', 1) == 1:
            if self.dragging_slider:
                self.dragging_slider = False
                self.save_progress()

        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            now = pygame.time.get_ticks()
            if hasattr(self, 'last_click_time') and now - self.last_click_time < 300: return
            self.last_click_time = now

            if self.typing_target:
                if not (300 < mx < 900 and 950 < menu_my < 1070):
                    self.set_typing_target(None)

            if 300 < mx < 900:
                for b in self.menu_buttons:
                    if b["y"] < menu_my < b["y"] + 110 * b["scale"]:
                        self.audio.play_click()
                        new_target = None
                        if b["id"] == "local": self.game_mode = "LOCAL"; self.audio.stop_music(); self.start_match()
                        elif b["id"] == "bot": self.game_mode = "BOT"; self.audio.stop_music(); self.start_match()
                        elif b["id"] == "chal": self.app_state = "CHALLENGE_MENU"
                        elif b["id"] == "options": self.app_state = "OPTIONS_MENU"
                        elif b["id"] in ["host", "join"]:
                            self.app_state = "ROOM_PROMPT"; new_target = "room"; self.net_action = b["id"]
                        elif b["id"] == "exit": self.net.close(); pygame.quit(); sys.exit()
                        self.set_typing_target(new_target)
                        break
            
            if getattr(self, 'btn_update', None) and self.btn_update.collidepoint(mx, my):
                if not getattr(self, 'is_updating', False):
                    self.is_updating = True
                    self.update_status = "updating..."
                    threading.Thread(target=self.perform_update, daemon=True).start()
            
            if self.btn_mute.collidepoint(mx, my):
                self.is_music_muted = not getattr(self, 'is_music_muted', False)
                self.audio.play_click()
                self.save_progress()
            
            if 330 < mx < 870 and 1450 < menu_my < 1650: 
                self.ai_difficulty = int(1 + max(0.0, min(1.0, (mx-350)/500.0))*9)
                self.audio.play_hover()
                self.save_progress()
        elif event.type == MOUSEMOTION and self.get_pointer_pressed():
            if 330 < mx < 870 and 1450 < menu_my < 1650: 
                self.ai_difficulty = int(1 + max(0.0, min(1.0, (mx-350)/500.0))*9)
                self.dragging_slider = True
        elif event.type == KEYDOWN and self.typing_target == "name":
            if event.key == K_RETURN: self.set_typing_target(None); self.save_progress()
            elif event.key == K_BACKSPACE: self.username = self.username[:-1]; self.save_progress()

    def handle_room_prompt_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if not self.prompt_rect.collidepoint(mx, my):
                self.app_state = "MENU"; self.set_typing_target(None)
            elif IS_ANDROID:
                self.audio.play_click()
                self.save_progress()
                self.app_state = "MENU"
                self.set_typing_target(None)
                self.game_mode = "HOST" if self.net_action == "host" else "JOIN"
                self.net.connect(self.username, self.net_action == "host", self.room_text, getattr(self, 'preferred_color', 0))

        if event.type == KEYDOWN and self.typing_target == "room":
            if event.key == K_RETURN and len(self.room_text) > 0:
                self.audio.play_click()
                self.save_progress()
                self.app_state = "MENU"
                self.set_typing_target(None)
                self.game_mode = "HOST" if self.net_action == "host" else "JOIN"
                self.net.connect(self.username, self.net_action == "host", self.room_text, getattr(self, 'preferred_color', 0))
            elif event.key == K_ESCAPE:
                self.app_state = "MENU"; self.set_typing_target(None)
            elif event.key == K_BACKSPACE: self.room_text = self.room_text[:-1]

    def handle_challenge_menu_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_return_menu.collidepoint(mx, my): self.audio.play_click(); self.app_state = "MENU"; return
            for i in range(25):
                row, col = i // 5, i % 5; rect = pygame.Rect(BASE_WIDTH//2 - 250 + col*100, 300 + row*100, 90, 90)
                if rect.collidepoint(mx, my):
                    self.audio.play_click(); self.game_mode = "CHALLENGE"; self.challenge_level = i+1
                    self.audio.stop_music(); self.start_match(); return

    def handle_pause_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_resume.collidepoint(mx, my): self.audio.play_click(); self.app_state = "PLAY"
            elif self.btn_quit_main.collidepoint(mx, my): self.audio.play_click(); self.return_to_menu()
                
    def handle_match_over_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if getattr(self, 'btn_leaderboard', None) and self.btn_leaderboard.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "LEADERBOARD"
                self.fetch_leaderboard()
            elif self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.return_to_menu()
                
    def handle_leaderboard_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "MATCH_OVER"

    def handle_play_events(self, event):
        mouse_pos = getattr(event, 'pos', self.get_pointer_pos())
        if isinstance(mouse_pos, tuple): mouse_pos = pygame.math.Vector2(mouse_pos)
        f_id = getattr(event, 'finger_id', 'mouse')
        
        if event.type == getattr(pygame, 'FINGERDOWN', 1792):
            self.last_finger_id = event.finger_id
            
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', 1) == 1 and self.is_dragging:
            # On Android, if we started drag with a finger, the MOUSEBUTTONUP might have 'mouse' as f_id,
            # so we should also accept it if IS_ANDROID
            if getattr(self, 'drag_finger_id', None) == f_id or (IS_ANDROID and f_id == 'mouse'):
                self.fire_stone()
            return

        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            if self.game_mode in ["HOST", "JOIN"] and self.btn_chat.collidepoint(mouse_pos.x, mouse_pos.y):
                self.audio.play_click()
                self.typing_chat = not getattr(self, 'typing_chat', False)
                if self.typing_chat:
                    try: pygame.key.start_text_input()
                    except: pass
                else:
                    try: pygame.key.stop_text_input()
                    except: pass
                return
            if self.btn_pause.collidepoint(mouse_pos.x, mouse_pos.y):
                self.audio.play_click()
                if self.game_mode in ["HOST", "JOIN"]: self.return_to_menu()
                else: self.app_state = "PAUSED"; self.pause_anim = 0.0; self.audio.update_slide(0.0); self.audio.update_sweep(0.0)
                return
        
        if self.turn_state == "END":
            if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1 and self.btn_next_end.collidepoint(mouse_pos.x, mouse_pos.y): self.advance_end_logic()
            elif event.type == KEYDOWN and event.key == K_SPACE: self.advance_end_logic()
            return

        has_control = (self.game_mode in ["LOCAL", "CHALLENGE"]) or (self.current_team == getattr(self, 'preferred_color', 0))

        if not has_control: return

        if self.turn_state == "AIMING":
            if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
                if self.btn_curl_l.collidepoint(mouse_pos.x, mouse_pos.y): self.selected_curl = max(-1.0, self.selected_curl - 0.2); self.audio.play_hover()
                elif self.btn_curl_r.collidepoint(mouse_pos.x, mouse_pos.y): self.selected_curl = min(1.0, self.selected_curl + 0.2); self.audio.play_hover()
                elif (mouse_pos - self.active_stone.pos).length() < 90 and not self.is_dragging: 
                    self.is_dragging = True
                    self.drag_start_pos = mouse_pos
                    self.drag_finger_id = getattr(self, 'last_finger_id', f_id) if IS_ANDROID else f_id
                    self.pull_history = []
                    self.virtual_pull = pygame.math.Vector2(0, 0)
            elif event.type == MOUSEMOTION and self.is_dragging and getattr(self, 'drag_start_pos', None):
                if f_id == getattr(self, 'drag_finger_id', None) or (IS_ANDROID and f_id == 'mouse'):
                    self.virtual_pull = self.drag_start_pos - mouse_pos
                    if not IS_ANDROID: self.virtual_pull.x *= 0.25; self.virtual_pull.y *= 0.5
                    self.pull_history.append(pygame.math.Vector2(self.virtual_pull))
                    if len(self.pull_history) > 5: self.pull_history.pop(0)
            elif event.type == MOUSEWHEEL: self.selected_curl = max(-1.0, min(1.0, self.selected_curl + event.y * 0.2))
            elif event.type == getattr(pygame, 'FINGERMOTION', 1792):
                if self.is_dragging and getattr(event, 'finger_id', None) != getattr(self, 'drag_finger_id', None):
                    self.selected_curl = max(-1.0, min(1.0, self.selected_curl + event.dx * 3.0))

    def update_physics(self):
        for p in self.particles[:]:
            p['pos'] += p['vel']; p['life'] -= p['decay']
            if p['life'] <= 0: self.particles.remove(p)

        if self.is_dragging:
            pull_viz = pygame.math.Vector2(self.virtual_pull.x, self.virtual_pull.y)
            if pull_viz.length() > 300: pull_viz.scale_to_length(300)
            self.curler_anim.update("BACKSWING", pull_viz)

        if self.turn_state == "LUNGING" or self.curler_anim.state == "LUNGING": self.curler_anim.update("LUNGING")

        if self.turn_state == "SLIDING":
            mouse_pos = self.get_pointer_pos()
            is_mouse_pressed = self.get_pointer_pressed()
            my_team = self.preferred_color if self.game_mode in ["BOT", "HOST", "JOIN"] else self.current_team
            
            can_sweep_legally = False
            for s in self.stones:
                if s.is_moving and (s.team == my_team or s.pos.y < self.house_pos.y):
                    can_sweep_legally = True
                    break
            
            is_sweeping = is_mouse_pressed and can_sweep_legally
            delta = (mouse_pos - self.last_mouse_pos).length()
            self.is_sweeping_now = is_sweeping and delta > 4
            
            if self.is_sweeping_now:
                self.sweep_power = min(12.0, self.sweep_power + delta * 0.18)
                self.audio.play_curler_call(self.sweep_power)
                for _ in range(2 if IS_ANDROID else 3): self.particles.append({'pos': mouse_pos + pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30)), 'vel': pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-3, 0)), 'life': 1.0, 'decay': random.uniform(0.02, 0.05), 'type': 'sweep'})

            for s in self.stones:
                can_player_sweep = is_sweeping and (mouse_pos - s.pos).length() < 350
                is_remote_sweeping = getattr(self, 'remote_sweep_timer', 0) > 0
                actual_sweep = self.sweep_power if (can_player_sweep and (s.team == my_team or s.pos.y < self.house_pos.y)) or (is_remote_sweeping and (s.team != my_team or s.pos.y < self.house_pos.y)) else 0.0
                s.update(actual_sweep, FRICTION_BASE)
                if s.is_moving and s.vel.length() > 0.5: self.particles.append({'pos': s.pos + pygame.math.Vector2(random.uniform(-15, 15), random.uniform(-15, 15)), 'vel': s.vel * -0.1, 'life': 1.0, 'decay': random.uniform(0.01, 0.03), 'type': 'trail'})
            
            if self.game_mode in ["HOST", "JOIN"] and self.frames_elapsed % 15 == 0:
                if self.sweep_power > 0.1 or getattr(self, 'last_sent_sweep', 0.0) > 0.1:
                    self.net.send_action({'cmd': 'sweep', 'p': round(self.sweep_power, 2)})
                    self.last_sent_sweep = self.sweep_power
            if self.game_mode == "HOST" and self.frames_elapsed % 30 == 0:
                self.net.send_action({'cmd': 'sync_state', 'stones': [s.get_state((BASE_HEIGHT//2)+100) for s in self.stones]})
            
            if getattr(self, 'remote_sweep_timer', 0) > 0:
                self.remote_sweep_timer -= 1
            else:
                self.sweep_power *= 0.86
                
            self.audio.update_sweep(self.sweep_power)
            
            moving = False; max_speed = 0.0
            self.handle_collisions()
            
            valid_stones = []
            for s in self.stones:
                if s.is_moving:
                    if s.pos.x - s.radius < 0 or s.pos.x + s.radius > BASE_WIDTH or s.pos.y < -s.radius:
                        s.is_moving = False; self.audio.play_clack(5.0)
                        for _ in range(8): self.particles.append({'pos': pygame.math.Vector2(s.pos), 'vel': pygame.math.Vector2(random.uniform(-4, 4), random.uniform(-4, 4)), 'life': 1.0, 'decay': 0.05, 'type': 'spark'})
                    else:
                        moving = True; max_speed = max(max_speed, s.vel.length()); valid_stones.append(s)
                else: valid_stones.append(s)
            
            self.stones = valid_stones
            self.audio.update_slide(max_speed)
            
            if not moving:
                self.audio.update_slide(0.0); self.audio.update_sweep(0.0)
                
                valid_stones_final = []
                hog_line_y = self.house_pos.y + 400
                back_line_y = self.house_pos.y - 210
                for s in self.stones:
                    if s.pos.y - s.radius < hog_line_y and s.pos.y + s.radius > back_line_y:
                        valid_stones_final.append(s)
                self.stones = valid_stones_final
                
                # Absolute End of Slide Sync Broadcast for Netcode
                if self.game_mode == "HOST" and hasattr(self, 'was_moving_last_frame') and self.was_moving_last_frame:
                    self.net.send_action({'cmd': 'sync_state', 'stones': [s.get_state((BASE_HEIGHT//2)+100) for s in self.stones]})
                
                if self.game_mode == "CHALLENGE":
                    if self.stones_thrown[0] == 1: 
                        self.challenge_attempts += 1; cx, cy = self.house_pos.x, self.house_pos.y
                        
                        if self.c_type in ["DRAW", "GUARD"]: 
                            self.challenge_success = False
                            for s in self.stones:
                                if s.team == 0:
                                    dist = (pygame.math.Vector2(s.pos) - pygame.math.Vector2(self.challenge_target[:2])).length()
                                    if dist <= (self.challenge_target[2] + (s.radius * 0.95)):
                                        self.challenge_success = True
                                        break
                                        
                        elif self.c_type == "TAKEOUT": self.challenge_success = (self.challenge_takeout_target not in self.stones) and any(s.team == 0 and (pygame.math.Vector2(s.pos) - pygame.math.Vector2(cx, cy)).length() <= 210 for s in self.stones)
                        elif self.c_type == "DOUBLE": self.challenge_success = len([s for s in self.stones if s.team == 1]) == 0
                        self.turn_state = "END"
                else:
                    if self.stones_thrown[0] == self.stones_per_team and self.stones_thrown[1] == self.stones_per_team:
                        in_house = [((s.pos - self.house_pos).length(), s.team) for s in self.stones if (s.pos - self.house_pos).length() <= 210]
                        if in_house:
                            in_house.sort(key=lambda x: x[0]); winner = in_house[0][1]
                            pts = sum(1 for d, t in in_house if t == winner and all(d < od for od, ot in in_house if ot != winner))
                            if pts > 0: self.score[winner][self.current_end - 1] = pts; self.hammer_team = 0 if winner == 1 else 1 
                        self.turn_state = "END"
                    else:
                        self.current_team = 1 if self.current_team == 0 else 0; self.turn_state = "AIMING"; self.selected_curl = 0.0; self.spawn_next_stone()
            
            self.was_moving_last_frame = moving
        elif self.turn_state == "AIMING" and self.game_mode == "BOT" and self.current_team != self.preferred_color: self.execute_ai()
        self.last_mouse_pos = self.get_pointer_pos()

    def update_network(self):
        if self.game_mode not in ["HOST", "JOIN"]: return
        if self.app_state == "MENU" and self.net.matched:
            self.app_state = "COIN_TOSS"; self.coin_timer = 30; self.coin_flip_result = random.choice([0, 1]) if self.game_mode == "HOST" else -1
            self.audio.stop_music(); self.audio.play_cheer()
            
        if not hasattr(self, 'deferred_actions'): self.deferred_actions = []
        actions_to_process = self.deferred_actions[:]
        self.deferred_actions = []
        
        while True:
            data = self.net.receive_action()
            if not data: break
            actions_to_process.append(data)
            
        for data in actions_to_process:
            if data.get('cmd') in ['shoot', 'sweep'] and getattr(self, 'app_state', 'MENU') != "PLAY":
                self.deferred_actions.append(data)
                continue
                
            if data.get('cmd') == 'chat':
                self.chat_messages.append({"text": f"{self.net.opponent.split('!')[0]}: {data['msg']}", "time": pygame.time.get_ticks()})
            elif data.get('cmd') == 'coin' and self.game_mode == "JOIN": self.coin_flip_result = data['result']
            elif data.get('cmd') == 'shoot':
                if not hasattr(self, 'active_stone'): self.spawn_next_stone()
                if getattr(self, 'turn_state', 'NONE') == "SLIDING":
                    self.current_team = 1 if getattr(self, 'current_team', 0) == 0 else 0
                    self.spawn_next_stone()
                if 'sid' in data: self.active_stone.id = data['sid']
                self.active_stone.vel = pygame.math.Vector2(data['vx'], data['vy']); self.active_stone.curl = data['c']; self.active_stone.is_moving = True
                self.stones_thrown[self.current_team] += 1; self.total_stones_played += 1; self.turn_state = "SLIDING"; self.audio.play_throw()
                self.curler_anim.update("LUNGING")
            elif data.get('cmd') == 'sweep':
                self.sweep_power = data['p']
                self.remote_sweep_timer = 20
            elif data.get('cmd') in ('sync_state', 'sync') and self.game_mode == "JOIN":
                if data.get('cmd') == 'sync':
                    self.turn_state = data['st']; self.current_team = data['t']; self.score = {int(k): v for k, v in data['sc'].items()}
                stones_data = data.get('stones') if 'stones' in data else data.get('s', [])
                offset_y = ((BASE_HEIGHT//2)+100) if data.get('cmd') == 'sync_state' else 0
                new_stones = []
                for i, s_data in enumerate(stones_data):
                    sid = s_data[8] if len(s_data) > 8 else None
                    if sid is not None and sid != -1:
                        existing = next((s for s in self.stones if getattr(s, 'id', -1) == sid), None)
                    else:
                        existing = self.stones[i] if i < len(self.stones) else None
                    
                    if existing:
                        existing.set_state(s_data, offset_y)
                        new_stones.append(existing)
                    else:
                        ns = Stone(0, 0, 0)
                        ns.set_state(s_data, offset_y)
                        new_stones.append(ns)
                
                if hasattr(self, 'active_stone') and self.active_stone in self.stones and self.active_stone not in new_stones:
                    if getattr(self, 'turn_state', 'NONE') == "AIMING":
                        new_stones.append(self.active_stone)

                self.stones = new_stones
            elif data.get('cmd') == 'set_color':
                self.preferred_color = 1 - data['color']
            elif data.get('cmd') == 'opponent_left':
                self.app_state = "MATCH_OVER"
                self.winner_text = "Opponent Disconnected"
                self.audio.play_cheer()
                
        if self.game_mode == "HOST" and self.app_state == "COIN_TOSS" and self.coin_timer == 25: self.net.send_action({'cmd': 'coin', 'result': self.coin_flip_result})

    def draw_menu(self):
        self.frames_since_start = getattr(self, 'frames_since_start', 0) + 1
        
        if not getattr(self, 'played_intro', False) and self.frames_since_start >= 30:
            if getattr(self.audio, 'snd_speech', None):
                self.audio.ch_sfx.play(self.audio.snd_speech)
                self.played_intro = True
            
        self.canvas.fill((10, 12, 16))
        self.last_starfield_speed = 2.0
        self.starfield.draw(self.canvas, 2.0); cx, t_ms = BASE_WIDTH//2, pygame.time.get_ticks() * 0.001
            
        if not getattr(self, 'is_music_muted', False) and self.app_state in ["MENU", "ROOM_PROMPT", "CHALLENGE_MENU", "OPTIONS_MENU"] and self.frames_since_start >= 210:
            self.audio.play_music()
        elif getattr(self, 'is_music_muted', False) or self.app_state not in ["MENU", "ROOM_PROMPT", "CHALLENGE_MENU", "OPTIONS_MENU"]:
            self.audio.stop_music()
            
        self.menu_dy = (BASE_HEIGHT - 1920) // 2
        self.menu_stone.draw(self.canvas, cx, 300 + self.menu_dy, self.get_pointer_pos())
        
        bx, by = cx - self.title_base.get_width()//2, 80 + self.menu_dy + int(math.sin(t_ms * 4.0) * 15) 
        
        # Draw pre-rendered soft outline (requires just 1 blit instead of 36)
        pad = 9 # outline_size (7) + 2
        self.canvas.blit(self.title_outline, (bx - pad, by - pad))
        
        # Draw live-calculated animated title (zero allocation, 2 C-level blits)
        offset = int((pygame.time.get_ticks() * 0.15) % 150)
        self.title_rainbow_frame.fill((0, 0, 0, 0))
        self.title_rainbow_frame.blit(self.title_base, (0, 0))
        self.title_rainbow_frame.blit(self.rainbow_grad, (-offset, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.canvas.blit(self.title_rainbow_frame, (bx, by))
        
        status_string = f"STATUS: ERROR - {self.net.connection_error}" if getattr(self.net, 'connection_error', "") else "STATUS: Connecting to Network..." if self.net.connecting else "STATUS: Match Found!" if self.net.matched else f"STATUS: Hosting {self.net.room_display}... Waiting." if getattr(self.net, 'is_host', False) and self.net.running else "STATUS: Offline Ready"
        color = HOUSE_RED if getattr(self.net, 'connection_error', "") else (TEAM_YELLOW if self.net.connecting or self.net.matched or self.net.running else (150, 160, 180))
        status_lbl = self.small_font.render(status_string, True, color); self.canvas.blit(status_lbl, (cx - status_lbl.get_width()//2, 210 + self.menu_dy))

        for btn in self.menu_buttons:
            text = btn["text"]
            
            is_hovered = (self.last_hovered == btn["id"])
            target_scale = 1.07 if is_hovered else 1.0
            if abs(btn["scale"] - target_scale) < 0.005: btn["scale"] = target_scale
            else: btn["scale"] += (target_scale - btn["scale"]) * 0.25 
            b_w, b_h = int(600 * btn["scale"]), int(100 * btn["scale"])
            rect = pygame.Rect(cx - b_w//2, btn["y"] + self.menu_dy + (100 - b_h)//2, b_w, b_h)
            
            draw_glass_rect(self.canvas, rect, btn["color"], rect.h // 2, is_hovered)
            
            if btn["id"] == "color":
                img = self.font.render(text, True, WHITE)
                txt_rect = img.get_rect(center=(rect.centerx - 30, rect.centery))
                self.canvas.blit(img, txt_rect)
                
                rock_x = txt_rect.right + 40
                rock_y = rect.centery
                stone_c = TEAM_YELLOW if self.preferred_color else HOUSE_RED
                rock_r = 26
                pygame.draw.circle(self.canvas, (160, 165, 170), (rock_x, rock_y), rock_r)
                pygame.draw.circle(self.canvas, (100, 105, 110), (rock_x, rock_y), rock_r, 2)
                pygame.draw.circle(self.canvas, stone_c, (rock_x, rock_y), 16)
                pygame.draw.circle(self.canvas, (max(0, stone_c[0]-50), max(0, stone_c[1]-50), max(0, stone_c[2]-50)), (rock_x, rock_y), 16, 2)
                pygame.draw.line(self.canvas, BLACK, (rock_x - 12, rock_y), (rock_x + 12, rock_y), 10)
                pygame.draw.circle(self.canvas, BLACK, (rock_x - 12, rock_y), 5)
                pygame.draw.circle(self.canvas, BLACK, (rock_x + 12, rock_y), 5)
                pygame.draw.line(self.canvas, stone_c, (rock_x - 12, rock_y), (rock_x + 12, rock_y), 6)
                pygame.draw.circle(self.canvas, stone_c, (rock_x - 12, rock_y), 3)
                pygame.draw.circle(self.canvas, stone_c, (rock_x + 12, rock_y), 3)
            else:
                img = self.font.render(text, True, WHITE)
                if img.get_width() > rect.w - 40:
                    scale = (rect.w - 40) / img.get_width()
                    img = pygame.transform.smoothscale(img, (int(rect.w - 40), int(img.get_height() * scale)))
                self.canvas.blit(img, img.get_rect(center=rect.center))

        pygame.draw.rect(self.canvas, (80, 95, 115), (cx - 250, 1550 + self.menu_dy, 500, 16), border_radius=8)
        handle_x = cx - 250 + int((self.ai_difficulty - 1) / 9.0 * 500)
        pygame.draw.circle(self.canvas, TEAM_YELLOW, (int(handle_x), 1558 + self.menu_dy), 26); pygame.draw.circle(self.canvas, WHITE, (int(handle_x), 1558 + self.menu_dy), 26, 4)
        diff_lbl = self.font.render(f"BOT DIFFICULTY: {self.ai_difficulty}", True, WHITE); self.canvas.blit(diff_lbl, (cx - diff_lbl.get_width()//2, 1490 + self.menu_dy))
        
        # Updater UI
        update_txt = getattr(self, "update_status", "check for update")
        upd_lbl = self.font.render(update_txt, True, (150, 200, 255))
        upd_lbl = pygame.transform.smoothscale(upd_lbl, (int(upd_lbl.get_width() * 1.3), int(upd_lbl.get_height() * 1.3)))
        self.btn_update = upd_lbl.get_rect(center=(cx, 1790 + self.menu_dy))
        self.canvas.blit(upd_lbl, self.btn_update)
        
        # Draw Mute Button
        draw_glass_rect(self.canvas, self.btn_mute, (50, 60, 80), 16, self.btn_mute.collidepoint(self.get_pointer_pos()))
        draw_speaker_icon(self.canvas, self.btn_mute.x + self.btn_mute.w//2 - 20, self.btn_mute.y + self.btn_mute.h//2 - 13, getattr(self, 'is_music_muted', False))
        self.draw_global_ui()

    def perform_update(self):
        try:
            import urllib.request
            import sys, os, re
            
            url_main = "https://raw.githubusercontent.com/jjivany/wincurl/main/main.py"
            req = urllib.request.Request(url_main, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as response:
                    new_code = response.read().decode('utf-8')
                m = re.search(r'VERSION\s*=\s*"([^"]+)"', new_code)
                remote_version = m.group(1) if m else "0"
                
                def parse_ver(v):
                    return tuple(map(int, v.split('.')))
                
                if parse_ver(remote_version) <= parse_ver(VERSION):
                    self.update_status = "no update available"
                    self.is_updating = False
                    return
            except Exception as e:
                print("Update check error:", e)
                self.update_status = "update failed"
                self.is_updating = False
                return

            if not IS_ANDROID:
                try:
                    import subprocess
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "wincurl"])
                    self.update_status = "Update installed! Restarting..."
                    pygame.time.wait(1000)
                    os.execl(sys.executable, sys.executable, *sys.argv)
                except Exception as e:
                    print("PC Update error:", e)
                    self.update_status = "update failed"
            else:
                try:
                    import webbrowser
                    apk_url = "https://github.com/jjivany/wincurl/releases/latest/download/wincurl_latest.apk"
                    webbrowser.open(apk_url)
                    self.update_status = "Browser opened. Download and install APK!"
                except Exception as e:
                    print("Android Update error:", e)
                    self.update_status = "update failed"
            self.is_updating = False
        except Exception as e:
            print("Update thread error:", e)
            self.update_status = "update failed"
            self.is_updating = False

    def post_score(self, username, score):
        def _post():
            import urllib.request, json
            url = "https://api.restful-api.dev/objects/ff8081819d82fab6019f55cbbafe4b47"
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())
                    scores = data.get("data", {}).get("scores", [])
                    
                scores.append({"name": username, "score": score})
                scores.sort(key=lambda x: x.get("score", 0), reverse=True)
                scores = scores[:10]
                
                payload = json.dumps({"data": {"scores": scores}}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method="PUT")
                with urllib.request.urlopen(req) as response:
                    pass
            except Exception as e:
                print("Failed to post score:", e)
        threading.Thread(target=_post, daemon=True).start()

    def fetch_leaderboard(self):
        self.leaderboard_data = None
        def _fetch():
            import urllib.request, json
            url = "https://api.restful-api.dev/objects/ff8081819d82fab6019f55cbbafe4b47"
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())
                    self.leaderboard_data = data.get("data", {}).get("scores", [])
            except Exception as e:
                self.leaderboard_data = [
                    {"name": "Jason Ivany", "score": 100},
                ]
                print("Failed to fetch leaderboard:", e)
        threading.Thread(target=_fetch, daemon=True).start()

    def draw_room_prompt(self):
        self.draw_menu()
        self.canvas.blit(self.dark_overlay_200, (0, 0))
        cx, cy = BASE_WIDTH//2, BASE_HEIGHT//2
        
        lbl_v = self.font_62.render("ENTER MATCHMAKING ROOM NAME", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, cy - 150))
        
        draw_glass_rect(self.canvas, self.prompt_rect, HOUSE_BLUE, self.prompt_rect.h // 2)
        txt = f"{self.room_text}_"
        img = self.font.render(txt, True, WHITE); self.canvas.blit(img, img.get_rect(center=(cx, cy + 10)))
        
        if IS_ANDROID: sub = self.small_font.render("Tap here to connect | Tap outside to cancel", True, (150, 160, 180))
        else: sub = self.small_font.render("Press ENTER to connect | ESC to cancel", True, (150, 160, 180))
        self.canvas.blit(sub, (cx - sub.get_width()//2, cy + 120))
        self.draw_global_ui()


    def draw_options_menu(self):
        self.canvas.fill((10, 12, 16))
        self.last_starfield_speed = 0.5
        self.starfield.draw(self.canvas, 0.5)
        
        cx, t_ms = BASE_WIDTH//2, pygame.time.get_ticks() * 0.001
        self.menu_dy = (BASE_HEIGHT - 1920) // 2
        bx, by = cx - self.title_base.get_width()//2, 80 + self.menu_dy + int(math.sin(t_ms * 4.0) * 15) 
        pad = 9
        self.canvas.blit(self.title_outline, (bx - pad, by - pad))
        offset = int((pygame.time.get_ticks() * 0.15) % 150)
        self.title_rainbow_frame.fill((0, 0, 0, 0))
        self.title_rainbow_frame.blit(self.title_base, (0, 0))
        self.title_rainbow_frame.blit(self.rainbow_grad, (-offset, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.canvas.blit(self.title_rainbow_frame, (bx, by))
        
        lbl_v = self.font_72.render("OPTIONS", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, 320 + getattr(self, 'menu_dy', 0)))
        lbl_build = self.font.render(f"(Build {VERSION})", True, (150, 160, 180))
        self.canvas.blit(lbl_build, (cx - lbl_build.get_width()//2, 385 + getattr(self, 'menu_dy', 0)))

        for btn in self.options_buttons:
            if (IS_ANDROID and btn["id"] in ["fxaa", "light_filter"]) or (not IS_ANDROID and btn["id"] in ["vibrate", "bilinear"]):
                continue
                
            if btn["id"] == "name": text = f"Name: {self.username}" + ("_" if self.typing_target == "name" else "")
            elif btn["id"] == "color": 
                btn["color"] = TEAM_YELLOW if self.preferred_color else HOUSE_RED
                text = "My Team:"
            elif btn["id"] == "vibrate":
                text = "Vibration: " + ("ON 📳" if getattr(self, 'vibrate_on', False) else "OFF")
                btn["color"] = (40, 120, 60) if getattr(self, 'vibrate_on', False) else TEAM_YELLOW
            elif btn["id"] == "fxaa":
                text = "FXAA: " + ("ON 🪄" if getattr(self, 'fxaa_on', False) else "OFF 🖥️")
                btn["color"] = (40, 120, 60) if getattr(self, 'fxaa_on', False) else TEAM_YELLOW
            elif btn["id"] == "bilinear":
                text = "Bilinear Filtering: " + ("ON" if getattr(self, 'bilinear_on', False) else "OFF")
                btn["color"] = (40, 120, 60) if getattr(self, 'bilinear_on', False) else TEAM_YELLOW
            elif btn["id"] == "light_filter":
                text = "Bilinear Filtering: " + ("ON" if getattr(self, 'lighter_filter', False) else "OFF")
                btn["color"] = (40, 120, 60) if getattr(self, 'lighter_filter', False) else TEAM_YELLOW
            else: text = btn["text"]

            is_hovered = (self.last_hovered == "opt_" + btn["id"])
            target_scale = 1.07 if is_hovered else 1.0
            if abs(btn["scale"] - target_scale) < 0.005: btn["scale"] = target_scale
            else: btn["scale"] += (target_scale - btn["scale"]) * 0.3
            
            rect = pygame.Rect(cx - 300*btn["scale"], btn["y"] + getattr(self, 'menu_dy', 0) - 15*btn["scale"], 600*btn["scale"], 95*btn["scale"])
            draw_glass_rect(self.canvas, rect, btn["color"], 16, is_hovered)
            
            if btn["id"] == "color":
                img = self.font.render(text, True, WHITE)
                txt_rect = img.get_rect(center=(rect.centerx - 30, rect.centery))
                self.canvas.blit(img, txt_rect)
                
                rock_x = txt_rect.right + 40
                rock_y = rect.centery
                stone_c = TEAM_YELLOW if self.preferred_color else HOUSE_RED
                rock_r = 26
                pygame.draw.circle(self.canvas, (160, 165, 170), (rock_x, rock_y), rock_r)
                pygame.draw.circle(self.canvas, (100, 105, 110), (rock_x, rock_y), rock_r, 2)
                pygame.draw.circle(self.canvas, stone_c, (rock_x, rock_y), 16)
                pygame.draw.circle(self.canvas, (max(0, stone_c[0]-50), max(0, stone_c[1]-50), max(0, stone_c[2]-50)), (rock_x, rock_y), 16, 2)
                pygame.draw.line(self.canvas, BLACK, (rock_x - 12, rock_y), (rock_x + 12, rock_y), 10)
                pygame.draw.circle(self.canvas, BLACK, (rock_x - 12, rock_y), 5)
                pygame.draw.circle(self.canvas, BLACK, (rock_x + 12, rock_y), 5)
                pygame.draw.line(self.canvas, stone_c, (rock_x - 12, rock_y), (rock_x + 12, rock_y), 6)
                pygame.draw.circle(self.canvas, stone_c, (rock_x - 12, rock_y), 3)
                pygame.draw.circle(self.canvas, stone_c, (rock_x + 12, rock_y), 3)
            else:
                img = self.font.render(text, True, WHITE) if btn["id"] not in ["fxaa", "vibrate"] else self.chat_font.render(text, True, WHITE)
                if img.get_width() > rect.w - 40:
                    scale = (rect.w - 40) / img.get_width()
                    img = pygame.transform.smoothscale(img, (int(rect.w - 40), int(img.get_height() * scale)))
                self.canvas.blit(img, img.get_rect(center=rect.center))

        self.draw_global_ui()

    def handle_options_events(self, event):
        mouse_pos = getattr(event, 'pos', self.get_pointer_pos())
        mx, my = mouse_pos[0] if isinstance(mouse_pos, tuple) else mouse_pos.x, mouse_pos[1] if isinstance(mouse_pos, tuple) else mouse_pos.y
        menu_my = my - getattr(self, 'menu_dy', 0)
        
        curr_hov = None
        for b in self.options_buttons:
            if (IS_ANDROID and b["id"] in ["fxaa", "light_filter"]) or (not IS_ANDROID and b["id"] in ["vibrate", "bilinear"]): continue
            if 300 < mx < 900 and b["y"] < menu_my < b["y"] + 110 * b["scale"]:
                curr_hov = "opt_" + b["id"]
                break
                
        if curr_hov != self.last_hovered:
            if curr_hov: self.audio.play_hover()
            self.last_hovered = curr_hov

        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            now = pygame.time.get_ticks()
            if hasattr(self, 'last_click_time') and now - getattr(self, 'last_click_time', 0) < 300: return
            self.last_click_time = now

            if self.typing_target:
                if not (300 < mx < 900 and 450 < menu_my < 570):
                    self.set_typing_target(None)

            if 300 < mx < 900:
                for b in self.options_buttons:
                    if (IS_ANDROID and b["id"] in ["fxaa", "light_filter"]) or (not IS_ANDROID and b["id"] in ["vibrate", "bilinear"]): continue
                    if b["y"] < menu_my < b["y"] + 110 * b["scale"]:
                        self.audio.play_click()
                        new_target = None
                        if b["id"] == "name": new_target = "name"
                        elif b["id"] == "color": self.preferred_color = 1 if self.preferred_color == 0 else 0; self.save_progress()
                        elif b["id"] == "vibrate":
                            self.vibrate_on = not getattr(self, 'vibrate_on', False)
                            global VIBRATE_ENABLED
                            VIBRATE_ENABLED = self.vibrate_on
                            self.save_progress()
                        elif b["id"] == "fxaa": self.fxaa_on = not getattr(self, 'fxaa_on', False); self.save_progress()
                        elif b["id"] == "bilinear": self.bilinear_on = not getattr(self, 'bilinear_on', False); self.save_progress()
                        elif b["id"] == "light_filter": self.lighter_filter = not getattr(self, 'lighter_filter', False); self.save_progress()
                        elif b["id"] == "back": self.app_state = "MENU"
                        self.set_typing_target(new_target)
                        break
        elif event.type == KEYDOWN and self.typing_target == "name":
            if event.key == K_RETURN: self.set_typing_target(None); self.save_progress()
            elif event.key == K_BACKSPACE: self.username = self.username[:-1]; self.save_progress()
            

    def draw_challenge_menu(self):
        self.canvas.fill((10, 12, 16)); self.last_starfield_speed = 2.0; self.starfield.draw(self.canvas, 2.0); cx = BASE_WIDTH // 2
        lbl_v = self.font_72.render("SELECT CHALLENGE", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, 120))
        
        for i in range(25):
            row, col = i // 5, i % 5; rect = pygame.Rect(cx - 250 + col*100, 300 + row*100, 90, 90)
            is_hov = rect.collidepoint(self.get_pointer_pos())
            draw_glass_rect(self.canvas, rect, (40, 120, 60) if self.challenge_progress[i] else PURPLE_SUIT, 16, is_hov)
            txt = self.font.render(str(i+1), True, WHITE); self.canvas.blit(txt, txt.get_rect(center=rect.center))
            if self.challenge_progress[i]: pygame.draw.line(self.canvas, HOUSE_RED, rect.topleft, rect.bottomright, 8)
            
        draw_glass_rect(self.canvas, self.btn_return_menu, HOUSE_BLUE, self.btn_return_menu.h // 2, self.btn_return_menu.collidepoint(self.get_pointer_pos()))
        lbl_btn = self.font.render("BACK TO MENU", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))
        self.draw_global_ui()

    def draw_coin_toss_screen(self):
        self.draw_ice()
        self.canvas.blit(self.dark_overlay_150, (0, 0))
        cx, cy, t = BASE_WIDTH//2, BASE_HEIGHT//2, 30 - self.coin_timer; scale_x = abs(math.cos(t * 0.6))
        
        if self.coin_timer > 5:
            is_red = (t // 3) % 2 == 0; text = "FLIPPING FOR HAMMER..."
        else:
            is_red = self.coin_flip_result == 0; text = "RED GETS HAMMER" if is_red else "YELLOW GETS HAMMER"
            
        if scale_x > 0.05: 
            c_surf = self.coin_red_surf if is_red else self.coin_yellow_surf
            w, h = c_surf.get_size()
            scaled = pygame.transform.scale(c_surf, (max(1, int(w * scale_x)), h))
            self.canvas.blit(scaled, (cx - scaled.get_width()//2, cy - h//2))
            
        lbl = self.font.render(text, True, WHITE); self.canvas.blit(lbl, (cx - lbl.get_width()//2, cy + 150))

    def draw_pause_icon(self, surface, x, y):
        pygame.draw.rect(surface, BLACK, (x, y, 8, 24), border_radius=2)
        pygame.draw.rect(surface, BLACK, (x + 14, y, 8, 24), border_radius=2)

    def draw_ice(self):
        self.canvas.blit(self.static_ice_surface, (0, 0))
        
        if self.game_mode == "CHALLENGE" and self.challenge_target:
            cx, cy, cr = self.challenge_target
            pygame.draw.circle(self.canvas, (0, 255, 100, 150), (int(cx), int(cy)), int(cr + ((math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5)*10), 4)
        
        cx = self.hack_pos.x
        hack_y = self.hack_pos.y + 35
        
        # Black bar behind the foot pads
        pygame.draw.rect(self.canvas, (10, 10, 10), (cx - 50, hack_y + 6, 100, 10), border_radius=3)
        # Center support
        pygame.draw.rect(self.canvas, (50, 55, 60), (cx - 10, hack_y + 5, 20, 6))
        
        # Left foot pad (25% taller)
        left_pad = [(cx - 40, hack_y - 2), (cx - 15, hack_y - 2), (cx - 10, hack_y + 18), (cx - 45, hack_y + 21)]
        pygame.draw.polygon(self.canvas, (20, 20, 22), left_pad)
        pygame.draw.polygon(self.canvas, (60, 60, 65), left_pad, 2)
        
        # Right foot pad (25% taller)
        right_pad = [(cx + 40, hack_y - 2), (cx + 15, hack_y - 2), (cx + 10, hack_y + 18), (cx + 45, hack_y + 21)]
        pygame.draw.polygon(self.canvas, (20, 20, 22), right_pad)
        pygame.draw.polygon(self.canvas, (60, 60, 65), right_pad, 2)

    def draw_ui(self):
        if not hasattr(self, 'score_bg'):
            self.score_bg = pygame.Surface((BASE_WIDTH, 130), pygame.SRCALPHA)
            self.score_bg.fill((20, 24, 34, 216))
        self.canvas.blit(self.score_bg, (0, 0))
        pygame.draw.line(self.canvas, HOUSE_RED, (0, 128), (BASE_WIDTH, 128), 3)
        
        if self.game_mode == "CHALLENGE":
            t1, t2 = self.font.render(self.challenge_text_1, True, WHITE), self.small_font.render(self.challenge_text_2, True, TEAM_YELLOW)
            self.canvas.blit(t1, (BASE_WIDTH//2 - t1.get_width()//2, 30)); self.canvas.blit(t2, (BASE_WIDTH//2 - t2.get_width()//2, 80))
        else:
            self.canvas.blit(self.score_font.render("RED", True, HOUSE_RED), (30, 20)); self.canvas.blit(self.score_font.render("YLW", True, TEAM_YELLOW), (30, 70))
            
            rem_r = self.stones_per_team - self.stones_thrown[0]
            rem_y = self.stones_per_team - self.stones_thrown[1]
            for i in range(rem_r): pygame.draw.circle(self.canvas, HOUSE_RED, (140 + i*18, 30), 6)
            for i in range(rem_y): pygame.draw.circle(self.canvas, TEAM_YELLOW, (140 + i*18, 80), 6)
            
            spacing = min(80, (BASE_WIDTH - 420) // 8)
            for e in range(1, 9):
                cx = 200 + (e * spacing); self.canvas.blit(self.small_font.render(str(e), True, (140, 150, 165)), (cx, 8))
                self.canvas.blit(self.score_font.render(str(self.score[0][e-1]) if e < self.current_end or (e == self.current_end and self.turn_state == "END") else "-", True, WHITE), (cx, 44))
                self.canvas.blit(self.score_font.render(str(self.score[1][e-1]) if e < self.current_end or (e == self.current_end and self.turn_state == "END") else "-", True, WHITE), (cx, 80))

            tot_x = 200 + (8 * spacing) + 80; pygame.draw.line(self.canvas, (80, 90, 105), (tot_x - 40, 0), (tot_x - 40, 130), 2)
            self.canvas.blit(self.small_font.render("TOT", True, WHITE), (tot_x, 8))
            self.canvas.blit(self.score_font.render(str(sum(self.score[0])), True, HOUSE_RED), (tot_x, 44)); self.canvas.blit(self.score_font.render(str(sum(self.score[1])), True, TEAM_YELLOW), (tot_x, 80))
            if getattr(self, 'hammer_team', 0) == 0: draw_hammer_icon(self.canvas, tot_x + 65, 48, HOUSE_RED)
            elif getattr(self, 'hammer_team', 0) == 1: draw_hammer_icon(self.canvas, tot_x + 65, 86, TEAM_YELLOW)

        for p in self.particles:
            if p['type'] == 'spark': pygame.draw.circle(self.canvas, lerp_color((255, 200, 50), ICE_COLOR, 1.0-p['life']), (int(p['pos'].x), int(p['pos'].y)), int(p['life']*4))
            elif p['type'] == 'trail': pygame.draw.circle(self.canvas, lerp_color(WHITE, ICE_COLOR, 1.0-p['life']), (int(p['pos'].x), int(p['pos'].y)), int(p['life']*6))
            elif p['type'] == 'sweep': pygame.draw.circle(self.canvas, lerp_color((200, 240, 255), ICE_COLOR, 1.0-p['life']), (int(p['pos'].x), int(p['pos'].y)), int(p['life']*5))

        m_pos = self.get_pointer_pos()
        draw_glass_rect(self.canvas, self.btn_pause, (50, 55, 65), self.btn_pause.h // 2, self.btn_pause.collidepoint(m_pos.x, m_pos.y))
        
        btn_text = "DISCONNECT" if self.game_mode in ("HOST", "JOIN") else "PAUSE"
        lbl_p = self.small_font.render(btn_text, True, BLACK)
        if self.game_mode in ("HOST", "JOIN"):
            total_w = 34 + 8 + lbl_p.get_width()
            start_x = self.btn_pause.centerx - total_w // 2
            # Disconnect Icon
            px, py = start_x + 17, self.btn_pause.centery
            pygame.draw.circle(self.canvas, BLACK, (px-8, py), 4)
            pygame.draw.line(self.canvas, BLACK, (px-8, py), (px-2, py), 3)
            pygame.draw.circle(self.canvas, BLACK, (px+8, py), 4)
            pygame.draw.line(self.canvas, BLACK, (px+8, py), (px+2, py), 3)
            pygame.draw.line(self.canvas, (255, 50, 50), (px-4, py-6), (px+4, py+6), 3)
            self.canvas.blit(lbl_p, (start_x + 42, self.btn_pause.centery - lbl_p.get_height()//2))

            draw_glass_rect(self.canvas, self.btn_chat, (50, 55, 65) if not self.typing_chat else (80, 150, 80), self.btn_chat.h // 2, self.btn_chat.collidepoint(m_pos.x, m_pos.y))
            lbl_chat = self.small_font.render("CHAT", True, BLACK)
            self.canvas.blit(lbl_chat, (self.btn_chat.centerx - lbl_chat.get_width()//2, self.btn_chat.centery - lbl_chat.get_height()//2))
        else:
            total_w = 22 + 12 + lbl_p.get_width()
            start_x = self.btn_pause.centerx - total_w // 2
            self.draw_pause_icon(self.canvas, start_x, self.btn_pause.centery - 12)
            self.canvas.blit(lbl_p, (start_x + 34, self.btn_pause.centery - lbl_p.get_height()//2))

        # Netcode Chat Render Support
        if self.game_mode in ["HOST", "JOIN"]:
            current_time = pygame.time.get_ticks()
            active_chat = [c for c in self.chat_messages[-5:] if current_time - c['time'] < 30000]
            max_alpha = 0
            if self.typing_chat: max_alpha = 255
            elif active_chat:
                for c in active_chat:
                    age = current_time - c['time']
                    max_alpha = max(max_alpha, 255 if age < 28000 else int(255 * (1.0 - (age - 28000)/2000.0)))
            
            if max_alpha > 0:
                chat_h = 40 + len(active_chat) * 40
                if self.typing_chat: chat_h += 60
                chat_rect = pygame.Rect(40, BASE_HEIGHT - 250 - chat_h, 800, chat_h)
                
                glass_surf = UICache.get_glass(chat_rect.w, chat_rect.h, (25, 30, 40, 200), 16, False)[1].copy()
                if max_alpha < 255:
                    temp = pygame.Surface(glass_surf.get_size(), pygame.SRCALPHA)
                    temp.fill((255, 255, 255, max_alpha))
                    glass_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.canvas.blit(glass_surf, chat_rect)
                
                y_offset = chat_rect.y + 20
                for c in active_chat:
                    txt_surf = self.chat_font.render(c['text'], True, (255, 255, 255)).copy()
                    shd_surf = self.chat_font.render(c['text'], True, (0, 0, 0)).copy()
                    if max_alpha < 255:
                        temp = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
                        temp.fill((255, 255, 255, max_alpha))
                        txt_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        shd_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.canvas.blit(shd_surf, (chat_rect.x + 22, y_offset + 2))
                    self.canvas.blit(txt_surf, (chat_rect.x + 20, y_offset))
                    y_offset += 40
                    
                if self.typing_chat:
                    if active_chat:
                        line_surf = pygame.Surface((chat_rect.w - 40, 2), pygame.SRCALPHA)
                        line_surf.fill((100, 110, 130, max_alpha))
                        self.canvas.blit(line_surf, (chat_rect.x + 20, y_offset))
                    y_offset += 15
                    txt_surf = self.chat_font.render("Say: " + self.chat_input + "_", True, TEAM_YELLOW).copy()
                    shd_surf = self.chat_font.render("Say: " + self.chat_input + "_", True, (0, 0, 0)).copy()
                    if max_alpha < 255:
                        temp = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
                        temp.fill((255, 255, 255, max_alpha))
                        txt_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        shd_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.canvas.blit(shd_surf, (chat_rect.x + 22, y_offset + 2))
                    self.canvas.blit(txt_surf, (chat_rect.x + 20, y_offset))
                
            if self.net.matched and getattr(self.net, 'opponent', None):
                opp_surf = self.small_font.render(f"VS: {self.net.opponent.split('!')[0]}", True, BLACK)
                self.canvas.blit(opp_surf, (40, 150))

        if self.turn_state == "AIMING":
            if self.active_stone: pygame.draw.circle(self.canvas, (100, 200, 255), (int(self.active_stone.pos.x), int(self.active_stone.pos.y)), int(40 + ((math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5) * 15), 2)
            
            draw_glass_rect(self.canvas, self.btn_curl_l, (255, 180, 180), 16, self.btn_curl_l.collidepoint(m_pos.x, m_pos.y))
            img_m = self.large_sym_font.render("-", True, HOUSE_RED); img_cl = self.small_font.render(" CURL L", True, BLACK)
            bx = self.btn_curl_l.centerx - (img_m.get_width() + img_cl.get_width())//2
            self.canvas.blit(img_m, (bx, self.btn_curl_l.centery - img_m.get_height()//2)); self.canvas.blit(img_cl, (bx + img_m.get_width(), self.btn_curl_l.centery - img_cl.get_height()//2))
            
            draw_glass_rect(self.canvas, self.btn_curl_r, (180, 255, 180), 16, self.btn_curl_r.collidepoint(m_pos.x, m_pos.y))
            img_p = self.large_sym_font.render("+", True, (40, 160, 40)); img_cr = self.small_font.render(" CURL R", True, BLACK)
            bx2 = self.btn_curl_r.centerx - (img_p.get_width() + img_cr.get_width())//2
            self.canvas.blit(img_p, (bx2, self.btn_curl_r.centery - img_p.get_height()//2)); self.canvas.blit(img_cr, (bx2 + img_p.get_width(), self.btn_curl_r.centery - img_cr.get_height()//2))

            if self.is_dragging:
                pull = pygame.math.Vector2(-self.virtual_pull.x / 4.0, -self.virtual_pull.y)
                if pull.length() > 5:
                    spos, svel = pygame.math.Vector2(self.active_stone.pos), pull.normalize() * min(16.0, pull.length() / 14.0)
                    svel_len = svel.length(); curl_factor = self.selected_curl * 0.05
                    sx, sy, px, py = svel.x, svel.y, spos.x, spos.y
                    rad_conv = math.pi / 180.0
                    for i in range(140):
                        if svel_len <= FRICTION_BASE: break
                        r = (svel_len - FRICTION_BASE) / svel_len
                        sx *= r; sy *= r
                        svel_len -= FRICTION_BASE
                        if svel_len > 0.4:
                            a = (1.4 / svel_len) * curl_factor * rad_conv
                            cos_a, sin_a = math.cos(a), math.sin(a)
                            sx, sy = sx * cos_a - sy * sin_a, sx * sin_a + sy * cos_a
                        px += sx; py += sy
                        if i % 5 == 0: pygame.draw.circle(self.canvas, (HOUSE_RED if self.current_team == 0 else HOUSE_BLUE), (int(px), int(py)), 6)
            shadow_col = (255, 255, 255)
            if self.selected_curl < 0:
                c = int(255 * (1.0 + self.selected_curl))
                shadow_col = (255, c, c)
            elif self.selected_curl > 0:
                c = int(255 * (1.0 - self.selected_curl))
                shadow_col = (c, 255, c)
            cb_str = f"CURL BIAS: {self.selected_curl:+.1f}"
            lbl_sh = self.font.render(cb_str, True, shadow_col)
            lbl_fg = self.font.render(cb_str, True, BLACK)
            bx, by = self.hack_pos.x - 130, self.hack_pos.y - 80
            self.canvas.blit(lbl_sh, (bx+3, by+3))
            self.canvas.blit(lbl_fg, (bx, by))
            
        elif self.turn_state == "SLIDING":
            if getattr(self, 'is_sweeping_now', False):
                angle = math.sin(pygame.time.get_ticks() * 0.05) * min(30, self.sweep_power * 2.0)
                rotated_broom = pygame.transform.rotate(self.broom_surf, angle)
                b_rect = rotated_broom.get_rect(center=(m_pos.x, m_pos.y - 120))
                self.canvas.blit(rotated_broom, b_rect.topleft)

        elif self.turn_state == "END":
            overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha(); overlay.fill((0, 0, 0, 195)); self.canvas.blit(overlay, (0, 0))
            
            if self.game_mode == "CHALLENGE":
                txt = "SUCCESS! ADVANCING..." if getattr(self, 'challenge_success', False) else "FAILED. RETRYING..."
                if self.challenge_attempts >= 3 and not getattr(self, 'challenge_success', False): txt = "FAILED - SKIPPING CHALLENGE"
            else: txt = "END COMPLETE"
                
            img_txt = self.font.render(txt, True, WHITE); self.canvas.blit(img_txt, (BASE_WIDTH//2 - img_txt.get_width()//2, BASE_HEIGHT//2 - 50))
            draw_glass_rect(self.canvas, self.btn_next_end, PURPLE_SUIT, self.btn_next_end.h // 2, self.btn_next_end.collidepoint(m_pos.x, m_pos.y))
            
            btn_txt = "NEXT" if self.game_mode=="CHALLENGE" and (getattr(self, 'challenge_success', False) or self.challenge_attempts >= 3) else "RETRY" if self.game_mode=="CHALLENGE" else "ADVANCE MATCH"
            lbl = self.small_font.render(btn_txt, True, WHITE); self.canvas.blit(lbl, lbl.get_rect(center=self.btn_next_end.center))

    def draw_pause_screen(self):
        self.pause_anim += (1.0 - self.pause_anim) * 0.15
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha(); overlay.fill((0, 0, 0, int(215 * self.pause_anim))); self.canvas.blit(overlay, (0, 0))
        self.last_starfield_speed = 0.5 * self.pause_anim
        self.starfield.draw(self.canvas, 0.5 * self.pause_anim)
        m_pos = self.get_pointer_pos()
        
        lbl_p = self.font_85.render("PAUSED", True, WHITE)
        self.canvas.blit(lbl_p, (BASE_WIDTH//2 - lbl_p.get_width()//2, BASE_HEIGHT//2 - 250 + int((1.0 - self.pause_anim) * -200)))
        
        res_rect = self.btn_resume.move(-int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, res_rect, HOUSE_BLUE, res_rect.h // 2, res_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("RESUME MATCH", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=res_rect.center))
        
        quit_rect = self.btn_quit_main.move(int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, quit_rect, HOUSE_RED, quit_rect.h // 2, quit_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_q = self.font.render("QUIT TO MENU", True, WHITE); self.canvas.blit(lbl_q, lbl_q.get_rect(center=quit_rect.center))

    def draw_match_over_screen(self):
        self.canvas.fill((16, 22, 34)); cx = BASE_WIDTH // 2
        if self.game_mode == "CHALLENGE":
            lbl_v = self.font_72.render("CHALLENGES COMPLETED!", True, TEAM_YELLOW)
            self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, 180))
        else:
            r_tot, y_tot = sum(self.score[0]), sum(self.score[1])
            o_txt, o_col = ("RED TEAM WINS!", HOUSE_RED) if r_tot > y_tot else ("YELLOW TEAM WINS!", TEAM_YELLOW) if y_tot > r_tot else ("TIE MATCH!", WHITE)
            if getattr(self, 'winner_text', '') == "Opponent Disconnected":
                o_txt, o_col = "OPPONENT DISCONNECTED", (255, 100, 100)
            lbl_victory = self.font_72.render(o_txt, True, o_col); self.canvas.blit(lbl_victory, (cx - lbl_victory.get_width()//2, 180))
            
            b_rect = pygame.Rect(cx - 480, 350, 960, 400)
            pygame.draw.rect(self.canvas, (28, 36, 50), b_rect, border_radius=16); pygame.draw.rect(self.canvas, (55, 70, 95), b_rect, 4, border_radius=16)
            
            self.canvas.blit(self.small_font.render("TEAM", True, (140, 160, 185)), (cx - 430, 380))
            spacing = min(75, 700 // 8)
            for e in range(1, 9): self.canvas.blit(self.small_font.render(f"E{e}", True, (140, 160, 185)), (cx - 320 + (e * spacing), 380))
            self.canvas.blit(self.small_font.render("TOTAL", True, WHITE), (cx + 360, 380))
            pygame.draw.line(self.canvas, (55, 70, 95), (cx - 450, 440), (cx + 450, 440), 2)
            
            self.canvas.blit(self.font.render("RED", True, HOUSE_RED), (cx - 430, 470))
            for e in range(1, 9): self.canvas.blit(self.font.render(str(self.score[0][e-1]), True, WHITE), (cx - 320 + (e * spacing), 470))
            self.canvas.blit(self.font.render(str(r_tot), True, HOUSE_RED), (cx + 380, 470))

            self.canvas.blit(self.font.render("YLW", True, TEAM_YELLOW), (cx - 430, 570))
            for e in range(1, 9): self.canvas.blit(self.font.render(str(self.score[1][e-1]), True, WHITE), (cx - 320 + (e * spacing), 570))
            self.canvas.blit(self.font.render(str(y_tot), True, TEAM_YELLOW), (cx + 380, 570))
            
        m_pos = self.get_pointer_pos()
        draw_glass_rect(self.canvas, self.btn_return_menu, HOUSE_BLUE, self.btn_return_menu.h // 2, self.btn_return_menu.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("MAIN MENU", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))
        
        self.btn_leaderboard = pygame.Rect(cx - 150, 750, 300, 70)
        draw_glass_rect(self.canvas, self.btn_leaderboard, (50, 60, 80), self.btn_leaderboard.h // 2, self.btn_leaderboard.collidepoint(m_pos.x, m_pos.y))
        lbl_lb = self.font.render("LEADERBOARD", True, WHITE)
        self.canvas.blit(lbl_lb, lbl_lb.get_rect(center=self.btn_leaderboard.center))

    def draw_leaderboard_screen(self):
        self.canvas.fill((16, 22, 34))
        cx = BASE_WIDTH // 2
        lbl = self.font_72.render("GLOBAL LEADERBOARD", True, WHITE)
        self.canvas.blit(lbl, (cx - lbl.get_width()//2, 80))
        
        b_rect = pygame.Rect(cx - 400, 200, 800, 650)
        pygame.draw.rect(self.canvas, (28, 36, 50), b_rect, border_radius=16); pygame.draw.rect(self.canvas, (55, 70, 95), b_rect, 4, border_radius=16)
        
        if getattr(self, 'leaderboard_data', None) is None:
            txt = self.font.render("LOADING...", True, (150, 200, 255))
            self.canvas.blit(txt, (cx - txt.get_width()//2, 400))
        elif getattr(self, 'leaderboard_data') == "ERROR":
            txt = self.font.render("FAILED TO LOAD DATA", True, (255, 100, 100))
            self.canvas.blit(txt, (cx - txt.get_width()//2, 400))
        else:
            for i, entry in enumerate(self.leaderboard_data[:10]):
                name = entry.get('name', 'Unknown')
                score = entry.get('score', 0)
                color = TEAM_YELLOW if i == 0 else WHITE if i < 3 else (180, 180, 180)
                n_lbl = self.font.render(f"{i+1}. {name}", True, color)
                s_lbl = self.font.render(str(score), True, color)
                self.canvas.blit(n_lbl, (cx - 350, 230 + i * 60))
                self.canvas.blit(s_lbl, (cx + 250, 230 + i * 60))
                
        m_pos = self.get_pointer_pos()
        draw_glass_rect(self.canvas, self.btn_return_menu, HOUSE_BLUE, self.btn_return_menu.h // 2, self.btn_return_menu.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("BACK", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

    def draw_global_ui(self):
        if not IS_ANDROID:
            m_pos = self.get_pointer_pos()
            draw_glass_rect(self.canvas, self.btn_fs, (50, 60, 80), self.btn_fs.h // 2, self.btn_fs.collidepoint(m_pos.x, m_pos.y))
            lbl = self.small_font.render("FULLSCREEN", True, WHITE)
            self.canvas.blit(lbl, lbl.get_rect(center=self.btn_fs.center))

    def render(self):
        ww, wh = self.screen.get_size()
        scale = min(ww / BASE_WIDTH, wh / BASE_HEIGHT)
        sw, sh = int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale)
        ox, oy = (ww - sw) // 2, (wh - sh) // 2
        
        if self.shake_amount > 0.1: 
            ox += int(random.uniform(-self.shake_amount, self.shake_amount))
            oy += int(random.uniform(-self.shake_amount, self.shake_amount))
            self.shake_amount *= 0.85 
        
        self.screen.fill((10, 12, 16))
        
        if not IS_ANDROID and getattr(self, 'border_starfield', None):
            self.border_starfield.draw(self.screen, getattr(self, 'last_starfield_speed', 0.5) * scale)
        
        if IS_ANDROID:
            if getattr(self, 'bilinear_on', False):
                # Bilinear requires manual scaling if we want to override GPU nearest (if SCALED is nearest)
                self.screen.blit(pygame.transform.smoothscale(self.canvas, (sw, sh)) if sw != BASE_WIDTH else self.canvas, (ox, oy))
            else:
                self.screen.blit(self.canvas, (ox, oy))
        else:
            if getattr(self, 'fxaa_on', False):
                self.screen.blit(pygame.transform.smoothscale(self.canvas, (sw, sh)), (ox, oy))
            elif getattr(self, 'lighter_filter', False):
                # Lighter weight filter = standard bilinear without extra passes, but pygame smoothscale is already just bilinear.
                # Let's use scale for off, and smoothscale for lighter/fxaa.
                self.screen.blit(pygame.transform.smoothscale(self.canvas, (sw, sh)), (ox, oy))
            else:
                self.screen.blit(pygame.transform.scale(self.canvas, (sw, sh)), (ox, oy))
            
        pygame.display.flip()

    def run(self):
        while True:
            self.frames_elapsed += 1
            for event in pygame.event.get():
                if event.type == QUIT: self.net.close(); pygame.quit(); sys.exit()
                
                if event.type in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
                    self.current_mapped_pos = self.scale_mouse(event.pos)
                    if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1: self.is_pointer_pressed = True
                    elif event.type == MOUSEBUTTONUP and getattr(event, 'button', 1) == 1: self.is_pointer_pressed = False
                    
                    if event.type == MOUSEMOTION:
                        event = pygame.event.Event(event.type, buttons=getattr(event, 'buttons', (1,0,0)), pos=self.current_mapped_pos, finger_id='mouse')
                    else:
                        event = pygame.event.Event(event.type, button=getattr(event, 'button', 1), pos=self.current_mapped_pos, finger_id='mouse')

                if event.type == VIDEORESIZE and not self.is_fullscreen and not IS_ANDROID:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                    self.border_starfield = Starfield(count=400, max_w=event.w, max_h=event.h)
                
                if event.type == getattr(pygame, 'TEXTINPUT', 771):
                    if self.app_state == "PLAY" and self.game_mode in ["HOST", "JOIN"] and self.typing_chat:
                        if len(self.chat_input) + len(event.text) <= 30:
                            self.chat_input += event.text
                    elif self.app_state == "MENU" and self.typing_target == "name":
                        if len(self.username) + len(event.text) <= 15:
                            self.username += event.text
                            self.save_progress()
                    elif self.app_state == "ROOM_PROMPT" and self.typing_target == "room":
                        if len(self.room_text) + len(event.text) <= 15:
                            self.room_text += event.text
                            self.save_progress()

                if event.type == KEYDOWN:
                    if self.app_state == "PLAY" and self.game_mode in ["HOST", "JOIN"]:
                        if self.typing_chat:
                            if event.key == K_RETURN:
                                if self.chat_input.strip():
                                    self.net.send_action({'cmd': 'chat', 'msg': self.chat_input})
                                    self.chat_messages.append({"text": f"Me: {self.chat_input}", "time": pygame.time.get_ticks()})
                                self.typing_chat = False
                                self.chat_input = ""
                                try: pygame.key.stop_text_input()
                                except: pass
                            elif event.key == K_BACKSPACE:
                                self.chat_input = self.chat_input[:-1]
                            continue
                        else:
                            if event.key == K_t or event.key == K_RETURN:
                                self.typing_chat = True
                                try: pygame.key.start_text_input()
                                except: pass
                                continue

                    if event.key == K_ESCAPE:
                        if self.app_state == "PLAY":
                            self.audio.play_click()
                            if self.game_mode in ["HOST", "JOIN"]: self.return_to_menu()
                            else: self.app_state = "PAUSED"; self.pause_anim = 0.0; self.audio.update_slide(0.0); self.audio.update_sweep(0.0)
                        elif self.app_state == "PAUSED":
                            self.audio.play_click(); self.app_state = "PLAY"
                        elif self.app_state == "ROOM_PROMPT":
                            self.app_state = "MENU"; self.set_typing_target(None)
                        continue
                    elif event.key == K_f:
                        if not IS_ANDROID: self.toggle_fullscreen()
                        continue
                    
                if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
                    m_pos = self.get_pointer_pos()
                    if self.app_state in ["MENU", "CHALLENGE_MENU", "ROOM_PROMPT", "MATCH_OVER"]:
                        if not IS_ANDROID and self.btn_fs.collidepoint(m_pos.x, m_pos.y):
                            self.toggle_fullscreen()
                            continue
                
                if self.app_state == "MENU": self.handle_menu_events(event)
                elif self.app_state == "ROOM_PROMPT": self.handle_room_prompt_events(event)
                elif self.app_state == "CHALLENGE_MENU": self.handle_challenge_menu_events(event)
                elif self.app_state == "OPTIONS_MENU": self.handle_options_events(event)
                elif self.app_state == "PLAY": self.handle_play_events(event)
                elif self.app_state == "PAUSED": self.handle_pause_events(event)
                elif self.app_state == "MATCH_OVER": self.handle_match_over_events(event)
                elif self.app_state == "LEADERBOARD": self.handle_leaderboard_events(event)

            if self.app_state in ["MENU", "ROOM_PROMPT", "CHALLENGE_MENU", "OPTIONS_MENU", "MATCH_OVER"]:
                if not getattr(self, 'is_music_muted', False) and getattr(self, 'frames_since_start', 0) >= 210: 
                    self.audio.play_music()
                else: 
                    self.audio.stop_music()
            else:
                self.audio.stop_music()
                
            self.update_network()
            if self.app_state == "MENU": 
                self.audio.process_pending_sounds()
                self.draw_menu()
            elif self.app_state == "ROOM_PROMPT": self.draw_room_prompt()
            elif self.app_state == "CHALLENGE_MENU": self.draw_challenge_menu()
            elif self.app_state == "OPTIONS_MENU": self.draw_options_menu()
            elif self.app_state == "COIN_TOSS":
                if self.game_mode == "JOIN" and getattr(self, 'coin_flip_result', -1) == -1:
                    pass
                else:
                    self.coin_timer -= 1
                    if self.coin_timer <= 0:
                        self.stones_thrown = {0: 0, 1: 0}
                        self.score = {0: [0]*8, 1: [0]*8}
                        self.current_end = 1
                        self.total_stones_played = 0
                        self.hammer_team = getattr(self, 'coin_flip_result', 0)
                        self.app_state = "PLAY"; self.reset_end()
                self.draw_coin_toss_screen()
            elif self.app_state == "PLAY":
                self.update_physics(); self.draw_ice(); [s.draw(self.canvas) for s in self.stones]
                self.curler_anim.draw(self.canvas, HOUSE_RED if self.current_team == 0 else TEAM_YELLOW); self.draw_ui()
            elif self.app_state == "PAUSED": 
                if self.game_mode in ["HOST", "JOIN"]: self.update_physics()
                self.draw_ice(); [s.draw(self.canvas) for s in self.stones]; self.curler_anim.draw(self.canvas, HOUSE_RED if self.current_team == 0 else TEAM_YELLOW); self.draw_ui(); self.draw_pause_screen()
            elif self.app_state == "MATCH_OVER": self.draw_match_over_screen()
            elif self.app_state == "LEADERBOARD": self.draw_leaderboard_screen()
                
            self.render(); self.clock.tick(FPS)

# --- DAL.NET IRC Socket Manager ---
class IRCNetworkManager:
    def __init__(self):
        self.sock = None; self.running = False; self.connecting = False; self.matched = False
        self.username = ""; self.opponent = ""; self.channel = "#wincurl3_net"
        self.room_display = ""
        self.connection_error = ""
        self.tx_queue = queue.Queue(); self.rx_queue = queue.Queue(); self.is_host = False

    def connect(self, username, is_host, room_name="", preferred_color=0):
        self.username = "WC_" + "".join(c for c in username if c.isalnum())[:10]
        if len(self.username) == 3: self.username += str(random.randint(100,999))
        
        safe_room = "".join(c for c in room_name if c.isalnum()) or "default"
        self.channel = f"#wc3_{safe_room}"
        self.room_display = f"'{safe_room}'"
        
        self.preferred_color = preferred_color
        self.connection_error = ""
        self.is_host = is_host; self.connecting = True; self.running = True
        threading.Thread(target=self._irc_thread, daemon=True).start()

    def _irc_thread(self):
        def enc_msg(msg_dict): return "Z" + base64.b64encode(zlib.compress(json.dumps(msg_dict).encode('utf-8'))).decode('utf-8')
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            try:
                self.sock.connect(("irc.dal.net", 6667))
            except Exception as e:
                print("DNS/IPv6 Failed, trying IPv4 fallback:", e)
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5.0)
                self.sock.connect(("194.14.236.50", 6667)) # Dal.net fallback IP
            self.sock.settimeout(None)
            self.sock.send(f"NICK {self.username}\r\nUSER {self.username} 8 * :WinCurl3\r\n".encode())
            buffer = ""
            last_hello_time = 0
            while self.running:
                if not self.is_host and not self.connecting and not self.matched:
                    if time.time() - last_hello_time > 3.0:
                        self.sock.send(f"PRIVMSG {self.channel} :{json.dumps({'cmd': 'hello'})}\r\n".encode())
                        last_hello_time = time.time()
                
                while not self.tx_queue.empty():
                    msg = self.tx_queue.get()
                    if self.matched and self.opponent: self.sock.send(f"PRIVMSG {self.opponent} :{enc_msg(msg)}\r\n".encode())
                
                self.sock.settimeout(0.1)
                try:
                    data = self.sock.recv(4096).decode('utf-8', errors='ignore')
                    if not data: break
                    buffer += data
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1); parts = line.split(" ")
                        if parts[0] == "PING": self.sock.send(f"PONG {parts[1]}\r\n".encode())
                        elif len(parts) > 1 and parts[1] == "433":
                            self.username += "too"
                            self.sock.send(f"NICK {self.username}\r\n".encode())
                        elif len(parts) > 1 and parts[1] in ("001", "376", "422"):
                            self.sock.send(f"JOIN {self.channel}\r\n".encode())
                            if self.is_host: self.connecting = False 
                            else: 
                                self.sock.send(f"PRIVMSG {self.channel} :{json.dumps({'cmd': 'hello'})}\r\n".encode())
                                self.connecting = False
                        elif len(parts) > 2 and parts[1] in ("PART", "QUIT"):
                            sender = parts[0].split("!")[0][1:]
                            if sender == getattr(self, 'opponent', ''):
                                self.rx_queue.put({'cmd': 'opponent_left'})
                        elif len(parts) > 3 and parts[1] == "PRIVMSG":
                            sender = parts[0].split("!")[0][1:]
                            target = parts[2]
                            msg_content = line.split(" :", 1)[1]
                            try:
                                if msg_content.startswith("Z"):
                                    raw = zlib.decompress(base64.b64decode(msg_content[1:])).decode('utf-8')
                                    msg_data = json.loads(raw)
                                else:
                                    msg_data = json.loads(msg_content)
                                    
                                if self.is_host and target == self.channel and msg_data.get('cmd') == 'hello':
                                    self.opponent = sender; self.matched = True
                                    self.sock.send(f"PRIVMSG {self.opponent} :{json.dumps({'cmd': 'hello_ack', 'color': getattr(self, 'preferred_color', 0)})}\r\n".encode())
                                elif not self.is_host and not self.matched and msg_data.get('cmd') == 'hello_ack':
                                    self.opponent = sender; self.matched = True
                                    self.rx_queue.put({'cmd': 'set_color', 'color': msg_data.get('color', 0)})
                                elif sender == self.opponent:
                                    self.rx_queue.put(msg_data)
                            except: pass
                except socket.timeout: pass
        except Exception as e:
            self.connection_error = str(e)
            print("NETWORK ERROR:", e)
        finally: self.close()

    def send_action(self, data_dict):
        if self.matched: self.tx_queue.put(data_dict)
    def receive_action(self):
        try: return self.rx_queue.get_nowait()
        except queue.Empty: return None
    def close(self):
        self.running, self.matched, self.connecting = False, False, False
        if self.sock:
            try: self.sock.close()
            except: pass

def main():
    import os, sys
    if not hasattr(sys, 'getandroidapilevel'):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    game = WinCurl3()
    game.setup_display()
    game.run()

if __name__ == "__main__":
    main()

import pygame
import math, random, sys, time, json, socket, threading, queue, base64, zlib
import struct
import io
import wave
import os
from pygame.locals import *

try:
    from plyer import vibrator
    def vibrate_android(ms):
        try: vibrator.vibrate(time=ms/1000.0)
        except: pass
except:
    def vibrate_android(ms): pass

# Define this immediately after imports
IS_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_BOOTLOGO' in os.environ
if IS_ANDROID:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- Immediate Environment Verification ---
print("\n" + "="*80)
print("     [SYSTEM] WINCURL 3 BUILD 14 FINAL")
print("     (3D STONES | NET CHAT | MULTI-SYLLABLE AUDIO | ANDROID FINGERDOWN FIX)")
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
        key = (w, h, base_color, radius, hovered)
        if key not in cls.glass_surfs:
            shadow = pygame.Surface((w+10, h+10), pygame.SRCALPHA).convert_alpha()
            pygame.draw.rect(shadow, (0, 0, 0, 50), (5, 5, w, h), border_radius=radius)
            
            btn_surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
            c = pygame.Color(*base_color[:3], 180)
            pygame.draw.rect(btn_surf, c, (0, 0, w, h), border_radius=radius)
            pygame.draw.rect(btn_surf, (255, 255, 255, 30), (0, 0, w, h//2), border_top_left_radius=radius, border_top_right_radius=radius)
            pygame.draw.ellipse(btn_surf, (255, 255, 255, 55), (w*0.05, 2, w*0.9, h*0.45))
            pygame.draw.rect(btn_surf, (0, 0, 0, 30), (0, h//2, w, h//2), border_bottom_left_radius=radius, border_bottom_right_radius=radius)

            if hovered:
                pygame.draw.rect(btn_surf, (255, 255, 255, 240), (0, 0, w, h), 3, border_radius=radius)
                pygame.draw.rect(btn_surf, (255, 255, 255, 50), (0, 0, w, h), 0, border_radius=radius)
            else:
                pygame.draw.rect(btn_surf, (255, 255, 255, 100), (0, 0, w, h), 2, border_radius=radius)
            cls.glass_surfs[key] = (shadow, btn_surf)
        return cls.glass_surfs[key]

def draw_glass_rect(surface, rect, base_color, border_radius=16, is_hovered=False):
    shadow, btn_surf = UICache.get_glass(rect.w, rect.h, base_color, border_radius, is_hovered)
    surface.blit(shadow, (rect.x-5, rect.y-5))
    surface.blit(btn_surf, rect.topleft)

# --- Audio Synthesis Engine ---
class WinCurlAudioEngine:
    def __init__(self):
        if IS_ANDROID: pygame.mixer.pre_init(44100, -16, 2, 4096)
        else: pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        
        self.ch_slide = pygame.mixer.Channel(0); self.ch_sweep = pygame.mixer.Channel(1)
        self.ch_sfx = pygame.mixer.Channel(2); self.ch_ui = pygame.mixer.Channel(3)
        self.ch_music = pygame.mixer.Channel(4); self.ch_crowd = pygame.mixer.Channel(5)
        self.ch_voice = pygame.mixer.Channel(6)
        
        self.sfx_on = True
        self.snd_slide = self._synthesize_rumble(); self.snd_sweep = self._synthesize_sweep()
        self.snd_throw = self._synthesize_throw(); self.snd_clack = self._synthesize_clack()
        self.snd_hover = self._synthesize_ui_sound(440, 0.05, "sine")
        self.snd_click = self._synthesize_ui_sound(587, 0.12, "square")
        self.snd_theme = self._synthesize_theme_song()
        
        # Authentic Build 13 Voice Restoration
        self.snd_speech = self._synthesize_sega_speech()  
        self.snd_hurry = self._synthesize_vosim_phrase("HURRY", 0.7)
        self.snd_hard = self._synthesize_vosim_phrase("HARD", 0.65)
        
        # BUILD 14 PREVIEW 2: Multi-Syllable Complex Vocals
        self.snd_chal_comp = self._synthesize_vosim_phrase("CHALLENGE_COMPLETE", 2.0)
        self.snd_red_wins = self._synthesize_vosim_phrase("RED_TEAM_WINS", 2.2)
        self.snd_ylw_wins = self._synthesize_vosim_phrase("YELLOW_TEAM_WINS", 2.4)
        
        self.snd_cheer = self._synthesize_cheer()
        self.snd_end_match = self._synthesize_end_of_match()
        
        self.ch_slide.play(self.snd_slide, loops=-1); self.ch_slide.set_volume(0.0)
        self.ch_sweep.play(self.snd_sweep, loops=-1); self.ch_sweep.set_volume(0.0)
        self.ch_sfx.play(self.snd_speech); self.last_call = 0

    def play_clack(self, intensity):
        if not self.sfx_on: return
        vol = max(0.1, min(1.0, intensity / 20.0))
        self.snd_clack.set_volume(vol)
        self.ch_sfx.play(self.snd_clack)
        if IS_ANDROID and vol > 0.3:
            vibrate_android(int(vol * 150))

    def _create_wav_sound(self, byte_buffer, sample_rate=44100):
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(byte_buffer)
        wav_io.seek(0)
        return pygame.mixer.Sound(wav_io)

    def _synthesize_sega_speech(self):
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
        return self._create_wav_sound(buf, 44100)

    def _synthesize_vosim_phrase(self, phrase, duration):
        steps = int(44100 * duration); buf = bytearray(steps * 4)
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
            f1_env = [(0.0,600), (0.2,530), (0.4,300), (0.6,500), (0.8,400), (1.0,200)]
            f2_env = [(0.0,1700), (0.4,1840), (0.6,1200), (1.0,1400)]
            f3_env = [(0.0,2400), (0.5,2200), (1.0,2500)]
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
                phase = ((i/44100) * f0) % 1.0; decay = math.exp(-phase * 2.2)
                val += (math.sin(2*math.pi*get_val(t_norm,f1_env)*phase/f0) + math.sin(2*math.pi*get_val(t_norm,f2_env)*phase/f0)*0.6 + math.sin(2*math.pi*get_val(t_norm,f3_env)*phase/f0)*0.3) * decay
            sample = int(max(-1.0, min(1.0, (val / len(chord)) * env * 2.0)) * 24000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100)

    def _synthesize_end_of_match(self):
        steps = int(44100 * 2.0); buf = bytearray(steps * 4)
        f1_env = [(0,400),(0.3,500),(0.6,300),(1.0,400),(1.4,700),(1.8,300),(2.0,200)]
        f2_env = [(0,1800),(0.3,1200),(0.6,1000),(1.0,900),(1.4,1200),(1.8,1800),(2.0,2400)]
        f3_env = [(0,2600),(0.5,2400),(1.0,2400),(1.5,2600),(2.0,2800)]
        
        def get_val(t, pts):
            for i in range(len(pts)-1):
                if pts[i][0] <= t <= pts[i+1][0]: return pts[i][1] + (pts[i+1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i+1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            t = i / 44100; env = math.sin((t / 2.0) * math.pi)
            f0 = 120.0 - t*15.0; phase = (t * f0) % 1.0; decay = math.exp(-phase * 4.0)
            noise = random.uniform(-1, 1) * max(0, (t-1.6)/0.4) * 0.5
            val = (math.sin(2*math.pi*get_val(t,f1_env)*phase/f0) + math.sin(2*math.pi*get_val(t,f2_env)*phase/f0)*0.6 + math.sin(2*math.pi*get_val(t,f3_env)*phase/f0)*0.3) * decay
            sample = int(max(-1.0, min(1.0, (val*0.6 + noise) * env)) * 24000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100)

    def _synthesize_cheer(self):
        duration = 3.5; steps = int(44100 * duration); buf = bytearray(steps * 4); val = 0.0
        for i in range(steps):
            t = i / 44100; val += (random.uniform(-1.0, 1.0) - val) * 0.02 
            sample = int(val * math.sin(t * math.pi / duration) * 18000 * (1.0 + 0.3 * math.sin(t*12))) 
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100)

    def _synthesize_rumble(self):
        buf = bytearray(44100 * 4); v = 0.0
        for i in range(44100):
            v = max(-0.4, min(0.4, (v + random.uniform(-0.08, 0.08)) * 0.98))
            struct.pack_into('<hh', buf, i * 4, int(v * 32767), int(v * 32767))
        return self._create_wav_sound(buf, 44100)

    def _synthesize_sweep(self):
        buf = bytearray(22050 * 4)
        for i in range(22050): struct.pack_into('<hh', buf, i*4, int(random.uniform(-0.15, 0.15)*32767), int(random.uniform(-0.15, 0.15)*32767))
        return self._create_wav_sound(buf, 22050)

    def _synthesize_throw(self):
        duration = 0.5; steps = int(44100 * duration); buf = bytearray(steps * 4)
        for i in range(steps):
            t = i / 44100; sample = int(math.sin(2 * math.pi * (180 - (t * 100)) * t) * (math.sin(t * math.pi / duration) * math.exp(-t * 2)) * 32767 * 0.7)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100)

    def _synthesize_clack(self):
        buf = bytearray(11025 * 4)
        for i in range(11025):
            t = i / 11025; sample = int(math.sin(2 * math.pi * (220 + random.uniform(-20, 20)) * t) * math.exp(-t * 25) * 32767)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 11025)

    def _synthesize_ui_sound(self, frequency, duration, type="sine"):
        steps = int(44100 * duration); buf = bytearray(steps * 4)
        for i in range(steps):
            t = i / 44100; val = math.sin(2 * math.pi * frequency * t) if type == "sine" else (1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0)
            struct.pack_into('<hh', buf, i * 4, int(val * math.exp(-t * (1.0 / duration * 3)) * 12000), int(val * math.exp(-t * (1.0 / duration * 3)) * 12000))
        return self._create_wav_sound(buf, 44100)

    def _synthesize_theme_song(self):
        bpm = 120; beat_len = 60.0 / bpm; total_beats = 8; duration = beat_len * total_beats; steps = int(44100 * duration); buf = bytearray(steps * 4)
        bass = [55.0, 55.0, 65.4, 65.4, 73.4, 82.4, 55.0, 55.0]; mel = [220.0, 261.6, 293.7, 329.6, 392.0, 329.6, 293.7, 220.0]
        for i in range(steps):
            t = i / 44100; beat = int((t / duration) * total_beats) % total_beats; b_t = t % beat_len
            val = ((2.0 * (t * bass[beat] - math.floor(t * bass[beat] + 0.5))) * 0.15 * math.exp(-b_t * 4.0)) + \
                  ((1.0 if math.sin(2 * math.pi * (mel[(beat * 3) % total_beats] * (1.0 + 0.02 * math.sin(2 * math.pi * 6.0 * t))) * t) > 0 else -1.0) * 0.08 * math.sin(b_t * math.pi / beat_len) * math.exp(-b_t * 2.0))
            struct.pack_into('<hh', buf, i * 4, int(max(-1.0, min(1.0, val)) * 32767), int(max(-1.0, min(1.0, val)) * 32767))
        return self._create_wav_sound(buf, 44100)

    def play_curler_call(self, intensity):
        now = pygame.time.get_ticks()
        if intensity > 8.0 and (now - self.last_call) > 2500:
            self.last_call = now
            if not self.ch_voice.get_busy():
                if random.random() > 0.5: self.ch_voice.play(self.snd_hurry)
                else: self.ch_voice.play(self.snd_hard)

    def stop_all_match_sounds(self):
        self.ch_slide.set_volume(0.0); self.ch_sweep.set_volume(0.0); self.ch_sfx.stop(); self.ch_crowd.stop()

    def play_cheer(self): 
        if not self.ch_crowd.get_busy(): self.ch_crowd.play(self.snd_cheer)
    def update_slide(self, speed): self.ch_slide.set_volume(min(0.15, speed * 0.04) if speed > 0.05 else 0.0)
    def update_sweep(self, intensity): self.ch_sweep.set_volume(min(0.5, intensity * 0.06))
    def play_throw(self): self.ch_sfx.play(self.snd_throw)
    
    def play_clack(self, force): 
        ch = pygame.mixer.find_channel()
        if ch:
            ch.play(self.snd_clack)
            ch.set_volume(min(0.4, force * 0.05))

    def play_hover(self): self.ch_ui.play(self.snd_hover)
    def play_click(self): self.ch_ui.play(self.snd_click)
    def play_music(self): 
        if not self.ch_music.get_busy(): self.ch_music.play(self.snd_theme, loops=-1); self.ch_music.set_volume(0.25)
    def stop_music(self): self.ch_music.stop()

# --- Visual Effects & Geometry ---
class Starfield:
    def __init__(self, count=150, max_w=BASE_WIDTH, max_h=BASE_HEIGHT):
        self.max_h = max_h
        self.stars = [(random.randint(0, max_w), random.randint(0, max_h), random.uniform(0.5, 3.0)) for _ in range(count)]
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
        r_max = 140
        surf = pygame.Surface((r_max*2+40, r_max*2+40), pygame.SRCALPHA).convert_alpha()
        bx, by = r_max + 10, r_max + 15
        
        pygame.draw.ellipse(surf, (10, 15, 20, 100), (bx - r_max + 10, by - r_max + 15, r_max*2, r_max*2-20))
        for r in range(r_max, 75, -1):
            t = (r_max - r) / (r_max - 75)
            col = lerp_color((90, 95, 100), (140, 145, 150), t)
            pygame.draw.circle(surf, col, (int(bx), int(by)), r)
            
        pygame.draw.circle(surf, (60, 65, 70), (int(bx), int(by)), 80)
        for r in range(75, 40, -1):
            t = (75 - r) / 35.0
            col = lerp_color(HOUSE_RED, (140, 20, 30), t)
            pygame.draw.circle(surf, col, (int(bx), int(by)), r)
            
        draw_maple_leaf(surf, bx, by + 6, 1.25, WHITE)
        hx_start, hy_start, hx_end, hy_end = bx - 65, by + 35, bx + 65, by - 35
        for i in range(120):
            p = i / 120.0; px, py = hx_start + (hx_end - hx_start)*p, hy_start + (hy_end - hy_start)*p
            h_col = lerp_color(BLACK, (70, 75, 80), 1.0 - abs(p - 0.5)*2)
            pygame.draw.circle(surf, h_col, (int(px), int(py - math.sin(p*math.pi)*45)), 16) 
            pygame.draw.circle(surf, HOUSE_RED, (int(px), int(py - math.sin(p*math.pi)*45)), 12) 
        
        for x, y in [(hx_start, hy_start), (hx_end, hy_end)]:
            pygame.draw.circle(surf, BLACK, (int(x), int(y)), 18); pygame.draw.circle(surf, HOUSE_RED, (int(x), int(y)), 14)
        pygame.draw.circle(surf, BLACK, (int(hx_start), int(hy_start)), 5); pygame.draw.circle(surf, WHITE, (int(hx_start), int(hy_start)), 2)
        
        # PROPER 3D CRESCENT GLARE REFLECTION
        glare = pygame.Surface((r_max*2, r_max*2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(glare, (255, 255, 255, 80), (r_max, r_max), r_max - 5)
        inner_mask = pygame.Surface((r_max*2, r_max*2), pygame.SRCALPHA)
        pygame.draw.circle(inner_mask, (255, 255, 255, 255), (r_max, r_max + 12), r_max - 5)
        glare.blit(inner_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        surf.blit(glare, (bx - r_max, by - r_max))
        cls.cached_surf = surf

    def draw(self, surface, center_x, center_y, mouse_pos):
        bx, by = center_x + (mouse_pos[0] - center_x)*0.03, center_y + (mouse_pos[1] - center_y)*0.03
        if self.cached_surf: surface.blit(self.cached_surf, (bx - 150, by - 155))

# --- Game Entities ---
class Stone:
    # OPTIMIZATION: Cache full un-rotated bases to save 6000 Pygame calls per second.
    cached_red_base = None
    cached_ylw_base = None
    cached_hl = None

    def __init__(self, x, y, team):
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
            shade = 110 + int(60 * (1.0 - r / self.radius))
            pygame.draw.circle(s, (shade, shade+2, shade+5), (self.radius+5, self.radius+5), r)
            
        pygame.draw.circle(s, color, (self.radius+5, self.radius+5), self.radius-4, 4)
        
        glare = pygame.Surface((self.radius*2+15, self.radius*2+15), pygame.SRCALPHA).convert_alpha()
        pygame.draw.ellipse(glare, (255, 255, 255, 70), (self.radius-3, self.radius-9, self.radius*1.2, self.radius*0.6))
        s.blit(glare, (0, 0))
        
        return s

    def get_state(self): return [round(self.pos.x, 1), round(self.pos.y, 1), round(self.vel.x, 2), round(self.vel.y, 2), self.team, round(self.curl, 2), round(self.rotation, 1), self.is_moving]
    def set_state(self, state): self.pos.x, self.pos.y, self.vel.x, self.vel.y, self.team, self.curl, self.rotation, self.is_moving = state

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

        def head(x, y):
            ix, iy = int(x), int(y)
            head_rw, head_rh = 17, 22

            # Base head (Hair/Back of head)
            if not override_color:
                for r in range(20, 0, -1):
                    shade = max(0, min(255, 60 + r * 3))
                    px = int(ix - (20-r)*0.1)
                    py = int(iy - (20-r)*0.2)
                    rw = max(1, int((head_rw/20.0)*r))
                    rh = max(1, int((head_rh/20.0)*r))
                    # Brownish hair gradient
                    pygame.draw.ellipse(surface, (shade, int(shade*0.75), int(shade*0.55)), (px - rw, py - rh, rw*2, rh*2))
            else:
                pygame.draw.ellipse(surface, c((80, 50, 30)), (ix-head_rw, iy-head_rh, head_rw*2, head_rh*2))

            # Beanie Base
            hat_rw, hat_rh = 19, 14
            hat_shade = (max(0, self.tc[0]-80), max(0, self.tc[1]-80), max(0, self.tc[2]-80))
            
            # The beanie pulled down over the back of the head
            pygame.draw.ellipse(surface, c(hat_shade), (ix-hat_rw-1, iy-head_rh-6, hat_rw*2+2, hat_rh*2+2))
            pygame.draw.ellipse(surface, c(self.tc), (ix-hat_rw, iy-head_rh-5, hat_rw*2, hat_rh*2))

            if not override_color:
                specular = pygame.Surface((hat_rw*2, hat_rh*2), pygame.SRCALPHA)
                pygame.draw.ellipse(specular, (255, 255, 255, 40), (4, 2, hat_rw*2-8, 6))
                surface.blit(specular, (ix-hat_rw, iy-head_rh-5))

            # Beanie Brim (Curves across the back of the head)
            pygame.draw.rect(surface, c(hat_shade), (ix-hat_rw-2, iy-head_rh+4, hat_rw*2+4, 10), border_radius=4)
            pygame.draw.rect(surface, c(self.tc), (ix-hat_rw-1, iy-head_rh+5, hat_rw*2+2, 8), border_radius=3)
            pygame.draw.rect(surface, c(CYAN_ACCENT), (ix-hat_rw-1, iy-head_rh+7, hat_rw*2+2, 3), border_radius=1)

            # Pom-pom (Slightly shifted up for back perspective)
            if not override_color:
                for r in range(9, 0, -1):
                    s = 140 + r*11
                    pygame.draw.circle(surface, (s,s,s), (ix, iy-head_rh-9), r)
            else:
                pygame.draw.circle(surface, c((255, 255, 255)), (ix, iy-head_rh-9), 9)

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
            self.shadow_surf = pygame.Surface((500, 800), pygame.SRCALPHA).convert_alpha()
        self.shadow_surf.fill((0,0,0,0))
        self._draw_char_geometry(self.shadow_surf, 250+18, 500+18, oy, ld, (0,0,0,100))
        surface.blit(self.shadow_surf, (self.hack_pos.x - 250, self.hack_pos.y - 500))
        
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
        return (self.current_mapped_pos.x, self.current_mapped_pos.y)

    def get_pointer_pressed(self):
        return self.is_pointer_pressed

    def scale_mouse(self, pos):
        # Directly return pos as the new input loop provides absolute scaled FINGER coordinates
        if isinstance(pos, pygame.math.Vector2): return pos
        return pygame.math.Vector2(pos[0], pos[1])

    def preload_assets(self):
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 34)
        self.title_font = pygame.font.Font(None, 105)
        self.large_sym_font = pygame.font.Font(None, 96)
        
        self.BOT_LOGIC_CACHE = {
            "easy": {"error_multiplier": 2.5, "takeout_chance": 0.1, "guard_chance": 0.3},
            "medium": {"error_multiplier": 1.0, "takeout_chance": 0.4, "guard_chance": 0.5},
            "hard": {"error_multiplier": 0.2, "takeout_chance": 0.8, "guard_chance": 0.7}
        }
        
        # Pre-render rainbow text background
        self.rainbow_grad = pygame.Surface((1500, 200), pygame.SRCALPHA).convert_alpha()
        for x in range(1500):
            c = pygame.Color(0); c.hsva = ((x / 1000.0) * 360 % 360, 85, 100, 100)
            pygame.draw.line(self.rainbow_grad, c, (x, 0), (x, 200))

        t_text = '"WinCurl" 3'
        self.title_base = self.title_font.render(t_text, True, WHITE)
        self.title_shadow = pygame.Surface((self.title_base.get_width()+15, self.title_base.get_height()+15), pygame.SRCALPHA)
        for dx, dy in [(-4,-4), (4,-4), (-4,4), (4,4), (0,-5), (0,5), (-5,0), (5,0)]:
            self.title_shadow.blit(self.title_font.render(t_text, True, BLACK), (dx+5, dy+5))
            
        # Realistic Olympic Push Broom Rendering
        self.broom_surf = pygame.Surface((80, 260), pygame.SRCALPHA)
        pygame.draw.rect(self.broom_surf, (215, 215, 30), (35, 0, 10, 220), border_radius=4)
        pygame.draw.rect(self.broom_surf, (40, 40, 45), (20, 220, 40, 20), border_radius=4)
        pygame.draw.rect(self.broom_surf, (225, 225, 225), (10, 240, 60, 18), border_radius=6)
        pygame.draw.line(self.broom_surf, (150, 150, 150), (12, 248), (68, 248), 2)
            
        # MASSIVE ANDROID FPS BOOST: Pre-calculate 72 frames of spinning fractal
        if IS_ANDROID:
            self.fractal_frames = []
            base_fractal = pygame.Surface((800, 800), pygame.SRCALPHA).convert_alpha()
            self.draw_fractal_house(base_fractal, 400, 400, 220, 0, 3, 0)
            for deg in range(0, 360, 5):
                self.fractal_frames.append(pygame.transform.rotate(base_fractal, deg))

        # Pre-render coins for butter-smooth Android coin flip
        self.coin_red_surf = self._render_coin_surface(True)
        self.coin_yellow_surf = self._render_coin_surface(False)
        ThreeDStone.render_cache()
        
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
        pygame.display.init()
        pygame.display.set_caption("WinCurl version 3.0")
        
        try:
            em_font = pygame.font.SysFont("segoe ui emoji", 32)
            icon = em_font.render("🥌", True, HOUSE_RED)
            pygame.display.set_icon(icon)
        except:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(icon, (160, 165, 170), (16, 16), 14)
            pygame.draw.circle(icon, HOUSE_RED, (16, 16), 10)
            pygame.draw.line(icon, BLACK, (8, 16), (24, 16), 4)
            pygame.display.set_icon(icon)

        flags = pygame.DOUBLEBUF | pygame.RESIZABLE
        info = pygame.display.Info()
        
        if IS_ANDROID:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            desk_h = info.current_h
            if desk_h > 0 and 1800 > desk_h * 0.95:
                target_h = int(desk_h * 0.95)
                target_w = int(target_h * (BASE_WIDTH / BASE_HEIGHT))
                self.screen = pygame.display.set_mode((target_w, target_h), flags)
            else:
                self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), flags)
        
        self.is_4k = (info.current_w >= 3840 or info.current_h >= 2160)
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
        
        base_dir = os.path.dirname(os.path.abspath(__file__)) if IS_ANDROID else os.path.expanduser("~")
        self.save_file = os.path.join(base_dir, ".wincurl3_save.json")
        self.load_progress()
        
        self.house_pos = pygame.math.Vector2(BASE_WIDTH // 2, 350)
        self.hack_pos = pygame.math.Vector2(BASE_WIDTH // 2, BASE_HEIGHT - 150)
        self.curler_anim = AnimatedCurler(self.hack_pos)
        self.starfield = Starfield()
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
        self.btn_pause, self.btn_resume = pygame.Rect(BASE_WIDTH - 220, 140, 180, 60), pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2-100, 500, 100)
        self.btn_quit_main, self.btn_return_menu = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2+40, 500, 100), pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT-250, 500, 100)
        
        self.btn_fs = pygame.Rect(BASE_WIDTH - 280, 30, 250, 60)

        self.menu_buttons = [
            {"id": "local", "y": 480, "text": "Local 1v1", "color": HOUSE_RED, "scale": 1.0},
            {"id": "bot", "y": 600, "text": "Local vs Bot", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "chal", "y": 720, "text": "Challenge Mode", "color": PURPLE_SUIT, "scale": 1.0},
            {"id": "color", "y": 840, "text": "My Team:", "color": HOUSE_RED, "scale": 1.0},
            {"id": "name", "y": 960, "text": f"Name: {self.username}", "color": (130, 140, 155), "scale": 1.0},
            {"id": "host", "y": 1080, "text": "Host IRC", "color": HOUSE_BLUE, "scale": 1.0},
            {"id": "join", "y": 1200, "text": "Join IRC", "color": HOUSE_BLUE, "scale": 1.0},
            {"id": "exit", "y": 1320, "text": "Exit Game", "color": HOUSE_RED, "scale": 1.0}
        ]
        self.last_hovered = None

        self.bg_pebble_layer = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        for _ in range(12000):
            px, py = random.randint(0, BASE_WIDTH), random.randint(0, BASE_HEIGHT)
            pygame.draw.circle(self.bg_pebble_layer, (0, 0, 0, 50), (px+1, py+1), 1)
            pygame.draw.circle(self.bg_pebble_layer, (255, 255, 255, 100), (px, py), 1)
            
        self.fg_pebble_layer = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        for _ in range(8000): pygame.draw.circle(self.fg_pebble_layer, (255, 255, 255, random.randint(30, 90)), (random.randint(0, BASE_WIDTH), random.randint(0, BASE_HEIGHT)), 1)
        
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
        for r, c, w in [(210, HOUSE_BLUE, 0), (140, WHITE, 0), (70, HOUSE_RED, 0), (20, WHITE, 0), (20, BLACK, 2), (6, BLACK, 0), (2, WHITE, 0)]:
            pygame.draw.circle(self.static_ice_surface, c, (int(self.house_pos.x), int(self.house_pos.y)), r, w)
        self.static_ice_surface.blit(self.ice_env_map, (0, 0))
        self.static_ice_surface.blit(self.fg_pebble_layer, (0, 0))

        self.reset_match()

    def set_typing_target(self, target):
        self.typing_target = target
        if target is not None:
            try: pygame.key.start_text_input()
            except: pass
        else:
            try: pygame.key.stop_text_input()
            except: pass

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.audio.play_click()
        if IS_ANDROID:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            if self.is_fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
            else:
                self.screen = pygame.display.set_mode((1200, 1800), pygame.RESIZABLE | pygame.DOUBLEBUF)
        
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
        except:
            self.challenge_progress = [False] * 25; self.username = ""; self.preferred_color = 0; self.room_text = ""; self.ai_difficulty = 5; self.challenge_completed_seen = False

        if not self.username:
            firsts = ["John", "Sarah", "Mike", "Emily", "Dave", "Lisa", "Chris", "Anna", "Tom", "Jessica"]
            lasts = ["McSizzle", "Gigglesnort", "Beefcake", "Wobblebottom", "Cheeseweasel", "Bumblefluff", "Pancakes", "Noodlearm"]
            self.username = random.choice(firsts) + random.choice(lasts)
            self.save_progress()

    def save_progress(self):
        try:
            data = {"challenge": self.challenge_progress[:25], "username": self.username, "color": self.preferred_color, "room": self.room_text, "bot_skill": self.ai_difficulty, "challenge_completed_seen": getattr(self, 'challenge_completed_seen', False)}
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
            self.app_state = "COIN_TOSS"; self.coin_timer = 60; self.coin_flip_result = random.choice([0, 1])
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
            s = Stone(cx - 20, cy, 1); self.stones.append(s); self.challenge_takeout_target = s
            if level == 25: self.stones.append(Stone(cx + 40, cy + 100, 1)) 

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
                            self.audio.play_clack(impulse * 12); self.shake_amount = min(25.0, impulse * 4.0)
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
        self.stones_thrown[1] += 1; self.total_stones_played += 1; self.turn_state = "SLIDING"

    def fire_stone(self):
        if getattr(self, 'pull_history', []):
            avg_x = sum(p.x for p in self.pull_history) / len(self.pull_history)
            avg_y = sum(p.y for p in self.pull_history) / len(self.pull_history)
            self.virtual_pull = pygame.math.Vector2(avg_x, avg_y)

        pull = pygame.math.Vector2(-self.virtual_pull.x, -self.virtual_pull.y)
        if abs(pull.x) < 3.5: 
            pull.x = 0
            
        if pull.length() > 5 and pull.y < 0:
            self.active_stone.vel = pull.normalize() * min(42.0, pull.length() / 10.0) 
            self.active_stone.curl = self.selected_curl; self.active_stone.is_moving = True
            self.stones_thrown[self.current_team] += 1; self.total_stones_played += 1; self.turn_state = "SLIDING"
            self.curler_anim.update("LUNGING"); self.audio.play_throw()
            if self.game_mode in ["HOST", "JOIN"]: self.net.send_action({'cmd': 'shoot', 'vx': self.active_stone.vel.x, 'vy': self.active_stone.vel.y, 'c': self.selected_curl})
        else: self.curler_anim.update("IDLE")
        self.is_dragging = False; self.virtual_pull = pygame.math.Vector2(0, 0)
        self.drag_start_pos = None
        self.drag_finger_id = None
        self.pull_history = []

    def advance_end_logic(self):
        if self.game_mode == "CHALLENGE":
            if getattr(self, 'challenge_success', False) or self.challenge_attempts >= 3: 
                if getattr(self, 'challenge_success', False): self.challenge_progress[self.challenge_level-1] = True; self.save_progress()
                
                start_lvl = self.challenge_level
                while True:
                    self.challenge_level = (self.challenge_level % 25) + 1
                    if not self.challenge_progress[self.challenge_level-1] or self.challenge_level == start_lvl:
                        break
                self.challenge_attempts = 0
            if all(self.challenge_progress[:25]) and not getattr(self, 'challenge_completed_seen', False): 
                if self.app_state != "MATCH_OVER":
                    self.app_state = "MATCH_OVER"
                    self.audio.play_cheer()
                    if not getattr(self, 'challenge_announced', False):
                        self.audio.ch_voice.play(self.audio.snd_chal_comp)
                        self.challenge_announced = True
                    self.challenge_completed_seen = True
                    self.save_progress()
            else: self.load_challenge(self.challenge_level)
            return

        self.current_end += 1
        if self.current_end > 8: 
            self.app_state = "MATCH_OVER"
            self.audio.play_cheer()
            
            r_tot, y_tot = sum(self.score[0]), sum(self.score[1])
            if r_tot > y_tot: self.audio.ch_voice.play(self.audio.snd_red_wins)
            elif y_tot > r_tot: self.audio.ch_voice.play(self.audio.snd_ylw_wins)
            else: self.audio.ch_voice.play(self.audio.snd_end_match)
        else: self.reset_end()

    def handle_menu_events(self, event):
        mouse_pos = getattr(event, 'pos', self.scale_mouse(self.get_pointer_pos()))
        mx, my = mouse_pos[0] if isinstance(mouse_pos, tuple) else mouse_pos.x, mouse_pos[1] if isinstance(mouse_pos, tuple) else mouse_pos.y
        curr_hov = next((b["id"] for b in self.menu_buttons if 300<mx<900 and b["y"]<my<b["y"]+110*b["scale"]), None)
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
                if not (300 < mx < 900 and 1000 < my < 1200):
                    self.set_typing_target(None)

            if 300 < mx < 900:
                for b in self.menu_buttons:
                    if b["y"] < my < b["y"] + 110 * b["scale"]:
                        self.audio.play_click(); self.set_typing_target(None)
                        if b["id"] == "local": self.game_mode = "LOCAL"; self.audio.stop_music(); self.start_match()
                        elif b["id"] == "bot": self.game_mode = "BOT"; self.audio.stop_music(); self.start_match()
                        elif b["id"] == "chal": self.app_state = "CHALLENGE_MENU"
                        elif b["id"] in ["host", "join"]:
                            self.app_state = "ROOM_PROMPT"; self.set_typing_target("room"); self.net_action = b["id"]
                        elif b["id"] == "name": self.set_typing_target("name")
                        elif b["id"] == "color": self.preferred_color = 1 if self.preferred_color == 0 else 0; self.save_progress()
                        elif b["id"] == "exit": self.net.close(); pygame.quit(); sys.exit()
                        break
            
            if 330 < mx < 870 and 1450 < my < 1650: 
                self.ai_difficulty = int(1 + max(0.0, min(1.0, (mx-350)/500.0))*9)
                self.audio.play_hover()
                self.save_progress()
        elif event.type == MOUSEMOTION and self.get_pointer_pressed():
            if 330 < mx < 870 and 1450 < my < 1650: 
                self.ai_difficulty = int(1 + max(0.0, min(1.0, (mx-350)/500.0))*9)
                self.dragging_slider = True
        elif event.type == KEYDOWN and self.typing_target == "name":
            if event.key == K_RETURN: self.set_typing_target(None); self.save_progress()
            elif event.key == K_BACKSPACE: self.username = self.username[:-1]
            elif event.unicode.isprintable() and len(self.username) < 15: self.username += event.unicode

    def handle_room_prompt_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.scale_mouse(self.get_pointer_pos())); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
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
            elif event.unicode.isprintable() and len(self.room_text) < 15: self.room_text += event.unicode

    def handle_challenge_menu_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.scale_mouse(self.get_pointer_pos())); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_return_menu.collidepoint(mx, my): self.audio.play_click(); self.app_state = "MENU"; return
            for i in range(25):
                row, col = i // 5, i % 5; rect = pygame.Rect(BASE_WIDTH//2 - 250 + col*100, 300 + row*100, 90, 90)
                if rect.collidepoint(mx, my):
                    self.audio.play_click(); self.game_mode = "CHALLENGE"; self.challenge_level = i+1
                    self.audio.stop_music(); self.start_match(); return

    def handle_pause_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.scale_mouse(self.get_pointer_pos())); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_resume.collidepoint(mx, my): self.audio.play_click(); self.app_state = "PLAY"
            elif self.btn_quit_main.collidepoint(mx, my): self.audio.play_click(); self.return_to_menu()
                
    def handle_match_over_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.scale_mouse(self.get_pointer_pos())); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.return_to_menu()

    def handle_play_events(self, event):
        mouse_pos = getattr(event, 'pos', self.scale_mouse(self.get_pointer_pos()))
        if isinstance(mouse_pos, tuple): mouse_pos = pygame.math.Vector2(mouse_pos)
        f_id = getattr(event, 'finger_id', 'mouse')
        
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', 1) == 1 and self.is_dragging:
            if getattr(self, 'drag_finger_id', None) == f_id:
                self.fire_stone()
            return

        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1 and self.btn_pause.collidepoint(mouse_pos.x, mouse_pos.y):
            self.audio.play_click(); self.app_state = "PAUSED"; self.pause_anim = 0.0; self.audio.update_slide(0.0); self.audio.update_sweep(0.0); return
        
        if self.turn_state == "END":
            if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1 and self.btn_next_end.collidepoint(mouse_pos.x, mouse_pos.y): self.advance_end_logic()
            elif event.type == KEYDOWN and event.key == K_SPACE: self.advance_end_logic()
            return

        has_control = (self.game_mode in ["LOCAL", "CHALLENGE"]) or (self.game_mode == "BOT" and self.current_team == self.preferred_color) or (self.game_mode == "HOST" and self.current_team == self.preferred_color) or (self.game_mode == "JOIN" and self.current_team != self.preferred_color)

        if not has_control: return

        if self.turn_state == "AIMING":
            if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
                if self.btn_curl_l.collidepoint(mouse_pos.x, mouse_pos.y): self.selected_curl = max(-1.0, self.selected_curl - 0.2); self.audio.play_hover()
                elif self.btn_curl_r.collidepoint(mouse_pos.x, mouse_pos.y): self.selected_curl = min(1.0, self.selected_curl + 0.2); self.audio.play_hover()
                elif (mouse_pos - self.active_stone.pos).length() < 90 and not self.is_dragging: 
                    self.is_dragging = True
                    self.drag_start_pos = mouse_pos
                    self.drag_finger_id = f_id
                    self.pull_history = []
                    self.virtual_pull = pygame.math.Vector2(0, 0)
            elif event.type == MOUSEMOTION and self.is_dragging and getattr(self, 'drag_start_pos', None):
                if f_id == getattr(self, 'drag_finger_id', None):
                    self.virtual_pull = self.drag_start_pos - mouse_pos
                    self.pull_history.append(pygame.math.Vector2(self.virtual_pull))
                    if len(self.pull_history) > 5: self.pull_history.pop(0)
            elif event.type == MOUSEWHEEL: self.selected_curl = max(-1.0, min(1.0, self.selected_curl + event.y * 0.2))

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
            mouse_pos = self.scale_mouse(self.get_pointer_pos())
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
                actual_sweep = self.sweep_power if can_player_sweep and (s.team == my_team or s.pos.y < self.house_pos.y) else 0.0
                s.update(actual_sweep, FRICTION_BASE)
                if s.is_moving and s.vel.length() > 0.5: self.particles.append({'pos': s.pos + pygame.math.Vector2(random.uniform(-15, 15), random.uniform(-15, 15)), 'vel': s.vel * -0.1, 'life': 1.0, 'decay': random.uniform(0.01, 0.03), 'type': 'trail'})
            
            if self.game_mode in ["HOST", "JOIN"] and self.frames_elapsed % 3 == 0: self.net.send_action({'cmd': 'sweep', 'p': round(self.sweep_power, 2)})
            
            self.sweep_power *= 0.86; self.audio.update_sweep(self.sweep_power)
            
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
                
                # Absolute End of Slide Sync Broadcast for Netcode
                if self.game_mode == "HOST" and hasattr(self, 'was_moving_last_frame') and self.was_moving_last_frame:
                    self.net.send_action({'cmd': 'sync_state', 'stones': [s.get_state() for s in self.stones]})

                valid_stones_final = []
                hog_line_y = self.house_pos.y + 400
                back_line_y = self.house_pos.y - 210
                for s in self.stones:
                    if s.pos.y - s.radius < hog_line_y and s.pos.y + s.radius > back_line_y:
                        valid_stones_final.append(s)
                self.stones = valid_stones_final
                
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
                        elif self.c_type == "DOUBLE": self.challenge_success = len([s for s in self.stones if s.team == 1]) == 0 and any(s.team == 0 and (pygame.math.Vector2(s.pos) - pygame.math.Vector2(cx, cy)).length() <= 210 for s in self.stones)
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
        self.last_mouse_pos = self.scale_mouse(self.get_pointer_pos())

    def update_network(self):
        if self.game_mode not in ["HOST", "JOIN"]: return
        if self.app_state == "MENU" and self.net.matched:
            self.app_state = "COIN_TOSS"; self.coin_timer = 60; self.coin_flip_result = random.choice([0, 1]) if self.game_mode == "HOST" else -1
            self.audio.stop_music(); self.audio.play_cheer()
            
        data = self.net.receive_action()
        if data:
            if data.get('cmd') == 'chat':
                self.chat_messages.append({"text": f"{self.net.opponent.split('!')[0]}: {data['msg']}", "time": pygame.time.get_ticks()})
            elif data.get('cmd') == 'coin' and self.game_mode == "JOIN": self.coin_flip_result = data['result']
            elif data.get('cmd') == 'shoot':
                self.active_stone.vel = pygame.math.Vector2(data['vx'], data['vy']); self.active_stone.curl = data['c']; self.active_stone.is_moving = True
                self.stones_thrown[self.current_team] += 1; self.total_stones_played += 1; self.turn_state = "SLIDING"; self.audio.play_throw()
            elif data.get('cmd') == 'sweep': self.sweep_power = data['p']
            elif data.get('cmd') == 'sync_state' and self.game_mode == "JOIN":
                for i, s_data in enumerate(data['stones']):
                    if i < len(self.stones): self.stones[i].set_state(s_data)
            elif data.get('cmd') == 'sync' and self.game_mode == "JOIN":
                self.turn_state = data['st']; self.current_team = data['t']; self.score = {int(k): v for k, v in data['sc'].items()}
                if len(data['s']) > len(self.stones): self.spawn_next_stone()
                for i, s_data in enumerate(data['s']):
                    if i < len(self.stones): self.stones[i].set_state(s_data)
            elif data.get('cmd') == 'set_color':
                self.preferred_color = 1 - data['color']
            elif data.get('cmd') == 'opponent_left':
                self.app_state = "MATCH_OVER"
                self.winner_text = "Opponent Disconnected"
                self.audio.play_cheer()
                
        if self.game_mode == "HOST" and self.app_state == "COIN_TOSS" and self.coin_timer == 50: self.net.send_action({'cmd': 'coin', 'result': self.coin_flip_result})
        elif self.game_mode == "HOST" and self.app_state == "PLAY" and getattr(self, 'turn_state', 'MENU') == "SLIDING" and self.frames_elapsed % 60 == 0: 
            self.net.send_action({'cmd': 'sync', 'st': self.turn_state, 't': self.current_team, 'sc': self.score, 's': [s.get_state() for s in self.stones]})

    def draw_fractal_house(self, surf, x, y, radius, depth, max_depth, morph_time):
        if depth > max_depth or radius < 8: return
        color = [HOUSE_BLUE, HOUSE_RED, TEAM_YELLOW, WHITE][depth % 4]
        pygame.draw.circle(surf, color, (int(x), int(y)), int(radius)); pygame.draw.circle(surf, color, (int(x), int(y)), int(radius), max(1, 6 - depth))
        for i in range(3):
            angle = (i * (2 * math.pi / 3)) + (morph_time * 0.25) + (depth * 0.5)
            self.draw_fractal_house(surf, x + math.cos(angle)*(radius*1.25), y + math.sin(angle)*(radius*1.25), radius*0.44, depth+1, max_depth, morph_time)

    def draw_menu(self):
        self.canvas.fill((10, 12, 16, 0))
        self.canvas.set_colorkey((10, 12, 16))
        self.starfield.draw(self.canvas, 2.0); cx, t_ms = BASE_WIDTH//2, pygame.time.get_ticks() * 0.001

        if IS_ANDROID:
            frame_idx = int((pygame.time.get_ticks() * 0.028) % 72)
            rotated_fractal = self.fractal_frames[frame_idx]
            self.canvas.blit(rotated_fractal, (cx - rotated_fractal.get_width()//2, 300 - rotated_fractal.get_height()//2))
        else:
            self.draw_fractal_house(self.canvas, cx, 300, 220, 0, 3, t_ms)
            
        self.menu_stone.draw(self.canvas, cx, 300, self.get_pointer_pos())
        
        bx, by = cx - self.title_base.get_width()//2, 80 + int(math.sin(t_ms * 4.0) * 15) 
        self.canvas.blit(self.title_shadow, (bx-5, by-5))
        
        if not hasattr(self, 'title_grad_surf'):
            self.title_grad_surf = pygame.Surface(self.title_base.get_size(), pygame.SRCALPHA).convert_alpha()
            
        self.title_grad_surf.fill((0,0,0,0))
        offset = int(t_ms * 100) % 500
        self.title_grad_surf.blit(self.rainbow_grad, (-offset, 0))
        self.title_grad_surf.blit(self.title_base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.canvas.blit(self.title_grad_surf, (bx, by))
        
        status_string = "STATUS: Connecting to Network..." if self.net.connecting else "STATUS: Match Found!" if self.net.matched else f"STATUS: Hosting {self.net.room_display}... Waiting." if getattr(self.net, 'is_host', False) and self.net.running else "STATUS: Offline Ready"
        lbl_status = self.small_font.render(status_string, True, (140, 165, 200)); self.canvas.blit(lbl_status, (cx - lbl_status.get_width()//2, 210))

        for btn in self.menu_buttons:
            if btn["id"] == "name": text = f"Name: {self.username}" + ("_" if self.typing_target == "name" else "")
            elif btn["id"] == "color": 
                btn["color"] = TEAM_YELLOW if self.preferred_color else HOUSE_RED
                text = "My Team:"
            else: text = btn["text"]
            
            is_hovered = (self.last_hovered == btn["id"])
            btn["scale"] += ((1.07 if is_hovered else 1.0) - btn["scale"]) * 0.25 
            b_w, b_h = int(600 * btn["scale"]), int(100 * btn["scale"])
            rect = pygame.Rect(cx - b_w//2, btn["y"] + (100 - b_h)//2, b_w, b_h)
            
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
                self.canvas.blit(img, img.get_rect(center=rect.center))

        pygame.draw.rect(self.canvas, (80, 95, 115), (cx - 250, 1550, 500, 16), border_radius=8)
        handle_x = cx - 250 + int((self.ai_difficulty - 1) / 9.0 * 500)
        pygame.draw.circle(self.canvas, TEAM_YELLOW, (int(handle_x), 1558), 26); pygame.draw.circle(self.canvas, WHITE, (int(handle_x), 1558), 26, 4)
        diff_lbl = self.font.render(f"BOT DIFFICULTY: {self.ai_difficulty}", True, WHITE); self.canvas.blit(diff_lbl, (cx - diff_lbl.get_width()//2, 1490))
        
        self.draw_global_ui()

    def draw_room_prompt(self):
        self.draw_menu()
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha(); overlay.fill((0, 0, 0, 200)); self.canvas.blit(overlay, (0, 0))
        cx, cy = BASE_WIDTH//2, BASE_HEIGHT//2
        
        lbl_v = pygame.font.Font(None, 62).render("ENTER MATCHMAKING ROOM NAME", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, cy - 150))
        
        draw_glass_rect(self.canvas, self.prompt_rect, HOUSE_BLUE, self.prompt_rect.h // 2)
        txt = f"{self.room_text}_"
        img = self.font.render(txt, True, WHITE); self.canvas.blit(img, img.get_rect(center=(cx, cy + 10)))
        
        if IS_ANDROID: sub = self.small_font.render("Tap here to connect | Tap outside to cancel", True, (150, 160, 180))
        else: sub = self.small_font.render("Press ENTER to connect | ESC to cancel", True, (150, 160, 180))
        self.canvas.blit(sub, (cx - sub.get_width()//2, cy + 120))
        self.draw_global_ui()

    def draw_challenge_menu(self):
        self.canvas.fill((10, 12, 16)); self.starfield.draw(self.canvas, 2.0); cx = BASE_WIDTH // 2
        lbl_v = pygame.font.Font(None, 72).render("SELECT CHALLENGE", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, 120))
        
        for i in range(25):
            row, col = i // 5, i % 5; rect = pygame.Rect(cx - 250 + col*100, 300 + row*100, 90, 90)
            is_hov = rect.collidepoint(self.scale_mouse(self.get_pointer_pos()))
            draw_glass_rect(self.canvas, rect, (40, 120, 60) if self.challenge_progress[i] else PURPLE_SUIT, 16, is_hov)
            txt = self.font.render(str(i+1), True, WHITE); self.canvas.blit(txt, txt.get_rect(center=rect.center))
            if self.challenge_progress[i]: pygame.draw.line(self.canvas, HOUSE_RED, rect.topleft, rect.bottomright, 8)
            
        draw_glass_rect(self.canvas, self.btn_return_menu, HOUSE_BLUE, self.btn_return_menu.h // 2, self.btn_return_menu.collidepoint(self.scale_mouse(self.get_pointer_pos())))
        lbl_btn = self.font.render("BACK TO MENU", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))
        self.draw_global_ui()

    def draw_coin_toss_screen(self):
        self.draw_ice()
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha(); overlay.fill((0, 0, 0, 150)); self.canvas.blit(overlay, (0, 0))
        cx, cy, t = BASE_WIDTH//2, BASE_HEIGHT//2, 60 - self.coin_timer; scale_x = abs(math.cos(t * 0.3))
        
        if self.coin_timer > 15:
            is_red = (t // 5) % 2 == 0; text = "FLIPPING FOR HAMMER..."
        else:
            is_red = self.coin_flip_result == 0; text = "RED GETS HAMMER" if is_red else "YELLOW GETS HAMMER"
            
        if scale_x > 0.05: 
            c_surf = self.coin_red_surf if is_red else self.coin_yellow_surf
            w, h = c_surf.get_size()
            scaled = pygame.transform.scale(c_surf, (max(1, int(w * scale_x)), h))
            self.canvas.blit(scaled, (cx - scaled.get_width()//2, cy - h//2))
            
        lbl = self.font.render(text, True, WHITE); self.canvas.blit(lbl, (cx - lbl.get_width()//2, cy + 150))

    def draw_pause_icon(self, surface, x, y):
        pygame.draw.rect(surface, WHITE, (x, y, 8, 24), border_radius=2)
        pygame.draw.rect(surface, WHITE, (x + 14, y, 8, 24), border_radius=2)

    def draw_ice(self):
        self.canvas.blit(self.static_ice_surface, (0, 0))
        
        if self.game_mode == "CHALLENGE" and self.challenge_target:
            cx, cy, cr = self.challenge_target
            pygame.draw.circle(self.canvas, (0, 255, 100, 150), (int(cx), int(cy)), int(cr + ((math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5)*10), 4)
        
        pygame.draw.rect(self.canvas, BLACK, (self.hack_pos.x - 65, self.hack_pos.y + 35, 130, 25), border_radius=6)

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
            self.canvas.blit(self.font.render("RED", True, HOUSE_RED), (30, 15)); self.canvas.blit(self.font.render("YLW", True, TEAM_YELLOW), (30, 65))
            
            rem_r = self.stones_per_team - self.stones_thrown[0]
            rem_y = self.stones_per_team - self.stones_thrown[1]
            for i in range(rem_r): pygame.draw.circle(self.canvas, HOUSE_RED, (120 + i*18, 30), 6)
            for i in range(rem_y): pygame.draw.circle(self.canvas, TEAM_YELLOW, (120 + i*18, 80), 6)
            
            spacing = min(80, (BASE_WIDTH - 420) // 8)
            for e in range(1, 9):
                cx = 200 + (e * spacing); self.canvas.blit(self.small_font.render(str(e), True, (140, 150, 165)), (cx, 8))
                self.canvas.blit(self.font.render(str(self.score[0][e-1]) if e < self.current_end or (e == self.current_end and self.turn_state == "END") else "-", True, WHITE), (cx, 38))
                self.canvas.blit(self.font.render(str(self.score[1][e-1]) if e < self.current_end or (e == self.current_end and self.turn_state == "END") else "-", True, WHITE), (cx, 76))

            tot_x = 200 + (8 * spacing) + 80; pygame.draw.line(self.canvas, (80, 90, 105), (tot_x - 40, 0), (tot_x - 40, 130), 2)
            self.canvas.blit(self.small_font.render("TOT", True, WHITE), (tot_x, 8))
            self.canvas.blit(self.font.render(str(sum(self.score[0])), True, HOUSE_RED), (tot_x, 38)); self.canvas.blit(self.font.render(str(sum(self.score[1])), True, TEAM_YELLOW), (tot_x, 76))
            if getattr(self, 'hammer_team', 0) == 0: draw_hammer_icon(self.canvas, tot_x + 65, 48, HOUSE_RED)
            elif getattr(self, 'hammer_team', 0) == 1: draw_hammer_icon(self.canvas, tot_x + 65, 86, TEAM_YELLOW)

        for p in self.particles:
            if p['type'] == 'spark': pygame.draw.circle(self.canvas, lerp_color((255, 200, 50), ICE_COLOR, 1.0-p['life']), (int(p['pos'].x), int(p['pos'].y)), int(p['life']*4))
            elif p['type'] == 'trail': pygame.draw.circle(self.canvas, lerp_color(WHITE, ICE_COLOR, 1.0-p['life']), (int(p['pos'].x), int(p['pos'].y)), int(p['life']*6))
            elif p['type'] == 'sweep': pygame.draw.circle(self.canvas, lerp_color((200, 240, 255), ICE_COLOR, 1.0-p['life']), (int(p['pos'].x), int(p['pos'].y)), int(p['life']*5))

        m_pos = self.scale_mouse(self.get_pointer_pos())
        draw_glass_rect(self.canvas, self.btn_pause, (50, 55, 65), self.btn_pause.h // 2, self.btn_pause.collidepoint(m_pos.x, m_pos.y))
        
        self.draw_pause_icon(self.canvas, self.btn_pause.centerx - 40, self.btn_pause.centery - 12)
        lbl_p = self.small_font.render("PAUSE", True, WHITE)
        self.canvas.blit(lbl_p, (self.btn_pause.centerx - 8, self.btn_pause.centery - lbl_p.get_height()//2))

        # Netcode Chat Render Support
        if self.game_mode in ["HOST", "JOIN"]:
            current_time = pygame.time.get_ticks()
            y_offset = BASE_HEIGHT - 450
            for c_msg in self.chat_messages[-5:]:
                age = current_time - c_msg['time']
                if age < 8000:
                    alpha = 255 if age < 6000 else int(255 * (1.0 - (age - 6000)/2000.0))
                    txt_surf = self.small_font.render(c_msg['text'], True, PURPLE_SUIT)
                    txt_surf.set_alpha(alpha)
                    self.canvas.blit(txt_surf, (50, y_offset))
                    y_offset += 40
                    
            if self.typing_chat:
                txt_surf = self.small_font.render("Chat: " + self.chat_input + "_", True, HOUSE_RED)
                self.canvas.blit(txt_surf, (50, BASE_HEIGHT - 100))
                
            if self.net.matched and getattr(self.net, 'opponent', None):
                opp_surf = self.small_font.render(f"VS: {self.net.opponent.split('!')[0]}", True, BLACK)
                self.canvas.blit(opp_surf, (BASE_WIDTH - 500, 150))

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
                pull = pygame.math.Vector2(-self.virtual_pull.x, -self.virtual_pull.y)
                if pull.length() > 5:
                    spos, svel = pygame.math.Vector2(self.active_stone.pos), pull.normalize() * min(42.0, pull.length() / 10.0)
                    for i in range(140):
                        if svel.length() <= FRICTION_BASE: break
                        svel.scale_to_length(svel.length() - FRICTION_BASE)
                        if svel.length() > 0.4: svel.rotate_ip((1.4 / svel.length()) * self.selected_curl * 0.05)
                        spos += svel
                        if i % 5 == 0: pygame.draw.circle(self.canvas, (HOUSE_RED if self.current_team == 0 else HOUSE_BLUE), (int(spos.x), int(spos.y)), 6)
            self.canvas.blit(self.small_font.render(f"CURL BIAS: {self.selected_curl:+.1f}", True, BLACK), (self.hack_pos.x - 130, self.hack_pos.y - 80))
            
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
        self.starfield.draw(self.canvas, 0.5 * self.pause_anim)
        m_pos = self.scale_mouse(self.get_pointer_pos())
        
        lbl_p = pygame.font.Font(None, 85).render("PAUSED", True, WHITE)
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
            lbl_v = pygame.font.Font(None, 72).render("CHALLENGES COMPLETED!", True, TEAM_YELLOW)
            self.canvas.blit(lbl_v, (cx - lbl_v.get_width()//2, 180))
        else:
            r_tot, y_tot = sum(self.score[0]), sum(self.score[1])
            o_txt, o_col = ("RED TEAM WINS!", HOUSE_RED) if r_tot > y_tot else ("YELLOW TEAM WINS!", TEAM_YELLOW) if y_tot > r_tot else ("TIE MATCH!", WHITE)
            lbl_victory = pygame.font.Font(None, 72).render(o_txt, True, o_col); self.canvas.blit(lbl_victory, (cx - lbl_victory.get_width()//2, 180))
            
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
            
        m_pos = self.scale_mouse(self.get_pointer_pos())
        draw_glass_rect(self.canvas, self.btn_return_menu, HOUSE_BLUE, self.btn_return_menu.h // 2, self.btn_return_menu.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("MAIN MENU", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

    def draw_global_ui(self):
        if not IS_ANDROID:
            m_pos = self.scale_mouse(self.get_pointer_pos())
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
        
        if getattr(self, 'is_4k', False):
            self.border_starfield.draw(self.screen, 0.5)
        
        if IS_ANDROID:
            self.screen.blit(pygame.transform.scale(self.canvas, (sw, sh)), (ox, oy))
        else:
            self.screen.blit(pygame.transform.smoothscale(self.canvas, (sw, sh)), (ox, oy))
            
        pygame.display.flip()

    def run(self):
        while True:
            self.frames_elapsed += 1
            for event in pygame.event.get():
                if event.type == QUIT: self.net.close(); pygame.quit(); sys.exit()
                
                if event.type in (FINGERDOWN, FINGERMOTION, FINGERUP):
                    # FINGER ABSOLUTE MAPPING BYPASS FIX FOR ANDROID SCREEN SHIFT
                    ww, wh = self.screen.get_size()
                    scale = min(ww / BASE_WIDTH, wh / BASE_HEIGHT)
                    sw, sh = int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale)
                    ox, oy = (ww - sw) // 2, (wh - sh) // 2
                    
                    raw_px, raw_py = event.x * pygame.display.Info().current_w, event.y * pygame.display.Info().current_h
                    
                    if not hasattr(self, 'global_touch_offset_x'): self.global_touch_offset_x = 0
                    if not hasattr(self, 'global_touch_offset_y'): self.global_touch_offset_y = 0
                    
                    px = raw_px - self.global_touch_offset_x
                    py = raw_py - self.global_touch_offset_y
                    
                    mx = (px - ox) / scale if scale > 0 else px
                    my = (py - oy) / scale if scale > 0 else py
                    self.current_mapped_pos = pygame.math.Vector2(mx, my)
                    
                    if event.type == FINGERDOWN: 
                        self.last_raw_finger_x = raw_px
                        self.last_raw_finger_y = raw_py
                        self.current_mapped_pos = pygame.math.Vector2(mx, my)
                        self.is_pointer_pressed = True
                        event = pygame.event.Event(MOUSEBUTTONDOWN, button=1, pos=self.current_mapped_pos, finger_id=event.finger_id)
                    elif event.type == FINGERUP: 
                        self.is_pointer_pressed = False
                        event = pygame.event.Event(MOUSEBUTTONUP, button=1, pos=self.current_mapped_pos, finger_id=event.finger_id)
                    elif event.type == FINGERMOTION:
                        event = pygame.event.Event(MOUSEMOTION, buttons=(1,0,0), pos=self.current_mapped_pos, finger_id=event.finger_id)
                        
                elif event.type in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
                    if IS_ANDROID and event.type == MOUSEBUTTONDOWN and hasattr(self, 'last_raw_finger_x') and not getattr(self, 'is_calibrated', False):
                        if abs(self.last_raw_finger_x - event.pos[0]) < 250 and abs(self.last_raw_finger_y - event.pos[1]) < 250:
                            self.global_touch_offset_x = self.last_raw_finger_x - event.pos[0]
                            self.global_touch_offset_y = self.last_raw_finger_y - event.pos[1]
                            self.is_calibrated = True
                        
                    ww, wh = self.screen.get_size(); scale = min(ww/BASE_WIDTH, wh/BASE_HEIGHT)
                    ox, oy = (ww - int(BASE_WIDTH * scale)) // 2, (wh - int(BASE_HEIGHT * scale)) // 2
                    mx = (event.pos[0] - ox) / scale if scale > 0 else event.pos[0]
                    my = (event.pos[1] - oy) / scale if scale > 0 else event.pos[1]
                    self.current_mapped_pos = pygame.math.Vector2(mx, my)
                    if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1: self.is_pointer_pressed = True
                    elif event.type == MOUSEBUTTONUP and getattr(event, 'button', 1) == 1: self.is_pointer_pressed = False
                    
                    if event.type == MOUSEMOTION:
                        event = pygame.event.Event(event.type, buttons=getattr(event, 'buttons', (1,0,0)), pos=self.current_mapped_pos, finger_id='mouse')
                    else:
                        event = pygame.event.Event(event.type, button=getattr(event, 'button', 1), pos=self.current_mapped_pos, finger_id='mouse')

                if event.type == VIDEORESIZE and not self.is_fullscreen and not IS_ANDROID:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                
                if event.type == KEYDOWN:
                    if self.app_state == "PLAY" and self.game_mode in ["HOST", "JOIN"]:
                        if self.typing_chat:
                            if event.key == K_RETURN:
                                if self.chat_input.strip():
                                    self.net.send_action({'cmd': 'chat', 'msg': self.chat_input})
                                    self.chat_messages.append({"text": f"Me: {self.chat_input}", "time": pygame.time.get_ticks()})
                                self.typing_chat = False
                                self.chat_input = ""
                            elif event.key == K_BACKSPACE:
                                self.chat_input = self.chat_input[:-1]
                            elif event.unicode.isprintable() and len(self.chat_input) < 30:
                                self.chat_input += event.unicode
                            continue
                        else:
                            if event.key == K_t or event.key == K_RETURN:
                                self.typing_chat = True
                                continue

                    if event.key == K_ESCAPE:
                        if self.app_state == "PLAY":
                            self.audio.play_click(); self.app_state = "PAUSED"; self.pause_anim = 0.0; self.audio.update_slide(0.0); self.audio.update_sweep(0.0)
                        elif self.app_state == "PAUSED":
                            self.audio.play_click(); self.app_state = "PLAY"
                        elif self.app_state == "ROOM_PROMPT":
                            self.app_state = "MENU"; self.set_typing_target(None)
                        continue
                    elif event.key == K_f:
                        if not IS_ANDROID: self.toggle_fullscreen()
                        continue
                    
                if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
                    m_pos = self.scale_mouse(self.get_pointer_pos())
                    if self.app_state in ["MENU", "CHALLENGE_MENU", "ROOM_PROMPT", "MATCH_OVER"]:
                        if not IS_ANDROID and self.btn_fs.collidepoint(m_pos.x, m_pos.y):
                            self.toggle_fullscreen()
                            continue
                
                if self.app_state == "MENU": self.handle_menu_events(event)
                elif self.app_state == "ROOM_PROMPT": self.handle_room_prompt_events(event)
                elif self.app_state == "CHALLENGE_MENU": self.handle_challenge_menu_events(event)
                elif self.app_state == "PLAY": self.handle_play_events(event)
                elif self.app_state == "PAUSED": self.handle_pause_events(event)
                elif self.app_state == "MATCH_OVER": self.handle_match_over_events(event)

            if self.app_state == "MENU": self.update_network(); self.audio.play_music(); self.draw_menu()
            elif self.app_state == "ROOM_PROMPT": self.draw_room_prompt()
            elif self.app_state == "CHALLENGE_MENU": self.draw_challenge_menu()
            elif self.app_state == "COIN_TOSS":
                self.coin_timer -= 1
                if self.coin_timer <= 0:
                    self.stones_thrown = {0: 0, 1: 0}
                    self.score = {0: [0]*8, 1: [0]*8}
                    self.current_end = 1
                    self.total_stones_played = 0
                    self.hammer_team = self.coin_flip_result
                    self.app_state = "PLAY"; self.reset_end()
                else: self.draw_coin_toss_screen()
            elif self.app_state == "PLAY":
                self.update_network(); self.update_physics(); self.draw_ice(); [s.draw(self.canvas) for s in self.stones]
                self.curler_anim.draw(self.canvas, HOUSE_RED if self.current_team == 0 else TEAM_YELLOW); self.draw_ui()
            elif self.app_state == "PAUSED": 
                self.draw_ice(); [s.draw(self.canvas) for s in self.stones]; self.curler_anim.draw(self.canvas, HOUSE_RED if self.current_team == 0 else TEAM_YELLOW); self.draw_ui(); self.draw_pause_screen()
            elif self.app_state == "MATCH_OVER": self.draw_match_over_screen()
                
            self.render(); self.clock.tick(FPS)

# --- DAL.NET IRC Socket Manager ---
class IRCNetworkManager:
    def __init__(self):
        if IS_ANDROID: pygame.mixer.pre_init(44100, -16, 2, 4096)
        else: pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.mixer.init()
        self.sock = None; self.running = False; self.connecting = False; self.matched = False
        self.username = ""; self.opponent = ""; self.channel = "#wincurl3_net"
        self.room_display = ""
        self.tx_queue = queue.Queue(); self.rx_queue = queue.Queue(); self.is_host = False

    def connect(self, username, is_host, room_name="", preferred_color=0):
        self.username = "WC_" + "".join(c for c in username if c.isalnum())[:10]
        if len(self.username) == 3: self.username += str(random.randint(100,999))
        
        safe_room = "".join(c for c in room_name if c.isalnum()) or "default"
        self.channel = f"#wc3_{safe_room}"
        self.room_display = f"'{safe_room}'"
        
        self.preferred_color = preferred_color
        self.is_host = is_host; self.connecting = True; self.running = True
        threading.Thread(target=self._irc_thread, daemon=True).start()

    def _irc_thread(self):
        def enc_msg(msg_dict): return "Z" + base64.b64encode(zlib.compress(json.dumps(msg_dict).encode('utf-8'))).decode('utf-8')
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); self.sock.connect(("irc.dal.net", 6667))
            self.sock.send(f"NICK {self.username}\r\nUSER {self.username} 8 * :WinCurl3\r\n".encode())
            buffer = ""
            while self.running:
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
                                    
                                if self.is_host and not self.matched and target == self.channel and msg_data.get('cmd') == 'hello':
                                    self.opponent = sender; self.matched = True
                                    self.sock.send(f"PRIVMSG {self.opponent} :{json.dumps({'cmd': 'hello_ack', 'color': getattr(self, 'preferred_color', 0)})}\r\n".encode())
                                elif not self.is_host and not self.matched and msg_data.get('cmd') == 'hello_ack':
                                    self.opponent = sender; self.matched = True
                                    self.rx_queue.put({'cmd': 'set_color', 'color': msg_data.get('color', 0)})
                                elif sender == self.opponent:
                                    self.rx_queue.put(msg_data)
                            except: pass
                except socket.timeout: pass
        except Exception: pass
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

if __name__ == "__main__":
    game = WinCurl3()
    game.setup_display()
    game.run()

import os, sys

if hasattr(os, "name") and os.name == "posix" and not hasattr(sys, "getandroidapilevel") and "ANDROID_ARGUMENT" not in os.environ:
    os.environ["SDL_VIDEO_WAYLAND_WMCLASS"] = "wincurl3"
    os.environ["SDL_VIDEO_X11_WMCLASS"] = "wincurl3"
import pygame
import math, random, time, json, socket, queue, base64, zlib
import sys

if not (hasattr(sys, "platform") and sys.platform == "emscripten"):
    import threading
import struct
import io
import collections
import asyncio
import sys
# Set up logging and constants
VERSION = "3.0 Build 106"
GAME_TITLE = f"WinCurl {VERSION}"


class CachedFont:
    def __init__(self, font):
        self.font = font
        self.cache = {}

    def __getattr__(self, attr):
        return getattr(self.font, attr)

    def render(self, text, antialias, color, background=None):
        key = (text, antialias, str(color), str(background))
        if key not in self.cache:
            if len(self.cache) > 2000:
                del self.cache[next(iter(self.cache))]
            if background:
                self.cache[key] = self.font.render(text, antialias, color, background)
            else:
                self.cache[key] = self.font.render(text, antialias, color)
        return self.cache[key]


class ChatFont:
    def __init__(self, size):
        self.target_size = size
        self.text_font = CachedFont(pygame.font.Font(None, size))
        self.emoji_font = None
        self.cache = {}

        try:
            ef = pygame.font.SysFont("segoeuiemoji,applecoloremoji,notocoloremoji,symbola", size)
            if ef:
                self.emoji_font = ef
        except:
            pass

        if not self.emoji_font:
            import os

            android_emoji = "/system/fonts/NotoColorEmoji.ttf"
            if os.path.exists(android_emoji):
                try:
                    self.emoji_font = CachedFont(pygame.font.Font(android_emoji, size))
                except:
                    pass

    def render(self, text, antialias, color, background=None):
        key = (text, antialias, str(color), str(background))
        if key in self.cache:
            return self.cache[key]
        if len(self.cache) > 256:
            self.cache.clear()

        if not self.emoji_font:
            if background:
                surf = self.text_font.render(text, antialias, color, background)
            else:
                surf = self.text_font.render(text, antialias, color)
            self.cache[key] = surf
            return surf

        chunks = []
        current_chunk = ""
        current_font_is_text = True

        for char in text:
            m = self.text_font.metrics(char)
            is_text = m is not None and len(m) > 0 and m[0] is not None

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
                if background:
                    s = font.render(chunk_text, antialias, color, background)
                else:
                    s = font.render(chunk_text, antialias, color)

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
        if background:
            final_surf.fill(background)

        x = 0
        for s in surfaces:
            final_surf.blit(s, (x, max_height // 2 - s.get_height() // 2))
            x += s.get_width()

        self.cache[key] = final_surf
        return final_surf


# --- Global Constants & Configurations ---
from pygame.locals import *

import os

VIBRATE_ENABLED = True


def vibrate_android(ms):
    global VIBRATE_ENABLED
    if not VIBRATE_ENABLED:
        return
    try:
        from plyer import vibrator

        vibrator.vibrate(time=ms / 1000.0)
        return
    except Exception as e:
        print("Plyer vibration failed:", e)

    try:
        from jnius import autoclass

        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        vibrator = PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
        if vibrator and vibrator.hasVibrator():
            VERSION = autoclass("android.os.Build$VERSION")
            if VERSION.SDK_INT >= 26:
                VibrationEffect = autoclass("android.os.VibrationEffect")
                vibrator.vibrate(VibrationEffect.createOneShot(int(ms), VibrationEffect.DEFAULT_AMPLITUDE))
            else:
                vibrator.vibrate(int(ms))
            return
    except Exception as e:
        print("Pyjnius vibration failed:", e)

    try:
        if pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            if not joy.get_init():
                joy.init()
            joy.rumble(0.5, 0.5, int(ms))
    except:
        pass


# Define this immediately after imports
IS_ANDROID = hasattr(sys, "getandroidapilevel") or "ANDROID_ARGUMENT" in os.environ or "ANDROID_BOOTLOGO" in os.environ
if IS_ANDROID:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- Immediate Environment Verification ---
print("\n" + "=" * 80)
print(f"     [SYSTEM] WINCURL 3 BUILD {VERSION}")
print("     (IMPROVED NETPLAY | NET CHAT | MULTI-SYLLABLE AUDIO | REALISM | VIBRATION)")
print("=" * 80 + "\n")


# --- Configuration & Canvas Setup ---
BASE_WIDTH, BASE_HEIGHT = 1200, 1800
FPS = 120
PHYSICS_FPS = 60
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
    pts = [
        (-0.45, 10.0),
        (-0.22, 5.72),
        (-0.77, 5.23),
        (-5.04, 5.98),
        (-4.46, 4.39),
        (-4.56, 4.03),
        (-9.23, 0.25),
        (-8.18, -0.24),
        (-8.01, -0.64),
        (-8.93, -3.47),
        (-6.24, -2.9),
        (-5.88, -3.09),
        (-5.36, -4.32),
        (-3.26, -2.06),
        (-2.71, -2.35),
        (-3.72, -7.57),
        (-2.1, -6.63),
        (-1.65, -6.76),
        (0.0, -10.0),
        (1.65, -6.76),
        (2.1, -6.63),
        (3.72, -7.57),
        (2.71, -2.35),
        (3.26, -2.06),
        (5.36, -4.32),
        (5.88, -3.09),
        (6.24, -2.9),
        (8.93, -3.47),
        (8.01, -0.64),
        (8.18, -0.24),
        (9.23, 0.25),
        (4.56, 4.03),
        (4.46, 4.39),
        (5.04, 5.98),
        (0.77, 5.23),
        (0.22, 5.72),
        (0.45, 10.0),
    ]
    polygon = []
    for x, y in pts:
        wrap_y = y + (x * x + y * y) * 0.015
        polygon.append((cx + x * scale * 2.5, cy + wrap_y * scale * 2.5))
    pygame.draw.polygon(surface, color, polygon)


def draw_hammer_icon(surface, x, y, color):
    pygame.draw.rect(surface, color, (x, y, 16, 8), border_radius=2)
    pygame.draw.rect(surface, color, (x + 6, y + 8, 4, 12))


# OPTIMIZATION: Cache glass buttons
class UICache:
    glass_surfs = {}

    @classmethod
    def get_glass(cls, w, h, base_color, radius, hovered, dark_mode=False):
        key = (w, h, tuple(base_color), radius, hovered, dark_mode)
        if key not in cls.glass_surfs:
            # 1. Shadow (No need for 2x, just draw and scale? Actually, 1x is fine for shadow)
            shadow = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA).convert_alpha()
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

            if dark_mode:
                pygame.draw.rect(content, (0, 0, 0, 80), (0, th // 2, tw, th // 2))
                pygame.draw.rect(content, (0, 0, 0, 160), (0, 0, tw, th))
            else:
                pygame.draw.rect(content, (255, 255, 255, 60), (0, 0, tw, th // 2))
                pygame.draw.ellipse(content, (255, 255, 255, 90), (tw * 0.05, -th * 0.2, tw * 0.9, th * 0.7))
                pygame.draw.rect(content, (0, 0, 0, 40), (0, th // 2, tw, th // 2))

            if hovered:
                pygame.draw.rect(content, (255, 255, 255, 60), (0, 0, tw, th))

            # Apply mask to clip overflowing gradients
            content.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Draw borders on top
            if hovered:
                pygame.draw.rect(content, (255, 255, 255, 240), (0, 0, tw, th), 6, border_radius=tr)
            else:
                border_alpha = 40 if dark_mode else 120
                pygame.draw.rect(content, (255, 255, 255, border_alpha), (0, 0, tw, th), 4, border_radius=tr)

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


def draw_trophy(surface, x, y, size=40):
    pygame.draw.circle(surface, (255, 215, 0), (int(x + size * 0.2), int(y + size * 0.35)), int(size * 0.2), 3)
    pygame.draw.circle(surface, (200, 150, 50), (int(x + size * 0.8), int(y + size * 0.35)), int(size * 0.2), 3)

    # Base and stem
    pygame.draw.rect(surface, (150, 100, 20), (int(x + size * 0.3), int(y + size * 0.8), int(size * 0.4), int(size * 0.2)))
    pygame.draw.rect(surface, (200, 150, 50), (int(x + size * 0.35), int(y + size * 0.85), int(size * 0.3), int(size * 0.1)))

    # Stem
    pygame.draw.rect(surface, (200, 150, 50), (int(x + size * 0.45), int(y + size * 0.5), int(size * 0.1), int(size * 0.3)))
    pygame.draw.rect(surface, (255, 215, 0), (int(x + size * 0.45), int(y + size * 0.5), int(size * 0.05), int(size * 0.3)))

    # Bowl
    pygame.draw.ellipse(surface, (200, 150, 50), (int(x + size * 0.2), int(y + size * 0.1), int(size * 0.6), int(size * 0.5)))
    pygame.draw.ellipse(surface, (255, 215, 0), (int(x + size * 0.25), int(y + size * 0.15), int(size * 0.3), int(size * 0.3)))

    # Lip
    pygame.draw.ellipse(surface, (255, 230, 100), (int(x + size * 0.2), int(y + size * 0.05), int(size * 0.6), int(size * 0.2)))
    pygame.draw.ellipse(surface, (180, 120, 30), (int(x + size * 0.25), int(y + size * 0.08), int(size * 0.5), int(size * 0.14)))


ACTIVE_UI_RECTS = []
ACTIVE_UI_RECTS_PREV = []

def draw_glass_rect(surface, rect, base_color, border_radius=16, is_hovered=False, dark_mode=False, animate_sheen=True):
    global ACTIVE_UI_RECTS
    ACTIVE_UI_RECTS.append(rect)
    if IS_ANDROID:
        animate_sheen = False
    shadow, btn_surf = UICache.get_glass(rect.w, rect.h, base_color, border_radius, is_hovered, dark_mode)
    if not IS_ANDROID:
        surface.blit(shadow, (rect.x - 5, rect.y - 5))
    surface.blit(btn_surf, rect.topleft)

    if animate_sheen:
        if not hasattr(UICache, "sheen_surfs"):
            UICache.sheen_surfs = {}
        sheen_key = (rect.w, rect.h, border_radius)
        if sheen_key not in UICache.sheen_surfs:
            sheen_base = pygame.Surface((rect.w * 3, rect.h), pygame.SRCALPHA)
            pygame.draw.polygon(
                sheen_base,
                (255, 255, 255, 7),
                [(rect.w, 0), (rect.w + rect.w * 0.3, 0), (rect.w + rect.w * 0.1, rect.h), (rect.w - rect.w * 0.2, rect.h)],
            )
            pygame.draw.polygon(
                sheen_base,
                (255, 255, 255, 15),
                [(rect.w + rect.w * 0.15, 0), (rect.w + rect.w * 0.2, 0), (rect.w, rect.h), (rect.w - rect.w * 0.05, rect.h)],
            )
            mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=border_radius)
            sheen_layer = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            UICache.sheen_surfs[sheen_key] = (sheen_base, mask, sheen_layer)

        sheen_base, mask, sheen_layer = UICache.sheen_surfs[sheen_key]

        t = pygame.time.get_ticks()
        sweep_x = (t * 0.4) % (rect.w + 1000) - 500

        sheen_layer.fill((0, 0, 0, 0))
        sheen_layer.blit(sheen_base, (sweep_x - rect.w, 0))
        sheen_layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(sheen_layer, rect.topleft)


# --- Audio Synthesis Engine ---
class WinCurlAudioEngine:
    def __init__(self):
        import sys
        is_emscripten = hasattr(sys, "platform") and sys.platform == "emscripten"

        try:
            if IS_ANDROID or is_emscripten:
                pygame.mixer.pre_init(44100, -16, 2, 4096)
            else:
                pygame.mixer.pre_init(44100, -16, 2, 1024)
            pygame.mixer.init()
            self.sfx_on = True
            
            self.ch_slide = pygame.mixer.Channel(0)
            self.ch_sweep = pygame.mixer.Channel(1)
            self.ch_sfx = pygame.mixer.Channel(2)
            self.ch_ui = pygame.mixer.Channel(3)
            self.ch_music = pygame.mixer.Channel(4)
            self.ch_crowd = pygame.mixer.Channel(5)
            self.ch_voice = pygame.mixer.Channel(6)
            pygame.mixer.set_num_channels(16)
        except Exception as e:
            print("Audio init failed:", e)
            self.sfx_on = False
            
            class DummyChannel:
                def play(self, *args, **kwargs): pass
                def set_volume(self, *args, **kwargs): pass
                def stop(self): pass
                def get_busy(self): return False
                def get_volume(self): return 0.0
                
            self.ch_slide = DummyChannel()
            self.ch_sweep = DummyChannel()
            self.ch_sfx = DummyChannel()
            self.ch_ui = DummyChannel()
            self.ch_music = DummyChannel()
            self.ch_crowd = DummyChannel()
            self.ch_voice = DummyChannel()

        self.snd_music = None
        self.snd_speech = None
        self.snd_cheer = None
        self.snd_end_match = None
        self.snd_hurry = None
        self.snd_hard = None
        self.snd_chal_comp = None
        self.snd_red_wins = None
        self.snd_ylw_wins = None
        self.snd_slide = None
        self.snd_sweep = None
        self.snd_throw = None
        self.snd_clack = None
        self.snd_hover = None
        self.snd_click = None

        self._synthesize_heavy_bg()
        self.last_call = 0

    def set_master_volume(self, vol):
        self.master_volume = vol
        pygame.mixer.music.set_volume(vol)
        for ch in [self.ch_slide, self.ch_sweep, self.ch_sfx, self.ch_ui, self.ch_music, self.ch_crowd, self.ch_voice]:
            ch.set_volume(ch.get_volume() * vol if vol > 0 else 0)

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

        try:
            self.snd_music = ["theme.ogg", os.path.join(asset_dir, "theme.ogg")]
        except:
            self.snd_music = None
        load_sound("snd_speech", "sega_speech.ogg", self._synthesize_sega_speech)
        load_sound("snd_cheer", "cheer.ogg", self._synthesize_cheer)
        load_sound("snd_end_match", "end_match.ogg", self._synthesize_end_of_match)
        load_sound(
            "snd_hurry",
            "vosim_HURRY.ogg",
            lambda return_bytes=False: self._synthesize_vosim_phrase("HURRY", 0.7, return_bytes=return_bytes),
        )
        load_sound(
            "snd_hard",
            "vosim_HARD.ogg",
            lambda return_bytes=False: self._synthesize_vosim_phrase("HARD", 0.65, return_bytes=return_bytes),
        )
        load_sound(
            "snd_you_win",
            "vosim_YOU_WIN.ogg",
            lambda return_bytes=False: self._synthesize_vosim_phrase("YOU_WIN", 1.2, return_bytes=return_bytes),
        )
        load_sound("snd_chal_comp", "challenge_complete.ogg", None)
        load_sound("snd_red_wins", "red_wins.ogg", None)
        load_sound("snd_ylw_wins", "yellow_wins.ogg", None)

        load_sound("snd_slide", "snd_slide.ogg", self._synthesize_rumble)
        load_sound("snd_sweep", "snd_sweep.ogg", self._synthesize_sweep)
        load_sound("snd_throw", "snd_throw.ogg", self._synthesize_throw)
        load_sound("snd_clack", "snd_clack.ogg", self._synthesize_clack)
        load_sound(
            "snd_hover",
            "snd_hover.ogg",
            lambda return_bytes=False: self._synthesize_ui_sound(440, 0.05, "sine", return_bytes=return_bytes),
        )
        load_sound(
            "snd_click",
            "snd_click.ogg",
            lambda return_bytes=False: self._synthesize_ui_sound(587, 0.12, "square", return_bytes=return_bytes),
        )

        import sys

        if hasattr(sys, "platform") and sys.platform == "emscripten":
            for attr_name, fallback in pending_tasks:
                try:
                    setattr(self, attr_name, fallback(return_bytes=True))
                except:
                    setattr(self, attr_name, None)
            return

        def bg_worker():
            for attr_name, fallback in pending_tasks:
                try:
                    setattr(self, attr_name, fallback(return_bytes=True))
                except Exception as e:
                    pass

        threading.Thread(target=bg_worker, daemon=True).start()

    def process_pending_sounds(self):
        import io, pygame

        for attr in [
            "snd_speech",
            "snd_cheer",
            "snd_end_match",
            "snd_hurry",
            "snd_hard",
            "snd_chal_comp",
            "snd_red_wins",
            "snd_ylw_wins",
            "snd_slide",
            "snd_sweep",
            "snd_throw",
            "snd_clack",
            "snd_hover",
            "snd_click",
        ]:
            val = getattr(self, attr, None)
            if isinstance(val, io.BytesIO):
                try:
                    snd = pygame.mixer.Sound(file=val)
                    setattr(self, attr, snd)
                    if attr == "snd_slide":
                        self.ch_slide.play(snd, loops=-1)
                        self.ch_slide.set_volume(0.0)
                    elif attr == "snd_sweep":
                        self.ch_sweep.play(snd, loops=-1)
                        self.ch_sweep.set_volume(0.0)
                except Exception as e:
                    print("Sound load error:", e)
                    setattr(self, attr, None)
            elif isinstance(val, str):
                try:
                    setattr(self, attr, pygame.mixer.Sound(file=val))
                except Exception as e:
                    print("Sound file load error:", e)
                    setattr(self, attr, None)


    def _get_cache_dir(self):
        import os, tempfile

        if IS_ANDROID:
            try:
                from jnius import autoclass

                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                cache_dir = os.path.join(PythonActivity.mActivity.getCacheDir().getAbsolutePath(), "wincurl_cache")
                os.makedirs(cache_dir, exist_ok=True)
                return cache_dir
            except:
                pass

        try:
            cache_dir = os.path.join(tempfile.gettempdir(), "wincurl_cache")
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        except:
            pass

        try:
            base_dir = pygame.system.get_pref_path("jason", "wincurl3")
            cache_dir = os.path.join(base_dir, "wincurl_cache")
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        except:
            pass

        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "wincurl_cache")

    def _get_cached_sound(self, cache_key, return_bytes=False):
        import os, io, threading, pygame

        cache_file = os.path.join(self._get_cache_dir(), f"{cache_key}.ogg")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    data = f.read()
                    if return_bytes:
                        return io.BytesIO(data)
                    return pygame.mixer.Sound(file=io.BytesIO(data))
            except:
                pass
        return None

    def _create_wav_sound(self, byte_buffer, sample_rate=44100, cache_key=None, return_path=False, channels=2, return_bytes=False):
        import os, struct, io, threading

        data_size = len(byte_buffer)
        bits = 16
        wav = b"RIFF"
        wav += struct.pack("<I", 36 + data_size)
        wav += b"WAVE"
        wav += b"fmt "
        wav += struct.pack(
            "<IHHIIHH", 16, 1, channels, sample_rate, sample_rate * channels * (bits // 8), channels * (bits // 8), bits
        )
        wav += b"data"
        wav += struct.pack("<I", data_size)
        wav += byte_buffer

        if cache_key:
            cache_dir = self._get_cache_dir()
            path = os.path.join(cache_dir, f"{cache_key}.ogg")
            try:
                os.makedirs(cache_dir, exist_ok=True)
                with open(path, "wb") as f:
                    f.write(wav)
                if return_path:
                    return path
            except:
                pass

        if return_path:
            return None
        if return_bytes:
            return io.BytesIO(wav)

        import io, threading, pygame

        return pygame.mixer.Sound(file=io.BytesIO(wav))

    def _synthesize_sega_speech(self, return_bytes=False):
        cached = self._get_cached_sound("sega_speech", return_bytes=return_bytes)
        if cached:
            return cached
        steps = int(44100 * 3.0)
        buf = bytearray(steps * 4)
        w_f1, w_f2, w_f3 = (
            [(0.0, 300), (0.9, 400), (1.4, 250)],
            [(0.0, 600), (0.9, 1900), (1.4, 1200)],
            [(0.0, 2200), (0.9, 2400), (1.4, 2600)],
        )
        c_f1, c_f2, c_f3 = (
            [(1.4, 500), (2.3, 350), (2.8, 300)],
            [(1.4, 1450), (2.3, 1000), (2.8, 900)],
            [(1.4, 2450), (1.8, 1400), (2.8, 2300)],
        )

        def get_val(t, pts):
            for i in range(len(pts) - 1):
                if pts[i][0] <= t <= pts[i + 1][0]:
                    return pts[i][1] + (pts[i + 1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / 44100
            val = 0.0
            if t < 1.4:
                env = min(1.0, t / 0.1) * max(0.0, min(1.0, (1.4 - t) / 0.2))
                chord = [155.56, 196.00, 233.08]
                for f0 in chord:
                    phase = (t * f0) % 1.0
                    decay = math.exp(-phase * 5.0)
                    val += (
                        math.sin(2 * math.pi * get_val(t, w_f1) * phase / f0)
                        + math.sin(2 * math.pi * get_val(t, w_f2) * phase / f0) * 0.6
                        + math.sin(2 * math.pi * get_val(t, w_f3) * phase / f0) * 0.3
                    ) * decay
                val = (val / 3.0) * env * 1.8
            elif t < 2.8:
                tc = t - 1.4
                env = min(1.0, tc / 0.1) * max(0.0, min(1.0, (2.8 - t) / 0.3))
                if tc < 0.1:
                    val += random.uniform(-1, 1) * max(0.0, 1.0 - tc / 0.1) * 0.35
                chord = [130.81, 164.81, 196.00]
                for f0 in chord:
                    phase = (t * f0) % 1.0
                    decay = math.exp(-phase * 5.0)
                    val += (
                        math.sin(2 * math.pi * get_val(t, c_f1) * phase / f0)
                        + math.sin(2 * math.pi * get_val(t, c_f2) * phase / f0) * 0.6
                        + math.sin(2 * math.pi * get_val(t, c_f3) * phase / f0) * 0.3
                    ) * decay
                val = (val / 3.0) * env * 1.8
            sample = int(max(-1.0, min(1.0, val)) * 24000)
            struct.pack_into("<hh", buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100, cache_key="sega_speech", return_bytes=return_bytes)

    def _synthesize_vosim_phrase(self, phrase, duration, return_bytes=False):
        cached = self._get_cached_sound(f"vosim_{phrase}", return_bytes=return_bytes)
        if cached:
            return cached
        SR = 44100
        steps = int(SR * duration)
        buf = bytearray(steps * 4)
        if phrase == "HURRY":
            f1_env, f2_env, f3_env = (
                [(0.0, 400), (0.5, 450), (1.0, 300)],
                [(0.0, 1000), (0.5, 1400), (1.0, 2400)],
                [(0.0, 2600), (0.5, 1600), (1.0, 2800)],
            )
            chord = [261.63, 329.63]
        elif phrase == "RED_TEAM_WINS":
            # Three dips in the frequency envelope simulate three words
            f1_env = [(0.0, 500), (0.2, 530), (0.3, 300), (0.5, 550), (0.7, 400), (0.8, 600), (1.0, 300)]
            f2_env = [(0.0, 1800), (0.3, 1840), (0.5, 1200), (0.8, 1600), (1.0, 1500)]
            f3_env = [(0.0, 2600), (0.5, 2400), (1.0, 2600)]
            chord = [220.00, 277.18]
        elif phrase == "YELLOW_TEAM_WINS":
            f1_env = [(0.0, 530), (0.2, 500), (0.3, 300), (0.5, 550), (0.7, 400), (0.8, 600), (1.0, 300)]
            f2_env = [(0.0, 1840), (0.3, 1200), (0.5, 1200), (0.8, 1600), (1.0, 1500)]
            f3_env = [(0.0, 2600), (0.3, 2000), (0.5, 2400), (1.0, 2600)]
            chord = [233.08, 293.66]
        elif phrase == "CHALLENGE_COMPLETE":
            f1_env = [(0.0, 600), (0.2, 500), (0.3, 300), (0.5, 600), (0.7, 300), (0.9, 400), (1.0, 200)]
            f2_env = [(0.0, 1700), (0.3, 1200), (0.5, 1800), (0.7, 1100), (1.0, 1400)]
            f3_env = [(0.0, 2400), (0.5, 2200), (0.8, 2500), (1.0, 2000)]
            chord = [261.63, 311.13]
        elif phrase == "YOU_WIN":
            f1_env = [(0.0, 300), (0.2, 500), (0.4, 600), (0.6, 200), (0.8, 400), (1.0, 600)]
            f2_env = [(0.0, 1000), (0.4, 1500), (0.6, 900), (1.0, 1200)]
            f3_env = [(0.0, 2400), (0.5, 2600), (1.0, 2400)]
            chord = [329.63, 440.00]
        else:  # "HARD" and fallback
            f1_env, f2_env, f3_env = (
                [(0.0, 400), (0.3, 750), (1.0, 200)],
                [(0.0, 1000), (0.8, 1400), (1.0, 1600)],
                [(0.0, 2600), (0.8, 1800), (1.0, 2400)],
            )
            chord = [246.94, 311.13]

        def get_val(t, pts):
            for i in range(len(pts) - 1):
                if pts[i][0] <= t <= pts[i + 1][0]:
                    return pts[i][1] + (pts[i + 1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t_norm = i / steps
            env = min(1.0, t_norm / 0.1) * max(0.0, min(1.0, (1.0 - t_norm) / 0.2))
            if t_norm < 0.1:
                env += random.uniform(-0.5, 0.5) * (0.1 - t_norm) * 15
            val = 0.0
            for f0 in chord:
                phase = ((i / SR) * f0) % 1.0
                decay = math.exp(-phase * 2.2)
                val += (
                    math.sin(2 * math.pi * get_val(t_norm, f1_env) * phase / f0)
                    + math.sin(2 * math.pi * get_val(t_norm, f2_env) * phase / f0) * 0.6
                    + math.sin(2 * math.pi * get_val(t_norm, f3_env) * phase / f0) * 0.3
                ) * decay
            sample = int(max(-1.0, min(1.0, (val / len(chord)) * env * 2.0)) * 24000)
            struct.pack_into("<hh", buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, SR, cache_key=f"vosim_{phrase}", return_bytes=return_bytes)

    def _synthesize_end_of_match(self, return_bytes=False):
        cached = self._get_cached_sound("end_match", return_bytes=return_bytes)
        if cached:
            return cached
        SR = 11025
        steps = int(SR * 2.0)
        buf = bytearray(steps * 4)
        f1_env = [(0, 400), (0.3, 500), (0.6, 300), (1.0, 400), (1.4, 700), (1.8, 300), (2.0, 200)]
        f2_env = [(0, 1800), (0.3, 1200), (0.6, 1000), (1.0, 900), (1.4, 1200), (1.8, 1800), (2.0, 2400)]
        f3_env = [(0, 2600), (0.5, 2400), (1.0, 2400), (1.5, 2600), (2.0, 2800)]

        def get_val(t, pts):
            for i in range(len(pts) - 1):
                if pts[i][0] <= t <= pts[i + 1][0]:
                    return pts[i][1] + (pts[i + 1][1] - pts[i][1]) * (t - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
            return pts[-1][1]

        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / SR
            env = math.sin((t / 2.0) * math.pi)
            f0 = 120.0 - t * 15.0
            phase = (t * f0) % 1.0
            decay = math.exp(-phase * 4.0)
            noise = random.uniform(-1, 1) * max(0, (t - 1.6) / 0.4) * 0.5
            val = (
                math.sin(2 * math.pi * get_val(t, f1_env) * phase / f0)
                + math.sin(2 * math.pi * get_val(t, f2_env) * phase / f0) * 0.6
                + math.sin(2 * math.pi * get_val(t, f3_env) * phase / f0) * 0.3
            ) * decay
            sample = int(max(-1.0, min(1.0, (val * 0.6 + noise) * env)) * 24000)
            struct.pack_into("<hh", buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, SR, cache_key="end_match", return_bytes=return_bytes)

    def _synthesize_cheer(self, return_bytes=False):
        cached = self._get_cached_sound("cheer", return_bytes=return_bytes)
        if cached:
            return cached
        SR = 11025
        duration = 3.5
        steps = int(SR * duration)
        buf = bytearray(steps * 4)
        val = 0.0
        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / SR
            val += (random.uniform(-1.0, 1.0) - val) * 0.02
            sample = int(val * math.sin(t * math.pi / duration) * 18000 * (1.0 + 0.3 * math.sin(t * 12)))
            struct.pack_into("<hh", buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, SR, cache_key="cheer", return_bytes=return_bytes)

    def _synthesize_rumble(self, return_bytes=False):
        cached = self._get_cached_sound("whoosh", return_bytes=return_bytes)
        if cached:
            return cached
        buf = bytearray(44100 * 4)
        v = 0.0
        for i in range(44100):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            v = max(-0.4, min(0.4, (v + random.uniform(-0.08, 0.08)) * 0.98))
            struct.pack_into("<hh", buf, i * 4, int(v * 32767), int(v * 32767))
        return self._create_wav_sound(buf, 44100, cache_key="whoosh", return_bytes=return_bytes)

    def _synthesize_sweep(self, return_bytes=False):
        cached = self._get_cached_sound("sweep", return_bytes=return_bytes)
        if cached:
            return cached
        buf = bytearray(22050 * 4)
        for i in range(22050):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            struct.pack_into("<hh", buf, i * 4, int(random.uniform(-0.15, 0.15) * 32767), int(random.uniform(-0.15, 0.15) * 32767))
        return self._create_wav_sound(buf, 22050, cache_key="sweep", return_bytes=return_bytes)

    def _synthesize_throw(self, return_bytes=False):
        cached = self._get_cached_sound("throw", return_bytes=return_bytes)
        if cached:
            return cached
        duration = 0.5
        steps = int(44100 * duration)
        buf = bytearray(steps * 4)
        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / 44100
            val = math.sin(2 * math.pi * (180 - (t * 100)) * t) * (math.sin(t * math.pi / duration) * math.exp(-t * 2))
            sample = int(max(-1.0, min(1.0, val * 0.5)) * 32767)
            struct.pack_into("<hh", buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100, cache_key="throw", return_bytes=return_bytes)

    def _synthesize_clack(self, return_bytes=False):
        cached = self._get_cached_sound("clack", return_bytes=return_bytes)
        if cached:
            return cached
        buf = bytearray(11025 * 4)
        for i in range(11025):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / 11025
            sample = int(math.sin(2 * math.pi * (220 + random.uniform(-20, 20)) * t) * math.exp(-t * 25) * 32767)
            struct.pack_into("<hh", buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 11025, cache_key="clack", return_bytes=return_bytes)

    def _synthesize_ui_sound(self, frequency, duration, type="sine", return_bytes=False):
        cached = self._get_cached_sound(f"ui_{frequency}_{duration}_{type}", return_bytes=return_bytes)
        if cached:
            return cached
        steps = int(44100 * duration)
        buf = bytearray(steps * 4)
        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / 44100
            val = (
                math.sin(2 * math.pi * frequency * t)
                if type == "sine"
                else (1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0)
            )
            struct.pack_into(
                "<hh",
                buf,
                i * 4,
                int(val * math.exp(-t * (1.0 / duration * 3)) * 12000),
                int(val * math.exp(-t * (1.0 / duration * 3)) * 12000),
            )
        return self._create_wav_sound(buf, 44100, cache_key=f"ui_{frequency}_{duration}_{type}", return_bytes=return_bytes)

    def _synthesize_theme_song(self, return_path=False):
        import os

        if return_path:
            cache_file = os.path.join(self._get_cache_dir(), "theme_v2.ogg")
            if os.path.exists(cache_file):
                return cache_file
        else:
            cached = self._get_cached_sound("theme_v2")
            if cached:
                return cached
        bpm = 125.0
        step_len = 60.0 / bpm / 4.0  # 16th notes
        total_steps = 512
        duration = step_len * total_steps
        steps = int(22050 * duration)
        buf = bytearray(steps * 2)

        # Phonk Melody (E Minor) extended
        cb_base = [
            329.6,
            0,
            392.0,
            0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            311.1,
            0,
            246.9,
            0,
            329.6,
            0,
            329.6,
            0,
            392.0,
            392.0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            493.9,
            0,
            392.0,
            369.9,
            329.6,
            0,
            329.6,
            0,
            392.0,
            0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            311.1,
            0,
            246.9,
            0,
            329.6,
            0,
            329.6,
            0,
            392.0,
            392.0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            493.9,
            0,
            392.0,
            369.9,
            329.6,
            0,
            329.6,
            0,
            392.0,
            0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            311.1,
            0,
            246.9,
            0,
            329.6,
            0,
            329.6,
            0,
            587.3,
            587.3,
            329.6,
            0,
            493.9,
            0,
            329.6,
            0,
            659.3,
            0,
            587.3,
            493.9,
            329.6,
            0,
            329.6,
            0,
            392.0,
            0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            311.1,
            0,
            246.9,
            0,
            329.6,
            0,
            329.6,
            0,
            587.3,
            587.3,
            329.6,
            0,
            493.9,
            0,
            329.6,
            0,
            659.3,
            0,
            587.3,
            493.9,
            329.6,
            0,
            329.6,
            0,
            392.0,
            392.0,
            329.6,
            0,
            440.0,
            0,
            329.6,
            0,
            392.0,
            0,
            369.9,
            369.9,
            329.6,
            0,
            329.6,
            0,
            493.9,
            0,
            329.6,
            0,
            587.3,
            0,
            329.6,
            0,
            659.3,
            0,
            587.3,
            493.9,
            329.6,
            0,
            329.6,
            0,
            392.0,
            392.0,
            329.6,
            0,
            440.0,
            0,
            329.6,
            0,
            392.0,
            0,
            369.9,
            369.9,
            329.6,
            0,
            329.6,
            0,
            493.9,
            0,
            329.6,
            0,
            587.3,
            0,
            329.6,
            0,
            659.3,
            0,
            587.3,
            493.9,
            329.6,
            0,
            329.6,
            0,
            392.0,
            0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            311.1,
            0,
            246.9,
            0,
            329.6,
            0,
            329.6,
            0,
            392.0,
            392.0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            493.9,
            0,
            392.0,
            369.9,
            329.6,
            0,
            329.6,
            0,
            659.3,
            659.3,
            329.6,
            0,
            587.3,
            0,
            329.6,
            0,
            493.9,
            0,
            392.0,
            0,
            329.6,
            0,
            329.6,
            0,
            783.9,
            783.9,
            329.6,
            0,
            659.3,
            0,
            329.6,
            0,
            587.3,
            0,
            493.9,
            392.0,
            329.6,
            0,
            329.6,
            0,
            392.0,
            0,
            329.6,
            0,
            369.9,
            0,
            329.6,
            0,
            311.1,
            0,
            246.9,
            0,
            329.6,
            0,
            329.6,
            0,
            587.3,
            587.3,
            329.6,
            0,
            493.9,
            0,
            329.6,
            0,
            659.3,
            0,
            587.3,
            493.9,
            329.6,
            0,
        ]

        # Evolving variations: pitched up, then arpeggiated
        cb_notes = (
            cb_base
            + [n * 1.5 if n > 0 else 0 for n in cb_base]
            + [n * 2.0 if n > 0 else 0 for n in cb_base]
            + [n * 0.75 if n > 0 else 0 for n in cb_base]
        )

        # 808 Bass Pattern (much longer and more complex)
        bass_pitches = [
            41.2,
            0,
            0,
            41.2,
            0,
            0,
            41.2,
            0,
            0,
            41.2,
            41.2,
            0,
            0,
            0,
            0,
            0,
            49.0,
            0,
            0,
            49.0,
            0,
            0,
            49.0,
            0,
            0,
            49.0,
            49.0,
            0,
            0,
            0,
            0,
            0,
            36.7,
            0,
            0,
            36.7,
            0,
            0,
            36.7,
            0,
            0,
            36.7,
            36.7,
            0,
            0,
            0,
            0,
            0,
            41.2,
            0,
            0,
            41.2,
            0,
            0,
            41.2,
            0,
            0,
            41.2,
            41.2,
            0,
            41.2,
            0,
            41.2,
            0,
        ] * 4  # Repeat 4 times for the full progression

        # Add high-end distortion noise for the hat and snare layers
        noise = [random.uniform(-1, 1) for _ in range(22050)]

        for i in range(steps):
            if i % 4000 == 0:
                import time

                time.sleep(0.001)
            t = i / 22050.0
            step = int((t / duration) * total_steps) % total_steps
            step_t = t - (step * step_len)

            # --- 808 BASS (Distorted Sine with Pitch Drop) ---
            bass = 0.0
            last_bass_step = step
            while last_bass_step >= 0 and bass_pitches[last_bass_step % len(bass_pitches)] == 0:
                last_bass_step -= 1
            if last_bass_step >= 0:
                b_t = t - (last_bass_step * step_len)
                if b_t < 1.0:
                    b_freq = bass_pitches[last_bass_step % len(bass_pitches)]
                    if step >= 512:
                        b_freq *= 1.0 + math.sin(b_t * math.pi * 8) * 0.03  # Wobbly bass in second half
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
            while last_cb_step >= 0 and cb_notes[last_cb_step % len(cb_notes)] == 0:
                last_cb_step -= 1
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
                        synth += (2.0 * ((cb_t * cb_freq * 3.0) % 1.0) - 1.0) * math.exp(-cb_t * 8.0) * 0.3  # Higher octave layer
                    cowbell = (v1 + v2) * 0.5 * math.exp(-cb_t * 15.0) * 0.35 + synth

            # --- TRAP PERCUSSION (Hats and Snare) ---
            hat = 0.0
            # Hi-hat ratchets (32nd notes) on specific steps
            is_ratchet = step % 16 in [14, 15] or (step >= 256 and step % 16 in [6, 7])
            hh_t = (step_t % (step_len / 2.0)) if is_ratchet else step_t
            if hh_t < 0.1:
                hat = noise[i % 22050] * math.exp(-hh_t * 45.0) * 0.3

            snare = 0.0
            if step % 16 == 8:  # Half-time snare on beat 3
                if step_t < 0.3:
                    sn_phase = 250 * step_t + (250 / 30.0) * (1.0 - math.exp(-step_t * 30.0))
                    sn_body = math.sin(sn_phase * 2 * math.pi) * math.exp(-step_t * 25.0)
                    sn_noise = noise[(i + 1000) % 22050] * math.exp(-step_t * 15.0)
                    snare = (sn_body + sn_noise * 1.5) * 0.55

            # --- MASTERING (Soft Clipping / Saturation) ---
            mixed = bass + cowbell + hat + snare
            mixed = math.tanh(mixed * 2.8) * 0.7  # Analog warmth & limiting

            sample = int(max(-32768, min(32767, mixed * 32767)))
            struct.pack_into("<h", buf, i * 2, sample)

        return self._create_wav_sound(buf, 22050, cache_key="theme_v2", return_path=return_path, channels=1)

    def play_curler_call(self, intensity):
        now = pygame.time.get_ticks()
        if intensity > 8.0 and (now - self.last_call) > 2500:
            self.last_call = now
            if getattr(self, "snd_hurry", None) and getattr(self, "snd_hard", None):
                if not self.ch_voice.get_busy():
                    if random.random() > 0.5:
                        self.ch_voice.play(self.snd_hurry)
                    else:
                        self.ch_voice.play(self.snd_hard)

    def stop_all_match_sounds(self):
        self.ch_slide.set_volume(0.0)
        self.ch_sweep.set_volume(0.0)
        self.ch_sfx.stop()
        self.ch_crowd.stop()

    def play_cheer(self):
        if not self.ch_crowd.get_busy() and getattr(self, "snd_cheer", None):
            self.ch_crowd.set_volume(getattr(self, "master_volume", 1.0))
            self.ch_crowd.play(self.snd_cheer)

    def update_slide(self, speed):
        self.ch_slide.set_volume((min(0.15, speed * 0.04) if speed > 0.05 else 0.0) * getattr(self, "master_volume", 1.0))

    def update_sweep(self, intensity):
        self.ch_sweep.set_volume(min(1.0, intensity * 1.25) * getattr(self, "master_volume", 1.0))
        if IS_ANDROID and intensity > 0.1:
            now = pygame.time.get_ticks()
            if not hasattr(self, "last_sweep_vib") or now - getattr(self, "last_sweep_vib", 0) > 100:
                self.last_sweep_vib = now
                vibrate_android(15)

    def play_throw(self):
        if isinstance(getattr(self, "snd_throw", None), pygame.mixer.Sound):
            self.ch_sfx.set_volume(getattr(self, "master_volume", 1.0))
            self.ch_sfx.play(self.snd_throw)

    def play_clack(self, force):
        now = pygame.time.get_ticks()
        if hasattr(self, "last_clack") and now - self.last_clack < 150:
            return
        self.last_clack = now
        ch = pygame.mixer.find_channel()
        if ch and isinstance(getattr(self, "snd_clack", None), pygame.mixer.Sound):
            ch.play(self.snd_clack)
            ch.set_volume(min(0.4, force * 0.05) * getattr(self, "master_volume", 1.0))

    def play_hover(self):
        if isinstance(getattr(self, "snd_hover", None), pygame.mixer.Sound):
            self.ch_ui.set_volume(getattr(self, "master_volume", 1.0))
            self.ch_ui.play(self.snd_hover)

    def play_click(self):
        if isinstance(getattr(self, "snd_click", None), pygame.mixer.Sound):
            self.ch_ui.set_volume(getattr(self, "master_volume", 1.0))
            self.ch_ui.play(self.snd_click)
        if IS_ANDROID:
            vibrate_android(15)

    def play_error(self):
        if isinstance(getattr(self, "snd_click", None), pygame.mixer.Sound):
            self.ch_ui.set_volume(getattr(self, "master_volume", 1.0) * 0.5)
            self.ch_ui.play(self.snd_click)

    def play_music(self, *args):
        if not getattr(self, "sfx_on", True) or not getattr(self, "snd_music", None):
            return

        target = args[0] if len(args) > 0 and args[0] else "theme"

        if getattr(self, "current_track", None) == target:
            if pygame.mixer.music.get_busy():
                return
            now = pygame.time.get_ticks()
            if now - getattr(self, "last_music_play_time", 0) < 3000:
                return

        self.current_track = target
        self.last_music_play_time = pygame.time.get_ticks()

        vol_mult = 0.8 if IS_ANDROID else 0.95
        pygame.mixer.music.set_volume(getattr(self, "master_volume", 1.0) * vol_mult)
        loaded = False

        if target != "theme":
            try:
                pygame.mixer.music.load(os.path.join(asset_dir, f"{target}.ogg"))
                loaded = True
            except:
                pass
        else:
            if isinstance(self.snd_music, list):
                for p in self.snd_music:
                    try:
                        pygame.mixer.music.load(p)
                        loaded = True
                        break
                    except:
                        pass
                if not loaded:
                    if not getattr(self, "_synth_started", False):
                        self._synth_started = True
                        import sys

                        if not (hasattr(sys, "platform") and sys.platform == "emscripten"):
                            import threading

                            def _synth_bg():
                                try:
                                    fallback = self._synthesize_theme_song(return_path=True)
                                    self._synth_ready_path = fallback
                                except:
                                    pass

                            threading.Thread(target=_synth_bg, daemon=True).start()
                        else:
                            self._synth_ready_path = "theme.ogg"

                    if getattr(self, "_synth_ready_path", None):
                        try:
                            self.snd_music = self._synth_ready_path
                            pygame.mixer.music.load(self._synth_ready_path)
                            loaded = True
                            self._synth_ready_path = None
                        except:
                            pass
            elif isinstance(self.snd_music, str):
                try:
                    pygame.mixer.music.load(self.snd_music)
                    loaded = True
                except:
                    pass

        if loaded:
            pygame.mixer.music.set_volume(getattr(self, "master_volume", 1.0) * 0.05)
            pygame.mixer.music.play(-1)

    def stop_music(self):
        pygame.mixer.music.stop()


# --- Visual Effects & Geometry ---
class Starfield:
    def __init__(self, count=150, max_w=None, max_h=None):
        self.max_h = max_h or BASE_HEIGHT
        self.stars = [
            (random.randint(0, max_w or BASE_WIDTH), random.randint(0, self.max_h), random.uniform(0.5, 3.0)) for _ in range(count)
        ]
        self.colors = {s: (int(min(255, 30 + s * 60)),) * 3 for _, _, s in self.stars}

    def draw(self, surface, speed_mult=1.0, time_mult=1.0):
        for i in range(len(self.stars)):
            x, y, s = self.stars[i]
            y = (y + s * speed_mult * time_mult) % self.max_h
            self.stars[i] = (x, y, s)
            size = max(1, int(s))
            surface.fill(self.colors[s], (int(x), int(y), size, size))


# OPTIMIZATION: Pre-rendered 3D stone for Menu to save drawing calls
class ThreeDStone:
    cached_surf = None

    @classmethod
    def render_cache(cls):
        if cls.cached_surf is not None:
            return
        r_max = 280
        surf = pygame.Surface((r_max * 2 + 80, r_max * 2 + 80), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        bx, by = r_max + 20, r_max + 30

        pygame.draw.ellipse(surf, (10, 15, 20, 100), (bx - r_max + 20, by - r_max + 30, r_max * 2, r_max * 2 - 40))
        for r in range(r_max, 150, -2):
            t = (r_max - r) / (r_max - 150)
            shade = int(70 + 80 * (1.0 - (1.0 - t) ** 3))
            pygame.draw.circle(surf, (shade, shade + 2, shade + 5), (int(bx), int(by)), r)

        pygame.draw.circle(surf, (60, 65, 70), (int(bx), int(by)), 160)
        for r in range(150, 80, -2):
            t = (150 - r) / 70.0
            col = lerp_color(HOUSE_RED, (140, 20, 30), t)
            pygame.draw.circle(surf, col, (int(bx), int(by)), r)

        draw_maple_leaf(surf, bx, by + 12, 2.5, WHITE)
        hx_start, hy_start, hx_end, hy_end = bx - 130, by + 70, bx + 130, by - 70
        for i in range(240):
            p = i / 240.0
            px, py = hx_start + (hx_end - hx_start) * p, hy_start + (hy_end - hy_start) * p
            h_col = lerp_color(BLACK, (70, 75, 80), 1.0 - abs(p - 0.5) * 2)
            pygame.draw.circle(surf, h_col, (int(px), int(py - math.sin(p * math.pi) * 90)), 32)
            pygame.draw.circle(surf, HOUSE_RED, (int(px), int(py - math.sin(p * math.pi) * 90)), 24)

        for x, y in [(hx_start, hy_start), (hx_end, hy_end)]:
            pygame.draw.circle(surf, BLACK, (int(x), int(y)), 36)
            pygame.draw.circle(surf, HOUSE_RED, (int(x), int(y)), 28)
        pygame.draw.circle(surf, BLACK, (int(hx_start), int(hy_start)), 10)
        pygame.draw.circle(surf, WHITE, (int(hx_start), int(hy_start)), 4)

        # PROPER 3D CRESCENT GLARE REFLECTION
        glare = pygame.Surface((r_max * 2, r_max * 2), pygame.SRCALPHA)
        glare.fill((0, 0, 0, 0))
        pygame.draw.circle(glare, (255, 255, 255, 120), (r_max, r_max), r_max - 10)
        pygame.draw.circle(glare, (255, 255, 255, 160), (r_max, r_max), r_max - 14)
        inner_mask = pygame.Surface((r_max * 2, r_max * 2), pygame.SRCALPHA)
        inner_mask.fill((0, 0, 0, 0))
        pygame.draw.circle(inner_mask, (255, 255, 255, 255), (r_max, r_max + 34), r_max - 10)
        glare.blit(inner_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        surf.blit(glare, (bx - r_max, by - r_max))
        cls.cached_surf = surf.convert_alpha()

    def draw(self, surface, center_x, center_y, mouse_pos):
        bx, by = center_x + (mouse_pos[0] - center_x) * 0.03, center_y + (mouse_pos[1] - center_y) * 0.03
        if self.cached_surf:
            surface.blit(self.cached_surf, (bx - 300, by - 310))


# --- Game Entities ---
class Stone:
    # OPTIMIZATION: Cache full un-rotated bases to save 6000 Pygame calls per second.
    cached_red_base = None
    cached_ylw_base = None
    cached_hl = None

    # OPTIMIZATION: Cache 360 degree rotated handles to save CPU line/circle draws per frame.
    cached_red_handles = None
    cached_ylw_handles = None

    next_id = 1

    def __init__(self, x, y, team, sid=None):
        self.id = sid if sid is not None else random.randint(1000, 9999999)
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.team, self.radius, self.mass, self.is_moving, self.curl, self.rotation = team, 32, 1.0, False, 0.0, 0.0

        if Stone.cached_red_base is None:
            Stone.cached_hl = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA).convert_alpha()
            pygame.draw.ellipse(
                Stone.cached_hl, HIGHLIGHT_COLOR, (self.radius * 0.6, self.radius * 0.2, self.radius * 0.8, self.radius * 0.4)
            )
            Stone.cached_red_base = self._render_base(HOUSE_RED)
            Stone.cached_ylw_base = self._render_base(TEAM_YELLOW)
            self._pre_render_handles()

    def _render_base(self, color):
        # BUILD 14 PREVIEW 2: Advanced 3D Geometry
        s = pygame.Surface((self.radius * 2 + 15, self.radius * 2 + 15), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(s, (0, 0, 0, 80), (self.radius + 8, self.radius + 8), self.radius)

        for r in range(self.radius, 0, -1):
            t = (self.radius - r) / self.radius
            shade = 70 + int(80 * (1.0 - (1.0 - t) ** 3))
            pygame.draw.circle(s, (shade, shade + 2, shade + 5), (self.radius + 5, self.radius + 5), r)

        pygame.draw.circle(s, color, (self.radius + 5, self.radius + 5), self.radius - 4, 6)
        # Highlight ring for 3D depth
        pygame.draw.circle(
            s,
            (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60)),
            (self.radius + 5, self.radius + 5),
            self.radius - 4,
            1,
        )

        glare = pygame.Surface((self.radius * 2 + 15, self.radius * 2 + 15), pygame.SRCALPHA).convert_alpha()
        pygame.draw.ellipse(glare, (255, 255, 255, 70), (self.radius - 3, self.radius - 9, self.radius * 1.2, self.radius * 0.6))
        s.blit(glare, (0, 0))

        return s

    @classmethod
    def _pre_render_handles(cls):
        cls.cached_red_handles = []
        cls.cached_ylw_handles = []
        for angle_deg in range(360):
            angle = math.radians(angle_deg)
            hx_s, hy_s = 32 - math.cos(angle) * 18, 32 - math.sin(angle) * 18
            hx_e, hy_e = 32 + math.cos(angle) * 22, 32 + math.sin(angle) * 22

            sr = pygame.Surface((64, 64), pygame.SRCALPHA).convert_alpha()
            sy = pygame.Surface((64, 64), pygame.SRCALPHA).convert_alpha()
            sr.fill((0, 0, 0, 0))
            sy.fill((0, 0, 0, 0))

            for s, color in [(sr, HOUSE_RED), (sy, TEAM_YELLOW)]:
                pygame.draw.line(s, (40, 40, 40), (hx_s, hy_s), (hx_e, hy_e), 14)
                for x, y in [(hx_s, hy_s), (hx_e, hy_e)]:
                    pygame.draw.circle(s, (40, 40, 40), (int(x), int(y)), 7)
                pygame.draw.line(s, color, (hx_s, hy_s), (hx_e, hy_e), 8)
                for x, y in [(hx_s, hy_s), (hx_e, hy_e)]:
                    pygame.draw.circle(s, color, (int(x), int(y)), 4)

            cls.cached_red_handles.append(sr)
            cls.cached_ylw_handles.append(sy)

    def get_state(self, offset_y=0):
        return [
            round(self.pos.x, 1),
            round(self.pos.y - offset_y, 1),
            round(self.vel.x, 2),
            round(self.vel.y, 2),
            self.team,
            round(self.curl, 2),
            round(self.rotation, 1),
            self.is_moving,
            getattr(self, "id", -1),
        ]

    def set_state(self, s, offset_y=0):
        nx, ny, nvx, nvy, self.team, self.curl, self.rotation, self.is_moving = (
            s[0],
            s[1] + offset_y,
            s[2],
            s[3],
            s[4],
            s[5],
            s[6],
            s[7],
        )
        if len(s) > 8:
            self.id = s[8]
        now = pygame.time.get_ticks()
        if hasattr(self, "last_collision_time") and now - self.last_collision_time < 400:
            return
        new_pos = pygame.math.Vector2(nx, ny)
        new_vel = pygame.math.Vector2(nvx, nvy)
        dist = (self.pos - new_pos).length()
        if not self.is_moving and not s[7]:
            self.pos.x, self.pos.y, self.vel.x, self.vel.y = nx, ny, nvx, nvy
            return
        if dist > 80.0:
            self.pos.x, self.pos.y, self.vel.x, self.vel.y = nx, ny, nvx, nvy
        else:
            if dist > 1.0:
                self.pos = self.pos.lerp(new_pos, 0.4)
            if (self.vel - new_vel).length() > 1.0:
                self.vel = self.vel.lerp(new_vel, 0.4)

    def update(self, sweep_intensity, base_friction):
        if not self.is_moving:
            return
        speed = self.vel.length()
        current_friction = max(0.008, base_friction - (sweep_intensity * 0.0012))
        if speed <= current_friction:
            self.vel.update(0, 0)
            self.is_moving = False
        else:
            self.vel.scale_to_length(speed - current_friction)
            if speed > 0.4:
                self.vel.rotate_ip((1.4 / speed) * self.curl * 0.05 * (1.0 - (sweep_intensity * 0.04)))
            self.rotation += speed * (self.curl * 2.8 if abs(self.curl * 2.8) >= 0.6 else (0.6 if self.curl >= 0 else -0.6))
            self.pos += self.vel

    def draw(self, surface, offset_x=0, offset_y=0):
        self.pos.x += offset_x
        self.pos.y += offset_y
        surface.blit(
            Stone.cached_red_base if self.team == 0 else Stone.cached_ylw_base,
            (self.pos.x - self.radius - 5, self.pos.y - self.radius - 5),
        )
        color = HOUSE_RED if self.team == 0 else TEAM_YELLOW

        deg = int(self.rotation) % 360
        handles = Stone.cached_red_handles if self.team == 0 else Stone.cached_ylw_handles
        surface.blit(handles[deg], (self.pos.x - 32, self.pos.y - 32))

        angle = math.radians(self.rotation)

        hl_s, hl_e = (
            self.pos.x - math.cos(angle) * 10 - math.sin(angle) * 2,
            self.pos.y - math.sin(angle) * 10 + math.cos(angle) * 2,
        )
        pygame.draw.circle(surface, WHITE, (int(hl_s), int(hl_e)), 2)

        surface.blit(Stone.cached_hl, (self.pos.x - self.radius, self.pos.y - self.radius))
        self.pos.x -= offset_x
        self.pos.y -= offset_y


import base64
import io


from portraits_data import PORTRAITS_B64

PIXEL_PORTRAIT_CACHE = {}


def get_pixel_portrait(name, size=(120, 120)):
    key = (name, size)
    if key in PIXEL_PORTRAIT_CACHE:
        return PIXEL_PORTRAIT_CACHE[key]

    b64 = PORTRAITS_B64.get(name, PORTRAITS_B64["Player"])
    data = base64.b64decode(b64)
    surf = pygame.image.load(io.BytesIO(data)).convert_alpha()

    # High res 2D Sprite
    scaled = pygame.transform.smoothscale(surf, size)

    PIXEL_PORTRAIT_CACHE[key] = scaled
    return scaled


RETRO_PORTRAIT_CACHE = {}


def get_retro_portrait(name, size=(300, 300), pixelation_factor=4):
    key = (name, size, pixelation_factor)
    if key in RETRO_PORTRAIT_CACHE:
        return RETRO_PORTRAIT_CACHE[key]

    b64 = PORTRAITS_B64.get(name, PORTRAITS_B64["Player"])
    data = base64.b64decode(b64)
    surf = pygame.image.load(io.BytesIO(data)).convert_alpha()

    small_size = (size[0] // pixelation_factor, size[1] // pixelation_factor)
    small_surf = pygame.transform.smoothscale(surf, small_size)
    pixelated = pygame.transform.scale(small_surf, size)

    RETRO_PORTRAIT_CACHE[key] = pixelated
    return pixelated


class AnimatedCurler:
    _head_cache = {}

    def __init__(self, hack_pos):
        self.hack_pos = pygame.math.Vector2(hack_pos)
        self.delivery_progress = 0.0
        self.state = "IDLE"

    def update(self, state, drag_vector=None):
        self.state = state
        if self.state == "LUNGING":
            self.delivery_progress = min(1.0, self.delivery_progress + 0.04)
            if self.delivery_progress >= 1.0:
                self.state = "IDLE"
                self.delivery_progress = 0.0
        elif self.state == "BACKSWING" and drag_vector:
            self.delivery_progress = min(1.0, drag_vector.length() / 250.0)
        else:
            self.delivery_progress = 0.0

    def _draw_char_geometry(self, surface, hx, hy, offset_y, lunge_dist, override_color=None, is_evil=False):
        def c(col):
            return override_color or col

        def draw_cylinder_line(surf, color, start, end, width):
            if override_color:
                pygame.draw.line(surf, override_color, start, end, width)
                return
            shadow_col = (max(0, color[0] - 70), max(0, color[1] - 70), max(0, color[2] - 70))
            mid_col = (max(0, color[0] - 20), max(0, color[1] - 20), max(0, color[2] - 20))
            hl_col = (min(255, color[0] + 80), min(255, color[1] + 80), min(255, color[2] + 80))
            pygame.draw.line(surf, shadow_col, start, end, width)
            pygame.draw.line(surf, mid_col, start, end, max(2, width - 4))
            pygame.draw.line(surf, color, start, end, max(1, width - 8))
            pygame.draw.line(surf, hl_col, (start[0] - 2, start[1]), (end[0] - 2, end[1]), max(1, width - 12))

        def draw_cylinder_rect(surf, color, rect, border_radius=0):
            if override_color:
                pygame.draw.rect(surf, override_color, rect, border_radius=border_radius)
                return
            x, y, w, h = rect
            shadow_col = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
            hl_col = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))

            pygame.draw.rect(surf, shadow_col, (x, y, w, h), border_radius=border_radius)
            if w > 8 and h > 4:
                pygame.draw.rect(surf, color, (x + 4, y + 2, w - 8, h - 4), border_radius=max(0, border_radius - 2))
            if w > 20 and h > 8:
                pygame.draw.rect(surf, hl_col, (x + 10, y + 4, w // 2 - 6, h - 8), border_radius=max(0, border_radius - 4))
                pygame.draw.rect(surf, color, (x + 14, y + 6, w // 2 - 12, h - 12), border_radius=max(0, border_radius - 6))

        def head(ix, iy, is_evil=False):
            cache_key = (self.tc, override_color, is_evil)
            if cache_key not in AnimatedCurler._head_cache:
                surf = pygame.Surface((60, 80), pygame.SRCALPHA)
                cx, cy = 30, 40

                head_rw, head_rh = 15, 12
                # Base skin tone
                pygame.draw.ellipse(surf, c((240, 200, 180)), (cx - head_rw, cy - head_rh, head_rw * 2, head_rh * 2))

                if is_evil and not override_color:
                    # Jagged Wario mustache sticking out the sides
                    pygame.draw.polygon(
                        surf,
                        (20, 20, 20),
                        [(cx - head_rw + 2, cy), (cx - head_rw - 8, cy - 8), (cx - head_rw - 2, cy + 6), (cx - head_rw - 12, cy)],
                    )
                    pygame.draw.polygon(
                        surf,
                        (20, 20, 20),
                        [(cx + head_rw - 2, cy), (cx + head_rw + 8, cy - 8), (cx + head_rw + 2, cy + 6), (cx + head_rw + 12, cy)],
                    )

                if not override_color:
                    import math
                    import random

                    rng = random.Random(self.tc[0] + self.tc[1])  # Deterministic seed based on team color
                    hair_poly = []
                    shade = max(0, self.tc[0] - 100)
                    hair_color = (shade, int(shade * 0.75), int(shade * 0.55))

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
                        hair_poly.append((cx + math.cos(rad) * r, cy + math.sin(rad) * r))

                    pygame.draw.polygon(surf, hair_color, hair_poly)
                else:
                    pygame.draw.ellipse(surf, c((80, 50, 30)), (cx - head_rw, cy - head_rh, head_rw * 2, head_rh * 2))

                # Beanie Base
                hat_rw, hat_rh = 19, 14
                hat_shade = (max(0, self.tc[0] - 80), max(0, self.tc[1] - 80), max(0, self.tc[2] - 80))

                # The beanie pulled down over the back of the head
                pygame.draw.ellipse(surf, c(hat_shade), (cx - hat_rw - 1, cy - head_rh - 6, hat_rw * 2 + 2, hat_rh * 2 + 2))
                pygame.draw.ellipse(surf, c(self.tc), (cx - hat_rw, cy - head_rh - 5, hat_rw * 2, hat_rh * 2))

                if not override_color:
                    pygame.draw.ellipse(
                        surf,
                        (min(255, self.tc[0] + 40), min(255, self.tc[1] + 40), min(255, self.tc[2] + 40)),
                        (cx - hat_rw + 4, cy - head_rh - 3, hat_rw * 2 - 8, 6),
                    )

                # Beanie Brim (Curves across the back of the head)
                pygame.draw.rect(surf, c(hat_shade), (cx - hat_rw - 2, cy - head_rh + 4, hat_rw * 2 + 4, 10), border_radius=4)
                pygame.draw.rect(surf, c(self.tc), (cx - hat_rw - 1, cy - head_rh + 5, hat_rw * 2 + 2, 8), border_radius=3)
                pygame.draw.rect(surf, c(CYAN_ACCENT), (cx - hat_rw - 1, cy - head_rh + 7, hat_rw * 2 + 2, 3), border_radius=1)

                # Pom-pom (Slightly shifted up for back perspective)
                if not override_color:
                    for r in range(9, 0, -1):
                        if is_evil:
                            s = (80 + r * 10, 20 + r * 5, 120 + r * 12)
                            pygame.draw.circle(surf, s, (cx, cy - head_rh - 9), r)
                        else:
                            s = 140 + r * 11
                            pygame.draw.circle(surf, (s, s, s), (cx, cy - head_rh - 9), r)
                else:
                    pygame.draw.circle(surf, c((180, 180, 180)), (cx, cy - head_rh - 9), 9)

                AnimatedCurler._head_cache[cache_key] = surf

            surface.blit(AnimatedCurler._head_cache[cache_key], (ix - 30, iy - 40))

        PURPLE_SUIT = (106, 13, 173)
        CYAN_ACCENT = (50, 200, 255)
        accent_color = PURPLE_SUIT if is_evil else CYAN_ACCENT

        if self.state == "BACKSWING":
            # 3D Legs
            draw_cylinder_line(surface, (30, 30, 35), (hx - 15, hy + 90 + offset_y), (hx - 20, hy + 140 + offset_y), 16)
            draw_cylinder_line(surface, (30, 30, 35), (hx + 15, hy + 90 + offset_y), (hx + 20, hy + 140 + offset_y), 16)

            # SHOES
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx - 28, hy + 135 + offset_y, 20, 30))
            pygame.draw.ellipse(surface, c((240, 240, 240)), (hx - 26, hy + 137 + offset_y, 16, 26))
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx + 12, hy + 135 + offset_y, 20, 30))
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx + 14, hy + 137 + offset_y, 16, 26))

            # Back of Neck
            if override_color:
                pygame.draw.rect(surface, c((240, 200, 180)), (int(hx - 8), int(hy + offset_y), 16, 20))
            else:
                pygame.draw.rect(surface, (200, 150, 130), (int(hx - 8), int(hy + offset_y), 16, 20))
                # Hair shadow cast onto the back of the neck
                pygame.draw.rect(surface, (160, 110, 90), (int(hx - 8), int(hy + offset_y), 16, 6))

            # 90s Tracksuit Body (Back View)
            if override_color:
                pygame.draw.rect(surface, c(PURPLE_SUIT), (hx - 35, hy + 20 + offset_y, 70, 80), border_radius=16)
            else:
                draw_cylinder_rect(surface, self.tc, (hx - 36, hy + 18 + offset_y, 72, 84), border_radius=16)

            # Tracksuit accent lines (Center zipper removed for back view)
            pygame.draw.line(surface, c(accent_color), (hx - 20, hy + 30 + offset_y), (hx - 20, hy + 92 + offset_y), 4)
            pygame.draw.line(surface, c(accent_color), (hx + 20, hy + 30 + offset_y), (hx + 20, hy + 92 + offset_y), 4)

            # Tracksuit Collar (Wraps fully around the back of the neck)
            if override_color:
                pygame.draw.rect(
                    surface, c(PURPLE_SUIT) if is_evil else c(accent_color), (hx - 16, hy + 10 + offset_y, 32, 14), border_radius=4
                )
            else:
                draw_cylinder_rect(surface, self.tc, (hx - 17, hy + 9 + offset_y, 34, 16), border_radius=4)

            # Full Head Overlap
            head(hx, hy - 8 + offset_y, is_evil)

            # 3D Forward Arm
            draw_cylinder_line(surface, (210, 180, 50), (hx - 55, hy + 10 + offset_y), (hx - 15, hy + 45 + offset_y), 10)

            # Hand & Hack Foot Shadows
            pygame.draw.ellipse(surface, c((90, 10, 15)), (hx - 71, hy - 1 + offset_y, 28, 20))
            if not override_color:
                pygame.draw.ellipse(surface, HOUSE_RED, (hx - 69, hy + 1 + offset_y, 24, 16))

            pygame.draw.ellipse(surface, c(PURPLE_SHADOW), (hx - 48, hy + 28 + offset_y, 31, 56))
            pygame.draw.ellipse(surface, c(self.tc), (hx - 45, hy + 30 + offset_y, 25, 50))
            pygame.draw.ellipse(surface, c(PURPLE_SHADOW), (hx + 17, hy + 28 + offset_y, 31, 56))
            pygame.draw.ellipse(surface, c(self.tc), (hx + 20, hy + 30 + offset_y, 25, 50))

            if not override_color:
                hl = (min(255, self.tc[0] + 40), min(255, self.tc[1] + 40), min(255, self.tc[2] + 40))
                pygame.draw.ellipse(surface, hl, (hx - 42, hy + 32 + offset_y, 10, 40))
                pygame.draw.ellipse(surface, hl, (hx + 22, hy + 32 + offset_y, 10, 40))

        elif self.state == "LUNGING":
            ly = hy + lunge_dist

            # 3D Forward Leg
            draw_cylinder_line(surface, (30, 30, 35), (hx - 12, ly + 60), (hx - 15, hy + 110), 18)
            # SHOE (Forward)
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx - 25, hy + 105, 24, 34))
            pygame.draw.ellipse(surface, c((240, 240, 240)), (hx - 23, hy + 107, 20, 30))

            # Trailing Leg
            pygame.draw.polygon(surface, c((15, 15, 20)), [(hx + 6, ly + 48), (hx + 34, ly + 99), (hx + 10, ly + 104)])
            if not override_color:
                pygame.draw.polygon(surface, (50, 50, 55), [(hx + 10, ly + 52), (hx + 30, ly + 94), (hx + 14, ly + 97)])
            # SHOE (Trailing)
            pygame.draw.ellipse(surface, c((20, 20, 20)), (hx + 22, ly + 94, 20, 30))

            # Back of Neck
            if override_color:
                pygame.draw.rect(surface, c((240, 200, 180)), (int(hx - 8), int(ly - 48), 16, 20))
            else:
                pygame.draw.rect(surface, (200, 150, 130), (int(hx - 8), int(ly - 48), 16, 20))
                # Hair shadow
                pygame.draw.rect(surface, (160, 110, 90), (int(hx - 8), int(ly - 48), 16, 6))

            # 90s Tracksuit Body (Back View)
            if override_color:
                pygame.draw.rect(surface, c(PURPLE_SUIT), (hx - 30, ly - 30, 60, 90), border_radius=15)
            else:
                draw_cylinder_rect(surface, self.tc, (hx - 32, ly - 32, 64, 94), border_radius=15)

            # Tracksuit accent lines (Center zipper removed for back view)
            pygame.draw.line(surface, c(accent_color), (hx - 15, ly - 15), (hx - 15, ly + 50), 4)
            pygame.draw.line(surface, c(accent_color), (hx + 15, ly - 15), (hx + 15, ly + 50), 4)

            # Tracksuit Collar
            if override_color:
                pygame.draw.rect(
                    surface, c(PURPLE_SUIT) if is_evil else c(accent_color), (hx - 16, ly - 39, 32, 14), border_radius=4
                )
            else:
                draw_cylinder_rect(surface, self.tc, (hx - 17, ly - 40, 34, 16), border_radius=4)

            # Full Head Overlap
            head(hx, ly - 45, is_evil)

            # 3D Lunging Arm
            draw_cylinder_line(surface, (210, 180, 50), (hx - 75, ly - 10), (hx - 20, ly + 20), 10)

            # Slider Hand
            pygame.draw.ellipse(surface, c((90, 10, 15)), (hx - 92, ly - 19, 32, 20))
            if not override_color:
                pygame.draw.ellipse(surface, HOUSE_RED, (hx - 90, ly - 17, 28, 16))

            # Broom Arm
            draw_cylinder_line(surface, self.tc, (hx - 25, ly - 10), (hx - 10, ly - 60), 16)

    def draw(self, surface, team_color, is_evil=False):
        if self.state == "IDLE" and self.delivery_progress == 0.0:
            return
        self.tc = team_color
        oy = self.delivery_progress * 70 if self.state == "BACKSWING" else 0
        ld = (1.0 - self.delivery_progress) * -190 if self.state == "LUNGING" else 0

        if not hasattr(self, "shadow_surf"):
            self.shadow_surf = pygame.Surface((250, 450), pygame.SRCALPHA).convert_alpha()
        self.shadow_surf.fill((0, 0, 0, 0))
        self._draw_char_geometry(self.shadow_surf, 125 + 18, 200 + 18, oy, ld, (0, 0, 0, 100), is_evil)
        surface.blit(self.shadow_surf, (self.hack_pos.x - 125, self.hack_pos.y - 200))

        self._draw_char_geometry(surface, self.hack_pos.x, self.hack_pos.y, oy, ld, None, is_evil)

    def render_portrait(self, surface, x, y, size, team_color, is_evil=False, bob_y=0):
        if not hasattr(self, "cached_portrait") or getattr(self, "cached_portrait_size", 0) != size:
            self.tc = team_color
            old_state = self.state
            self.state = "BACKSWING"

            temp_surf = pygame.Surface((180, 260), pygame.SRCALPHA).convert_alpha()
            temp_surf.fill((255, 255, 255, 0))
            self._draw_char_geometry(temp_surf, 90, 60, 0, 0, None, is_evil)

            scaled = pygame.transform.smoothscale(temp_surf, (size, int(size * 260 / 180))).convert_alpha()
            self.cached_portrait = scaled
            self.cached_portrait_size = size
            self.state = old_state

        surface.blit(self.cached_portrait, (x, y + bob_y))


STORY_RINKS = [
    {
        "name": "Corporate Lobby",
        "boss": "CEO Smogsworth",
        "color": (255, 50, 50),
        "intro_dialog": [
            "I'm CEO Smogsworth, and I've just acquired your curling club.",
            "This entire building is being demolished to build our new corporate parking garage.",
            "You think you can stop me? I'm wearing a $5,000 suit!",
            "I've optimized my curling strategy through endless corporate synergies.",
            "Let's get this over with, I have a tee time at 4.",
        ],
        "win_dialog": ["My suit is ruined! My stock options! I'll buy you out!", "This was not in the quarterly projections!"],
        "taunts": [
            "Synergy!",
            "Think outside the box!",
            "Let's circle back to my victory!",
            "You're fired!",
            "Hostile takeover!",
            "My lawyers will hear about this!",
            "Quarterly profits are up!",
            "Liquidating your assets!",
            "Corporate restructuring!",
            "I'm delegating your defeat!",
            "Downsizing your score!",
            "Let's touch base on how bad you are!",
            "Outsourced!",
            "Low hanging fruit!",
            "Core competency!",
            "Leveraging my advantage!",
            "Paradigm shift!",
            "Monetizing this win!",
            "You're not a team player!",
            "Performance review: FAIL!",
            "Strategic misalignment!",
            "Return on investment!",
            "Executive decision!",
        ],
        "difficulty": 3,
    },
    {
        "name": "Crypto Mine Rink",
        "boss": "Tremor",
        "color": (200, 180, 50),
        "intro_dialog": [
            "We're melting the ice to liquid-cool our crypto rigs!",
            "Do you have any idea how many CurlCoins I'm mining?",
            "Your traditional curling club is standing in the way of decentralization.",
            "Fiat currency is dead. Welcome to the new digital economy.",
            "I'm going to blockchain you out of existence!",
        ],
        "win_dialog": ["My wallet got hacked! The market crashed!", "I lost my private keys!"],
        "taunts": [
            "To the moon!",
            "Blockchain verified!",
            "Mining another point!",
            "Decentralized destruction!",
            "Liquid cooling engaged!",
            "Your hash rate is too low!",
            "Proof of work!",
            "Minting a victory!",
            "Crypto dominance!",
            "You're getting liquidated!",
            "Diamond hands!",
            "Smart contract executed!",
            "Bear market for you!",
            "HODL this defeat!",
            "Gas fees are too high!",
            "Rug pull!",
            "Bullish on me, bearish on you!",
            "Yield farming!",
            "Pump and dump!",
            "Altcoin energy!",
            "Staking my claim!",
            "Web3 superiority!",
            "NFT drop incoming!",
            "Airdropping a loss on you!",
            "Market cap exceeded!",
        ],
        "difficulty": 5,
    },
    {
        "name": "Social Media Hub",
        "boss": "Poly Mer",
        "color": (220, 100, 150),
        "intro_dialog": [
            "We're turning this place into a giant content house!",
            "Curling isn't viral enough. We need TikTok dances on the ice!",
            "I'm live-streaming my victory to millions of followers right now.",
            "Make sure to smash that subscribe button while I smash your stones.",
            "Don't forget to like, subscribe, and watch me win!",
        ],
        "win_dialog": ["I'm losing followers! My engagement is tanking!", "I'm being cancelled!"],
        "taunts": [
            "Trending #1!",
            "Going viral!",
            "Check out this content!",
            "Like and subscribe!",
            "Live-streaming my victory!",
            "You're getting cancelled!",
            "My engagement is off the charts!",
            "Sponsored shot!",
            "Algorithm favored!",
            "Do it for the views!",
            "You're losing followers!",
            "Unsubscribed!",
            "Shadowbanned!",
            "Perfect aesthetic!",
            "Ratio'd!",
            "Clickbait curling!",
            "Influencer status!",
            "You didn't pass the vibe check!",
            "Collab denied!",
            "Swipe up to lose!",
            "Monetized!",
            "Brand deal secured!",
            "Spill the tea!",
            "Main character energy!",
            "Getting demonetized!",
        ],
        "difficulty": 6,
    },
    {
        "name": "AI Startup Arena",
        "boss": "Dr. Sludge",
        "color": (150, 200, 150),
        "intro_dialog": [
            "My predictive AI models have solved curling.",
            "Human error is a flaw we've completely engineered out of the game.",
            "We're replacing the ice with a massive neural network cooling system.",
            "I have simulated this match 14 million times.",
            "Your defeat has a 99.9% probability.",
        ],
        "win_dialog": ["Error 404: Victory not found. Recalibrating...", "Division by zero!"],
        "taunts": [
            "Predictive model accurate!",
            "Neural network engaged!",
            "Human error detected!",
            "Machine learning complete!",
            "Probability of your success: 0%!",
            "Automated victory!",
            "My algorithms are superior!",
            "Calculating trajectory...",
            "Artificial intelligence wins!",
            "You're obsolete!",
            "Optimizing shot parameters!",
            "Data set complete!",
            "Deep learning in action!",
            "System update: You lose!",
            "Turing test failed!",
            "Garbage in, garbage out!",
            "I'm recursively destroying you!",
            "Vector math wins!",
            "Gradient descent!",
            "Overfitting your weaknesses!",
            "Backpropagation successful!",
            "Heuristic analysis complete!",
            "Self-driving stone!",
            "You need more training data!",
        ],
        "difficulty": 7,
    },
    {
        "name": "Metaverse Dome",
        "boss": "Timber Baroness",
        "color": (100, 50, 150),
        "intro_dialog": [
            "Why curl in the real world when the Metaverse is so much better?",
            "We're bulldozing this physical club to build a massive VR simulation center.",
            "Put on the headset and accept the new digital reality.",
            "Physical friction is just a setting in my physics engine.",
            "I'm about to disconnect you!",
        ],
        "win_dialog": ["My headset is glitching! I'm stuck in the real world!", "VR sickness kicking in!"],
        "taunts": [
            "Virtual reality check!",
            "You're lagging in the matrix!",
            "My avatar is unstoppable!",
            "Metaverse dominance!",
            "Disconnecting your hopes!",
            "Digital perfection!",
            "Welcome to the simulation!",
            "Your reality is flawed!",
            "Uploading defeat!",
            "Virtual victory!",
            "Headset firmly on!",
            "Escaping to the digital realm!",
            "You're just an NPC!",
            "System crash imminent for you!",
            "Polygon perfection!",
            "Respawn denied!",
            "Glitch in the system!",
            "Your graphics card is too weak!",
            "Rendered useless!",
            "Hitbox advantage!",
            "Clipping through your defense!",
            "Cyber-curling champion!",
            "VR sickness!",
            "Bandwidth throttled!",
        ],
        "difficulty": 8,
    },
    {
        "name": "Big Data Complex",
        "boss": "Baron Von Crude",
        "color": (80, 100, 80),
        "intro_dialog": [
            "This curling rink takes up too much prime real estate.",
            "We're installing 10,000 server racks right where the button is.",
            "Your data belongs to us now.",
            "I have indexed every possible move you could make.",
            "Prepare to be formatted!",
        ],
        "win_dialog": ["Critical system failure! Data corrupted!", "My hard drives!"],
        "taunts": [
            "Data collected!",
            "Formatting your hopes!",
            "Server racks cooling!",
            "Big data always wins!",
            "Analyzing your weaknesses!",
            "Storing your defeat!",
            "My bandwidth is unlimited!",
            "Downloading a victory!",
            "You're out of storage!",
            "System override!",
            "Processing power at max!",
            "Your firewall has been breached!",
            "Data corrupted!",
            "Server farm dominance!",
            "Packet loss detected!",
            "Query successful!",
            "Indexed and archived!",
            "You've been fragmented!",
            "Caching the win!",
            "SQL injection successful!",
            "Database locked!",
            "Root access granted!",
            "Overclocked!",
            "Ransomware activated!",
        ],
        "difficulty": 9,
    },
    {
        "name": "Cloud Host Club",
        "boss": "Syntax Terror",
        "color": (120, 150, 200),
        "intro_dialog": [
            "I am Syntax Terror, architect of the global data grid.",
            "This pathetic analog club is standing in the way of my server expansion.",
            "Your archaic physical stones stand no chance against my optimized algorithms.",
            "I control the cloud, the data, and the physics of this rink.",
            "Prepare for a fatal exception!",
        ],
        "win_dialog": ["Server offline! My ping is spiking! Nooo!", "Kernel panic!"],
        "taunts": [
            "Fatal exception!",
            "High latency!",
            "You're lagging!",
            "My algorithms are flawless!",
            "Data center dominance!",
            "Cloud superiority!",
            "Uploading a perfect shot!",
            "Your processing power is weak!",
            "Optimized trajectory!",
            "Server cooling engaged!",
            "Virtual perfection!",
            "Your analog skills are obsolete!",
            "Buffering... defeat!",
            "Ping timeout!",
            "Cloud computing wins!",
            "Segmentation fault!",
            "Connection lost!",
            "Blue screen of death!",
        ],
        "difficulty": 10,
    },
]


class StoryManager:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.stats = {"power": 0, "curl_control": 0, "trajectory_preview": 0}
        self.current_rink = 0
        self.trophies = []

    def to_dict(self):
        return {
            "level": self.level,
            "xp": self.xp,
            "stats": self.stats,
            "current_rink": self.current_rink,
            "trophies": self.trophies,
        }

    def from_dict(self, d):
        self.level = d.get("level", 1)
        self.xp = d.get("xp", 0)
        self.stats = d.get("stats", {"power": 0, "curl_control": 0, "trajectory_preview": 0})
        for k in self.stats:
            self.stats[k] = int(self.stats[k]) if getattr(self.stats[k], "is_integer", lambda: True)() else 0
        self.current_rink = d.get("current_rink", 0)
        self.trophies = d.get("trophies", [])


# --- Main Engine ---
class WinCurl3:
    def __init__(self):
        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

        self.ui_selected_index = 0
        self.ui_nav_dir = None
        self.ui_nav_select = False
        self.last_nav_time = 0

        self.screen = None
        self.canvas = None
        self.current_mapped_pos = pygame.math.Vector2(BASE_WIDTH // 2, BASE_HEIGHT // 2)
        self.is_pointer_pressed = False

        self.story = StoryManager()

        # BUILD 14 PREVIEW 2: Advanced Chat State
        self.chat_messages = []
        self.typing_chat = False
        self.chat_input = ""
        self.frames_elapsed = 0

    def get_active_ui_rects(self):
        global ACTIVE_UI_RECTS_PREV
        return ACTIVE_UI_RECTS_PREV

    def get_pointer_pos(self):
        return self.current_mapped_pos

    def get_pointer_pressed(self):
        return self.is_pointer_pressed

    def scale_mouse(self, pos):
        if IS_ANDROID or getattr(self, "is_web", False):
            if isinstance(pos, pygame.math.Vector2):
                return pos
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
        self.title_font = CachedFont(pygame.font.Font(None, 120))
        self.large_sym_font = CachedFont(pygame.font.Font(None, 95))
        self.font_62 = CachedFont(pygame.font.Font(None, 60))
        self.font_72 = CachedFont(pygame.font.Font(None, 70))
        self.font_85 = CachedFont(pygame.font.Font(None, 82))

        self.sprites = {}

        # Pre-allocate dark overlays used in UI
        self.dark_overlay_150 = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.dark_overlay_150.fill((0, 0, 0, 150))
        self.dark_overlay_200 = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.dark_overlay_200.fill((0, 0, 0, 200))

        t_text = "WinCurl 3"

        # Use standard Pygame font for the original heavy bold look.
        # Render at exactly 2x scale (210) to bypass SDL_ttf hinting clipping bugs on the top edge of letters like "C".
        ss_font = CachedFont(pygame.font.Font(None, 240))
        ss_white = ss_font.render(t_text, True, WHITE)
        ss_purple = ss_font.render(t_text, True, (80, 20, 140))

        # Smoothscale down by exactly half to get a pristine, unclipped 105-point title
        target_size = (ss_white.get_width() // 2, ss_white.get_height() // 2)
        self.title_base = pygame.transform.smoothscale(ss_white, target_size)
        self.title_shadow = pygame.transform.smoothscale(ss_purple, target_size)

        # Pre-render the thick 36-sample rounded outline so we don't kill the FPS doing 36 blits per frame!
        outline_size = 7
        pad = outline_size + 2
        self.title_outline = pygame.Surface(
            (self.title_shadow.get_width() + pad * 2, self.title_shadow.get_height() + pad * 2), pygame.SRCALPHA
        )
        self.title_outline.fill((0, 0, 0, 0))  # Explicitly clear to transparent to fix backend black-rectangle bug
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            dx, dy = math.cos(rad) * outline_size, math.sin(rad) * outline_size
            self.title_outline.blit(self.title_shadow, (pad + dx, pad + dy))

        # Pre-render hypnotic rainbow text background (tighter period for trippier effect)
        rw = self.title_base.get_width() + 600
        self.rainbow_grad = pygame.Surface((rw, 200)).convert()
        for x in range(rw):
            c = pygame.Color(0)
            c.hsva = ((x / 150.0) * 360 % 360, 90, 100, 100)
            pygame.draw.line(self.rainbow_grad, c, (x, 0), (x, 200))

        # Live-rendered rainbow text avoids a 50-frame pre-generation delay (fixes Android load time)
        self.title_rainbow_frame = pygame.Surface(self.title_base.get_size(), pygame.SRCALPHA).convert_alpha()

        # Realistic Olympic Push Broom Rendering
        self.broom_surf = pygame.Surface((80, 260), pygame.SRCALPHA)
        pygame.draw.rect(self.broom_surf, (215, 215, 30), (35, 0, 10, 220), border_radius=4)
        pygame.draw.rect(self.broom_surf, (40, 40, 45), (20, 220, 40, 20), border_radius=4)
        pygame.draw.rect(self.broom_surf, (225, 225, 225), (10, 240, 60, 18), border_radius=6)
        pygame.draw.line(self.broom_surf, (150, 150, 150), (12, 248), (68, 248), 2)

        self.broom_cache = {}
        for i in range(-30, 32, 2):
            self.broom_cache[i] = pygame.transform.rotate(self.broom_surf, i)

        # Pre-render coins for butter-smooth Android coin flip
        self.coin_red_surf = self._render_coin_surface(True)
        self.coin_yellow_surf = self._render_coin_surface(False)
        ThreeDStone.render_cache()

        # Pre-cache all UI buttons to eliminate Android boot-lag
        for c in [(40, 120, 200), (60, 60, 65), TEAM_YELLOW, HOUSE_RED, (40, 150, 80), (150, 40, 80), HOUSE_BLUE]:
            UICache.get_glass(600, 100, c, 50, False)
        for c in [(50, 60, 80), (50, 55, 65)]:
            UICache.get_glass(80, 80, c, 40, False)
        UICache.get_glass(200, 90, (255, 180, 180), 16, False)
        UICache.get_glass(200, 90, (180, 255, 180), 16, False)

    def _render_coin_surface(self, is_red):
        surf = pygame.Surface((280, 280), pygame.SRCALPHA).convert_alpha()
        cx, cy, r_w, r_h = 140, 140, 120, 120
        for i in range(15):
            pygame.draw.ellipse(surf, (150, 110, 10), (cx - r_w, cy - r_h // 2 + 15 - i, r_w * 2, r_h))
        pygame.draw.ellipse(surf, (255, 215, 0), (cx - r_w, cy - r_h // 2, r_w * 2, r_h))
        pygame.draw.ellipse(
            surf, (220, 170, 20), (cx - int(r_w * 0.85), cy - int(r_h * 0.85) // 2, int(r_w * 0.85) * 2, int(r_h * 0.85))
        )
        pygame.draw.ellipse(
            surf, (255, 215, 0), (cx - int(r_w * 0.75), cy - int(r_h * 0.75) // 2, int(r_w * 0.75) * 2, int(r_h * 0.75))
        )
        if is_red:
            draw_maple_leaf(surf, cx, cy, 2.0, HOUSE_RED)
        else:
            rw = 55
            pygame.draw.ellipse(surf, (90, 95, 100), (cx - rw, cy - 10, rw * 2, 30))
            pygame.draw.ellipse(surf, (150, 155, 160), (cx - rw, cy - 25, rw * 2, 35))
            pygame.draw.ellipse(surf, HOUSE_BLUE, (cx - rw, cy - 15, rw * 2, 18))
            pygame.draw.ellipse(surf, (170, 175, 180), (cx - rw * 0.75, cy - 32, rw * 1.5, 25))
            pygame.draw.ellipse(surf, HOUSE_BLUE, (cx - rw * 0.25, cy - 35, rw * 0.5, 12))
            pygame.draw.lines(
                surf,
                HOUSE_BLUE,
                False,
                [(cx - rw * 0.4, cy - 25), (cx - rw * 0.4, cy - 48), (cx + rw * 0.2, cy - 48), (cx + rw * 0.4, cy - 25)],
                8,
            )

        glare = pygame.Surface((r_w * 2, r_h), pygame.SRCALPHA).convert_alpha()
        pygame.draw.ellipse(glare, (255, 255, 255, 60), (int(r_w * 0.2), int(r_h * 0.1), int(r_w * 1.6), int(r_h * 0.4)))
        surf.blit(glare, (cx - r_w, cy - r_h // 2))
        return surf

    def setup_display(self):
        import sys

        if sys.platform == "win32":
            import ctypes

            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
        import os

        os.environ["SDL_RENDER_SCALE_QUALITY"] = "1"

        pygame.display.init()
        gm = getattr(self, "game_mode", "MENU")
        pygame.display.set_caption(f"WinCurl {VERSION}{'' if gm == 'MENU' else ' - ' + gm}")

        info = pygame.display.Info()

        try:
            allowed = [pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]
            for attr in ["FINGERDOWN", "FINGERUP", "FINGERMOTION", "WINDOWRESIZED", "WINDOWEXPOSED", "TEXTINPUT"]:
                if hasattr(pygame, attr):
                    allowed.append(getattr(pygame, attr))
            pygame.event.set_allowed(allowed)
        except:
            pass

        global BASE_HEIGHT
        if IS_ANDROID and info.current_w > 0 and info.current_h > 0:
            aspect = info.current_h / info.current_w
            BASE_HEIGHT = int(BASE_WIDTH * aspect)

        if sys.platform == "emscripten":
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.SCALED)
        elif IS_ANDROID:
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.SCALED)
        else:
            desk_h = info.current_h
            if desk_h > 0 and BASE_HEIGHT > desk_h * 0.85:
                target_h = int(desk_h * 0.85)
                target_w = int(target_h * (BASE_WIDTH / BASE_HEIGHT))
                self.screen = pygame.display.set_mode((target_w, target_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
            else:
                self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)

        try:
            if not IS_ANDROID:
                ThreeDStone.render_cache()
                try:
                    pygame.image.save(ThreeDStone.cached_surf, "icon.png")
                except:
                    pass
                try:
                    pygame.image.save(ThreeDStone.cached_surf, "icon.png")
                except:
                    pass
                try:
                    import shutil

                    for target_dir in [
                        "wincurl_android",
                        "wincurl_android/wincurl_build_clean",
                        "wincurl/wincurl_android",
                        "wincurl/wincurl_android/wincurl_build_clean",
                    ]:
                        if os.path.exists(target_dir):
                            pygame.image.save(ThreeDStone.cached_surf, os.path.join(target_dir, "icon.png"))
                except:
                    pass

            if not IS_ANDROID:
                try:
                    pygame.display.set_icon(pygame.image.load("icon.png"))
                except:
                    pass

                if hasattr(os, "name") and os.name == "posix":
                    desk_dir = os.path.expanduser("~/.local/share/applications")
                    os.makedirs(desk_dir, exist_ok=True)
                    desk_path = os.path.join(desk_dir, "wincurl3.desktop")
                    if not os.path.exists(desk_path):
                        icon_path = os.path.abspath("icon.png")
                        exec_path = os.path.abspath(sys.argv[0])
                        with open(desk_path, "w") as f:
                            f.write(
                                f"[Desktop Entry]\nName=WinCurl 3\nExec=python3 {exec_path}\nIcon={icon_path}\nType=Application\nTerminal=false\nCategories=Game;\nStartupWMClass=wincurl3\n"
                            )
                        os.system(f"update-desktop-database {desk_dir} >/dev/null 2>&1")
        except:
            pass

        self.is_4k = info.current_w >= 1920 or info.current_h >= 1080
        if IS_ANDROID or getattr(self, "is_web", False):
            self.canvas = self.screen
        else:
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

        if IS_ANDROID:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.environ.get("ANDROID_PRIVATE", os.path.abspath(os.path.join(app_dir, "..")))
        else:
            base_dir = os.path.expanduser("~")

        self.save_file = os.path.join(base_dir, ".wincurl3_save.json")

        # Fallback to pref path if it exists but home dir save doesn't
        try:
            pref_path = pygame.system.get_pref_path("jason", "wincurl3")
            pref_save = os.path.join(pref_path, ".wincurl3_save.json")
            if os.path.exists(pref_save) and not os.path.exists(self.save_file):
                self.save_file = pref_save
        except:
            pass
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
        self.typing_target = None
        self.net_action = None
        self.prompt_rect = pygame.Rect(BASE_WIDTH // 2 - 350, BASE_HEIGHT // 2 - 50, 700, 120)

        self.btn_curl_l, self.btn_curl_r = pygame.Rect(120, BASE_HEIGHT - 260, 200, 90), pygame.Rect(
            BASE_WIDTH - 320, BASE_HEIGHT - 260, 200, 90
        )

        self.btn_next_end = pygame.Rect(BASE_WIDTH // 2 - 200, BASE_HEIGHT // 2 + 120, 400, 95)
        self.btn_pause = pygame.Rect(BASE_WIDTH - 280, 140, 240, 60)
        self.btn_chat = pygame.Rect(BASE_WIDTH - 280, 220, 240, 60)
        self.btn_resume = pygame.Rect(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 - 220, 500, 100)
        self.btn_options_pause = pygame.Rect(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 - 100, 500, 100)
        self.btn_save_quit = pygame.Rect(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 + 20, 500, 100)
        self.btn_quit_main = pygame.Rect(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 + 140, 500, 100)
        self.btn_return_menu = pygame.Rect(BASE_WIDTH // 2 - 250, BASE_HEIGHT - 250, 500, 100)
        self.btn_mute = pygame.Rect(40, 30, 80, 60)
        self.is_music_muted = False

        self.btn_fs = pygame.Rect(BASE_WIDTH - 280, 30, 240, 60)
        self.menu_buttons = []
        self.update_menu_buttons()

        self.options_buttons = [
            {"id": "master_vol", "y": 480, "text": "Volume", "color": (150, 180, 200), "scale": 1.0},
            {"id": "name", "y": 570, "text": "Name:", "color": (130, 140, 155), "scale": 1.0},
            {"id": "color", "y": 660, "text": "My Team:", "color": HOUSE_RED, "scale": 1.0},
            {"id": "hi_res_mode", "y": 750, "text": "Hi-Res Mode:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "smoothscale", "y": 840, "text": "Smoothscale:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "update", "y": 930, "text": "Check for update", "color": (150, 200, 255), "scale": 1.0},
            {"id": "back", "y": 1020, "text": "Back", "color": HOUSE_RED, "scale": 1.0},
        ]
        self.last_hovered = None

        self.bg_pebble_layer = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.fg_pebble_layer = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()

        tile_size = 256
        bg_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        fg_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)

        for _ in range(30 if IS_ANDROID else 600):
            px, py = random.randint(0, tile_size), random.randint(0, tile_size)
            pygame.draw.circle(bg_tile, (0, 0, 0, 50), (px + 1, py + 1), 1)
            pygame.draw.circle(bg_tile, (255, 255, 255, 100), (px, py), 1)

        for _ in range(20 if IS_ANDROID else 400):
            pygame.draw.circle(
                fg_tile, (255, 255, 255, random.randint(30, 90)), (random.randint(0, tile_size), random.randint(0, tile_size)), 1
            )

        for tx in range(0, BASE_WIDTH, tile_size):
            for ty in range(0, BASE_HEIGHT, tile_size):
                self.bg_pebble_layer.blit(bg_tile, (tx, ty))
                self.fg_pebble_layer.blit(fg_tile, (tx, ty))

        self.ice_env_map = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        pygame.draw.polygon(self.ice_env_map, (255, 255, 255, 18), [(300, 0), (800, 0), (200, BASE_HEIGHT), (-300, BASE_HEIGHT)])
        pygame.draw.polygon(self.ice_env_map, (255, 255, 255, 12), [(900, 0), (1300, 0), (700, BASE_HEIGHT), (300, BASE_HEIGHT)])
        pygame.draw.rect(self.ice_env_map, (0, 0, 0, 30), (0, 0, 100, BASE_HEIGHT))
        pygame.draw.rect(self.ice_env_map, (0, 0, 0, 30), (BASE_WIDTH - 100, 0, 100, BASE_HEIGHT))

        for x in range(0, BASE_WIDTH, 15):
            dist_from_center = abs(x - BASE_WIDTH // 2)
            alpha = max(0, 45 - int((dist_from_center / (BASE_WIDTH // 2)) * 45))
            pygame.draw.rect(self.ice_env_map, (255, 255, 255, alpha), (x, 0, 15, BASE_HEIGHT))

        self.static_ice_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT)).convert()
        for y in range(0, BASE_HEIGHT, 45):
            pygame.draw.rect(
                self.static_ice_surface, (max(0, ICE_COLOR[0] - int((y / BASE_HEIGHT) * 18)),) * 3, (0, y, BASE_WIDTH, 45)
            )
        self.static_ice_surface.blit(self.bg_pebble_layer, (0, 0))
        for y in range(0, BASE_HEIGHT, 80):
            pygame.draw.line(self.static_ice_surface, ICE_SHADOW, (0, y), (BASE_WIDTH, y), 2)
        pygame.draw.line(self.static_ice_surface, TEE_LINE_COLOR, (0, self.house_pos.y), (BASE_WIDTH, self.house_pos.y), 6)
        pygame.draw.line(self.static_ice_surface, (200, 212, 226), (self.house_pos.x, 0), (self.house_pos.x, BASE_HEIGHT), 3)
        pygame.draw.line(
            self.static_ice_surface, HOG_LINE_COLOR, (0, self.house_pos.y + 400), (BASE_WIDTH, self.house_pos.y + 400), 10
        )
        pygame.draw.line(
            self.static_ice_surface, (10, 10, 10), (0, self.house_pos.y - 220), (BASE_WIDTH, self.house_pos.y - 220), 4
        )

        house_layer = pygame.Surface((440, 440))
        house_layer.fill((255, 0, 255))
        house_layer.set_colorkey((255, 0, 255))
        house_layer.set_alpha(80)
        for r, c, w in [
            (210, HOUSE_BLUE, 0),
            (140, WHITE, 0),
            (70, HOUSE_RED, 0),
            (20, WHITE, 0),
            (20, BLACK, 2),
            (6, BLACK, 0),
            (2, WHITE, 0),
        ]:
            pygame.draw.circle(house_layer, c, (220, 220), r, w)
        self.static_ice_surface.blit(house_layer, (int(self.house_pos.x - 220), int(self.house_pos.y - 220)))

        # Cache the Hack
        cx = self.hack_pos.x
        hack_y = self.hack_pos.y + 35
        pygame.draw.rect(self.static_ice_surface, (10, 10, 10), (cx - 50, hack_y + 6, 100, 10), border_radius=3)
        pygame.draw.rect(self.static_ice_surface, (50, 55, 60), (cx - 10, hack_y + 5, 20, 6))
        left_pad = [(cx - 40, hack_y - 2), (cx - 15, hack_y - 2), (cx - 10, hack_y + 18), (cx - 45, hack_y + 21)]
        pygame.draw.polygon(self.static_ice_surface, (20, 20, 22), left_pad)
        pygame.draw.polygon(self.static_ice_surface, (60, 60, 65), left_pad, 2)
        right_pad = [(cx + 40, hack_y - 2), (cx + 15, hack_y - 2), (cx + 10, hack_y + 18), (cx + 45, hack_y + 21)]
        pygame.draw.polygon(self.static_ice_surface, (20, 20, 22), right_pad)
        pygame.draw.polygon(self.static_ice_surface, (60, 60, 65), right_pad, 2)

        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
        overlay.fill((235, 245, 255, 15))
        self.static_ice_surface.blit(overlay, (0, 0))

        self.static_ice_surface.blit(self.ice_env_map, (0, 0))

        self.static_ice_surface.blit(self.fg_pebble_layer, (0, 0))

        self.reset_match()

    def set_typing_target(self, target):
        if getattr(self, "typing_target", None) == target:
            return
        was_typing = getattr(self, "typing_target", None) is not None
        if was_typing:
            self.save_progress()
        self.typing_target = target
        if IS_ANDROID:
            try:
                if target is not None:
                    pygame.key.start_text_input()
                else:
                    pygame.key.stop_text_input()
            except:
                pass

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if IS_ANDROID:
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.SCALED)
        else:
            if self.is_fullscreen:
                modes = pygame.display.list_modes()
                best_mode = modes[0] if modes else (0, 0)
                self.screen = pygame.display.set_mode(best_mode, pygame.FULLSCREEN | pygame.DOUBLEBUF)
            else:
                info = pygame.display.Info()
                desk_h = info.current_h
                if desk_h > 0 and BASE_HEIGHT > desk_h * 0.85:
                    target_h = int(desk_h * 0.85)
                    target_w = int(target_h * (BASE_WIDTH / BASE_HEIGHT))
                    self.screen = pygame.display.set_mode((target_w, target_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                else:
                    self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
            ww, wh = self.screen.get_size()
            self.border_starfield = Starfield(count=400, max_w=ww, max_h=wh)

    def load_progress(self):
        self.challenge_progress = [False] * 25
        self.username = ""
        self.preferred_color = 0
        self.room_text = ""
        self.ai_difficulty = 5
        self.challenge_completed_seen = False
        self.is_music_muted = False
        self.fxaa_on = False
        self.bilinear_on = False
        self.lighter_filter = False
        self.time_mult = 1.0
        self.hi_res_mode = False
        import sys

        self.is_web = hasattr(sys, "platform") and sys.platform == "emscripten"
        self.light_physics = False
        self.active_slot = 0
        self.slots_data = [{}, {}, {}]
        self.bot_slots_data = [{}, {}, {}]
        self.local_slots_data = [{}, {}, {}]
        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)
                self.username = data.get("username", "")
                self.preferred_color = data.get("color", 0)
                self.room_text = data.get("room", "")
                self.ai_difficulty = data.get("bot_skill", 5)
                self.challenge_completed_seen = data.get("challenge_completed_seen", False)
                self.is_music_muted = data.get("is_music_muted", False)
                if getattr(self, "audio", None):
                    self.audio.set_master_volume(data.get("master_vol", 1.0))
                self.fxaa_on = data.get("fxaa_on", False)
                self.bilinear_on = data.get("bilinear_on", False)
                self.lighter_filter = data.get("lighter_filter", False)
                self.hi_res_mode = data.get("hi_res_mode", False)

                if "slots" in data:
                    self.slots_data = data["slots"]
                else:
                    self.slots_data[0] = {
                        "challenge": data.get("challenge", [False] * 25),
                        "story": data.get("story", None),
                        "saved_match_state": data.get("saved_match_state", None),
                    }
                if "bot_slots" in data:
                    self.bot_slots_data = data["bot_slots"]
                if "local_slots" in data:
                    self.local_slots_data = data["local_slots"]
        except:
            print("No previous save file found, starting fresh.")

        self.load_slot(self.active_slot)

        self.update_menu_buttons()

        if not self.username:
            firsts = ["John", "Sarah", "Mike", "Emily", "Dave", "Lisa", "Chris", "Anna", "Tom", "Jessica"]
            lasts = [
                "Sweeps",
                "McPebble",
                "Hackman",
                "Slider",
                "Broomfield",
                "Skip",
                "Hammer",
                "Hogline",
                "Iceburn",
                "Von Curl",
                "Rocksley",
                "Stoned",
                "Freezeman",
            ]
            self.username = f"{random.choice(firsts)} {random.choice(lasts)}"[:15]
            self.save_progress()

    def load_slot(self, slot_idx):
        self.active_slot = slot_idx
        if getattr(self, "game_mode", "") == "BOT":
            slots = self.bot_slots_data
        elif getattr(self, "game_mode", "") == "LOCAL":
            slots = self.local_slots_data
        else:
            slots = self.slots_data
        slot = slots[slot_idx] if slot_idx < len(slots) else {}
        self.challenge_progress = slot.get("challenge", [False] * 25)
        self.story = StoryManager()
        if slot.get("story"):
            self.story.from_dict(slot["story"])
        self.saved_match_state = slot.get("saved_match_state", None)

    def save_progress(self):
        try:
            while len(self.slots_data) < 3:
                self.slots_data.append({})
            while getattr(self, "bot_slots_data", []) and len(self.bot_slots_data) < 3:
                self.bot_slots_data.append({})
            if not getattr(self, "bot_slots_data", []):
                self.bot_slots_data = [{}, {}, {}]
            while getattr(self, "local_slots_data", []) and len(self.local_slots_data) < 3:
                self.local_slots_data.append({})
            if not getattr(self, "local_slots_data", []):
                self.local_slots_data = [{}, {}, {}]

            if getattr(self, "game_mode", "") == "BOT":
                slots = self.bot_slots_data
            elif getattr(self, "game_mode", "") == "LOCAL":
                slots = self.local_slots_data
            else:
                slots = self.slots_data

            # Ensure saved_match_state matches the slot type to avoid segfault cross-pollination
            sm_state = getattr(self, "saved_match_state", None)
            if sm_state and sm_state.get("game_mode", "") != getattr(self, "game_mode", ""):
                sm_state = None

            story_dict = self.story.to_dict() if getattr(self, "story", None) else {}
            slots[self.active_slot] = {
                "challenge": self.challenge_progress[:25],
                "story": story_dict,
                "saved_match_state": sm_state,
            }
            data = {
                "slots": self.slots_data,
                "bot_slots": self.bot_slots_data,
                "local_slots": self.local_slots_data,
                "username": self.username,
                "color": self.preferred_color,
                "room": self.room_text,
                "bot_skill": self.ai_difficulty,
                "challenge_completed_seen": getattr(self, "challenge_completed_seen", False),
                "is_music_muted": getattr(self, "is_music_muted", False),
                "fxaa_on": getattr(self, "fxaa_on", False),
                "bilinear_on": getattr(self, "bilinear_on", False),
                "lighter_filter": getattr(self, "lighter_filter", False),
                "hi_res_mode": getattr(self, "hi_res_mode", False),
                "master_vol": getattr(self.audio, "master_volume", 1.0) if getattr(self, "audio", None) else 1.0,
            }
            import os
            tmp_file = self.save_file + ".tmp"
            with open(tmp_file, "w") as f:
                json.dump(data, f)
            os.replace(tmp_file, self.save_file)
        except Exception as e:
            print(f"Game Progress Save Failed: {e}")

    def update_menu_buttons(self):
        self.menu_buttons = []
        self.menu_buttons.extend(
            [
                {"id": "story", "y": 480, "text": "Story Mode", "color": (100, 200, 100), "scale": 1.0},
                {"id": "local", "y": 600, "text": "Local 1v1", "color": HOUSE_RED, "scale": 1.0},
                {"id": "bot", "y": 720, "text": "Local vs Bot", "color": TEAM_YELLOW, "scale": 1.0},
                {"id": "chal", "y": 840, "text": "Challenge Mode", "color": PURPLE_SUIT, "scale": 1.0},
                {"id": "options", "y": 960, "text": "Options", "color": HOUSE_RED, "scale": 1.0},
                {"id": "host", "y": 1080, "text": "Host IRC", "color": HOUSE_BLUE, "scale": 1.0},
                {"id": "join", "y": 1200, "text": "Join IRC", "color": HOUSE_BLUE, "scale": 1.0},
                {"id": "exit", "y": 1320, "text": "Exit Game", "color": HOUSE_RED, "scale": 1.0},
            ]
        )

    def save_match(self):
        state = {
            "stones": [s.get_state() for s in self.stones],
            "score": self.score,
            "current_end": self.current_end,
            "hammer_team": self.hammer_team,
            "current_team": self.current_team,
            "stones_thrown": getattr(self, "stones_thrown_this_end", 0),
            "game_mode": self.game_mode,
            "challenge_level": self.challenge_level,
            "turn_state": getattr(self, "turn_state", "AIMING"),
            "active_stone_id": getattr(self.active_stone, "id", None) if getattr(self, "active_stone", None) else None,
            "story_rival_score": getattr(self, "story_rival_score", 0),
            "story_player_score": getattr(self, "story_player_score", 0),
            "stones_thrown_dict": self.stones_thrown,
            "coords_version": 2,
        }
        for s in state["stones"]:
            s[1] -= (BASE_HEIGHT // 2) + 100
        self.saved_match_state = state
        self.save_progress()
        self.update_menu_buttons()

    def restore_match(self):
        if not getattr(self, "saved_match_state", None):
            return
        state = self.saved_match_state
        self.score = {int(k): v for k, v in state.get("score", {"0": [0] * 8, "1": [0] * 8}).items()}
        self.current_end = state.get("current_end", 1)
        self.hammer_team = state.get("hammer_team", 0)
        self.current_team = state.get("current_team", 0)
        self.stones_thrown_this_end = state.get("stones_thrown", 0)
        self.stones_thrown = {int(k): v for k, v in state.get("stones_thrown_dict", {"0": 0, "1": 0}).items()}
        self.game_mode = state.get("game_mode", "LOCAL")
        self.challenge_level = state.get("challenge_level", 1)
        self.turn_state = state.get("turn_state", "AIMING")
        self.story_rival_score = state.get("story_rival_score", 0)
        self.story_player_score = state.get("story_player_score", 0)
        self.is_dragging = False
        self.virtual_pull = pygame.math.Vector2(0, 0)
        self.pull_history = []
        self.selected_curl = 0.0
        self.sweep_power = 0.0
        self.is_sweeping_now = False
        self.last_mouse_pos = pygame.math.Vector2(0, 0)
        self.dragging_slider = False
        self.drag_start_pos = None
        self.drag_finger_id = None

        self.stones = []
        self.active_stone = None
        coords_version = state.get("coords_version", 1)
        for s in state.get("stones", []):
            if coords_version == 2:
                s[1] += (BASE_HEIGHT // 2) + 100
            st = Stone(s[0], s[1], s[4], sid=s[8] if len(s) > 8 else None)
            st.set_state(s)
            self.stones.append(st)
            if len(s) > 8 and st.id == state.get("active_stone_id"):
                self.active_stone = st

        # Failsafe: Ensure stones_thrown is AT LEAST the number of stones currently on the ice
        counts = {0: 0, 1: 0}
        for s in self.stones:
            if s != getattr(self, "active_stone", None):
                if getattr(s, "team", -1) in counts:
                    counts[s.team] += 1
        self.stones_thrown[0] = max(self.stones_thrown[0], counts[0])
        self.stones_thrown[1] = max(self.stones_thrown[1], counts[1])

        # We no longer wipe the save here, it persists until overwritten
        self.update_menu_buttons()
        self.app_state = "PLAY"

        if self.game_mode == "STORY":
            self.audio.play_music(f"battle{min(self.story.current_rink + 1, 3)}")
        elif self.game_mode == "CHALLENGE":
            self.audio.play_music("challenge")
        else:
            self.audio.play_music()

    def reset_turn_vars(self):
        if not getattr(self, "is_web", False):
            pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        self.turn_state = "AIMING"
        self.is_dragging = False
        self.virtual_pull = pygame.math.Vector2(0, 0)
        self.selected_curl = 0.0
        self.sweep_power = 0.0
        self.is_sweeping_now = False
        self.last_mouse_pos = pygame.math.Vector2(0, 0)
        self.dragging_slider = False
        self.drag_start_pos = None
        self.drag_finger_id = None
        self.pull_history = []
        self.spawn_next_stone()

    def return_to_menu(self):
        self.audio.stop_all_match_sounds()
        self.sweep_power = 0.0
        self.particles = []
        if not getattr(self, "is_web", False):
            pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        if self.game_mode in ["HOST", "JOIN"]:
            self.net.close()
            self.net = IRCNetworkManager()
        self.app_state = "MENU"
        self.turn_state = "MENU"

    def reset_match(self):
        self.score = {0: [0] * 8, 1: [0] * 8}
        self.current_end = 1
        self.total_stones_played = 0
        self.stones_per_team = 8
        self.stones = []
        self.stones_thrown = {0: 0, 1: 0}

    def start_match(self):
        self.reset_match()
        if hasattr(self, "end_delay_timer"):
            del self.end_delay_timer
        self.parallax_y = 1000.0  # mode 7 slide in
        self.parallax_x = 0.0
        if self.game_mode == "CHALLENGE":
            self.app_state = "PLAY"
            self.challenge_attempts = 0
            self.load_challenge(self.challenge_level)
            self.challenge_announced = False
        else:
            if getattr(self, "game_mode", None) == "STORY":
                rink_idx = min(getattr(self.story, "current_rink", 0), len(STORY_RINKS) - 1) if getattr(self, "story", None) else 0
                self.match_ai_difficulty = STORY_RINKS[rink_idx]["difficulty"]

            else:
                self.match_ai_difficulty = self.ai_difficulty
            self.app_state = "COIN_TOSS"
            self.coin_timer = 30
            self.coin_flip_result = random.choice([0, 1])
            self.audio.play_cheer()

    def load_challenge(self, level):
        self.stones = []
        self.stones_thrown = {0: 0, 1: 0}
        self.stones_per_team = 1
        self.current_team = 0
        self.challenge_success = False
        cx, cy = self.house_pos.x, self.house_pos.y
        self.challenge_target = None
        self.challenge_takeout_target = None

        if level <= 5:
            self.c_type = "DRAW"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] THE DRAW", "Land inside the highlighted target."
            self.challenge_target = (cx + (level % 2) * 30, cy + (5 - level) * 40, max(20, 80 - level * 10))
        elif level <= 10:
            self.c_type = "GUARD"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] THE GUARD", "Place a rock in the target zone (Guard)."
            self.challenge_target = (cx, cy + 300 - (level - 6) * 20, 40)
        elif level <= 15:
            self.c_type = "TAKEOUT"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] TAKEOUT", "Remove the yellow rock. Stay in play."
            s = Stone(cx + (level - 12) * 15, cy + (level - 13) * 20, 1)
            self.stones.append(s)
            self.challenge_takeout_target = s
            if level > 13:
                self.stones.append(Stone(cx - 30, cy + 180, 0))
        elif level == 16:
            self.c_type = "DRAW"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] HIT AND ROLL", "Hit the rock and roll into the target."
            self.stones.append(Stone(cx + 40, cy + 50, 1))
            self.challenge_target = (cx - 40, cy, 45)
        elif level <= 21:
            self.c_type = "DOUBLE"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] DOUBLE TAKEOUT", "Clear ALL yellow rocks from the house."
            self.stones.extend([Stone(cx - 25, cy + 15, 1), Stone(cx + 25, cy - 15, 1)])
            if level > 19:
                self.stones.append(Stone(cx, cy + 60, 1))
        else:
            self.c_type = "TAKEOUT"
            self.challenge_text_1, self.challenge_text_2 = f"[{level}/25] ANGLE RAISE", "Raise the red guard into the yellow rock."
            self.stones.append(Stone(cx, cy + 150, 0))
            s = Stone(cx - 10, cy + 10, 1)
            self.stones.append(s)
            self.challenge_takeout_target = s
            if level == 25:
                self.stones.append(Stone(cx + 60, cy + 120, 1))

        self.reset_turn_vars()

    def reset_end(self):
        self.stones = []
        self.stones_thrown = {0: 0, 1: 0}
        self.current_team = 1 if getattr(self, "hammer_team", 0) == 0 else 0
        self.reset_turn_vars()

    def spawn_next_stone(self):
        self.active_stone = Stone(self.hack_pos.x, self.hack_pos.y, self.current_team)
        self.stones.append(self.active_stone)

    def handle_collisions(self):
        for i in range(len(self.stones)):
            for j in range(i + 1, len(self.stones)):
                s1, s2 = self.stones[i], self.stones[j]
                dist_vec = s2.pos - s1.pos
                dist = dist_vec.length()
                min_dist = s1.radius + s2.radius
                if 0 < dist < min_dist:
                    overlap = min_dist - dist
                    normal = dist_vec.normalize()
                    s1.pos -= normal * (overlap / 2)
                    s2.pos += normal * (overlap / 2)
                    v_normal = (s1.vel - s2.vel).dot(normal)
                    if v_normal > 0:
                        impulse = (1.94) * v_normal / (s1.mass + s2.mass)
                        s1.vel -= normal * (impulse * s2.mass)
                        s2.vel += normal * (impulse * s1.mass)
                        s1.is_moving, s2.is_moving = True, True
                        if impulse * 12 > 0.8:
                            s1.last_collision_time = pygame.time.get_ticks()
                            s2.last_collision_time = pygame.time.get_ticks()
                            self.audio.play_clack(impulse * 12)
                            self.shake_amount = min(25.0, impulse * 4.0)
                            if IS_ANDROID:
                                try:
                                    vibrate_android(50)
                                except:
                                    pass
                            mid_x, mid_y = (s1.pos.x + s2.pos.x) / 2, (s1.pos.y + s2.pos.y) / 2
                            for _ in range(int(impulse * 5)):
                                self.particles.append(
                                    {
                                        "pos": pygame.math.Vector2(mid_x, mid_y),
                                        "vel": normal.rotate(random.uniform(-45, 45)) * random.uniform(2, 10),
                                        "life": 1.0,
                                        "decay": random.uniform(0.02, 0.05),
                                        "type": "spark",
                                    }
                                )

    def execute_ai(self):
        diff = int(getattr(self, "match_ai_difficulty", 5))
        err_mult = max(0.01, 3.0 - ((diff - 1) * 0.40))
        takeout_chance = min(0.95, (diff - 1) * 0.12)
        guard_chance = min(0.85, 0.15 + (diff - 1) * 0.10)
        params = {"error_multiplier": err_mult, "takeout_chance": takeout_chance, "guard_chance": guard_chance}

        if not hasattr(self, "ai_wait_start"):
            self.ai_wait_start = pygame.time.get_ticks()
            return

        if pygame.time.get_ticks() - self.ai_wait_start < 1000:
            return

        delattr(self, "ai_wait_start")

        err = (11 - getattr(self, "match_ai_difficulty", 5)) * params["error_multiplier"]
        target = self.house_pos + pygame.math.Vector2(random.uniform(-7, 7) * err, random.uniform(-6, 6) * err)

        p_stones = sorted(
            [s for s in self.stones if s.team == 0 and s != self.active_stone], key=lambda s: (s.pos - self.house_pos).length()
        )
        if p_stones and (p_stones[0].pos - self.house_pos).length() < 170 and random.random() < params["takeout_chance"]:
            target = p_stones[0].pos + pygame.math.Vector2(random.uniform(-2, 2) * err, 12)

        req_spd = max(
            2.5, min(35.0, math.sqrt(2 * FRICTION_BASE * (target - self.hack_pos).length()) + random.uniform(-0.05, 0.05) * err)
        )

        self.curler_anim.update("LUNGING")
        self.audio.play_throw()
        self.active_stone.vel = (target - self.hack_pos).normalize() * req_spd
        self.active_stone.curl = random.choice([-0.55, 0.55])
        self.active_stone.is_moving = True
        self.stones_thrown[self.current_team] += 1
        self.total_stones_played += 1
        self.turn_state = "SLIDING"

    def fire_stone(self):
        if getattr(self, "pull_history", []):
            avg_x = sum(p.x for p in self.pull_history) / len(self.pull_history)
            avg_y = sum(p.y for p in self.pull_history) / len(self.pull_history)
            self.virtual_pull = pygame.math.Vector2(avg_x, avg_y)

        pull = pygame.math.Vector2(self.virtual_pull.x / 4.0, self.virtual_pull.y)
        if abs(pull.x) < 2.0:
            pull.x = 0

        if pull.length() > 20:
            max_vel = 16.0
            if getattr(self, "game_mode", None) == "STORY":
                max_vel += self.story.stats.get("power", 0) * 1.5

            vel = pull.normalize() * min(max_vel, pull.length() / 14.0)
            self.active_stone.vel = vel

            curl_factor = self.selected_curl
            if getattr(self, "game_mode", None) == "STORY":
                curl_factor *= 1.0 + self.story.stats.get("curl_control", 0) * 0.25
            self.active_stone.curl = curl_factor

            self.active_stone.is_moving = True
            self.stones_thrown[self.current_team] += 1
            self.total_stones_played += 1
            self.turn_state = "SLIDING"
            self.curler_anim.update("LUNGING")
            self.audio.play_throw()
            if self.game_mode in ["HOST", "JOIN"]:
                self.net.send_action(
                    {
                        "cmd": "shoot",
                        "vx": self.active_stone.vel.x,
                        "vy": self.active_stone.vel.y,
                        "c": self.selected_curl,
                        "sid": getattr(self.active_stone, "id", -1),
                    }
                )
        else:
            self.curler_anim.update("IDLE")
        self.is_dragging = False
        self.virtual_pull = pygame.math.Vector2(0, 0)
        self.drag_start_pos = None
        self.drag_finger_id = None
        self.pull_history = []
        if not getattr(self, "is_web", False):
            pygame.event.set_grab(False)

    def advance_end_logic(self):
        if self.game_mode == "CHALLENGE":
            if getattr(self, "challenge_success", False) or self.challenge_attempts >= 3:
                if getattr(self, "challenge_success", False):
                    self.challenge_progress[self.challenge_level - 1] = True
                    self.save_progress()

                if all(self.challenge_progress[:25]):
                    if getattr(self, "challenge_success", False) and not getattr(self, "challenge_completed_seen", False):
                        if self.app_state != "MATCH_OVER":
                            self.app_state = "MATCH_OVER"
                            self.audio.play_cheer()
                            if not getattr(self, "challenge_announced", False) and getattr(self.audio, "snd_chal_comp", None):
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
                    if not self.challenge_progress[self.challenge_level - 1] or self.challenge_level == start_lvl:
                        break
                self.challenge_attempts = 0
            self.load_challenge(self.challenge_level)
            return

        self.current_end += 1
        if self.current_end > 8:
            self.app_state = "MATCH_OVER"
            self.saved_match_state = None
            self.save_progress()
            self.audio.play_cheer()

            r_tot, y_tot = sum(self.score[0]), sum(self.score[1])
            if getattr(self, "game_mode", None) in ["HOST", "JOIN"]:
                my_score = r_tot if getattr(self, "preferred_color", 0) == 0 else y_tot
                self.post_score(getattr(self, "username", "Player"), my_score)

            if getattr(self, "game_mode", None) == "STORY":
                if r_tot > y_tot:
                    rink_idx = min(self.story.current_rink, len(STORY_RINKS) - 1)
                    xp_gained = 100 * STORY_RINKS[rink_idx]["difficulty"]
                    self.story.xp += xp_gained
                    while self.story.xp >= self.story.level * 100:
                        self.story.xp -= self.story.level * 100
                        self.story.level += 1
                    self.story.current_rink += 1
                    self.save_progress()

            if not getattr(self, "match_winner_announced", False):
                self.match_winner_announced = True
                if r_tot > y_tot and getattr(self.audio, "snd_red_wins", None):
                    self.audio.ch_voice.play(self.audio.snd_red_wins)
                elif y_tot > r_tot and getattr(self.audio, "snd_ylw_wins", None):
                    self.audio.ch_voice.play(self.audio.snd_ylw_wins)
                elif getattr(self.audio, "snd_end_match", None):
                    self.audio.ch_voice.play(self.audio.snd_end_match)
        else:
            self.reset_end()
            if getattr(self, "game_mode", None) in ["STORY", "BOT"]:
                self.save_match()

    def handle_menu_events(self, event):
        mouse_pos = getattr(event, "pos", self.get_pointer_pos())
        mx, my = mouse_pos[0] if isinstance(mouse_pos, tuple) else mouse_pos.x, (
            mouse_pos[1] if isinstance(mouse_pos, tuple) else mouse_pos.y
        )
        menu_my = my - getattr(self, "menu_dy", 0)
        curr_hov = None

        # UI Navigation from keyboard/controller
        if getattr(self, "ui_nav_dir", None):
            now = pygame.time.get_ticks()
            if now - getattr(self, "last_nav_time", 0) > 200:
                if self.ui_nav_dir in ["up", "left"]:
                    self.ui_selected_index = (self.ui_selected_index - 1) % len(self.menu_buttons)
                elif self.ui_nav_dir in ["down", "right"]:
                    self.ui_selected_index = (self.ui_selected_index + 1) % len(self.menu_buttons)
                self.last_nav_time = now
                self.audio.play_hover()
            self.ui_nav_dir = None

        if event.type == MOUSEMOTION:
            curr_hov = next(
                (b["id"] for b in self.menu_buttons if 300 < mx < 900 and b["y"] < menu_my < b["y"] + 110 * b["scale"]), None
            )
            if curr_hov:
                try:
                    self.ui_selected_index = next(i for i, b in enumerate(self.menu_buttons) if b["id"] == curr_hov)
                except StopIteration:
                    pass

        self.last_hovered = self.menu_buttons[self.ui_selected_index]["id"] if self.menu_buttons else None

        if event.type == MOUSEBUTTONUP and getattr(event, "button", 1) == 1:
            if self.dragging_slider:
                self.dragging_slider = False
                self.save_progress()

        is_select = (event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1) or getattr(self, "ui_nav_select", False)

        if is_select:
            if getattr(self, "ui_nav_select", False):
                curr_hov = self.last_hovered
                self.ui_nav_select = False
            else:
                curr_hov = next(
                    (b["id"] for b in self.menu_buttons if 300 < mx < 900 and b["y"] < menu_my < b["y"] + 110 * b["scale"]), None
                )

            now = pygame.time.get_ticks()
            if hasattr(self, "last_click_time") and now - self.last_click_time < 300:
                return
            self.last_click_time = now

            if self.typing_target:
                if not (300 < mx < 900 and 950 < menu_my < 1070):
                    self.set_typing_target(None)

            for b in self.menu_buttons:
                if b["id"] == curr_hov:
                    self.audio.play_click()
                    new_target = None
                    if b["id"] == "local":
                        self.game_mode = "LOCAL"
                        self.slot_intention = "local"
                        self.app_state = "SAVE_SLOTS"
                    elif b["id"] == "bot":
                        self.game_mode = "BOT"
                        self.slot_intention = "bot"
                        self.app_state = "SAVE_SLOTS"
                    elif b["id"] == "chal":
                        self.app_state = "CHALLENGE_MENU"
                    elif b["id"] == "story":
                        self.game_mode = "STORY"
                        self.slot_intention = "story"
                        self.app_state = "SAVE_SLOTS"
                    elif b["id"] == "options":
                        self.app_state = "OPTIONS_MENU"
                        self.prev_state = "MENU"
                    elif b["id"] in ["host", "join"]:
                        self.app_state = "ROOM_PROMPT"
                        new_target = "room"
                        self.net_action = b["id"]
                    elif b["id"] == "exit":
                        self.net.close()
                        pygame.quit()
                        sys.exit()
                    self.set_typing_target(new_target)
                    break

            if 330 < mx < 870 and 1450 < menu_my < 1650:
                self.ai_difficulty = int(1 + max(0.0, min(1.0, (mx - 350) / 500.0)) * 9)
                self.audio.play_hover()
                self.save_progress()
        elif event.type == MOUSEMOTION and self.get_pointer_pressed():
            if 330 < mx < 870 and 1450 < menu_my < 1650:
                self.ai_difficulty = int(1 + max(0.0, min(1.0, (mx - 350) / 500.0)) * 9)
                self.dragging_slider = True
        elif event.type == KEYDOWN and self.typing_target == "name":
            if event.key in (K_RETURN, K_KP_ENTER):
                self.set_typing_target(None)
                self.save_progress()
            elif event.key == K_BACKSPACE:
                self.username = self.username[:-1]
                self.save_progress()
            else:
                if hasattr(event, "unicode") and event.unicode.isprintable() and len(self.username) + len(event.unicode) <= 12:
                    self.username += event.unicode
                    self.save_progress()

    def handle_room_prompt_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            m = getattr(event, "pos", self.get_pointer_pos())
            mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if not self.prompt_rect.collidepoint(mx, my):
                self.app_state = "MENU"
                self.set_typing_target(None)
            elif IS_ANDROID:
                self.audio.play_click()
                self.save_progress()
                self.app_state = "MENU"
                self.set_typing_target(None)
                self.game_mode = "HOST" if self.net_action == "host" else "JOIN"
                self.net.connect(self.username, self.net_action == "host", self.room_text, getattr(self, "preferred_color", 0))

        if event.type == KEYDOWN and self.typing_target == "room":
            if event.key in (K_RETURN, K_KP_ENTER) and len(self.room_text) > 0:
                self.audio.play_click()
                self.save_progress()
                self.app_state = "MENU"
                self.set_typing_target(None)
                self.game_mode = "HOST" if self.net_action == "host" else "JOIN"
                self.net.connect(self.username, self.net_action == "host", self.room_text, getattr(self, "preferred_color", 0))
            elif event.key == K_ESCAPE:
                self.app_state = "MENU"
                self.set_typing_target(None)
            elif event.key == K_BACKSPACE:
                self.room_text = self.room_text[:-1]
                self.save_progress()

    def handle_challenge_menu_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            m = getattr(event, "pos", self.get_pointer_pos())
            mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "MENU"
                return
            for i in range(25):
                row, col = i // 5, i % 5
                rect = pygame.Rect(BASE_WIDTH // 2 - 250 + col * 100, 300 + row * 100, 90, 90)
                if rect.collidepoint(mx, my):
                    self.audio.play_click()
                    self.game_mode = "CHALLENGE"
                    self.challenge_level = i + 1
                    self.audio.stop_music()
                    self.start_match()
                    return

    def handle_save_slots_events(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self.get_pointer_pos()
            cx = BASE_WIDTH // 2

            for i in range(3):
                rect = pygame.Rect(cx - 300, 300 + i * 200, 600, 150)
                if rect.collidepoint(mx, my):
                    self.audio.play_click()
                    self.load_slot(i)
                    if getattr(self, "slot_intention", "story") == "story":
                        self.app_state = "STORY_MAP"
                    else:
                        self.app_state = "BOT_MENU"
                    return

            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "MENU"

    def handle_bot_menu_events(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self.get_pointer_pos()
            cx = BASE_WIDTH // 2

            if getattr(self, "saved_match_state", None) and self.saved_match_state.get("game_mode") == getattr(
                self, "game_mode", ""
            ):
                start_btn = pygame.Rect(cx - 200, 450, 400, 100)
                if start_btn.collidepoint(mx, my):
                    self.audio.play_click()
                    self.audio.stop_music()
                    self.restore_match()
                    return
                new_btn = pygame.Rect(cx - 200, 600, 400, 100)
                if new_btn.collidepoint(mx, my):
                    self.audio.play_click()
                    self.saved_match_state = None
                    self.audio.stop_music()
                    self.start_match()
                    return
            else:
                start_btn = pygame.Rect(cx - 200, 500, 400, 100)
                if start_btn.collidepoint(mx, my):
                    self.audio.play_click()
                    self.audio.stop_music()
                    self.start_match()
                    return

            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "MENU"

    def handle_story_map_events(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            m = getattr(event, "pos", self.get_pointer_pos())
            mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y

            if self.app_state == "STORY_DIALOG":
                self.audio.play_click()
                rink = STORY_RINKS[min(self.story.current_rink, len(STORY_RINKS) - 1)]
                self.dialog_index += 1
                self.dialog_time = pygame.time.get_ticks()
                if self.dialog_index >= len(rink["intro_dialog"]):
                    self.game_mode = "STORY"
                    self.audio.stop_music()
                    self.start_match()
                return

            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "MENU"
                return

            if getattr(self, "btn_upgrades", None):
                spent_points = sum(self.story.stats.values())
                avail_points = max(0, (self.story.level - 1) - spent_points)
                for k, btn in self.btn_upgrades.items():
                    if btn.collidepoint(mx, my):
                        if avail_points > 0 and self.story.stats.get(k, 0) < 5:
                            self.audio.play_click()
                            self.story.stats[k] = self.story.stats.get(k, 0) + 1
                            self.save_progress()
                        else:
                            self.audio.play_error()
                        return

            if getattr(self, "saved_match_state", None):
                cont_btn = pygame.Rect(BASE_WIDTH // 2 - 200, 750, 400, 80)
                new_btn = pygame.Rect(BASE_WIDTH // 2 - 200, 850, 400, 80)
                if cont_btn.collidepoint(mx, my):
                    self.audio.play_click()
                    self.restore_match()
                    return
                elif new_btn.collidepoint(mx, my):
                    self.audio.play_click()
                    if self.story.current_rink < len(STORY_RINKS):
                        self.saved_match_state = None
                        self.save_progress()
                        self.app_state = "STORY_DIALOG"
                        self.dialog_index = 0
                        self.dialog_time = pygame.time.get_ticks()
            else:
                start_btn = pygame.Rect(BASE_WIDTH // 2 - 200, 800, 400, 100)
                if start_btn.collidepoint(mx, my):
                    self.audio.play_click()
                    if self.story.current_rink < len(STORY_RINKS):
                        self.app_state = "STORY_DIALOG"
                        self.dialog_index = 0
                        self.dialog_time = pygame.time.get_ticks()

    def handle_pause_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            m = getattr(event, "pos", self.get_pointer_pos())
            mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_resume.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "PLAY"
            elif self.btn_options_pause.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "OPTIONS_MENU"
                self.prev_state = "PAUSED"
            elif self.btn_save_quit.collidepoint(mx, my):
                self.audio.play_click()
                self.save_match()
                self.return_to_menu()
            elif self.btn_quit_main.collidepoint(mx, my):
                self.audio.play_click()
                self.return_to_menu()

    def handle_match_over_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            m = getattr(event, "pos", self.get_pointer_pos())
            mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if getattr(self, "btn_leaderboard", None) and self.btn_leaderboard.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "LEADERBOARD"
                self.fetch_leaderboard()
            elif self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                if getattr(self, "game_mode", None) == "STORY":
                    if getattr(self, "story", None) and getattr(self.story, "current_rink", 0) >= len(STORY_RINKS):
                        self.app_state = "STORY_WIN"
                        if getattr(self.audio, "snd_you_win", None):
                            self.audio.ch_voice.play(self.audio.snd_you_win)
                    else:
                        self.app_state = "STORY_MAP"
                else:
                    self.return_to_menu()

    def handle_story_win_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            self.audio.play_click()
            self.app_state = "CREDITS"

    def handle_credits_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            self.audio.play_click()
            self.return_to_menu()
            self.credits_y = BASE_HEIGHT

    def handle_leaderboard_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            m = getattr(event, "pos", self.get_pointer_pos())
            mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_return_menu.collidepoint(mx, my):
                self.audio.play_click()
                self.app_state = "MATCH_OVER"

    def handle_play_events(self, event):
        mouse_pos = getattr(event, "pos", self.get_pointer_pos())
        if isinstance(mouse_pos, tuple):
            mouse_pos = pygame.math.Vector2(mouse_pos)
        f_id = getattr(event, "finger_id", "mouse")

        if event.type == getattr(pygame, "FINGERDOWN", 1792):
            mx, my = self.map_touch(event.x, event.y)
            self.is_pointer_pressed = True
            if hasattr(self, "btn_mute") and self.btn_mute.collidepoint(mx, my):
                self.is_music_muted = not getattr(self, "is_music_muted", False)
            self.last_finger_id = event.finger_id
            if self.turn_state == "AIMING":
                finger_x = event.x * self.screen.get_width()
                finger_y = event.y * self.screen.get_height()
                fpos = self.scale_mouse((finger_x, finger_y))
                if getattr(self, "btn_curl_l", None) and self.btn_curl_l.collidepoint(fpos.x, fpos.y):
                    self.selected_curl = max(-1.0, self.selected_curl - 0.2)
                    self.audio.play_hover()
                elif getattr(self, "btn_curl_r", None) and self.btn_curl_r.collidepoint(fpos.x, fpos.y):
                    self.selected_curl = min(1.0, self.selected_curl + 0.2)
                    self.audio.play_hover()

        if event.type == MOUSEBUTTONUP and getattr(event, "button", 1) == 1 and self.is_dragging:
            if getattr(self, "drag_finger_id", None) == f_id or (IS_ANDROID and f_id == "mouse"):
                self.fire_stone()
            return

        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            if self.game_mode in ["HOST", "JOIN"] and self.btn_chat.collidepoint(mouse_pos.x, mouse_pos.y):
                self.audio.play_click()
                self.typing_chat = not getattr(self, "typing_chat", False)
                if self.typing_chat:
                    try:
                        pygame.key.start_text_input()
                    except:
                        pass
                else:
                    try:
                        pygame.key.stop_text_input()
                    except:
                        pass
                return
            if self.btn_pause.collidepoint(mouse_pos.x, mouse_pos.y):
                self.audio.play_click()
                if self.game_mode in ["HOST", "JOIN"]:
                    self.return_to_menu()
                else:
                    self.app_state = "PAUSED"
                    self.pause_anim = 0.0
                    self.audio.update_slide(0.0)
                    self.audio.update_sweep(0.0)
                return

        if self.turn_state == "END":
            if (
                event.type == MOUSEBUTTONDOWN
                and getattr(event, "button", 1) == 1
                and self.btn_next_end.collidepoint(mouse_pos.x, mouse_pos.y)
            ):
                self.advance_end_logic()
            elif event.type == KEYDOWN and event.key == K_SPACE:
                self.advance_end_logic()
            return

        has_control = (self.game_mode in ["LOCAL", "CHALLENGE"]) or (self.current_team == getattr(self, "preferred_color", 0))

        if not has_control:
            return

        if self.turn_state == "AIMING":
            if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
                if self.btn_curl_l.collidepoint(mouse_pos.x, mouse_pos.y):
                    self.selected_curl = max(-1.0, self.selected_curl - 0.2)
                    self.audio.play_hover()
                elif self.btn_curl_r.collidepoint(mouse_pos.x, mouse_pos.y):
                    self.selected_curl = min(1.0, self.selected_curl + 0.2)
                    self.audio.play_hover()
                elif (mouse_pos - self.active_stone.pos).length() < 90 and not self.is_dragging:
                    self.is_dragging = True
                    self.drag_start_pos = mouse_pos
                    self.drag_finger_id = getattr(self, "last_finger_id", f_id) if IS_ANDROID else f_id
                    self.pull_history = []
                    self.virtual_pull = pygame.math.Vector2(0, 0)
                    if not getattr(self, "is_web", False):
                        pygame.event.set_grab(True)
            elif event.type == MOUSEMOTION and self.is_dragging and getattr(self, "drag_start_pos", None):
                if f_id == getattr(self, "drag_finger_id", None) or (IS_ANDROID and f_id == "mouse"):
                    self.virtual_pull = pygame.math.Vector2(
                        (mouse_pos.x - self.drag_start_pos.x) * 0.70, (mouse_pos.y - self.drag_start_pos.y) * 0.30
                    )
                    self.pull_history.append(pygame.math.Vector2(self.virtual_pull))
                    if len(self.pull_history) > 5:
                        self.pull_history.pop(0)
            elif event.type == MOUSEWHEEL:
                self.selected_curl = max(-1.0, min(1.0, self.selected_curl + event.y * 0.2))
            elif event.type == getattr(pygame, "FINGERMOTION", 1792):
                if self.is_dragging and getattr(event, "finger_id", None) != getattr(self, "drag_finger_id", None):
                    self.selected_curl = max(-1.0, min(1.0, self.selected_curl + event.dx * 3.0))

    def update_physics(self):
        for p in self.particles[:]:
            p["pos"] += p["vel"]
            p["life"] -= p["decay"]
            if p["life"] <= 0:
                self.particles.remove(p)

        if self.is_dragging:
            pull_viz = pygame.math.Vector2(self.virtual_pull.x, self.virtual_pull.y)
            if pull_viz.length() > 300:
                pull_viz.scale_to_length(300)
            self.curler_anim.update("BACKSWING", pull_viz)

        if self.turn_state == "LUNGING" or self.curler_anim.state == "LUNGING":
            self.curler_anim.update("LUNGING")

        if self.turn_state == "SLIDING":
            mouse_pos = self.get_pointer_pos()
            is_mouse_pressed = self.get_pointer_pressed()
            my_team = self.preferred_color if self.game_mode in ["BOT", "HOST", "JOIN", "STORY"] else self.current_team

            can_sweep_legally = False
            for s in self.stones:
                if s.is_moving and (s.team == my_team or s.pos.y < self.house_pos.y):
                    can_sweep_legally = True
                    break

            is_sweeping = is_mouse_pressed and can_sweep_legally
            delta = (mouse_pos - self.last_mouse_pos).length()
            self.is_sweeping_now = is_sweeping

            if self.is_sweeping_now:
                if delta > 4:
                    self.sweep_power = min(1.0, self.sweep_power + 0.1)
                else:
                    self.sweep_power = max(0.0, self.sweep_power - 0.05)

                if self.sweep_power > 0:
                    self.audio.play_curler_call(self.sweep_power)
                    self.audio.update_sweep(self.sweep_power)
                    if not IS_ANDROID or random.random() < 0.10:
                        for _ in range(1 if IS_ANDROID else 3):
                            self.particles.append(
                                {
                                    "pos": mouse_pos + pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30)),
                                    "vel": pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-3, 0)),
                                    "life": 1.0,
                                    "decay": random.uniform(0.02, 0.05),
                                    "type": "sweep",
                                }
                            )
                else:
                    self.audio.update_sweep(0.0)
            else:
                self.sweep_power = max(0.0, self.sweep_power - 0.05)
                self.audio.update_sweep(0.0)

            mouse_pos = self.get_pointer_pos()

            for s in self.stones:
                can_player_sweep = is_sweeping and (mouse_pos - s.pos).length() < 350
                is_remote_sweeping = getattr(self, "remote_sweep_timer", 0) > 0
                actual_sweep = (
                    self.sweep_power
                    if (can_player_sweep and (s.team == my_team or s.pos.y < self.house_pos.y))
                    or (is_remote_sweeping and (s.team != my_team or s.pos.y < self.house_pos.y))
                    else 0.0
                )
                if getattr(self, "game_mode", None) == "STORY" and can_player_sweep and actual_sweep > 0:
                    actual_sweep *= 1.0 + self.story.level * 0.15
                s.update(actual_sweep, FRICTION_BASE)
                if s.is_moving and s.vel.length() > 0.5:
                    self.particles.append(
                        {
                            "pos": s.pos + pygame.math.Vector2(random.uniform(-15, 15), random.uniform(-15, 15)),
                            "vel": s.vel * -0.1,
                            "life": 1.0,
                            "decay": random.uniform(0.01, 0.03),
                            "type": "trail",
                        }
                    )

            if self.game_mode in ["HOST", "JOIN"] and self.frames_elapsed % 60 == 0:
                if self.sweep_power > 0.1 or getattr(self, "last_sent_sweep", 0.0) > 0.1:
                    self.net.send_action({"cmd": "sweep", "p": round(self.sweep_power, 2)})
                    self.last_sent_sweep = self.sweep_power

            if getattr(self, "remote_sweep_timer", 0) > 0:
                self.remote_sweep_timer -= 1
            else:
                self.sweep_power *= 0.86

            self.audio.update_sweep(self.sweep_power)

            moving = False
            max_speed = 0.0
            self.handle_collisions()

            valid_stones = []
            for s in self.stones:
                if s.is_moving:
                    if s.pos.x - s.radius < 0 or s.pos.x + s.radius > BASE_WIDTH or s.pos.y < -s.radius:
                        s.is_moving = False
                        self.audio.play_clack(5.0)
                        for _ in range(8):
                            self.particles.append(
                                {
                                    "pos": pygame.math.Vector2(s.pos),
                                    "vel": pygame.math.Vector2(random.uniform(-4, 4), random.uniform(-4, 4)),
                                    "life": 1.0,
                                    "decay": 0.05,
                                    "type": "spark",
                                }
                            )
                    else:
                        moving = True
                        max_speed = max(max_speed, s.vel.length())
                        valid_stones.append(s)
                else:
                    valid_stones.append(s)

            self.stones = valid_stones
            self.audio.update_slide(max_speed)

            if not moving:
                self.audio.update_slide(0.0)
                self.audio.update_sweep(0.0)

                valid_stones_final = []
                hog_line_y = self.house_pos.y + 400
                back_line_y = self.house_pos.y - 220
                for s in self.stones:
                    if s.pos.y - s.radius < hog_line_y and s.pos.y + s.radius > back_line_y:
                        valid_stones_final.append(s)
                self.stones = valid_stones_final

                # Absolute End of Slide Sync Broadcast for Netcode
                if self.game_mode == "HOST" and hasattr(self, "was_moving_last_frame") and self.was_moving_last_frame:
                    self.net.send_action(
                        {"cmd": "sync_state", "stones": [s.get_state((BASE_HEIGHT // 2) + 100) for s in self.stones]}
                    )

                if self.game_mode == "CHALLENGE":
                    if self.stones_thrown[0] == 1:
                        self.challenge_attempts += 1
                        cx, cy = self.house_pos.x, self.house_pos.y

                        if self.c_type in ["DRAW", "GUARD"]:
                            self.challenge_success = False
                            for s in self.stones:
                                if s.team == 0:
                                    dist = (pygame.math.Vector2(s.pos) - pygame.math.Vector2(self.challenge_target[:2])).length()
                                    if dist <= (self.challenge_target[2] + (s.radius * 0.95)):
                                        self.challenge_success = True
                                        break

                        elif self.c_type == "TAKEOUT":
                            self.challenge_success = (self.challenge_takeout_target not in self.stones) and any(
                                s.team == 0 and (pygame.math.Vector2(s.pos) - pygame.math.Vector2(cx, cy)).length() <= 252
                                for s in self.stones
                            )
                        elif self.c_type == "DOUBLE":
                            self.challenge_success = len([s for s in self.stones if s.team == 1]) == 0
                        self.turn_state = "END"
                else:
                    if self.stones_thrown[0] >= self.stones_per_team and self.stones_thrown[1] >= self.stones_per_team:
                        in_house = [
                            ((s.pos - self.house_pos).length(), s.team)
                            for s in self.stones
                            if (s.pos - self.house_pos).length() <= 252
                        ]
                        if in_house:
                            in_house.sort(key=lambda x: x[0])
                            winner = in_house[0][1]
                            pts = sum(1 for d, t in in_house if t == winner and all(d < od for od, ot in in_house if ot != winner))
                            if pts > 0:
                                self.score[winner][self.current_end - 1] = pts
                                self.hammer_team = 0 if winner == 1 else 1
                        self.turn_state = "END"
                    else:
                        self.current_team = 1 if self.current_team == 0 else 0
                        self.turn_state = "AIMING"
                        self.selected_curl = 0.0
                        self.spawn_next_stone()

            self.was_moving_last_frame = moving
        elif self.turn_state == "AIMING" and self.game_mode in ("BOT", "STORY") and self.current_team != self.preferred_color:
            self.execute_ai()
        self.last_mouse_pos = self.get_pointer_pos()

    def update_network(self):
        if self.game_mode not in ["HOST", "JOIN"]:
            return
        if self.app_state == "MENU" and self.net.matched:
            self.reset_match()
            self.app_state = "COIN_TOSS"
            self.coin_timer = 30
            self.coin_flip_result = random.choice([0, 1]) if self.game_mode == "HOST" else -1
            self.audio.stop_music()
            self.audio.play_cheer()

        if not hasattr(self, "deferred_actions"):
            self.deferred_actions = []
        actions_to_process = self.deferred_actions[:]
        self.deferred_actions = []

        while True:
            data = self.net.receive_action()
            if not data:
                break
            actions_to_process.append(data)

        for data in actions_to_process:
            if data.get("cmd") in ["shoot", "sweep"] and getattr(self, "app_state", "MENU") != "PLAY":
                self.deferred_actions.append(data)
                continue

            if data.get("cmd") == "chat":
                self.chat_messages.append(
                    {"text": f"{self.net.opponent.split('!')[0]}: {data['msg']}", "time": pygame.time.get_ticks()}
                )
            elif data.get("cmd") == "coin" and self.game_mode == "JOIN":
                self.coin_flip_result = data["result"]
            elif data.get("cmd") == "shoot":
                if not hasattr(self, "active_stone"):
                    self.spawn_next_stone()
                if getattr(self, "turn_state", "NONE") == "SLIDING":
                    self.current_team = 1 if getattr(self, "current_team", 0) == 0 else 0
                    self.spawn_next_stone()
                if "sid" in data:
                    self.active_stone.id = data["sid"]
                self.active_stone.vel = pygame.math.Vector2(data["vx"], data["vy"])
                self.active_stone.curl = data["c"]
                self.active_stone.is_moving = True
                self.stones_thrown[self.current_team] += 1
                self.total_stones_played += 1
                self.turn_state = "SLIDING"
                self.audio.play_throw()
                self.curler_anim.update("LUNGING")
            elif data.get("cmd") == "sweep":
                self.sweep_power = data["p"]
                self.remote_sweep_timer = 20
            elif data.get("cmd") in ("sync_state", "sync") and self.game_mode == "JOIN":
                if data.get("cmd") == "sync":
                    self.turn_state = data["st"]
                    self.current_team = data["t"]
                    self.score = {int(k): v for k, v in data["sc"].items()}
                stones_data = data.get("stones") if "stones" in data else data.get("s", [])
                offset_y = ((BASE_HEIGHT // 2) + 100) if data.get("cmd") == "sync_state" else 0
                new_stones = []
                for i, s_data in enumerate(stones_data):
                    sid = s_data[8] if len(s_data) > 8 else None
                    if sid is not None and sid != -1:
                        existing = next((s for s in self.stones if getattr(s, "id", -1) == sid), None)
                    else:
                        existing = self.stones[i] if i < len(self.stones) else None

                    if existing:
                        existing.set_state(s_data, offset_y)
                        new_stones.append(existing)
                    else:
                        ns = Stone(0, 0, 0)
                        ns.set_state(s_data, offset_y)
                        new_stones.append(ns)

                if hasattr(self, "active_stone") and self.active_stone in self.stones and self.active_stone not in new_stones:
                    if getattr(self, "turn_state", "NONE") == "AIMING":
                        new_stones.append(self.active_stone)

                self.stones = new_stones
            elif data.get("cmd") == "set_color":
                self.preferred_color = 1 - data["color"]
            elif data.get("cmd") == "opponent_left":
                self.app_state = "MATCH_OVER"
                self.winner_text = "Opponent Disconnected"
                self.audio.play_cheer()

        if self.game_mode == "HOST" and self.app_state == "COIN_TOSS" and self.coin_timer == 25:
            self.net.send_action({"cmd": "coin", "result": self.coin_flip_result})

    def draw_menu(self):
        self.frames_since_start = getattr(self, "frames_since_start", 0) + 1

        if not getattr(self, "played_intro", False) and self.frames_since_start >= 30:
            if getattr(self.audio, "snd_speech", None):
                self.audio.ch_sfx.play(self.audio.snd_speech)
                self.played_intro = True

        self.canvas.fill((10, 12, 16))
        self.last_starfield_speed = 2.0
        self.starfield.draw(self.canvas, 2.0, getattr(self, "time_mult", 1.0))
        cx, t_ms = BASE_WIDTH // 2, pygame.time.get_ticks() * 0.001

        if (
            not getattr(self, "is_music_muted", False)
            and self.app_state in ["MENU", "ROOM_PROMPT", "CHALLENGE_MENU", "OPTIONS_MENU"]
            and self.frames_since_start >= 210
        ):
            self.audio.play_music()
        elif getattr(self, "is_music_muted", False) or self.app_state not in [
            "MENU",
            "ROOM_PROMPT",
            "CHALLENGE_MENU",
            "OPTIONS_MENU",
        ]:
            self.audio.stop_music()

        self.menu_dy = (BASE_HEIGHT - 1920) // 2
        self.menu_stone.draw(self.canvas, cx, 300 + self.menu_dy, self.get_pointer_pos())

        bx, by = cx - self.title_base.get_width() // 2, 80 + self.menu_dy + int(math.sin(t_ms * 4.0) * 15)

        # Draw pre-rendered soft outline (requires just 1 blit instead of 36)
        pad = 9  # outline_size (7) + 2
        self.canvas.blit(self.title_outline, (bx - pad, by - pad))

        # Draw live-calculated animated title (zero allocation, 2 C-level blits)
        offset = int((pygame.time.get_ticks() * 0.15) % 150)
        self.title_rainbow_frame.fill((0, 0, 0, 0))
        self.title_rainbow_frame.blit(self.title_base, (0, 0))
        self.title_rainbow_frame.blit(self.rainbow_grad, (-offset, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.canvas.blit(self.title_rainbow_frame, (bx, by))

        status_string = (
            f"STATUS: ERROR - {self.net.connection_error}"
            if getattr(self.net, "connection_error", "")
            else (
                "STATUS: Connecting to Network..."
                if self.net.connecting
                else (
                    "STATUS: Match Found!"
                    if self.net.matched
                    else (
                        f"STATUS: Hosting {self.net.room_display}... Waiting."
                        if getattr(self.net, "is_host", False) and self.net.running
                        else "STATUS: Offline Ready"
                    )
                )
            )
        )
        color = (
            HOUSE_RED
            if getattr(self.net, "connection_error", "")
            else (TEAM_YELLOW if self.net.connecting or self.net.matched or self.net.running else (150, 160, 180))
        )
        status_lbl = self.small_font.render(status_string, True, color)
        self.canvas.blit(status_lbl, (cx - status_lbl.get_width() // 2, 210 + self.menu_dy))

        for btn in self.menu_buttons:
            text = btn["text"]

            is_hovered = self.last_hovered == btn["id"]
            target_scale = 1.07 if is_hovered else 1.0
            if abs(btn["scale"] - target_scale) < 0.005:
                btn["scale"] = target_scale
            else:
                btn["scale"] += (target_scale - btn["scale"]) * 0.25
            b_w, b_h = int(600 * btn["scale"]), int(100 * btn["scale"])
            rect = pygame.Rect(cx - b_w // 2, btn["y"] + self.menu_dy + (100 - b_h) // 2, b_w, b_h)

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
                pygame.draw.circle(
                    self.canvas,
                    (max(0, stone_c[0] - 50), max(0, stone_c[1] - 50), max(0, stone_c[2] - 50)),
                    (rock_x, rock_y),
                    16,
                    2,
                )
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
        pygame.draw.circle(self.canvas, TEAM_YELLOW, (int(handle_x), 1558 + self.menu_dy), 26)
        pygame.draw.circle(self.canvas, WHITE, (int(handle_x), 1558 + self.menu_dy), 26, 4)
        diff_lbl = self.font.render(f"BOT DIFFICULTY: {self.ai_difficulty}", True, WHITE)
        self.canvas.blit(diff_lbl, (cx - diff_lbl.get_width() // 2, 1490 + self.menu_dy))

        # Draw Mute Button moved to global UI
        self.draw_global_ui()

    def perform_update(self):
        try:
            import urllib.request
            import sys, os, re

            url_main = "https://raw.githubusercontent.com/jjivany/wincurl/main/main.py"
            req = urllib.request.Request(url_main, headers={"User-Agent": "Mozilla/5.0"})
            try:
                with urllib.request.urlopen(req) as response:
                    new_code = response.read().decode("utf-8")
                m = re.search(r'VERSION\s*=\s*".*?Build\s+(\d+)"', new_code)
                remote_build = int(m.group(1)) if m else 0

                local_m = re.search(r"Build\s+(\d+)", VERSION)
                local_build = int(local_m.group(1)) if local_m else 0

                if remote_build <= local_build:
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
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="PUT")
                with urllib.request.urlopen(req) as response:
                    pass
            except Exception as e:
                print("Failed to post score:", e)

        import sys

        if hasattr(sys, "platform") and sys.platform == "emscripten":
            return
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

        import sys

        if hasattr(sys, "platform") and sys.platform == "emscripten":
            return
        threading.Thread(target=_fetch, daemon=True).start()

    def draw_room_prompt(self):
        self.draw_menu()
        self.canvas.blit(self.dark_overlay_200, (0, 0))
        cx, cy = BASE_WIDTH // 2, BASE_HEIGHT // 2

        lbl_v = self.font_62.render("ENTER MATCHMAKING ROOM NAME", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, cy - 150))

        draw_glass_rect(self.canvas, self.prompt_rect, HOUSE_BLUE, self.prompt_rect.h // 2, animate_sheen=False)
        txt = f"{self.room_text}_"
        img = self.font.render(txt, True, WHITE)
        self.canvas.blit(img, img.get_rect(center=(cx, cy + 10)))

        if IS_ANDROID:
            sub = self.small_font.render("Tap here to connect | Tap outside to cancel", True, (150, 160, 180))
        else:
            sub = self.small_font.render("Press ENTER to connect | ESC to cancel", True, (150, 160, 180))
        self.canvas.blit(sub, (cx - sub.get_width() // 2, cy + 120))
        self.draw_global_ui()

    def draw_options_menu(self):
        self.canvas.fill((10, 12, 16))
        self.last_starfield_speed = 0.5
        self.starfield.draw(self.canvas, 0.5, getattr(self, "time_mult", 1.0))

        cx, t_ms = BASE_WIDTH // 2, pygame.time.get_ticks() * 0.001
        self.menu_dy = (BASE_HEIGHT - 1920) // 2
        bx, by = cx - self.title_base.get_width() // 2, 80 + self.menu_dy + int(math.sin(t_ms * 4.0) * 15)
        pad = 9
        self.canvas.blit(self.title_outline, (bx - pad, by - pad))
        offset = int((pygame.time.get_ticks() * 0.15) % 150)
        self.title_rainbow_frame.fill((0, 0, 0, 0))
        self.title_rainbow_frame.blit(self.title_base, (0, 0))
        self.title_rainbow_frame.blit(self.rainbow_grad, (-offset, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.canvas.blit(self.title_rainbow_frame, (bx, by))

        lbl_v = self.font_72.render("OPTIONS", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, 320 + getattr(self, "menu_dy", 0)))
        lbl_build = self.font.render(f"(Build {VERSION})", True, (150, 160, 180))
        self.canvas.blit(lbl_build, (cx - lbl_build.get_width() // 2, 385 + getattr(self, "menu_dy", 0)))

        for btn in self.options_buttons:
            if (not IS_ANDROID and btn["id"] == "hi_res_mode") or (
                IS_ANDROID and not getattr(self, "hi_res_mode", False) and btn["id"] == "smoothscale"
            ):
                continue

            if btn["id"] == "name":
                text = f"Name: {self.username}" + ("_" if self.typing_target == "name" else "")
            elif btn["id"] == "color":
                btn["color"] = TEAM_YELLOW if self.preferred_color else HOUSE_RED
                text = "My Team:"
            elif btn["id"] == "master_vol":
                text = "Volume"
            elif btn["id"] == "hi_res_mode":
                text = "Hi-Res Mode: " + ("ON" if getattr(self, "hi_res_mode", False) else "OFF")
                btn["color"] = (40, 120, 60) if getattr(self, "hi_res_mode", False) else TEAM_YELLOW
            elif btn["id"] == "smoothscale":
                text = "Smoothscale: " + ("ON" if getattr(self, "fxaa_on", False) else "OFF")
                btn["color"] = (40, 120, 60) if getattr(self, "fxaa_on", False) else TEAM_YELLOW
            elif btn["id"] == "update":
                text = getattr(self, "update_status", "Check for update")
            else:
                text = btn["text"]

            is_hovered = self.last_hovered == "opt_" + btn["id"]
            target_scale = 1.07 if is_hovered else 1.0
            if abs(btn["scale"] - target_scale) < 0.005:
                btn["scale"] = target_scale
            else:
                btn["scale"] += (target_scale - btn["scale"]) * 0.3

            rect = pygame.Rect(
                cx - 300 * btn["scale"],
                btn["y"] + getattr(self, "menu_dy", 0) - 15 * btn["scale"],
                600 * btn["scale"],
                95 * btn["scale"],
            )
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
                pygame.draw.circle(
                    self.canvas,
                    (max(0, stone_c[0] - 50), max(0, stone_c[1] - 50), max(0, stone_c[2] - 50)),
                    (rock_x, rock_y),
                    16,
                    2,
                )
                pygame.draw.line(self.canvas, BLACK, (rock_x - 12, rock_y), (rock_x + 12, rock_y), 10)
                pygame.draw.circle(self.canvas, BLACK, (rock_x - 12, rock_y), 5)
                pygame.draw.circle(self.canvas, BLACK, (rock_x + 12, rock_y), 5)
                pygame.draw.line(self.canvas, stone_c, (rock_x - 12, rock_y), (rock_x + 12, rock_y), 6)
                pygame.draw.circle(self.canvas, stone_c, (rock_x - 12, rock_y), 3)
                pygame.draw.circle(self.canvas, stone_c, (rock_x + 12, rock_y), 3)
            elif btn["id"] == "master_vol":
                img = self.font.render(text, True, WHITE)
                txt_rect = img.get_rect(center=(rect.left + 160, rect.centery))
                self.canvas.blit(img, txt_rect)

                bar_x, bar_w = txt_rect.right + 30, 240
                pygame.draw.line(self.canvas, (80, 90, 100), (bar_x, rect.centery), (bar_x + bar_w, rect.centery), 10)
                vol = getattr(self.audio, "master_volume", 1.0)
                pygame.draw.line(self.canvas, (200, 210, 220), (bar_x, rect.centery), (bar_x + int(bar_w * vol), rect.centery), 10)
                pygame.draw.circle(self.canvas, WHITE, (bar_x + int(bar_w * vol), rect.centery), 12)
            else:
                img = self.font.render(text, True, WHITE) if btn["id"] != "fxaa" else self.chat_font.render(text, True, WHITE)
                if img.get_width() > rect.w - 40:
                    scale = (rect.w - 40) / img.get_width()
                    img = pygame.transform.smoothscale(img, (int(rect.w - 40), int(img.get_height() * scale)))
                self.canvas.blit(img, img.get_rect(center=rect.center))
                if btn["id"] == "back":
                    self.draw_back_icon(self.canvas, rect.x + 30, rect.centery - 10)

        self.draw_global_ui()

    def handle_options_events(self, event):
        mouse_pos = getattr(event, "pos", self.get_pointer_pos())
        mx, my = mouse_pos[0] if isinstance(mouse_pos, tuple) else mouse_pos.x, (
            mouse_pos[1] if isinstance(mouse_pos, tuple) else mouse_pos.y
        )
        menu_my = my - getattr(self, "menu_dy", 0)

        curr_hov = None
        for b in self.options_buttons:
            if (not IS_ANDROID and b["id"] == "hi_res_mode") or (
                IS_ANDROID and not getattr(self, "hi_res_mode", False) and b["id"] == "smoothscale"
            ):
                continue
            if 300 < mx < 900 and b["y"] < menu_my < b["y"] + 90 * b["scale"]:
                curr_hov = "opt_" + b["id"]
                break

        if curr_hov != self.last_hovered:
            if curr_hov:
                self.audio.play_hover()
            self.last_hovered = curr_hov

        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            now = pygame.time.get_ticks()
            if hasattr(self, "last_click_time") and now - getattr(self, "last_click_time", 0) < 300:
                return
            self.last_click_time = now

            if self.typing_target:
                if not (300 < mx < 900 and 570 < menu_my < 690):
                    self.set_typing_target(None)

            if 300 < mx < 900:
                for b in self.options_buttons:
                    if (not IS_ANDROID and b["id"] == "hi_res_mode") or (
                        IS_ANDROID and not getattr(self, "hi_res_mode", False) and b["id"] == "smoothscale"
                    ):
                        continue
                    if b["y"] < menu_my < b["y"] + 90 * b["scale"]:
                        self.audio.play_click()
                        new_target = None
                        if b["id"] == "name":
                            new_target = "name"
                        elif b["id"] == "master_vol":
                            pass  # Handled by drag
                        elif b["id"] == "color":
                            self.preferred_color = 1 if self.preferred_color == 0 else 0
                            self.save_progress()
                        elif b["id"] == "hi_res_mode":
                            self.hi_res_mode = not getattr(self, "hi_res_mode", False)
                            self.save_progress()
                        elif b["id"] == "smoothscale":
                            self.fxaa_on = not getattr(self, "fxaa_on", False)
                            self.save_progress()

                        elif b["id"] == "update":
                            if not getattr(self, "is_updating", False):
                                self.is_updating = True
                                self.update_status = "updating..."
                                import sys

                                if not (hasattr(sys, "platform") and sys.platform == "emscripten"):
                                    threading.Thread(target=self.perform_update, daemon=True).start()
                        elif b["id"] == "back":
                            self.app_state = "MENU"
                        self.set_typing_target(new_target)
                        break
        elif event.type == KEYDOWN and self.typing_target == "name":
            if event.key in (K_RETURN, K_KP_ENTER):
                self.set_typing_target(None)
                self.save_progress()
            elif event.key == K_BACKSPACE:
                self.username = self.username[:-1]
                self.save_progress()
        if self.is_pointer_pressed:
            for b in self.options_buttons:
                if b["id"] == "master_vol" and 300 < mx < 900 and b["y"] < menu_my < b["y"] + 110 * b["scale"]:
                    text_str = "Volume"
                    img = self.font.render(text_str, True, (255, 255, 255))
                    txt_rect = img.get_rect(center=(BASE_WIDTH // 2 - 300 * b["scale"] + 160, b["y"] + 55 * b["scale"]))
                    bar_x = txt_rect.right + 30
                    vol = max(0.0, min(1.0, (mx - bar_x) / 240))
                    self.audio.set_master_volume(vol)
                    self.save_progress()
                    break

    def draw_challenge_menu(self):
        self.canvas.fill((10, 12, 16))
        self.last_starfield_speed = 2.0
        self.starfield.draw(self.canvas, 2.0, getattr(self, "time_mult", 1.0))
        cx = BASE_WIDTH // 2
        lbl_v = self.font_72.render("SELECT CHALLENGE", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, 120))

        for i in range(25):
            row, col = i // 5, i % 5
            rect = pygame.Rect(cx - 250 + col * 100, 300 + row * 100, 90, 90)
            is_hov = rect.collidepoint(self.get_pointer_pos())
            draw_glass_rect(self.canvas, rect, (40, 120, 60) if self.challenge_progress[i] else PURPLE_SUIT, 16, is_hov)
            txt = self.font.render(str(i + 1), True, WHITE)
            self.canvas.blit(txt, txt.get_rect(center=rect.center))
            if self.challenge_progress[i]:
                pygame.draw.line(self.canvas, HOUSE_RED, rect.topleft, rect.bottomright, 8)

        draw_glass_rect(
            self.canvas,
            self.btn_return_menu,
            HOUSE_BLUE,
            self.btn_return_menu.h // 2,
            self.btn_return_menu.collidepoint(self.get_pointer_pos()),
        )
        lbl_btn = self.font.render("BACK TO MENU", True, WHITE)
        self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))
        self.draw_global_ui()

    def draw_bot_menu(self):
        self.screen.fill((10, 12, 16))
        self.canvas.fill((10, 12, 16))
        cx = BASE_WIDTH // 2
        lbl_v = self.font_72.render("LOCAL VS BOT" if getattr(self, "game_mode", "") == "BOT" else "LOCAL 1V1 MATCH", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, 100))

        if getattr(self, "saved_match_state", None) and self.saved_match_state.get("game_mode") == getattr(self, "game_mode", ""):
            start_btn = pygame.Rect(cx - 200, 450, 400, 100)
            draw_glass_rect(self.canvas, start_btn, HOUSE_RED, start_btn.h // 2, start_btn.collidepoint(self.get_pointer_pos()))
            lbl_btn2 = self.font.render("RESUME MATCH", True, WHITE)
            self.canvas.blit(lbl_btn2, lbl_btn2.get_rect(center=start_btn.center))

            new_btn = pygame.Rect(cx - 200, 600, 400, 100)
            draw_glass_rect(self.canvas, new_btn, (100, 100, 100), new_btn.h // 2, new_btn.collidepoint(self.get_pointer_pos()))
            lbl_new = self.font.render("NEW MATCH", True, WHITE)
            self.canvas.blit(lbl_new, lbl_new.get_rect(center=new_btn.center))
        else:
            start_btn = pygame.Rect(cx - 200, 500, 400, 100)
            draw_glass_rect(self.canvas, start_btn, HOUSE_RED, start_btn.h // 2, start_btn.collidepoint(self.get_pointer_pos()))
            lbl_btn2 = self.font.render("START MATCH", True, WHITE)
            self.canvas.blit(lbl_btn2, lbl_btn2.get_rect(center=start_btn.center))

        draw_glass_rect(
            self.canvas,
            self.btn_return_menu,
            HOUSE_BLUE,
            self.btn_return_menu.h // 2,
            self.btn_return_menu.collidepoint(self.get_pointer_pos()),
        )
        lbl_btn = self.font.render("BACK TO MENU", True, WHITE)
        self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

    def draw_save_slots(self):
        self.screen.fill((10, 12, 16))
        self.canvas.fill((10, 12, 16))

        cx, cy = BASE_WIDTH // 2, BASE_HEIGHT // 2
        title = self.font.render("SELECT SAVE SLOT", True, TEAM_YELLOW)
        self.canvas.blit(title, (cx - title.get_width() // 2, 150))

        if getattr(self, "game_mode", "") == "BOT":
            slots = self.bot_slots_data
        elif getattr(self, "game_mode", "") == "LOCAL":
            slots = self.local_slots_data
        else:
            slots = self.slots_data
        for i in range(3):
            rect = pygame.Rect(cx - 300, 300 + i * 200, 600, 150)
            is_hover = rect.collidepoint(self.get_pointer_pos())
            draw_glass_rect(self.canvas, rect, (60, 60, 80) if not is_hover else HOUSE_BLUE, rect.h // 4, is_hover)

            slot_data = slots[i] if i < len(slots) else {}
            if slot_data:
                # Summary of slot
                if getattr(self, "game_mode", "") == "BOT":
                    txt_main = self.font.render(f"BOT SLOT {i+1}", True, WHITE)
                elif getattr(self, "game_mode", "") == "LOCAL":
                    txt_main = self.font.render(f"1V1 SLOT {i+1}", True, WHITE)
                else:
                    prog = slot_data.get("story", {}).get("current_rink", 0) + 1
                    txt_main = self.font.render(f"SLOT {i+1} - STORY RINK {prog}", True, WHITE)
                has_save = slot_data.get("saved_match_state") is not None
                if has_save:
                    txt_sub = self.font.render(
                        f"[MATCH SAVED: {slot_data.get('saved_match_state').get('game_mode', '')}]", True, TEAM_YELLOW
                    )
                    self.canvas.blit(txt_sub, (cx - txt_sub.get_width() // 2, rect.centery + 10))
                self.canvas.blit(txt_main, (cx - txt_main.get_width() // 2, rect.centery - (20 if has_save else 0)))
            else:
                txt = self.font.render(f"SLOT {i+1} - EMPTY", True, (150, 150, 150))
                self.canvas.blit(txt, (cx - txt.get_width() // 2, rect.centery))

        draw_glass_rect(
            self.canvas,
            self.btn_return_menu,
            HOUSE_RED,
            self.btn_return_menu.h // 2,
            self.btn_return_menu.collidepoint(self.get_pointer_pos()),
        )
        lbl_btn = self.font.render("BACK TO MENU", True, WHITE)
        self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

    def draw_story_map(self):
        self.screen.fill((10, 12, 16))
        self.canvas.fill((10, 12, 16))
        self.last_starfield_speed = 1.0
        self.starfield.draw(self.canvas, 1.0, getattr(self, "time_mult", 1.0))
        cx = BASE_WIDTH // 2
        lbl_v = self.font_72.render("STORY PROGRESS", True, WHITE)
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, 70))

        lbl_defeated = self.font.render(f"RINK LEADERS DEFEATED: {getattr(self.story, 'current_rink', 0)}", True, TEAM_YELLOW)
        self.canvas.blit(lbl_defeated, (cx - lbl_defeated.get_width() // 2, 130))

        # Trophies (Mario Kart style)
        trophy_w = 40
        spacing = 10
        cur_rink = getattr(self.story, "current_rink", 0)
        total_w = cur_rink * (trophy_w + spacing) - spacing
        start_x = cx - total_w // 2
        for i in range(cur_rink):
            rink = STORY_RINKS[i] if i < len(STORY_RINKS) else STORY_RINKS[-1]
            draw_trophy(self.canvas, start_x + i * (trophy_w + spacing), 165, size=trophy_w)

        xp_needed = getattr(self.story, "level", 1) * 100
        xp_rect = pygame.Rect(cx - 300, 220, 600, 30)
        draw_glass_rect(self.canvas, xp_rect, (50, 50, 50), 15, False, animate_sheen=False)
        fill_width = int(600 * (getattr(self.story, "xp", 0) / max(1, xp_needed)))
        if fill_width > 0:
            draw_glass_rect(self.canvas, pygame.Rect(cx - 300, 220, fill_width, 30), TEAM_YELLOW, 15, False, animate_sheen=False)
        xp_txt = self.small_font.render(f"XP: {getattr(self.story, 'xp', 0)} / {xp_needed}", True, WHITE)
        self.canvas.blit(xp_txt, xp_txt.get_rect(center=xp_rect.center))

        spent_points = sum(getattr(self.story, "stats", {}).values())
        avail_points = max(0, (getattr(self.story, "level", 1) - 1) - spent_points)
        pts_txt = self.font.render(
            f"LEVEL {getattr(self.story, 'level', 1)} - SKILL POINTS: {avail_points}",
            True,
            (100, 255, 100) if avail_points > 0 else WHITE,
        )
        self.canvas.blit(pts_txt, (cx - pts_txt.get_width() // 2, 265))

        stat_names = [
            ("power", "LAUNCH POWER", "Increases max throwing velocity"),
            ("curl_control", "CURL CONTROL", "Improves stone curl responsiveness"),
            ("trajectory_preview", "TRAJECTORY PREVIEW", "Lengthens the aiming line"),
        ]
        self.btn_upgrades = {}

        if self.story.current_rink < len(STORY_RINKS):
            rink = STORY_RINKS[self.story.current_rink]
        else:
            rink = {"color": WHITE, "boss": "None", "intro_dialog": []}

        if self.app_state != "STORY_DIALOG":
            for i, (k, name, sub) in enumerate(stat_names):
                y = 300 + i * 100
                val = self.story.stats.get(k, 0)
                lbl = self.font.render(f"{name}: {val}/5", True, WHITE)
                self.canvas.blit(lbl, (cx - 280, y))
                sub_lbl = self.small_font.render(sub, True, (150, 160, 180))
                self.canvas.blit(sub_lbl, (cx - 280, y + 45))

                btn = pygame.Rect(cx + 150, y - 10, 80, 50)
                color = HOUSE_RED if avail_points > 0 and val < 5 else (100, 100, 100)
                draw_glass_rect(self.canvas, btn, color, 15, btn.collidepoint(self.get_pointer_pos()))
                btn_txt = self.font.render("+", True, WHITE)
                self.canvas.blit(btn_txt, btn_txt.get_rect(center=btn.center))
                self.btn_upgrades[k] = btn

            txt = self.font.render(f"Rink: {self.story.current_rink + 1} / 8", True, TEAM_YELLOW)
            self.canvas.blit(txt, (cx - txt.get_width() // 2, 580))

            if self.story.current_rink < len(STORY_RINKS):
                rink_txt = self.font.render(f"Next: {rink['name']} ({rink['boss']})", True, rink["color"])
                self.canvas.blit(rink_txt, (cx - rink_txt.get_width() // 2, 640))

                if getattr(self, "saved_match_state", None) and self.saved_match_state.get("game_mode") == "STORY":
                    start_btn = pygame.Rect(cx - 200, 750, 400, 80)
                    draw_glass_rect(
                        self.canvas, start_btn, HOUSE_RED, start_btn.h // 2, start_btn.collidepoint(self.get_pointer_pos())
                    )
                    lbl_btn2 = self.font.render("RESUME MATCH", True, WHITE)
                    self.canvas.blit(lbl_btn2, lbl_btn2.get_rect(center=start_btn.center))

                    new_btn = pygame.Rect(cx - 200, 850, 400, 80)
                    draw_glass_rect(
                        self.canvas, new_btn, (100, 100, 100), new_btn.h // 2, new_btn.collidepoint(self.get_pointer_pos())
                    )
                    lbl_new = self.font.render("NEW MATCH", True, WHITE)
                    self.canvas.blit(lbl_new, lbl_new.get_rect(center=new_btn.center))
                else:
                    start_btn = pygame.Rect(cx - 200, 800, 400, 100)
                    draw_glass_rect(
                        self.canvas, start_btn, HOUSE_RED, start_btn.h // 2, start_btn.collidepoint(self.get_pointer_pos())
                    )
                    lbl_btn2 = self.font.render("BATTLE NEXT RINK", True, WHITE)
                    self.canvas.blit(lbl_btn2, lbl_btn2.get_rect(center=start_btn.center))
            else:
                txt_win = self.font.render("YOU BEAT THE GAME!", True, (100, 255, 100))
                self.canvas.blit(txt_win, (cx - txt_win.get_width() // 2, 320))

            draw_glass_rect(
                self.canvas,
                self.btn_return_menu,
                HOUSE_BLUE,
                self.btn_return_menu.h // 2,
                self.btn_return_menu.collidepoint(self.get_pointer_pos()),
            )
            lbl_btn = self.font.render("BACK TO MENU", True, WHITE)
            self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

        if self.app_state == "STORY_DIALOG" and getattr(self, "dialog_index", 0) < len(rink["intro_dialog"]):
            dt_ticks = pygame.time.get_ticks() - getattr(self, "dialog_time", pygame.time.get_ticks())

            self.canvas.blit(self.dark_overlay_200, (0, 0))

            if self.story.scene == "intro":
                for i in range(-15, 15):
                    grid_y = BASE_HEIGHT // 2 + (i * 120 + int(self.frames_elapsed) % 120)
                    pygame.draw.line(self.canvas, (55, 70, 95), (0, grid_y), (BASE_WIDTH, grid_y), 2)
                for i in range(-25, 25):
                    grid_x = BASE_WIDTH // 2 + (i * 120)
                    pygame.draw.line(self.canvas, (55, 70, 95), (grid_x, 0), (grid_x, BASE_HEIGHT), 2)

            dialog_rect = pygame.Rect(cx - 500, BASE_HEIGHT - 350, 1000, 250)

            draw_glass_rect(self.canvas, dialog_rect, (40, 40, 50), 24, False, True, animate_sheen=False)
            pygame.draw.rect(self.canvas, rink["color"], dialog_rect, 6, border_radius=24)
            pygame.draw.rect(self.canvas, WHITE, dialog_rect.inflate(-12, -12), 2, border_radius=22)

            boss_name = rink["boss"]
            slide_in = max(0, 300 - dt_ticks) if self.dialog_index == 0 else 0

            player_surf = get_pixel_portrait("Player", (240, 240))
            boss_surf = get_pixel_portrait(boss_name, (280, 280))

            def draw_shadow(surf, key_name, x, y):
                shadow_key = key_name + "_shadow"
                if shadow_key not in PIXEL_PORTRAIT_CACHE:
                    mask = pygame.mask.from_surface(surf)
                    PIXEL_PORTRAIT_CACHE[shadow_key] = mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
                self.canvas.blit(PIXEL_PORTRAIT_CACHE[shadow_key], (x + 12, y + 15))

            player_bob = math.sin(pygame.time.get_ticks() * 0.005) * 6
            px, py = dialog_rect.x + 20 - slide_in, dialog_rect.y - 240 + player_bob
            flipped_player_key = "Player_flipped_240"
            if flipped_player_key not in PIXEL_PORTRAIT_CACHE:
                PIXEL_PORTRAIT_CACHE[flipped_player_key] = pygame.transform.flip(player_surf, True, False)
            flipped_player = PIXEL_PORTRAIT_CACHE[flipped_player_key]
            draw_shadow(flipped_player, flipped_player_key, px, py)
            self.canvas.blit(flipped_player, (px, py))

            boss_bob = math.sin(pygame.time.get_ticks() * 0.005 + 2) * 8
            bx, by = dialog_rect.right - 300 + slide_in, dialog_rect.y - 280 + boss_bob
            draw_shadow(boss_surf, boss_name + "_280", bx, by)
            self.canvas.blit(boss_surf, (bx, by))

            boss_lbl = self.font.render(boss_name, True, WHITE)
            self.canvas.blit(boss_lbl, (dialog_rect.x + 40, dialog_rect.y + 20))

            import textwrap

            full_text = rink["intro_dialog"][self.dialog_index]
            chars_to_show = dt_ticks // 5
            typed_text = full_text[:chars_to_show]

            if not hasattr(self, "dialog_text_cache_index") or self.dialog_text_cache_index != self.dialog_index:
                self.dialog_text_cache = {}
                self.dialog_text_cache_index = self.dialog_index

            if typed_text not in self.dialog_text_cache:
                lines = textwrap.wrap(typed_text, width=50)
                self.dialog_text_cache[typed_text] = [self.font.render(line, True, (220, 220, 220)) for line in lines]

            for j, line_lbl in enumerate(self.dialog_text_cache[typed_text]):
                self.canvas.blit(line_lbl, (dialog_rect.x + 40, dialog_rect.y + 80 + j * 45))

            if chars_to_show >= len(full_text) and (pygame.time.get_ticks() % 1000 > 500):
                tap_lbl = self.small_font.render(f"Tap anywhere...", True, (150, 150, 150))
                self.canvas.blit(tap_lbl, (dialog_rect.right - 30 - tap_lbl.get_width(), dialog_rect.bottom - 40))

        self.draw_global_ui()

    def draw_coin_toss_screen(self):
        self.draw_ice()
        self.canvas.blit(self.dark_overlay_150, (0, 0))
        cx, cy, t = BASE_WIDTH // 2, BASE_HEIGHT // 2, 30 - self.coin_timer
        scale_x = abs(math.cos(t * 0.6))

        if self.coin_timer > 5:
            is_red = (t // 3) % 2 == 0
            text = "FLIPPING FOR HAMMER..."
        else:
            is_red = self.coin_flip_result == 0
            text = "RED GETS HAMMER" if is_red else "YELLOW GETS HAMMER"

        if scale_x > 0.05:
            c_surf = self.coin_red_surf if is_red else self.coin_yellow_surf
            w, h = c_surf.get_size()
            scaled = pygame.transform.scale(c_surf, (max(1, int(w * scale_x)), h)).convert_alpha()
            self.canvas.blit(scaled, (cx - scaled.get_width() // 2, cy - h // 2))

        lbl = self.font.render(text, True, WHITE)
        self.canvas.blit(lbl, (cx - lbl.get_width() // 2, cy + 150))

    def draw_pause_icon(self, surface, x, y):
        pygame.draw.rect(surface, BLACK, (x, y, 8, 24), border_radius=2)
        pygame.draw.rect(surface, BLACK, (x + 14, y, 8, 24), border_radius=2)

    def draw_back_icon(self, surface, x, y, color=WHITE):
        pygame.draw.polygon(surface, color, [(x, y + 10), (x + 12, y), (x + 12, y + 20)])
        pygame.draw.rect(surface, color, (x + 10, y + 6, 14, 8))

    def draw_gear_icon(self, surface, x, y, color=WHITE):
        pygame.draw.circle(surface, color, (x + 10, y + 10), 5, 2)
        for i in range(8):
            angle = math.radians(i * 45)
            dx1, dy1 = int(math.cos(angle) * 6), int(math.sin(angle) * 6)
            dx2, dy2 = int(math.cos(angle) * 9), int(math.sin(angle) * 9)
            pygame.draw.line(surface, color, (x + 10 + dx1, y + 10 + dy1), (x + 10 + dx2, y + 10 + dy2), 2)

    def draw_floppy_icon(self, surface, x, y, color=WHITE):
        pygame.draw.rect(surface, color, (x, y, 20, 20), 2)
        pygame.draw.rect(surface, color, (x + 4, y, 12, 6), 1)
        pygame.draw.rect(surface, color, (x + 4, y + 10, 12, 10), 1)
        pygame.draw.rect(surface, color, (x + 12, y + 2, 2, 2))

    def draw_ice(self):
        self.canvas.fill((10, 12, 16))
        self.canvas.blit(self.static_ice_surface, (int(getattr(self, "parallax_x", 0)), int(getattr(self, "parallax_y", 0))))

        t = pygame.time.get_ticks()
        if not IS_ANDROID:
            if not hasattr(self, "ice_sheen_surf"):
                self.ice_sheen_surf = pygame.Surface((1800, BASE_HEIGHT), pygame.SRCALPHA)
                self.ice_sheen_surf.fill((0, 0, 0, 0))
                pygame.draw.polygon(
                    self.ice_sheen_surf, (255, 255, 255, 40), [(600, 0), (1400, 0), (800, BASE_HEIGHT), (0, BASE_HEIGHT)]
                )
                pygame.draw.polygon(
                    self.ice_sheen_surf, (255, 255, 255, 80), [(900, 0), (1000, 0), (300, BASE_HEIGHT), (400, BASE_HEIGHT)]
                )
            sweep_x = (t * 0.1) % (BASE_WIDTH + 3000) - 1000
            self.canvas.blit(self.ice_sheen_surf, (sweep_x - 600, 0))

        if self.game_mode == "CHALLENGE" and self.challenge_target:
            cx, cy, cr = self.challenge_target
            pygame.draw.circle(
                self.canvas,
                (0, 255, 100, 150),
                (int(cx), int(cy)),
                int(cr + ((math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5) * 10),
                4,
            )

    def draw_ui(self):
        score_rect = pygame.Rect(0, 0, BASE_WIDTH, 130)
        draw_glass_rect(self.canvas, score_rect, (5, 5, 12, 190), border_radius=0, dark_mode=True, animate_sheen=False)

        # Animated light-up tinted glass effect
        t = pygame.time.get_ticks()
        if not hasattr(self, "glass_fx_grad"):
            self.glass_fx_grad = pygame.Surface((BASE_WIDTH, 130), pygame.SRCALPHA)
            for y in range(130):
                a = int(210 * (1.0 - y / 130.0))
                pygame.draw.line(self.glass_fx_grad, (0, 0, 0, a), (0, y), (BASE_WIDTH, y))
        self.canvas.blit(self.glass_fx_grad, (0, 0))

        # Sweeping glare light
        if not IS_ANDROID:
            if not hasattr(self, "score_sheen_surf"):
                self.score_sheen_surf = pygame.Surface((700, 130), pygame.SRCALPHA)
                pygame.draw.polygon(self.score_sheen_surf, (255, 255, 255, 25), [(260, 0), (320, 0), (220, 130), (160, 130)])
            sweep_x = (t * 0.6) % (BASE_WIDTH + 1500) - 500
            self.canvas.blit(self.score_sheen_surf, (sweep_x - 400, 0))
        pulse = (math.sin(t * 0.003) + 1.0) * 0.5
        border_alpha = int(60 + pulse * 100)
        pygame.draw.line(self.canvas, (150, 50, 50, border_alpha), (0, 128), (BASE_WIDTH, 128), 3)
        pygame.draw.line(self.canvas, (255, 100, 100, int(border_alpha * 0.5)), (0, 127), (BASE_WIDTH, 127), 1)

        if self.game_mode == "CHALLENGE":
            t1, t2 = self.font.render(self.challenge_text_1, True, WHITE), self.small_font.render(
                self.challenge_text_2, True, TEAM_YELLOW
            )
            self.canvas.blit(t1, (BASE_WIDTH // 2 - t1.get_width() // 2, 30))
            self.canvas.blit(t2, (BASE_WIDTH // 2 - t2.get_width() // 2, 80))
        else:
            pygame.draw.circle(self.canvas, HOUSE_RED, (30, 35), 12)
            pygame.draw.circle(self.canvas, (60, 60, 60), (30, 35), 12, 2)
            pygame.draw.circle(self.canvas, (100, 100, 100), (30, 35), 6, 2)
            self.canvas.blit(self.score_font.render("RED", True, HOUSE_RED), (55, 20))

            pygame.draw.circle(self.canvas, TEAM_YELLOW, (30, 85), 12)
            pygame.draw.circle(self.canvas, (60, 60, 60), (30, 85), 12, 2)
            pygame.draw.circle(self.canvas, (100, 100, 100), (30, 85), 6, 2)
            self.canvas.blit(self.score_font.render("YLW", True, TEAM_YELLOW), (55, 70))

            rem_r = self.stones_per_team - self.stones_thrown[0]
            rem_y = self.stones_per_team - self.stones_thrown[1]
            if self.turn_state in ["AIMING", "POWER", "CURL", "LUNGING"]:
                if self.current_team == 0:
                    rem_r -= 1
                else:
                    rem_y -= 1
            for i in range(max(0, rem_r)):
                pygame.draw.circle(self.canvas, HOUSE_RED, (140 + i * 18, 30), 6)
            for i in range(max(0, rem_y)):
                pygame.draw.circle(self.canvas, TEAM_YELLOW, (140 + i * 18, 80), 6)

            spacing = min(80, (BASE_WIDTH - 420) // 8)
            for e in range(1, 9):
                cx = 200 + (e * spacing)
                self.canvas.blit(self.small_font.render(str(e), True, (140, 150, 165)), (cx, 8))
                self.canvas.blit(
                    self.score_font.render(
                        (
                            str(self.score[0][e - 1])
                            if e < self.current_end or (e == self.current_end and self.turn_state == "END")
                            else "-"
                        ),
                        True,
                        WHITE,
                    ),
                    (cx, 44),
                )
                self.canvas.blit(
                    self.score_font.render(
                        (
                            str(self.score[1][e - 1])
                            if e < self.current_end or (e == self.current_end and self.turn_state == "END")
                            else "-"
                        ),
                        True,
                        WHITE,
                    ),
                    (cx, 80),
                )

            tot_x = 200 + (8 * spacing) + 80
            pygame.draw.line(self.canvas, (80, 90, 105), (tot_x - 40, 0), (tot_x - 40, 130), 2)
            self.canvas.blit(self.small_font.render("TOT", True, WHITE), (tot_x, 8))
            self.canvas.blit(self.score_font.render(str(sum(self.score[0])), True, HOUSE_RED), (tot_x, 44))
            self.canvas.blit(self.score_font.render(str(sum(self.score[1])), True, TEAM_YELLOW), (tot_x, 80))
            if getattr(self, "hammer_team", 0) == 0:
                draw_hammer_icon(self.canvas, tot_x + 65, 48, HOUSE_RED)
            elif getattr(self, "hammer_team", 0) == 1:
                draw_hammer_icon(self.canvas, tot_x + 65, 86, TEAM_YELLOW)

            if self.game_mode == "STORY":
                bob_y = math.sin(pygame.time.get_ticks() * 0.005) * 5
                is_evil = self.current_team != getattr(self, "preferred_color", 0)
                team_c = HOUSE_RED if self.current_team == 0 else TEAM_YELLOW

                if is_evil:
                    rink_idx = (
                        min(getattr(self.story, "current_rink", 0), len(STORY_RINKS) - 1) if getattr(self, "story", None) else 0
                    )
                    boss_name = STORY_RINKS[rink_idx]["boss"]
                else:
                    boss_name = "Player"

                portrait_surf = get_pixel_portrait(boss_name, (120, 120))
                self.canvas.blit(portrait_surf, (20, 140 + bob_y))

                rink_idx = min(getattr(self.story, "current_rink", 0), len(STORY_RINKS) - 1) if getattr(self, "story", None) else 0
                rink = STORY_RINKS[rink_idx]
                player_taunts = [
                    "Let's clean this up!",
                    "For the environment!",
                    "Recycle that!",
                    "Eco sweep!",
                    "Sustainable curling!",
                    "I'm carbon neutral!",
                    "Green energy shot!",
                    "Biodegradable stone!",
                    "Compost this!",
                    "Protect the wildlife!",
                    "Clear the air!",
                    "Leave no trace!",
                    "Save the redwoods!",
                    "Clean water initiative!",
                    "Renewable power!",
                    "Mother Nature sends her regards!",
                    "Reduce, reuse, curl!",
                    "Solar powered sweep!",
                    "Wind farm momentum!",
                    "Ozone layer defense!",
                    "Zero emissions throw!",
                    "Organic trajectory!",
                    "Planting trees, sinking stones!",
                    "Tidal wave of ice!",
                    "Earth friendly slide!",
                    "Geothermal precision!",
                    "Eco warrior strike!",
                    "Naturally superior!",
                    "Conserving momentum!",
                    "Habitat restored!",
                    "Clean energy victory!",
                    "Biomass acceleration!",
                    "Global cooling!",
                    "Defending the biosphere!",
                ]
                taunts = rink.get("taunts", []) if is_evil else player_taunts

                total_thrown = self.stones_thrown[0] + self.stones_thrown[1]
                if taunts:
                    taunt_text = taunts[total_thrown % len(taunts)]
                    txt = self.small_font.render(taunt_text, True, BLACK)
                    bubble_rect = pygame.Rect(140, 150 + bob_y, txt.get_width() + 20, 40)
                    draw_glass_rect(self.canvas, bubble_rect, (255, 255, 255, 216), border_radius=8, animate_sheen=False)
                    self.canvas.blit(txt, (150, 155 + bob_y))

        for p in self.particles:
            if p["type"] == "spark":
                pygame.draw.circle(
                    self.canvas,
                    lerp_color((255, 200, 50), ICE_COLOR, 1.0 - p["life"]),
                    (int(p["pos"].x), int(p["pos"].y)),
                    int(p["life"] * 4),
                )
            elif p["type"] == "trail":
                pygame.draw.circle(
                    self.canvas,
                    lerp_color(WHITE, ICE_COLOR, 1.0 - p["life"]),
                    (int(p["pos"].x), int(p["pos"].y)),
                    int(p["life"] * 6),
                )
            elif p["type"] == "sweep":
                pygame.draw.circle(
                    self.canvas,
                    lerp_color((200, 240, 255), ICE_COLOR, 1.0 - p["life"]),
                    (int(p["pos"].x), int(p["pos"].y)),
                    int(p["life"] * 5),
                )

        m_pos = self.get_pointer_pos()
        draw_glass_rect(
            self.canvas, self.btn_pause, (50, 55, 65), self.btn_pause.h // 2, self.btn_pause.collidepoint(m_pos.x, m_pos.y)
        )

        btn_text = "DISCONNECT" if self.game_mode in ("HOST", "JOIN") else "PAUSE"
        lbl_p = self.small_font.render(btn_text, True, BLACK)
        if self.game_mode in ("HOST", "JOIN"):
            total_w = 34 + 8 + lbl_p.get_width()
            start_x = self.btn_pause.centerx - total_w // 2
            # Disconnect Icon
            px, py = start_x + 17, self.btn_pause.centery
            pygame.draw.circle(self.canvas, BLACK, (px - 8, py), 4)
            pygame.draw.line(self.canvas, BLACK, (px - 8, py), (px - 2, py), 3)
            pygame.draw.circle(self.canvas, BLACK, (px + 8, py), 4)
            pygame.draw.line(self.canvas, BLACK, (px + 8, py), (px + 2, py), 3)
            pygame.draw.line(self.canvas, (255, 50, 50), (px - 4, py - 6), (px + 4, py + 6), 3)
            self.canvas.blit(lbl_p, (start_x + 42, self.btn_pause.centery - lbl_p.get_height() // 2))

            draw_glass_rect(
                self.canvas,
                self.btn_chat,
                (50, 55, 65) if not self.typing_chat else (80, 150, 80),
                self.btn_chat.h // 2,
                self.btn_chat.collidepoint(m_pos.x, m_pos.y),
            )
            lbl_chat = self.small_font.render("CHAT", True, BLACK)
            self.canvas.blit(
                lbl_chat, (self.btn_chat.centerx - lbl_chat.get_width() // 2, self.btn_chat.centery - lbl_chat.get_height() // 2)
            )
        else:
            total_w = 22 + 12 + lbl_p.get_width()
            start_x = self.btn_pause.centerx - total_w // 2
            self.draw_pause_icon(self.canvas, start_x, self.btn_pause.centery - 12)
            self.canvas.blit(lbl_p, (start_x + 34, self.btn_pause.centery - lbl_p.get_height() // 2))

        # Netcode Chat Render Support
        if self.game_mode in ["HOST", "JOIN"]:
            current_time = pygame.time.get_ticks()
            active_chat = [c for c in self.chat_messages[-5:] if current_time - c["time"] < 30000]
            max_alpha = 0
            if self.typing_chat:
                max_alpha = 255
            elif active_chat:
                for c in active_chat:
                    age = current_time - c["time"]
                    max_alpha = max(max_alpha, 255 if age < 28000 else int(255 * (1.0 - (age - 28000) / 2000.0)))

            if max_alpha > 0:
                chat_h = 40 + len(active_chat) * 40
                if self.typing_chat:
                    chat_h += 60
                chat_rect = pygame.Rect(40, BASE_HEIGHT - 250 - chat_h, 800, chat_h)

                glass_surf = UICache.get_glass(chat_rect.w, chat_rect.h, (25, 30, 40, 200), 16, False)[1].copy()
                if max_alpha < 255:
                    temp = pygame.Surface(glass_surf.get_size(), pygame.SRCALPHA)
                    temp.fill((255, 255, 255, max_alpha))
                    glass_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.canvas.blit(glass_surf, chat_rect)

                y_offset = chat_rect.y + 20
                for c in active_chat:
                    txt_surf = self.chat_font.render(c["text"], True, (255, 255, 255)).copy()
                    shd_surf = self.chat_font.render(c["text"], True, (0, 0, 0)).copy()
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

            if self.net.matched and getattr(self.net, "opponent", None):
                raw_name = self.net.opponent.split("!")[0]
                if raw_name.startswith("WC_"):
                    raw_name = raw_name[3:]
                opp_surf = self.small_font.render(f"VS: {raw_name}", True, BLACK)

                opp_c = TEAM_YELLOW if self.preferred_color == 0 else HOUSE_RED
                rock_x = 56
                rock_y = 150 + opp_surf.get_height() // 2

                rock_r = 16
                pygame.draw.circle(self.canvas, (160, 165, 170), (rock_x, rock_y), rock_r)
                pygame.draw.circle(self.canvas, (100, 105, 110), (rock_x, rock_y), rock_r, 2)
                pygame.draw.circle(self.canvas, opp_c, (rock_x, rock_y), 10)
                pygame.draw.circle(
                    self.canvas, (max(0, opp_c[0] - 50), max(0, opp_c[1] - 50), max(0, opp_c[2] - 50)), (rock_x, rock_y), 10, 2
                )
                pygame.draw.line(self.canvas, BLACK, (rock_x - 7, rock_y), (rock_x + 7, rock_y), 6)
                pygame.draw.circle(self.canvas, BLACK, (rock_x - 7, rock_y), 3)
                pygame.draw.circle(self.canvas, BLACK, (rock_x + 7, rock_y), 3)
                pygame.draw.line(self.canvas, opp_c, (rock_x - 7, rock_y), (rock_x + 7, rock_y), 4)
                pygame.draw.circle(self.canvas, opp_c, (rock_x - 7, rock_y), 2)
                pygame.draw.circle(self.canvas, opp_c, (rock_x + 7, rock_y), 2)

                self.canvas.blit(opp_surf, (rock_x + 20, 150))

        if self.turn_state == "AIMING":
            if self.active_stone and self.app_state != "PAUSED":
                pygame.draw.circle(
                    self.canvas,
                    (100, 200, 255),
                    (int(self.active_stone.pos.x), int(self.active_stone.pos.y)),
                    int(40 + ((math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5) * 15),
                    2,
                )

            draw_glass_rect(self.canvas, self.btn_curl_l, (255, 180, 180), 16, self.btn_curl_l.collidepoint(m_pos.x, m_pos.y))
            img_m = self.large_sym_font.render("-", True, HOUSE_RED)
            img_cl = self.small_font.render(" CURL L", True, BLACK)
            bx = self.btn_curl_l.centerx - (img_m.get_width() + img_cl.get_width()) // 2
            self.canvas.blit(img_m, (bx, self.btn_curl_l.centery - img_m.get_height() // 2))
            self.canvas.blit(img_cl, (bx + img_m.get_width(), self.btn_curl_l.centery - img_cl.get_height() // 2))

            draw_glass_rect(self.canvas, self.btn_curl_r, (180, 255, 180), 16, self.btn_curl_r.collidepoint(m_pos.x, m_pos.y))
            img_p = self.large_sym_font.render("+", True, (40, 160, 40))
            img_cr = self.small_font.render(" CURL R", True, BLACK)
            bx2 = self.btn_curl_r.centerx - (img_p.get_width() + img_cr.get_width()) // 2
            self.canvas.blit(img_p, (bx2, self.btn_curl_r.centery - img_p.get_height() // 2))
            self.canvas.blit(img_cr, (bx2 + img_p.get_width(), self.btn_curl_r.centery - img_cr.get_height() // 2))

            if self.is_dragging:
                vp = self.virtual_pull
                if getattr(self, "pull_history", []):
                    avg_x = sum(p.x for p in self.pull_history) / len(self.pull_history)
                    avg_y = sum(p.y for p in self.pull_history) / len(self.pull_history)
                    vp = pygame.math.Vector2(avg_x, avg_y)

                pull = pygame.math.Vector2(vp.x / 4.0, vp.y)
                if abs(pull.x) < 2.0:
                    pull.x = 0

                if pull.length() > 5:
                    max_vel = 16.0
                    if getattr(self, "game_mode", None) == "STORY":
                        max_vel += self.story.stats.get("power", 0) * 1.5
                    spos, svel = pygame.math.Vector2(self.active_stone.pos), pull.normalize() * min(max_vel, pull.length() / 14.0)
                    svel_len = svel.length()

                    curl_factor = self.selected_curl * 0.05
                    if getattr(self, "game_mode", None) == "STORY":
                        curl_factor *= 1.0 + self.story.stats.get("curl_control", 0) * 0.25

                    sx, sy, px, py = svel.x, svel.y, spos.x, spos.y
                    rad_conv = math.pi / 180.0
                    num_steps = 140
                    if getattr(self, "game_mode", None) == "STORY":
                        num_steps += self.story.stats.get("trajectory_preview", 0) * 40

                    for i in range(num_steps):
                        if svel_len <= FRICTION_BASE:
                            break
                        r = (svel_len - FRICTION_BASE) / svel_len
                        sx *= r
                        sy *= r
                        svel_len -= FRICTION_BASE
                        if svel_len > 0.4:
                            a = (1.4 / svel_len) * curl_factor * rad_conv
                            cos_a, sin_a = math.cos(a), math.sin(a)
                            sx, sy = sx * cos_a - sy * sin_a, sx * sin_a + sy * cos_a
                        px += sx
                        py += sy
                        if i % 5 == 0:
                            pygame.draw.circle(
                                self.canvas, (HOUSE_RED if self.current_team == 0 else HOUSE_BLUE), (int(px), int(py)), 6
                            )
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
            self.canvas.blit(lbl_sh, (bx + 3, by + 3))
            self.canvas.blit(lbl_fg, (bx, by))

        elif self.turn_state == "SLIDING":
            should_draw_broom = self.get_pointer_pressed()
            if should_draw_broom:
                angle = (
                    math.sin(pygame.time.get_ticks() * 0.05) * min(30, self.sweep_power * 2.0)
                    if getattr(self, "is_sweeping_now", False)
                    else 0.0
                )
                angle_int = int(round(angle / 2.0) * 2.0)
                rotated_broom = getattr(self, "broom_cache", {}).get(angle_int, self.broom_surf)
                b_rect = rotated_broom.get_rect(center=(m_pos.x, m_pos.y - 120))
                self.canvas.blit(rotated_broom, b_rect.topleft)

        elif self.turn_state == "END":
            self.canvas.blit(self.dark_overlay_200, (0, 0))

            if self.game_mode == "CHALLENGE":
                txt = "SUCCESS! ADVANCING..." if getattr(self, "challenge_success", False) else "FAILED. RETRYING..."
                if self.challenge_attempts >= 3 and not getattr(self, "challenge_success", False):
                    txt = "FAILED - SKIPPING CHALLENGE"
            else:
                txt = "END COMPLETE"

            img_txt = self.font.render(txt, True, WHITE)
            self.canvas.blit(img_txt, (BASE_WIDTH // 2 - img_txt.get_width() // 2, BASE_HEIGHT // 2 - 50))
            draw_glass_rect(
                self.canvas,
                self.btn_next_end,
                PURPLE_SUIT,
                self.btn_next_end.h // 2,
                self.btn_next_end.collidepoint(m_pos.x, m_pos.y),
            )

            btn_txt = (
                "NEXT"
                if self.game_mode == "CHALLENGE" and (getattr(self, "challenge_success", False) or self.challenge_attempts >= 3)
                else "RETRY" if self.game_mode == "CHALLENGE" else "ADVANCE MATCH"
            )
            lbl = self.small_font.render(btn_txt, True, WHITE)
            self.canvas.blit(lbl, lbl.get_rect(center=self.btn_next_end.center))

        self.draw_global_ui()

    def draw_pause_screen(self):
        if hasattr(self.canvas, "white_tex"):
            tex = self.canvas.white_tex
            tex.color = (50, 55, 60)
            tex.alpha = 180
            tex.draw(dstrect=pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT))
            tex.color = (255, 255, 255)
            tex.alpha = 255
        else:
            if not hasattr(self, "pause_grey_overlay"):
                self.pause_grey_overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA).convert_alpha()
                self.pause_grey_overlay.fill((50, 55, 60, 180))
            self.canvas.blit(self.pause_grey_overlay, (0, 0))

        # 2. Draw global UI / scoreboard so it is visible as requested
        self.draw_ui()

        self.pause_anim += (1.0 - self.pause_anim) * 0.15
        m_pos = self.get_pointer_pos()

        lbl_p = self.font_85.render("PAUSED", True, WHITE)
        self.canvas.blit(
            lbl_p, (BASE_WIDTH // 2 - lbl_p.get_width() // 2, BASE_HEIGHT // 2 - 350 + int((1.0 - self.pause_anim) * -200))
        )

        res_rect = self.btn_resume.move(-int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, res_rect, HOUSE_BLUE, res_rect.h // 2, res_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("RESUME MATCH", True, WHITE)
        self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=res_rect.center))

        opt_rect = self.btn_options_pause.move(int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, opt_rect, (50, 60, 80), opt_rect.h // 2, opt_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_opt = self.font.render("OPTIONS", True, WHITE)
        self.canvas.blit(lbl_opt, lbl_opt.get_rect(center=opt_rect.center))
        self.draw_gear_icon(self.canvas, opt_rect.x + 30, opt_rect.centery - 10)

        if self.game_mode not in ["HOST", "JOIN"]:
            sq_rect = self.btn_save_quit.move(-int((1.0 - self.pause_anim) * 400), 0)
            draw_glass_rect(self.canvas, sq_rect, PURPLE_SUIT, sq_rect.h // 2, sq_rect.collidepoint(m_pos.x, m_pos.y))
            lbl_sq = self.font.render("SAVE & QUIT", True, WHITE)
            self.canvas.blit(lbl_sq, lbl_sq.get_rect(center=sq_rect.center))
            self.draw_floppy_icon(self.canvas, sq_rect.x + 30, sq_rect.centery - 10)

        quit_rect = self.btn_quit_main.move(int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, quit_rect, HOUSE_RED, quit_rect.h // 2, quit_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_quit = self.font.render("QUIT TO MENU", True, WHITE)
        self.canvas.blit(lbl_quit, lbl_quit.get_rect(center=quit_rect.center))
        self.draw_back_icon(self.canvas, quit_rect.x + 30, quit_rect.centery - 10, color=(100, 255, 100))

        self.draw_global_ui()

    def draw_story_win(self):
        self.canvas.fill((16, 22, 34))
        cx = BASE_WIDTH // 2

        lbl_v = self.font_72.render("CONGRATULATIONS!", True, (100, 255, 100))
        self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, 200))

        lbl_sub = self.font.render("You have defeated all the corporate bosses!", True, WHITE)
        self.canvas.blit(lbl_sub, (cx - lbl_sub.get_width() // 2, 300))

        lbl_sub2 = self.font.render("The Curling Club is saved!", True, TEAM_YELLOW)
        self.canvas.blit(lbl_sub2, (cx - lbl_sub2.get_width() // 2, 350))

        if getattr(self, "frames_elapsed", 0) % 60 < 30:
            lbl_cont = self.font.render("Click anywhere to continue...", True, (200, 200, 200))
            self.canvas.blit(lbl_cont, (cx - lbl_cont.get_width() // 2, 500))

        self.draw_global_ui()

    def draw_credits(self):
        self.canvas.fill((16, 22, 34))
        cx = BASE_WIDTH // 2

        if not hasattr(self, "credits_y"):
            self.credits_y = BASE_HEIGHT
        credits_text = [
            "WINCURL",
            "",
            "A game by",
            "Jason Ivany",
            "&",
            "Antigravity (Google)",
            "",
            "Game Design & Art Direction",
            "Jason Ivany",
            "",
            "Programming & AI Engineering",
            "Antigravity",
            "",
            "Original Audio Synthesis",
            "WinCurlAudioEngine",
            "",
            "Thanks for playing!",
            "",
            "(Click anywhere to return to menu)",
        ]

        y_offset = self.credits_y
        for line in credits_text:
            if line:
                if line in ["WINCURL", "Thanks for playing!"]:
                    lbl = self.font_72.render(line, True, TEAM_YELLOW)
                elif line in ["Jason Ivany", "Antigravity (Google)", "Antigravity", "WinCurlAudioEngine"]:
                    lbl = self.font.render(line, True, (100, 255, 100))
                else:
                    lbl = self.font.render(line, True, WHITE)
                self.canvas.blit(lbl, (cx - lbl.get_width() // 2, y_offset))
            y_offset += 50

        self.credits_y -= 1.5

        if self.credits_y < -len(credits_text) * 50:
            self.credits_y = BASE_HEIGHT

        self.draw_global_ui()

    def draw_match_over_screen(self):
        self.canvas.fill((16, 22, 34))
        cx = BASE_WIDTH // 2
        if self.game_mode == "CHALLENGE":
            lbl_v = self.font_72.render("CHALLENGES COMPLETED!", True, TEAM_YELLOW)
            self.canvas.blit(lbl_v, (cx - lbl_v.get_width() // 2, 180))
        else:
            r_tot, y_tot = sum(self.score[0]), sum(self.score[1])
            if self.game_mode == "STORY":
                o_txt, o_col = (
                    ("YOU WIN!", (100, 255, 100))
                    if r_tot > y_tot
                    else ("YOU LOSE!", (255, 100, 100)) if y_tot > r_tot else ("TIE MATCH!", WHITE)
                )
            else:
                o_txt, o_col = (
                    ("RED TEAM WINS!", HOUSE_RED)
                    if r_tot > y_tot
                    else ("YELLOW TEAM WINS!", TEAM_YELLOW) if y_tot > r_tot else ("TIE MATCH!", WHITE)
                )
            if getattr(self, "winner_text", "") == "Opponent Disconnected":
                o_txt, o_col = "OPPONENT DISCONNECTED", (255, 100, 100)
            lbl_victory = self.font_72.render(o_txt, True, o_col)
            self.canvas.blit(lbl_victory, (cx - lbl_victory.get_width() // 2, 180))

            b_rect = pygame.Rect(cx - 480, 350, 960, 400)
            pygame.draw.rect(self.canvas, (28, 36, 50), b_rect, border_radius=16)
            pygame.draw.rect(self.canvas, (55, 70, 95), b_rect, 4, border_radius=16)

            self.canvas.blit(self.small_font.render("TEAM", True, (140, 160, 185)), (cx - 430, 380))
            spacing = min(75, 700 // 8)
            for e in range(1, 9):
                self.canvas.blit(self.small_font.render(f"E{e}", True, (140, 160, 185)), (cx - 320 + (e * spacing), 380))
            self.canvas.blit(self.small_font.render("TOTAL", True, WHITE), (cx + 360, 380))
            pygame.draw.line(self.canvas, (55, 70, 95), (cx - 450, 440), (cx + 450, 440), 2)

            self.canvas.blit(self.font.render("RED", True, HOUSE_RED), (cx - 430, 470))
            for e in range(1, 9):
                self.canvas.blit(self.font.render(str(self.score[0][e - 1]), True, WHITE), (cx - 320 + (e * spacing), 470))
            self.canvas.blit(self.font.render(str(r_tot), True, HOUSE_RED), (cx + 380, 470))

            self.canvas.blit(self.font.render("YLW", True, TEAM_YELLOW), (cx - 430, 570))
            for e in range(1, 9):
                self.canvas.blit(self.font.render(str(self.score[1][e - 1]), True, WHITE), (cx - 320 + (e * spacing), 570))
            self.canvas.blit(self.font.render(str(y_tot), True, TEAM_YELLOW), (cx + 380, 570))

        m_pos = self.get_pointer_pos()
        draw_glass_rect(
            self.canvas,
            self.btn_return_menu,
            HOUSE_BLUE,
            self.btn_return_menu.h // 2,
            self.btn_return_menu.collidepoint(m_pos.x, m_pos.y),
        )
        lbl_btn = self.font.render("MAIN MENU", True, WHITE)
        self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

        self.btn_leaderboard = pygame.Rect(cx - 150, 750, 300, 70)
        draw_glass_rect(
            self.canvas,
            self.btn_leaderboard,
            (50, 60, 80),
            self.btn_leaderboard.h // 2,
            self.btn_leaderboard.collidepoint(m_pos.x, m_pos.y),
        )
        lbl_lb = self.font.render("LEADERBOARD", True, WHITE)
        self.canvas.blit(lbl_lb, lbl_lb.get_rect(center=self.btn_leaderboard.center))

    def draw_leaderboard_screen(self):
        self.canvas.fill((16, 22, 34))
        cx = BASE_WIDTH // 2
        lbl = self.font_72.render("GLOBAL LEADERBOARD", True, WHITE)
        self.canvas.blit(lbl, (cx - lbl.get_width() // 2, 80))

        b_rect = pygame.Rect(cx - 400, 200, 800, 650)
        pygame.draw.rect(self.canvas, (28, 36, 50), b_rect, border_radius=16)
        pygame.draw.rect(self.canvas, (55, 70, 95), b_rect, 4, border_radius=16)

        if getattr(self, "leaderboard_data", None) is None:
            txt = self.font.render("LOADING...", True, (150, 200, 255))
            self.canvas.blit(txt, (cx - txt.get_width() // 2, 400))
        elif getattr(self, "leaderboard_data") == "ERROR":
            txt = self.font.render("FAILED TO LOAD DATA", True, (255, 100, 100))
            self.canvas.blit(txt, (cx - txt.get_width() // 2, 400))
        else:
            for i, entry in enumerate(self.leaderboard_data[:10]):
                name = entry.get("name", "Unknown")
                score = entry.get("score", 0)
                color = TEAM_YELLOW if i == 0 else WHITE if i < 3 else (180, 180, 180)
                n_lbl = self.font.render(f"{i+1}. {name}", True, color)
                s_lbl = self.font.render(str(score), True, color)
                self.canvas.blit(n_lbl, (cx - 350, 230 + i * 60))
                self.canvas.blit(s_lbl, (cx + 250, 230 + i * 60))

        m_pos = self.get_pointer_pos()
        draw_glass_rect(
            self.canvas,
            self.btn_return_menu,
            HOUSE_BLUE,
            self.btn_return_menu.h // 2,
            self.btn_return_menu.collidepoint(m_pos.x, m_pos.y),
        )
        lbl_btn = self.font.render("BACK", True, WHITE)
        self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=self.btn_return_menu.center))

    def draw_global_ui(self):
        if self.app_state not in ["MENU", "OPTIONS_MENU", "CHALLENGE_MENU"]:
            return
        m_pos = self.get_pointer_pos()
        draw_glass_rect(self.canvas, self.btn_mute, (50, 60, 80), 16, self.btn_mute.collidepoint(m_pos.x, m_pos.y))
        draw_speaker_icon(
            self.canvas,
            self.btn_mute.x + self.btn_mute.w // 2 - 20,
            self.btn_mute.y + self.btn_mute.h // 2 - 13,
            getattr(self, "is_music_muted", False),
        )
        if not IS_ANDROID:
            draw_glass_rect(self.canvas, self.btn_fs, (50, 60, 80), 16, self.btn_fs.collidepoint(m_pos.x, m_pos.y))
            fs_text = self.font.render("FULLSCREEN", True, WHITE)
            self.canvas.blit(fs_text, fs_text.get_rect(center=self.btn_fs.center))

    def render(self):
        ww, wh = self.screen.get_size()
        scale = min(ww / BASE_WIDTH, wh / BASE_HEIGHT)
        sw, sh = int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale)
        ox, oy = (ww - sw) // 2, (wh - sh) // 2

        mult = getattr(self, "time_mult", 1.0)
        decay = math.pow(0.85, mult)

        if getattr(self, "parallax_y", 0) > 0.1:
            self.parallax_y *= decay
        if self.shake_amount > 0.1:
            # Apply shake directly to parallax so UI and Ice are decoupled
            self.parallax_x = random.uniform(-self.shake_amount, self.shake_amount)
            self.parallax_y = getattr(self, "parallax_y", 0) * decay + random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_amount *= decay
        else:
            self.parallax_x = 0
            if getattr(self, "parallax_y", 0) < 0.1:
                self.parallax_y = 0

        if IS_ANDROID:
            pass
        else:
            self.screen.fill((10, 12, 16))
            if getattr(self, "border_starfield", None):
                self.border_starfield.draw(
                    self.screen, getattr(self, "last_starfield_speed", 0.5) * scale, getattr(self, "time_mult", 1.0)
                )

            if self.canvas is not self.screen and sw > 0 and sh > 0:
                self.screen.blit(pygame.transform.scale(self.canvas, (sw, sh)), (ox, oy))

        pygame.display.flip()

    async def run(self):
        self.accumulator = 0.0
        FPS = 60.0
        FIXED_DT = 1000.0 / PHYSICS_FPS
        while getattr(self, "running", True):
            if getattr(self, "dragging_slider", False) and not self.get_pointer_pressed():
                self.dragging_slider = False
                self.save_progress()

            if IS_ANDROID:
                ms_passed = self.clock.tick_busy_loop(FPS)
            elif getattr(sys, "platform", "") == "emscripten":
                ms_passed = self.clock.tick(0)
            else:
                ms_passed = self.clock.tick(FPS)

            self.time_mult = ms_passed / (1000.0 / PHYSICS_FPS)
            self.accumulator += ms_passed
            if self.accumulator > 200:
                self.accumulator = 200  # Prevent spiral of death

            for event in pygame.event.get():
                if event.type == QUIT or getattr(event, "type", None) in (
                    getattr(pygame, "APP_TERMINATING", 260),
                    getattr(pygame, "APP_WILLENTERBACKGROUND", 261),
                ):
                    if self.app_state in ["PLAY", "PAUSED"] and getattr(self, "game_mode", None) in ["STORY", "BOT"]:
                        self.save_match()
                    if event.type == QUIT:
                        self.net.close()
                        pygame.quit()
                        sys.exit()

                if event.type in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
                    if getattr(event, "simulated", False):
                        self.current_mapped_pos = event.pos
                    else:
                        self.current_mapped_pos = self.scale_mouse(event.pos)
                    if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
                        self.is_pointer_pressed = True
                    elif event.type == MOUSEBUTTONUP and getattr(event, "button", 1) == 1:
                        self.is_pointer_pressed = False

                    if event.type == MOUSEMOTION:
                        event = pygame.event.Event(
                            event.type, buttons=getattr(event, "buttons", (1, 0, 0)), pos=self.current_mapped_pos, finger_id="mouse"
                        )
                    else:
                        event = pygame.event.Event(
                            event.type, button=getattr(event, "button", 1), pos=self.current_mapped_pos, finger_id="mouse"
                        )
                        if event.type == MOUSEBUTTONDOWN:
                            mx, my = self.current_mapped_pos
                            if self.app_state in ["MENU", "OPTIONS_MENU", "CHALLENGE_MENU"]:
                                if self.btn_mute.collidepoint(mx, my):
                                    self.is_music_muted = not getattr(self, "is_music_muted", False)
                                    self.audio.play_click()
                                    self.save_progress()
                                    continue
                                if not IS_ANDROID and self.btn_fs.collidepoint(mx, my):
                                    self.audio.play_click()
                                    self.toggle_fullscreen()
                                    continue

                if event.type == VIDEORESIZE and not self.is_fullscreen and not IS_ANDROID:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                    self.border_starfield = Starfield(count=400, max_w=event.w, max_h=event.h)

                if event.type == getattr(pygame, "TEXTINPUT", 771):
                    if self.app_state == "PLAY" and self.game_mode in ["HOST", "JOIN"] and self.typing_chat:
                        if len(self.chat_input) + len(event.text) <= 30:
                            self.chat_input += event.text
                    elif self.app_state == "OPTIONS_MENU" and self.typing_target == "name":
                        if len(self.username) + len(event.text) <= 15:
                            self.username += event.text
                            self.save_progress()
                    elif self.app_state == "ROOM_PROMPT" and self.typing_target == "room":
                        if len(self.room_text) + len(event.text) <= 15:
                            self.room_text += event.text
                            self.save_progress()

                if event.type == KEYDOWN:
                    if not IS_ANDROID and getattr(event, "key", None) == K_f:
                        self.audio.play_click()
                        self.toggle_fullscreen()
                        continue
                    if self.app_state == "PLAY" and self.game_mode in ["HOST", "JOIN"]:
                        if self.typing_chat:
                            if event.key in (K_RETURN, K_KP_ENTER):
                                if self.chat_input.strip():
                                    self.net.send_action({"cmd": "chat", "msg": self.chat_input})
                                    self.chat_messages.append({"text": f"Me: {self.chat_input}", "time": pygame.time.get_ticks()})
                                self.typing_chat = False
                                self.chat_input = ""
                                try:
                                    pygame.key.stop_text_input()
                                except:
                                    pass
                            elif event.key == K_BACKSPACE:
                                self.chat_input = self.chat_input[:-1]
                            continue
                        else:
                            if event.key == K_t or event.key in (K_RETURN, K_KP_ENTER):
                                self.typing_chat = True
                                try:
                                    pygame.key.start_text_input()
                                except:
                                    pass
                                continue

                    if event.key == K_ESCAPE:
                        if self.app_state == "PLAY":
                            self.audio.play_click()
                            if self.game_mode in ["HOST", "JOIN"]:
                                self.return_to_menu()
                            else:
                                self.app_state = "PAUSED"
                                self.pause_anim = 0.0
                                self.audio.update_slide(0.0)
                                self.audio.update_sweep(0.0)
                        elif self.app_state == "PAUSED":
                            self.audio.play_click()
                            self.app_state = "PLAY"
                        elif self.app_state == "ROOM_PROMPT":
                            self.app_state = "MENU"
                            self.set_typing_target(None)
                        continue

                    if not self.typing_target and not self.typing_chat:
                        if event.key in (K_UP, K_w):
                            self.ui_nav_dir = "up"
                        elif event.key in (K_DOWN, K_s):
                            self.ui_nav_dir = "down"
                        elif event.key in (K_LEFT, K_a):
                            self.ui_nav_dir = "left"
                        elif event.key in (K_RIGHT, K_d):
                            self.ui_nav_dir = "right"
                        elif event.key in (K_RETURN, K_KP_ENTER, K_SPACE):
                            self.ui_nav_select = True

                if event.type == getattr(pygame, "JOYHATMOTION", 1538):
                    if getattr(event, "value", (0, 0))[1] > 0.5:
                        self.ui_nav_dir = "up"
                    elif getattr(event, "value", (0, 0))[1] < -0.5:
                        self.ui_nav_dir = "down"
                    elif getattr(event, "value", (0, 0))[0] < -0.5:
                        self.ui_nav_dir = "left"
                    elif getattr(event, "value", (0, 0))[0] > 0.5:
                        self.ui_nav_dir = "right"

                if event.type == getattr(pygame, "JOYAXISMOTION", 1536):
                    axis = getattr(event, "axis", 0)
                    value = getattr(event, "value", 0.0)
                    if axis == 1:
                        if value < -0.5:
                            self.ui_nav_dir = "up"
                        elif value > 0.5:
                            self.ui_nav_dir = "down"
                    elif axis == 0:
                        if self.app_state == "PLAY" and self.turn_state == "AIMING" and abs(value) > 0.1:
                            self.selected_curl = max(-1.0, min(1.0, self.selected_curl + value * 0.05))
                        elif value < -0.5:
                            self.ui_nav_dir = "left"
                        elif value > 0.5:
                            self.ui_nav_dir = "right"

                if event.type == getattr(pygame, "JOYBUTTONDOWN", 1539):
                    btn = getattr(event, "button", 0)
                    if btn == 0:
                        self.ui_nav_select = True
                    elif btn == 11:
                        self.ui_nav_dir = "up"
                    elif btn == 12:
                        self.ui_nav_dir = "down"
                    elif btn == 13:
                        self.ui_nav_dir = "left"
                    elif btn == 14:
                        self.ui_nav_dir = "right"
                    elif btn == 6 or btn == 7:
                        if self.app_state == "PLAY":
                            self.audio.play_click()
                            if self.game_mode in ["HOST", "JOIN"]:
                                self.return_to_menu()
                            else:
                                self.app_state = "PAUSED"
                                self.pause_anim = 0.0
                                self.audio.update_slide(0.0)
                                self.audio.update_sweep(0.0)
                        elif self.app_state == "PAUSED":
                            self.audio.play_click()
                            self.app_state = "PLAY"

                if getattr(self, "ui_nav_dir", None) and self.app_state != "PLAY":
                    now = pygame.time.get_ticks()
                    if now - getattr(self, "last_global_nav", 0) > 200:
                        self.last_global_nav = now
                        rects = self.get_active_ui_rects()
                        if rects:
                            curr_pos = self.current_mapped_pos
                            best_rect = None
                            best_dist = float("inf")
                            for rect in rects:
                                dx = rect.centerx - curr_pos.x
                                dy = rect.centery - curr_pos.y
                                if dx == 0 and dy == 0: continue
                                
                                valid = False
                                if self.ui_nav_dir == "up" and dy < -10: valid = True
                                elif self.ui_nav_dir == "down" and dy > 10: valid = True
                                elif self.ui_nav_dir == "left" and dx < -10: valid = True
                                elif self.ui_nav_dir == "right" and dx > 10: valid = True
                                
                                if valid:
                                    dist = dx*dx + dy*dy
                                    if dist < best_dist:
                                        best_dist = dist
                                        best_rect = rect
                            if best_rect:
                                self.current_mapped_pos = pygame.math.Vector2(best_rect.centerx, best_rect.centery)
                                pygame.event.post(pygame.event.Event(MOUSEMOTION, {"pos": self.current_mapped_pos, "rel": (0,0), "buttons": (0,0,0)}))
                                if not getattr(self, "is_web", False) and not IS_ANDROID:
                                    sw, sh = self.screen.get_size()
                                    pygame.mouse.set_pos((int(best_rect.centerx * (sw / BASE_WIDTH)), int(best_rect.centery * (sh / BASE_HEIGHT))))
                                else:
                                    # Pygbag web doesn't support mouse warping well, rely on get_pointer_pos override
                                    pass
                    self.ui_nav_dir = None

                if getattr(self, "ui_nav_select", False):
                    pygame.event.post(pygame.event.Event(MOUSEBUTTONDOWN, {"pos": self.current_mapped_pos, "button": 1, "finger_id": "mouse"}))
                    pygame.event.post(pygame.event.Event(MOUSEBUTTONUP, {"pos": self.current_mapped_pos, "button": 1, "finger_id": "mouse"}))
                    self.ui_nav_select = False

                if event.type == MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
                    m_pos = self.get_pointer_pos()

                if self.app_state == "MENU":
                    self.handle_menu_events(event)
                elif self.app_state == "ROOM_PROMPT":
                    self.handle_room_prompt_events(event)
                elif self.app_state == "CHALLENGE_MENU":
                    self.handle_challenge_menu_events(event)
                elif self.app_state == "SAVE_SLOTS":
                    self.handle_save_slots_events(event)
                elif self.app_state in ("STORY_MAP", "STORY_DIALOG"):
                    self.handle_story_map_events(event)
                elif self.app_state == "BOT_MENU":
                    self.handle_bot_menu_events(event)
                elif self.app_state == "OPTIONS_MENU":
                    self.handle_options_events(event)
                elif self.app_state == "PLAY":
                    self.handle_play_events(event)
                elif self.app_state == "PAUSED":
                    self.handle_pause_events(event)
                elif self.app_state == "MATCH_OVER":
                    self.handle_match_over_events(event)
                elif self.app_state == "STORY_WIN":
                    self.handle_story_win_events(event)
                elif self.app_state == "CREDITS":
                    self.handle_credits_events(event)
                elif self.app_state == "LEADERBOARD":
                    self.handle_leaderboard_events(event)

            if self.app_state in [
                "MENU",
                "ROOM_PROMPT",
                "CHALLENGE_MENU",
                "STORY_MAP",
                "OPTIONS_MENU",
                "MATCH_OVER",
                "SAVE_SLOTS",
                "STORY_WIN",
                "CREDITS",
            ]:
                if not getattr(self, "is_music_muted", False) and getattr(self, "frames_elapsed", 0) >= 210:
                    self.audio.play_music()
                else:
                    self.audio.stop_music()
            else:
                self.audio.stop_music()

            self.update_network()

            # Physics loop (Fixed timestep)
            while self.accumulator >= FIXED_DT:
                self.frames_elapsed += 1
                if self.app_state == "PLAY":
                    self.update_physics()
                elif self.app_state == "PAUSED" and self.game_mode in ["HOST", "JOIN"]:
                    self.update_physics()
                self.accumulator -= FIXED_DT

            if self.app_state == "MENU":
                self.audio.process_pending_sounds()
                self.draw_menu()
            elif self.app_state == "ROOM_PROMPT":
                self.draw_room_prompt()
            elif self.app_state == "CHALLENGE_MENU":
                self.draw_challenge_menu()
            elif self.app_state == "SAVE_SLOTS":
                self.draw_save_slots()
            elif self.app_state == "BOT_MENU":
                self.draw_bot_menu()
            elif self.app_state in ["STORY_MAP", "STORY_DIALOG"]:
                self.draw_story_map()
            elif self.app_state == "OPTIONS_MENU":
                self.draw_options_menu()
            elif self.app_state == "COIN_TOSS":
                if self.game_mode == "JOIN" and getattr(self, "coin_flip_result", -1) == -1:
                    pass
                else:
                    self.coin_timer -= 1
                    if self.coin_timer <= 0:
                        self.stones_thrown = {0: 0, 1: 0}
                        self.score = {0: [0] * 8, 1: [0] * 8}
                        self.current_end = 1
                        self.total_stones_played = 0
                        self.hammer_team = getattr(self, "coin_flip_result", 0)
                        self.app_state = "PLAY"
                        self.reset_end()
                self.draw_coin_toss_screen()
            elif self.app_state == "PLAY":
                self.draw_ice()
                [s.draw(self.canvas, getattr(self, "parallax_x", 0), getattr(self, "parallax_y", 0)) for s in self.stones]
                is_evil = self.game_mode == "STORY" and self.current_team != getattr(self, "preferred_color", 0)
                self.curler_anim.draw(self.canvas, HOUSE_RED if self.current_team == 0 else TEAM_YELLOW, is_evil=is_evil)
                self.draw_ui()
            elif self.app_state == "PAUSED":
                self.draw_ice()
                [s.draw(self.canvas, getattr(self, "parallax_x", 0), getattr(self, "parallax_y", 0)) for s in self.stones]
                is_evil = self.game_mode == "STORY" and self.current_team != getattr(self, "preferred_color", 0)
                self.curler_anim.draw(self.canvas, HOUSE_RED if self.current_team == 0 else TEAM_YELLOW, is_evil=is_evil)
                self.draw_pause_screen()
            elif self.app_state == "MATCH_OVER":
                self.draw_match_over_screen()
            elif self.app_state == "STORY_WIN":
                self.draw_story_win()
            elif self.app_state == "CREDITS":
                self.draw_credits()
            elif self.app_state == "LEADERBOARD":
                self.draw_leaderboard_screen()
            self.render()
            
            global ACTIVE_UI_RECTS, ACTIVE_UI_RECTS_PREV
            ACTIVE_UI_RECTS_PREV = ACTIVE_UI_RECTS.copy()
            ACTIVE_UI_RECTS.clear()
            
            if hasattr(sys, "platform") and sys.platform == "emscripten":
                await asyncio.sleep(0)


# --- DAL.NET IRC Socket Manager ---
class IRCNetworkManager:
    def __init__(self):
        self.sock = None
        self.running = False
        self.connecting = False
        self.matched = False
        self.username = ""
        self.opponent = ""
        self.channel = "#wincurl3_net"
        self.room_display = ""
        self.connection_error = ""
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()
        self.is_host = False

    def connect(self, username, is_host, room_name="", preferred_color=0):
        self.username = "WC_" + "".join(c for c in username if c.isalnum())[:10]
        if len(self.username) == 3:
            self.username += str(random.randint(100, 999))

        safe_room = "".join(c for c in room_name if c.isalnum()) or "default"
        self.channel = f"#wc3_{safe_room}"
        self.room_display = f"'{safe_room}'"

        self.preferred_color = preferred_color
        self.connection_error = ""
        self.is_host = is_host
        self.connecting = True
        self.running = True
        import sys

        if hasattr(sys, "platform") and sys.platform == "emscripten":
            self.connecting = False
            self.running = False
            self.connection_error = "Multiplayer unsupported on Web"
            return
        threading.Thread(target=self._irc_thread, daemon=True).start()

    def _irc_thread(self):
        def enc_msg(msg_dict):
            return "Z" + base64.b64encode(zlib.compress(json.dumps(msg_dict).encode("utf-8"))).decode("utf-8")

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            try:
                self.sock.connect(("irc.dal.net", 6667))
            except Exception as e:
                print("DNS/IPv6 Failed, trying IPv4 fallback:", e)
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5.0)
                self.sock.connect(("194.14.236.50", 6667))  # Dal.net fallback IP
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
                    if self.matched and self.opponent:
                        self.sock.send(f"PRIVMSG {self.opponent} :{enc_msg(msg)}\r\n".encode())

                self.sock.settimeout(0.1)
                try:
                    data = self.sock.recv(4096).decode("utf-8", errors="ignore")
                    if not data:
                        break
                    buffer += data
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        parts = line.split(" ")
                        if parts[0] == "PING":
                            self.sock.send(f"PONG {parts[1]}\r\n".encode())
                        elif len(parts) > 1 and parts[1] == "433":
                            self.username += "too"
                            self.sock.send(f"NICK {self.username}\r\n".encode())
                        elif len(parts) > 1 and parts[1] in ("001", "376", "422"):
                            self.sock.send(f"JOIN {self.channel}\r\n".encode())
                            if self.is_host:
                                self.connecting = False
                            else:
                                self.sock.send(f"PRIVMSG {self.channel} :{json.dumps({'cmd': 'hello'})}\r\n".encode())
                                self.connecting = False
                        elif len(parts) > 2 and parts[1] in ("PART", "QUIT"):
                            sender = parts[0].split("!")[0][1:]
                            if sender == getattr(self, "opponent", ""):
                                self.rx_queue.put({"cmd": "opponent_left"})
                        elif len(parts) > 3 and parts[1] == "PRIVMSG":
                            sender = parts[0].split("!")[0][1:]
                            target = parts[2]
                            msg_content = line.split(" :", 1)[1]
                            try:
                                if msg_content.startswith("Z"):
                                    raw = zlib.decompress(base64.b64decode(msg_content[1:])).decode("utf-8")
                                    msg_data = json.loads(raw)
                                else:
                                    msg_data = json.loads(msg_content)

                                if self.is_host and target == self.channel and msg_data.get("cmd") == "hello":
                                    self.opponent = sender
                                    self.matched = True
                                    self.sock.send(
                                        f"PRIVMSG {self.opponent} :{json.dumps({'cmd': 'hello_ack', 'color': getattr(self, 'preferred_color', 0)})}\r\n".encode()
                                    )
                                elif not self.is_host and not self.matched and msg_data.get("cmd") == "hello_ack":
                                    self.opponent = sender
                                    self.matched = True
                                    self.rx_queue.put({"cmd": "set_color", "color": msg_data.get("color", 0)})
                                elif sender == self.opponent:
                                    self.rx_queue.put(msg_data)
                            except:
                                pass
                except socket.timeout:
                    pass
        except Exception as e:
            self.connection_error = str(e)
            print("NETWORK ERROR:", e)
        finally:
            self.close()

    def send_action(self, data_dict):
        if self.matched:
            self.tx_queue.put(data_dict)

    def get_active_ui_rects(self):
        global ACTIVE_UI_RECTS_PREV
        return ACTIVE_UI_RECTS_PREV

    def receive_action(self):
        try:
            return self.rx_queue.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        self.running, self.matched, self.connecting = False, False, False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass


async def main():
    import os, sys, traceback

    try:
        if not hasattr(sys, "getandroidapilevel") and not (hasattr(sys, "platform") and sys.platform == "emscripten"):
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        game = WinCurl3()
        game.setup_display()
        await game.run()
    except Exception as e:
        print(f"FATAL ERROR in main: {e}")
        traceback.print_exc()
        import asyncio

        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

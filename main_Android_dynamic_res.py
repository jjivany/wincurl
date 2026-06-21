import pygame
import math
import random
import sys
import struct
import socket
import json
import queue
import threading
import os
from pygame.locals import *

# --- 4K / High-DPI Awareness ---
try:
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

print("\n" + "="*60)
print("     [SYSTEM] WINCURL 3 BUILD 12 (ANDROID OPTIMIZED)")
print("     (NOTO SANS | GRANITE 3D STONE | SPRITE UI | BOT JSON)")
print("="*60 + "\n")

# ==========================================
# 1. ANDROID RESOLUTION & SCALING SETTINGS
# ==========================================
# The internal resolution is what the CPU actually calculates.
INTERNAL_W, INTERNAL_H = 1200, 1800 
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
PURPLE_SUIT = (90, 15, 150)
PURPLE_LIGHT = (140, 40, 210)
HIGHLIGHT_COLOR = (255, 255, 255, 120)

def lerp_color(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t), int(c1[2] + (c2[2] - c1[2]) * t))

def draw_maple_leaf(surface, cx, cy, scale, color):
    points = [
        (0, -28), (7, -11), (4, -7), (14, -10), (21, -2), 
        (14, 6), (2, 8), (3, 21), (-3, 21), (-2, 8), 
        (-14, 6), (-21, -2), (-14, -10), (-4, -7), (-7, -11)
    ]
    pygame.draw.polygon(surface, color, [(cx + x * scale, cy + y * scale) for x, y in points])

def draw_hammer_icon(surface, x, y, color):
    pygame.draw.rect(surface, color, (x, y, 16, 8), border_radius=2)
    pygame.draw.rect(surface, color, (x+6, y+8, 4, 12))

def draw_glass_rect(surface, rect, base_color, border_radius=16, is_hovered=False):
    shadow = pygame.Surface((rect.w+10, rect.h+10), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 50), (5, 5, rect.w, rect.h), border_radius=border_radius)
    surface.blit(shadow, (rect.x-5, rect.y-5))
    
    btn_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    c = pygame.Color(*base_color[:3], 180)
    pygame.draw.rect(btn_surf, c, (0, 0, rect.w, rect.h), border_radius=border_radius)
    pygame.draw.rect(btn_surf, (255, 255, 255, 30), (0, 0, rect.w, rect.h//2), border_top_left_radius=border_radius, border_top_right_radius=border_radius)
    pygame.draw.ellipse(btn_surf, (255, 255, 255, 55), (rect.w*0.05, 2, rect.w*0.9, rect.h*0.45))
    pygame.draw.rect(btn_surf, (0, 0, 0, 30), (0, rect.h//2, rect.w, rect.h//2), border_bottom_left_radius=border_radius, border_bottom_right_radius=border_radius)

    if is_hovered:
        pygame.draw.rect(btn_surf, (255, 255, 255, 240), (0, 0, rect.w, rect.h), 3, border_radius=border_radius)
        pygame.draw.rect(btn_surf, (255, 255, 255, 50), (0, 0, rect.w, rect.h), 0, border_radius=border_radius) 
    else:
        pygame.draw.rect(btn_surf, (255, 255, 255, 100), (0, 0, rect.w, rect.h), 2, border_radius=border_radius)
    surface.blit(btn_surf, rect.topleft)

# ==========================================
# 2. OPTIMIZED GAME ENTITIES (PRE-RENDERED SPRITES)
# ==========================================
class Stone:
    def __init__(self, x, y, team):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.team = team
        self.radius = 32
        self.mass = 1.0
        self.is_moving = False
        self.curl = 0.0
        self.rotation = 0.0
        
        # ANDROID OPTIMIZATION: PRE-RENDER THE STONE ONCE
        # This saves thousands of CPU draw calls per second
        self.image = pygame.Surface((self.radius*2 + 10, self.radius*2 + 10), pygame.SRCALPHA)
        
        # Shadow
        pygame.draw.ellipse(self.image, (0,0,0,60), (4, 8, self.radius*2, self.radius*2-4))
        
        center = (self.radius + 2, self.radius + 2)
        color = HOUSE_RED if self.team == 0 else TEAM_YELLOW
        
        # Body and rings
        pygame.draw.circle(self.image, (160, 165, 170), center, self.radius)
        pygame.draw.circle(self.image, (100, 105, 110), center, self.radius, 3)
        pygame.draw.circle(self.image, (180, 185, 190), center, self.radius - 8)
        
        # Colored band
        pygame.draw.circle(self.image, color, center, 22)
        pygame.draw.circle(self.image, (max(0, color[0]-50), max(0, color[1]-50), max(0, color[2]-50)), center, 22, 3)
        
        self.image = self.image.convert_alpha()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def get_state(self): 
        return [round(self.pos.x, 1), round(self.pos.y, 1), round(self.vel.x, 2), round(self.vel.y, 2), self.team, round(self.curl, 2), round(self.rotation, 1), self.is_moving]
    
    def set_state(self, state): 
        self.pos.x, self.pos.y, self.vel.x, self.vel.y, self.team, self.curl, self.rotation, self.is_moving = state

    def update(self, sweep_intensity, base_friction):
        if not self.is_moving: return
        speed = self.vel.length()
        current_friction = max(0.008, base_friction - (sweep_intensity * 0.0012))
        
        if speed <= current_friction: 
            self.vel.update(0, 0)
            self.is_moving = False
        else: 
            self.vel.scale_to_length(speed - current_friction)
            if speed > 0.4: 
                self.vel.rotate_ip((1.4 / speed) * self.curl * 0.05 * (1.0 - (sweep_intensity * 0.04)))
            self.rotation += speed * (self.curl * 2.8 if abs(self.curl * 2.8) >= 0.6 else (0.6 if self.curl>=0 else -0.6))
            self.pos += self.vel
            
        # Update the rect for the fast-blit
        self.rect.centerx = int(self.pos.x)
        self.rect.centery = int(self.pos.y)

    def draw(self, surface):
        # ANDROID OPTIMIZATION: FAST BLIT
        surface.blit(self.image, self.rect)
        
        # Draw the rotating handle dynamically
        angle = math.radians(self.rotation)
        hx_s = self.pos.x - math.cos(angle)*18
        hy_s = self.pos.y - math.sin(angle)*18
        hx_e = self.pos.x + math.cos(angle)*18
        hy_e = self.pos.y + math.sin(angle)*18
        pygame.draw.line(surface, (40, 40, 45), (hx_s, hy_s), (hx_e, hy_e), 8)
        pygame.draw.circle(surface, (40, 40, 45), (int(hx_s), int(hy_s)), 6)

# ==========================================
# 3. NON-BLOCKING MULTIPLAYER (IRC)
# ==========================================
class IRCManager:
    def __init__(self, host, port, channel, is_host=False):
        self.host = host
        self.port = port
        self.channel = channel
        self.is_host = is_host
        self.sock = None
        self.running = False
        self.matched = False
        self.connecting = False
        self.opponent = None
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()
        # Keep connection on a Daemon thread so Android never freezes
        self.thread = threading.Thread(target=self._network_loop, daemon=True)

    def connect(self):
        if not self.running:
            self.running = True
            self.connecting = True
            self.thread.start()

    def _network_loop(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.host, self.port))
            
            # Send initial registration (Modify with your exact IRC handshake)
            nickname = f"WinCurl_{random.randint(1000,9999)}"
            self.sock.send(f"NICK {nickname}\r\n".encode())
            self.sock.send(f"USER {nickname} 0 * :WinCurl Player\r\n".encode())
            
            while self.running:
                # 1. Process Outgoing Commands
                while not self.tx_queue.empty():
                    data = self.tx_queue.get()
                    if self.matched and self.opponent:
                        msg = json.dumps(data)
                        self.sock.send(f"PRIVMSG {self.opponent} :{msg}\r\n".format().encode())

                # 2. Process Incoming Data
                try:
                    data = self.sock.recv(4096).decode()
                    for line in data.split("\r\n"):
                        if not line: continue
                        parts = line.split()
                        
                        if parts[0] == "PING":
                            self.sock.send(f"PONG {parts[1]}\r\n".encode())
                        elif len(parts) > 1 and parts[1] in ("376", "422"):
                            self.sock.send(f"JOIN {self.channel}\r\n".encode())
                            if self.is_host: 
                                self.connecting = False 
                            else: 
                                self.matched = True
                                self.connecting = False
                                self.tx_queue.put({"cmd": "hello"})
                        elif len(parts) > 3 and parts[1] == "PRIVMSG":
                            sender = parts[0].split("!")[0][1:]
                            msg_content = line.split(" :", 1)[1]
                            
                            if self.is_host and not self.matched and "hello" in msg_content:
                                self.opponent = sender
                                self.matched = True
                                self.tx_queue.put({"cmd": "hello_ack"})
                            elif sender == self.opponent:
                                try:
                                    self.rx_queue.put(json.loads(msg_content))
                                except:
                                    pass
                except socket.timeout:
                    pass
        except Exception:
            pass
        finally:
            self.close()

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

# ==========================================
# 4. MAIN GAME LOOP & SCALING PIPELINE
# ==========================================
def main():
    pygame.init()
    
    # 1. GRAB DEVICE RESOLUTION
    display_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    device_w, device_h = display_screen.get_size()
    
    # 2. CREATE INTERNAL CANVAS
    game_surface = pygame.Surface((INTERNAL_W, INTERNAL_H)).convert()
    
    clock = pygame.time.Clock()
    
    # Initialize your audio engine and map entities
    # audio = WinCurlAudioEngine()
    
    stones = [Stone(INTERNAL_W//2, INTERNAL_H - 100, 0)]
    
    running = True
    while running:
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # ANDROID TOUCH-SCALING FIX
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                # We intercept the raw phone touch and scale it back to the 1200x1800 canvas
                scale_x = INTERNAL_W / device_w
                scale_y = INTERNAL_H / device_h
                
                touch_x, touch_y = event.pos
                mapped_x = touch_x * scale_x
                mapped_y = touch_y * scale_y
                
                # Update the event position so your existing UI logic doesn't break
                event.pos = (mapped_x, mapped_y)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Example: Trigger throw
                    for stone in stones:
                        if not stone.is_moving:
                            stone.vel = pygame.math.Vector2(0, -15.0)
                            stone.is_moving = True

        # --- LOGIC UPDATES ---
        for stone in stones:
            stone.update(sweep_intensity=0.0, base_friction=FRICTION_BASE)
            
        # --- RENDER TO INTERNAL SURFACE ---
        game_surface.fill(ICE_COLOR)
        
        # Draw House (Your vector palette)
        pygame.draw.circle(game_surface, HOUSE_BLUE, (INTERNAL_W//2, 200), 160)
        pygame.draw.circle(game_surface, WHITE, (INTERNAL_W//2, 200), 105)
        pygame.draw.circle(game_surface, HOUSE_RED, (INTERNAL_W//2, 200), 55)
        pygame.draw.circle(game_surface, WHITE, (INTERNAL_W//2, 200), 15)
        
        # Draw Entities
        for stone in stones:
            stone.draw(game_surface)
            
        # --- THE PERFORMANCE MAGIC ---
        # Scale the 1200x1800 canvas up/down to the physical Android screen natively
        scaled_surface = pygame.transform.scale(game_surface, (device_w, device_h))
        display_screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()

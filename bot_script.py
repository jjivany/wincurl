import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import random
import time
import sys

import sys
import threading

# Import main directly
import main as wc

class BotCurl(wc.WinCurl3):
    def __init__(self, room_name):
        super().__init__()
        try: pygame.mixer.music.stop()
        except: pass
        self.setup_display()
        self.room_name = room_name
        self.app_state = "MENU"
        self.game_mode = "JOIN"
        self.net.connect("Bot", False, self.room_name, 0)
        self.bot_timer = 0
        
        self.chat_queue = []
        self.last_chat_len = 0
        def file_reader():
            import os, time
            with open("chat_out.txt", "w") as f: f.write("")
            while True:
                if os.path.exists("chat_in.txt"):
                    with open("chat_in.txt", "r") as f:
                        content = f.read().strip()
                    if content:
                        for line in content.split("\n"):
                            if line.strip(): self.chat_queue.append(line.strip())
                        open("chat_in.txt", "w").close()
                time.sleep(0.5)
        threading.Thread(target=file_reader, daemon=True).start()

    def calculate_best_shot(self):
        import math
        FRICTION_BASE = 0.022
        
        class SimStone:
            def __init__(self, p, v, c, team):
                self.pos = pygame.math.Vector2(p.x, p.y)
                self.vel = pygame.math.Vector2(v.x, v.y)
                self.curl = c
                self.team = team
                self.is_moving = (self.vel.length() > 0)
                
            def update(self):
                if not self.is_moving: return
                speed = self.vel.length()
                current_friction = max(0.008, FRICTION_BASE)
                if speed <= current_friction:
                    self.vel.update(0, 0)
                    self.is_moving = False
                else:
                    self.vel.scale_to_length(speed - current_friction)
                    if speed > 0.4:
                        self.vel.rotate_ip((1.4 / speed) * self.curl * 0.05)
                    self.pos += self.vel

        def simulate(vx, vy, curl):
            sim_stones = []
            for s in self.stones:
                if s != self.active_stone:
                    sim_stones.append(SimStone(s.pos, pygame.math.Vector2(0,0), 0, s.team))
            sim_active = SimStone(self.hack_pos, pygame.math.Vector2(vx, vy), curl, self.current_team)
            sim_stones.append(sim_active)
            
            steps = 0
            while any(s.is_moving for s in sim_stones) and steps < 3000:
                steps += 1
                for s in sim_stones: s.update()
                
                for i in range(len(sim_stones)):
                    s1 = sim_stones[i]
                    for j in range(i+1, len(sim_stones)):
                        s2 = sim_stones[j]
                        diff = s2.pos - s1.pos
                        dist = diff.length()
                        if dist < 64:
                            if dist == 0: dist = 0.001
                            overlap = 64 - dist
                            normal = diff / dist
                            s1.pos -= normal * (overlap/2)
                            s2.pos += normal * (overlap/2)
                            rel_vel = s2.vel - s1.vel
                            speed = rel_vel.dot(normal)
                            if speed < 0:
                                impulse = -(1 + 0.95) * speed / 2
                                s1.vel -= normal * impulse
                                s2.vel += normal * impulse
                                s1.is_moving = True
                                s2.is_moving = True
            
            score = 0
            for s in sim_stones:
                dist_to_button = (s.pos - self.house_pos).length()
                if dist_to_button < 160:
                    pts = (160 - dist_to_button)
                    if s.team == self.current_team:
                        score += pts
                    else:
                        score -= pts * 1.5 
                elif s.team == self.current_team and s.pos.y > self.house_pos.y + 160 and s.pos.y < self.house_pos.y + 400:
                    if abs(s.pos.x - self.house_pos.x) < 64:
                        score += 30
            return score

        best_score = -999999
        best_shot = None
        
        opponent_stones = [s for s in self.stones if s.team != self.current_team and s != self.active_stone and (s.pos - self.house_pos).length() < 200]
        targets = [(os.pos, True) for os in opponent_stones]
        targets.extend([
            (self.house_pos, False),
            (self.house_pos + pygame.math.Vector2(0, 200), False),
            (self.house_pos + pygame.math.Vector2(-40, 0), False),
            (self.house_pos + pygame.math.Vector2(40, 0), False)
        ])

        for target, is_takeout in targets:
            dist = (target - self.hack_pos).length()
            base_speeds = [math.sqrt(2 * FRICTION_BASE * (dist + 400))] if is_takeout else [math.sqrt(2 * FRICTION_BASE * dist) + 0.05]
                
            for speed in base_speeds:
                for curl in [-1.0, 0.0, 1.0]:
                    base_dir = (target - self.hack_pos).normalize()
                    base_angle = math.atan2(base_dir.y, base_dir.x)
                    for angle_offset in [-0.04, -0.02, 0.0, 0.02, 0.04]:
                        test_angle = base_angle + angle_offset + (curl * 0.015)
                        vx = math.cos(test_angle) * speed
                        vy = math.sin(test_angle) * speed
                        score = simulate(vx, vy, curl)
                        if score > best_score:
                            best_score = score
                            best_shot = (vx, vy, curl)

        if not best_shot:
            speed = math.sqrt(2 * FRICTION_BASE * (self.house_pos - self.hack_pos).length())
            dir = (self.house_pos - self.hack_pos).normalize()
            best_shot = (dir.x * speed, dir.y * speed, 0.0)
            
        import random
        fx, fy, fc = best_shot
        speed = math.hypot(fx, fy)
        angle = math.atan2(fy, fx)
        speed += random.uniform(-0.02, 0.02)
        angle += random.uniform(-0.002, 0.002)
        return math.cos(angle) * speed, math.sin(angle) * speed, fc        
    def run(self):
        while True:
            self.frames_elapsed += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.net.close()
                    pygame.quit()
                    sys.exit()
                    
            if self.chat_queue:
                msg = self.chat_queue.pop(0)
                self.net.send_action({'cmd': 'chat', 'msg': msg})
                self.chat_messages.append({'text': f"Bot: {msg}", 'time': pygame.time.get_ticks()})
                self.last_chat_len = len(self.chat_messages)
                
            self.update_network()
            
            while self.last_chat_len < len(self.chat_messages):
                c = self.chat_messages[self.last_chat_len]['text']
                if not c.startswith("Bot:"):
                    print(f"CHAT_IN: {c}", flush=True)
                    with open("chat_out.txt", "a") as f: f.write(c + "\n")
                self.last_chat_len += 1            
            if self.frames_elapsed % 60 == 0:
                print(f"Frame: {self.frames_elapsed}, Room: {self.room_name}, State: {self.app_state}, Turn: {getattr(self, 'turn_state', 'NONE')}, Team: {getattr(self, 'current_team', -1)}, Color: {getattr(self, 'preferred_color', -1)}, NetRunning: {self.net.running}, Matched: {self.net.matched}", flush=True)

            if not self.net.running and not self.net.matched and self.frames_elapsed % 300 == 0:
                print("Network disconnected or failed. Reconnecting...", flush=True)
                self.net.close()
                self.net = wc.WinCurlNet()
                self.net.connect("Bot", False, self.room_name, 0)

            if self.app_state == "MATCH_OVER":
                if self.bot_timer == 0:
                    self.bot_timer = pygame.time.get_ticks()
                elif pygame.time.get_ticks() - self.bot_timer > 5000:
                    print("Match over. Returning to menu to wait for next match.", flush=True)
                    self.net.close()
                    self.net = wc.IRCNetworkManager()
                    self.app_state = "MENU"
                    self.game_mode = "JOIN"
                    self.net.connect("Bot", False, self.room_name, 0)
                    self.bot_timer = 0

            if self.app_state == "COIN_TOSS":
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

            if self.app_state == "PLAY":
                if getattr(self, 'turn_state', 'NONE') == "AIMING" and self.current_team == getattr(self, 'preferred_color', 0):
                    if self.bot_timer == 0:
                        self.bot_timer = pygame.time.get_ticks()
                    elif pygame.time.get_ticks() - self.bot_timer > 2000:
                        vx, vy, curl = self.calculate_best_shot()
                        svel = pygame.math.Vector2(vx, vy)
                        self.selected_curl = curl
                        self.active_stone.vel = svel
                        self.active_stone.curl = self.selected_curl
                        self.active_stone.is_moving = True
                        
                        self.net.send_action({'cmd': 'shoot', 'vx': svel.x, 'vy': svel.y, 'c': self.selected_curl})
                        
                        self.stones_thrown[self.current_team] += 1
                        self.total_stones_played += 1
                        self.turn_state = "SLIDING"
                        self.curler_anim.update("LUNGING")
                        try:
                            self.audio.play_throw()
                        except:
                            pass
                        self.bot_timer = 0
                
                elif getattr(self, 'turn_state', 'NONE') == "SLIDING":
                    self.update_physics()
                elif getattr(self, 'turn_state', 'NONE') == "END":
                    if self.bot_timer == 0:
                        self.bot_timer = pygame.time.get_ticks()
                    elif pygame.time.get_ticks() - self.bot_timer > 3000:
                        self.advance_end_logic()
                        self.bot_timer = 0
            
            self.clock.tick(60)

if __name__ == "__main__":
    room_name = "WinCurl"
    if len(sys.argv) > 1:
        room_name = sys.argv[1]
    bot = BotCurl(room_name)
    bot.run()

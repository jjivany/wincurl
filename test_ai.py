import pygame
import main as wc
import math
import random

pygame.init()
game = wc.WinCurl3()
game.app_state = "PLAY"
game.house_pos = pygame.math.Vector2(540, 200)
game.hack_pos = pygame.math.Vector2(540, 2200)
game.active_stone = wc.Stone(540, 2200, 0)
game.stones = [game.active_stone]
game.current_team = 0

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
    for s in game.stones:
        if s != game.active_stone:
            sim_stones.append(SimStone(s.pos, pygame.math.Vector2(0,0), 0, s.team))
            
    sim_active = SimStone(game.hack_pos, pygame.math.Vector2(vx, vy), curl, game.current_team)
    sim_stones.append(sim_active)
    
    steps = 0
    while any(s.is_moving for s in sim_stones) and steps < 3000:
        steps += 1
        for s in sim_stones:
            s.update()
        
        # Collisions
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
        dist_to_button = (s.pos - game.house_pos).length()
        if dist_to_button < 160:
            pts = (160 - dist_to_button)
            if s.team == game.current_team:
                score += pts
            else:
                score -= pts * 1.5 
        
        elif s.team == game.current_team and s.pos.y > game.house_pos.y + 160 and s.pos.y < game.house_pos.y + 400:
            if abs(s.pos.x - game.house_pos.x) < 64:
                score += 30
                
    return score

best_score = -999999
best_shot = None

targets = []
targets.append((game.house_pos, False))
targets.append((game.house_pos + pygame.math.Vector2(0, 200), False))
targets.append((game.house_pos + pygame.math.Vector2(-40, 0), False))
targets.append((game.house_pos + pygame.math.Vector2(40, 0), False))

for target, is_takeout in targets:
    dist = (target - game.hack_pos).length()
    base_speeds = [math.sqrt(2 * FRICTION_BASE * dist) + 0.05]
        
    for speed in base_speeds:
        for curl in [-1.0, 0.0, 1.0]:
            base_dir = (target - game.hack_pos).normalize()
            base_angle = math.atan2(base_dir.y, base_dir.x)
            
            for angle_offset in [-0.04, -0.02, 0.0, 0.02, 0.04]:
                test_angle = base_angle + angle_offset + (curl * 0.015)
                vx = math.cos(test_angle) * speed
                vy = math.sin(test_angle) * speed
                
                score = simulate(vx, vy, curl)
                if score > best_score:
                    best_score = score
                    best_shot = (vx, vy, curl)

print("Best shot:", best_shot, "Score:", best_score)

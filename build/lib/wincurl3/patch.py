import re

with open("main.py", "r") as f:
    text = f.read()

# 1. Update version to 30.31
text = text.replace('__version__ = "3.0.30"', '__version__ = "3.0.31"')

# 2. Add btn_options_pause and fix positions
text = text.replace(
'''        self.btn_pause, self.btn_resume = pygame.Rect(BASE_WIDTH - 280, 140, 240, 60), pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2-100, 500, 100)
        self.btn_chat = pygame.Rect(BASE_WIDTH - 500, 140, 180, 60)
        self.btn_quit_main, self.btn_return_menu = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2+40, 500, 100), pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT-250, 500, 100)''',
'''        self.btn_pause = pygame.Rect(BASE_WIDTH - 280, 140, 240, 60)
        self.btn_resume = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2-160, 500, 100)
        self.btn_options_pause = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2-40, 500, 100)
        self.btn_chat = pygame.Rect(BASE_WIDTH - 500, 140, 180, 60)
        self.btn_quit_main = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT//2+80, 500, 100)
        self.btn_return_menu = pygame.Rect(BASE_WIDTH//2-250, BASE_HEIGHT-250, 500, 100)'''
)

# 3. Update options_buttons
text = text.replace(
'''        self.options_buttons = [
            {"id": "master_vol", "y": 480, "text": "Master Volume", "color": (150, 180, 200), "scale": 1.0},
            {"id": "name", "y": 600, "text": "Name:", "color": (130, 140, 155), "scale": 1.0},
            {"id": "color", "y": 720, "text": "My Team:", "color": HOUSE_RED, "scale": 1.0},
            {"id": "bilinear", "y": 840, "text": "Bilinear Filtering:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "fxaa", "y": 960, "text": "FXAA:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "light_filter", "y": 1080, "text": "Bilinear Filtering:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "update", "y": 1200, "text": "Check for update", "color": (150, 200, 255), "scale": 1.0},
            {"id": "back", "y": 1320, "text": "Back", "color": HOUSE_RED, "scale": 1.0}
        ]''',
'''        self.options_buttons = [
            {"id": "master_vol", "y": 480, "text": "Volume", "color": (150, 180, 200), "scale": 1.0},
            {"id": "name", "y": 600, "text": "Name:", "color": (130, 140, 155), "scale": 1.0},
            {"id": "color", "y": 720, "text": "My Team:", "color": HOUSE_RED, "scale": 1.0},
            {"id": "bilinear", "y": 840, "text": "Bilinear Filtering:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "fxaa", "y": 960, "text": "FXAA:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "light_filter", "y": 1080, "text": "Lighter ICE:", "color": TEAM_YELLOW, "scale": 1.0},
            {"id": "fullscreen", "y": 1200, "text": "Toggle Fullscreen", "color": (100, 200, 150), "scale": 1.0},
            {"id": "update", "y": 1320, "text": "Check for update", "color": (150, 200, 255), "scale": 1.0},
            {"id": "back", "y": 1440, "text": "Back", "color": HOUSE_RED, "scale": 1.0}
        ]'''
)

# 4. Remove btn_fs from __init__ (it is not needed globally)
text = text.replace(
'''        self.btn_fs = pygame.Rect(BASE_WIDTH - 280, 30, 250, 60)''',
'''        # self.btn_fs removed in favor of options menu button'''
)

# 5. prev_state logic when entering OPTIONS_MENU from MENU
text = text.replace(
'''elif b["id"] == "options": self.app_state = "OPTIONS_MENU"''',
'''elif b["id"] == "options": self.app_state = "OPTIONS_MENU"; self.prev_state = "MENU"'''
)

# 6. Pause events - handle btn_options_pause
text = text.replace(
'''    def handle_pause_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_resume.collidepoint(mx, my): self.audio.play_click(); self.app_state = "PLAY"
            elif self.btn_quit_main.collidepoint(mx, my): self.audio.play_click(); self.return_to_menu()''',
'''    def handle_pause_events(self, event):
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', 1) == 1:
            m = getattr(event, 'pos', self.get_pointer_pos()); mx, my = m[0] if isinstance(m, tuple) else m.x, m[1] if isinstance(m, tuple) else m.y
            if self.btn_resume.collidepoint(mx, my): self.audio.play_click(); self.app_state = "PLAY"
            elif self.btn_options_pause.collidepoint(mx, my): self.audio.play_click(); self.app_state = "OPTIONS_MENU"; self.prev_state = "PAUSED"
            elif self.btn_quit_main.collidepoint(mx, my): self.audio.play_click(); self.return_to_menu()'''
)

# 7. is_sweeping bug fix in update_physics
text = text.replace(
'''                if self.is_sweeping:
                    if self.sweep_power < 1.0: self.sweep_power += 0.1
                else:
                    if self.sweep_power > 0.0: self.sweep_power -= 0.02
                self.sweep_power = max(0.0, min(1.0, self.sweep_power))
                
                if self.is_sweeping and self.sweep_power > 0:
                    self.audio.update_sweep(self.sweep_power)
                    if not getattr(self, 'last_sweep_sound', False):
                        self.audio.play_sweep_start(); self.last_sweep_sound = True
                else:
                    self.audio.update_sweep(0.0)
                    if getattr(self, 'last_sweep_sound', False):
                        self.audio.play_sweep_stop(); self.last_sweep_sound = False
                        
                mouse_pos = self.get_pointer_pos()
                
                if self.is_sweeping and (not IS_ANDROID or random.random() < 0.33):''',
'''                if is_sweeping:
                    if self.sweep_power < 1.0: self.sweep_power += 0.1
                else:
                    if self.sweep_power > 0.0: self.sweep_power -= 0.02
                self.sweep_power = max(0.0, min(1.0, self.sweep_power))
                
                if is_sweeping and self.sweep_power > 0:
                    self.audio.update_sweep(self.sweep_power)
                    if not getattr(self, 'last_sweep_sound', False):
                        self.audio.play_sweep_start(); self.last_sweep_sound = True
                else:
                    self.audio.update_sweep(0.0)
                    if getattr(self, 'last_sweep_sound', False):
                        self.audio.play_sweep_stop(); self.last_sweep_sound = False
                        
                mouse_pos = self.get_pointer_pos()
                
                if is_sweeping and (not IS_ANDROID or random.random() < 0.33):'''
)

# 8. Options Menu Slider logic fix
text = text.replace(
'''                if b["id"] == "master_vol" and 300 < mx < 900 and b["y"] < menu_my < b["y"] + 110 * b["scale"]:
                    vol = max(0.0, min(1.0, (mx - (BASE_WIDTH//2 - 300*b["scale"] + 460)) / 240))
                    self.audio.set_master_volume(vol)
                    self.save_progress()
                    break''',
'''                if b["id"] == "master_vol" and 300 < mx < 900 and b["y"] < menu_my < b["y"] + 110 * b["scale"]:
                    text_str = "Volume"
                    img = self.font.render(text_str, True, (255, 255, 255))
                    txt_rect = img.get_rect(center=(BASE_WIDTH//2 - 300*b["scale"] + 160, b["y"] + 55 * b["scale"]))
                    bar_x = txt_rect.right + 30
                    vol = max(0.0, min(1.0, (mx - bar_x) / 240))
                    self.audio.set_master_volume(vol)
                    self.save_progress()
                    break'''
)

# 9. Options menu: "Master Volume" text display logic change to "Volume" and fullscreen logic
text = text.replace(
'''            elif btn["id"] == "master_vol":
                text = "Master Volume"
            elif btn["id"] == "fxaa":''',
'''            elif btn["id"] == "master_vol":
                text = "Volume"
            elif btn["id"] == "fullscreen":
                text = "Toggle Fullscreen"
            elif btn["id"] == "fxaa":'''
)

text = text.replace(
'''                        if b["id"] == "back":
                            self.app_state = "MENU"
                            self.save_progress()''',
'''                        if b["id"] == "back":
                            self.app_state = getattr(self, 'prev_state', "MENU")
                            self.save_progress()
                        elif b["id"] == "fullscreen" and not IS_ANDROID:
                            self.toggle_fullscreen()'''
)

text = text.replace(
'''                    if (IS_ANDROID and b["id"] in ["fxaa", "light_filter"]) or (not IS_ANDROID and b["id"] == "bilinear"): continue''',
'''                    if (IS_ANDROID and b["id"] in ["fxaa", "light_filter", "fullscreen"]) or (not IS_ANDROID and b["id"] == "bilinear"): continue'''
)

# 10. Pause menu rendering
text = text.replace(
'''        res_rect = self.btn_resume.move(-int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, res_rect, HOUSE_BLUE, res_rect.h // 2, res_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("RESUME MATCH", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=res_rect.center))
        
        quit_rect = self.btn_quit_main.move(int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, quit_rect, HOUSE_RED, quit_rect.h // 2, quit_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_q = self.font.render("QUIT TO MENU", True, WHITE); self.canvas.blit(lbl_q, lbl_q.get_rect(center=quit_rect.center))''',
'''        res_rect = self.btn_resume.move(-int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, res_rect, HOUSE_BLUE, res_rect.h // 2, res_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_btn = self.font.render("RESUME MATCH", True, WHITE); self.canvas.blit(lbl_btn, lbl_btn.get_rect(center=res_rect.center))
        
        opt_rect = self.btn_options_pause.move(int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, opt_rect, (50, 60, 80), opt_rect.h // 2, opt_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_opt = self.font.render("OPTIONS", True, WHITE); self.canvas.blit(lbl_opt, lbl_opt.get_rect(center=opt_rect.center))

        quit_rect = self.btn_quit_main.move(-int((1.0 - self.pause_anim) * 400), 0)
        draw_glass_rect(self.canvas, quit_rect, HOUSE_RED, quit_rect.h // 2, quit_rect.collidepoint(m_pos.x, m_pos.y))
        lbl_q = self.font.render("QUIT TO MENU", True, WHITE); self.canvas.blit(lbl_q, lbl_q.get_rect(center=quit_rect.center))'''
)


# 11. draw_global_ui should only draw in menus
# We will do this by early returning if state is not MENU, CHALLENGE, OPTIONS
text = text.replace(
'''    def draw_global_ui(self):
        m_pos = self.get_pointer_pos()
        draw_glass_rect(self.canvas, self.btn_mute, (50, 60, 80), 16, self.btn_mute.collidepoint(m_pos.x, m_pos.y))
        draw_speaker_icon(self.canvas, self.btn_mute.x + self.btn_mute.w//2 - 20, self.btn_mute.y + self.btn_mute.h//2 - 13, getattr(self, 'is_music_muted', False))
        if not IS_ANDROID:
            draw_glass_rect(self.canvas, self.btn_fs, (50, 60, 80), self.btn_fs.h // 2, self.btn_fs.collidepoint(m_pos.x, m_pos.y))
            lbl = self.small_font.render("FULLSCREEN", True, WHITE)
            self.canvas.blit(lbl, lbl.get_rect(center=self.btn_fs.center))''',
'''    def draw_global_ui(self):
        if self.app_state not in ["MENU", "OPTIONS_MENU", "CHALLENGE_MENU"]:
            return
        m_pos = self.get_pointer_pos()
        draw_glass_rect(self.canvas, self.btn_mute, (50, 60, 80), 16, self.btn_mute.collidepoint(m_pos.x, m_pos.y))
        draw_speaker_icon(self.canvas, self.btn_mute.x + self.btn_mute.w//2 - 20, self.btn_mute.y + self.btn_mute.h//2 - 13, getattr(self, 'is_music_muted', False))'''
)


# 12. event handler for btn_mute / btn_fs
text = text.replace(
'''                        if event.type == MOUSEBUTTONDOWN:
                            mx, my = self.current_mapped_pos
                            if self.btn_mute.collidepoint(mx, my):
                                self.is_music_muted = not getattr(self, 'is_music_muted', False)
                                self.audio.play_click()
                                self.save_progress()
                                continue
                            if not IS_ANDROID and self.btn_fs.collidepoint(mx, my):
                                self.toggle_fullscreen()
                                self.audio.play_click()
                                continue''',
'''                        if event.type == MOUSEBUTTONDOWN:
                            mx, my = self.current_mapped_pos
                            if self.app_state in ["MENU", "OPTIONS_MENU", "CHALLENGE_MENU"]:
                                if self.btn_mute.collidepoint(mx, my):
                                    self.is_music_muted = not getattr(self, 'is_music_muted', False)
                                    self.audio.play_click()
                                    self.save_progress()
                                    continue'''
)

with open("main.py", "w") as f:
    f.write(text)

print("Patch applied.")

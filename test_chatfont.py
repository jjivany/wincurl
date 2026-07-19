import pygame
pygame.init()

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

cf = ChatFont(31)
surf = cf.render("Me: Hello 😊🌍 World!", True, (255, 255, 255))
print(f"Surface size: {surf.get_size()}")

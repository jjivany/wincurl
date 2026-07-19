import pygame
pygame.init()
import pygame.freetype
pygame.freetype.init()

# Let's try standard pygame font first
for f in ['segoeuiemoji', 'notocoloremoji', 'applecoloremoji', 'symbola', 'dejavusans']:
    font = pygame.font.SysFont(f, 31)
    if font:
        try:
            surf = font.render("A 😊", True, (255,255,255))
            print(f"Font {f}: A size {font.render('A', True, (255,255,255)).get_size()}, Emoji size {font.render('😊', True, (255,255,255)).get_size()}")
        except Exception as e:
            print(f"Font {f} error: {e}")


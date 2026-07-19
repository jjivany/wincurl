import pygame
pygame.init()
font_names = "segoeuiemoji,notocoloremoji,applecoloremoji,symbola,dejavusans"
font = pygame.font.SysFont(font_names, 31)
print(f"Loaded font: {font}")
# Try rendering an emoji and a letter
try:
    surf = font.render("Hello 😊", True, (255,255,255))
    print(f"Surface size: {surf.get_size()}")
except Exception as e:
    print(f"Error rendering: {e}")

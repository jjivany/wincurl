import pygame
pygame.init()

font_name = "segoeuiemoji,applecoloremoji,notocoloremoji,symbola,sans"
font = pygame.font.SysFont(font_name, 31)

surf = font.render("Hello 😊", True, (255,255,255))
print(f"Original size: {surf.get_size()}")

if surf.get_height() > 50:
    scale_factor = 31 / surf.get_height()
    new_w = int(surf.get_width() * scale_factor)
    new_h = 31
    surf = pygame.transform.smoothscale(surf, (new_w, new_h))
    print(f"Scaled size: {surf.get_size()}")


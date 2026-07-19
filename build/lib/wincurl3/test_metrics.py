import pygame
pygame.init()
font = pygame.font.Font(None, 31)
print(f"Metrics for 'A': {font.metrics('A')}")
print(f"Metrics for '😊': {font.metrics('😊')}")

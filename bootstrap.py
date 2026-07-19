# bootstrap.py
import os
import sys

# Minimal flag
IS_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ

def main():
    print(f"DEBUG: IS_ANDROID is {IS_ANDROID}")
    # Minimal pygame init
    import pygame
    pygame.init()
    print("Pygame initialized successfully.")

if __name__ == "__main__":
    main()

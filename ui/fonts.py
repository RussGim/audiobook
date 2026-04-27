import pygame

_fonts = {}

def init():
    global _fonts
    _fonts = {
        "large":  pygame.font.SysFont(
            "sans", 64,  bold=True),
        "medium": pygame.font.SysFont(
            "sans", 48,  bold=True),
        "normal": pygame.font.SysFont(
            "sans", 36,  bold=False),
        "small":  pygame.font.SysFont(
            "sans", 28,  bold=False),
        "tiny":   pygame.font.SysFont(
            "sans", 22,  bold=False),
        "mono":   pygame.font.SysFont(
            "monospace", 52, bold=True),
        "nav":    pygame.font.SysFont(
            "sans", 26,  bold=True),
    }

def get(name):
    return _fonts.get(name, _fonts["normal"])

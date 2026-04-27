import pygame
from ui.colours import *
from ui import fonts
from constants import (SCREEN_BOOKS, SCREEN_PLAYER,
                       SCREEN_CHAPTERS, SCREEN_SETTINGS)

NAV_H      = 80
NAV_LABELS = ["Books", "Player", "Chapters", "Settings"]
NAV_COLS   = [BLUE, GREEN, ORANGE, GREY]

# Usable screen height — content must stay above this
CONTENT_H  = 720 - NAV_H  # = 640

class NavBar:
    def __init__(self, screen_w, screen_h):
        self.w       = screen_w
        self.h       = screen_h
        self.y       = screen_h - NAV_H
        self.btn_w   = screen_w // 4
        self.current = SCREEN_PLAYER
        self.rects   = [
            pygame.Rect(i * self.btn_w, self.y,
                        self.btn_w, NAV_H)
            for i in range(4)
        ]

    def draw(self, surface):
        # Nav background
        pygame.draw.rect(surface, (15, 15, 15),
                         (0, self.y, self.w, NAV_H))
        pygame.draw.line(surface, GREY,
                         (0, self.y),
                         (self.w, self.y), 1)

        font = fonts.get("nav")
        for i, (rect, label, col) in enumerate(
                zip(self.rects, NAV_LABELS, NAV_COLS)):
            if i == self.current:
                pygame.draw.rect(surface,
                                 (30, 30, 50), rect)
                pygame.draw.rect(
                    surface, col,
                    (rect.x, self.y, rect.w, 3))
            tcol = col if i == self.current else GREY
            txt  = font.render(label, True, tcol)
            tr   = txt.get_rect(
                center=(rect.x + rect.w // 2,
                        self.y + NAV_H // 2))
            surface.blit(txt, tr)
            if i < 3:
                pygame.draw.line(
                    surface, GREY,
                    (rect.right, self.y + 10),
                    (rect.right,
                     self.y + NAV_H - 10), 1)

        # Thin white border around content area
        pygame.draw.rect(surface, WHITE,
                         (0, 0, self.w -0,
                          self.h - 0), 2)

    def handle_touch(self, x, y):
        if y < self.y: return -1
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(x, y):
                self.current = i
                return i
        return -1

import pygame
from ui.colours import *
from ui import fonts

def draw_triangle(surface, col, points):
    pygame.draw.polygon(surface, col, points)

def draw_button_rect(surface, rect, col, border=2,
                     radius=16, border_col=WHITE):
    pygame.draw.rect(surface, col, rect,
                     border_radius=radius)
    if border:
        pygame.draw.rect(surface, border_col, rect,
                         border, border_radius=radius)

def draw_text(surface, text, font_name, col,
              cx, cy, align="center"):
    font = fonts.get(font_name)
    surf = font.render(str(text), True, col)
    r    = surf.get_rect()
    if   align == "center": r.center  = (cx, cy)
    elif align == "left":   r.midleft = (cx, cy)
    elif align == "right":  r.midright= (cx, cy)
    surface.blit(surf, r)
    return r

def draw_progress_bar(surface, x, y, w, h,
                      value, maximum,
                      col=None, bg=None, border=None):
    from ui.colours import ORANGE, DARK_GREY, GREY
    col    = col    or ORANGE
    bg     = bg     or DARK_GREY
    border = border or GREY
    pygame.draw.rect(surface, bg,
                     (x, y, w, h),
                     border_radius=h//2)
    if maximum > 0:
        fill = int((value / maximum) * w)
        fill = max(0, min(fill, w))
        if fill > 0:
            pygame.draw.rect(surface, col,
                             (x, y, fill, h),
                             border_radius=h//2)
    pygame.draw.rect(surface, border,
                     (x, y, w, h), 2,
                     border_radius=h//2)

def draw_volume_bar(surface, x, y, w, h, volume):
    from ui.colours import GREEN, WHITE
    draw_progress_bar(surface, x, y, w, h,
                      volume, 100, col=GREEN)
    draw_text(surface, f"Vol: {volume}%",
              "small", WHITE,
              x + w + 55, y + h // 2)

class ScrollList:
    def __init__(self, x, y, w, h, item_h=90):
        self.x        = x
        self.y        = y
        self.w        = w
        self.h        = h
        self.item_h   = item_h
        self.items    = []
        self.scroll   = 0
        self.selected = -1
        self._drag_start = None
        self._drag_y     = 0

    def set_items(self, items):
        self.items    = items
        self.scroll   = 0
        self.selected = -1

    def set_selected(self, idx):
        self.selected = idx
        if idx >= 0:
            item_y = idx * self.item_h - self.scroll
            if item_y < 0:
                self.scroll = idx * self.item_h
            elif item_y + self.item_h > self.h:
                self.scroll = (idx * self.item_h
                               - self.h
                               + self.item_h + 10)

    def draw(self, surface):
        from ui.colours import (BLUE, WHITE, DARK_GREY,
                                 GREY, YELLOW)
        clip = pygame.Rect(
            self.x, self.y, self.w, self.h)
        surface.set_clip(clip)
        for i, item in enumerate(self.items):
            iy = (self.y + i * self.item_h
                  - self.scroll)
            if iy + self.item_h < self.y: continue
            if iy > self.y + self.h:      break
            r = pygame.Rect(self.x + 4, iy + 4,
                            self.w - 8,
                            self.item_h - 8)
            if i == self.selected:
                pygame.draw.rect(surface, BLUE, r,
                                 border_radius=12)
                pygame.draw.rect(surface, WHITE, r,
                                 2, border_radius=12)
            else:
                pygame.draw.rect(surface, DARK_GREY,
                                 r, border_radius=12)
                pygame.draw.rect(surface, GREY, r,
                                 1, border_radius=12)
            col = WHITE if i == self.selected \
                  else YELLOW
            draw_text(surface, item, "medium", col,
                      self.x + 30,
                      iy + self.item_h // 2,
                      align="left")
        surface.set_clip(None)
        if len(self.items) * self.item_h > self.h:
            total = len(self.items) * self.item_h
            bar_h = max(40,
                int(self.h * self.h / total))
            bar_y = self.y + int(
                self.scroll / total * self.h)
            pygame.draw.rect(
                surface, GREY,
                (self.x + self.w - 8,
                 bar_y, 6, bar_h),
                border_radius=3)

    def handle_touch_down(self, x, y):
        if not (self.x <= x <= self.x + self.w and
                self.y <= y <= self.y + self.h):
            return False
        self._drag_start = y
        self._drag_y     = self.scroll
        return True

    def handle_touch_up(self, x, y, start_x, start_y):
        if not (self.x <= x <= self.x + self.w and
                self.y <= y <= self.y + self.h):
            return -1
        if abs(y - start_y) > 15:
            return -1
        iy = ((y - self.y + self.scroll)
              // self.item_h)
        if 0 <= iy < len(self.items):
            return iy
        return -1

    def handle_touch_move(self, x, y):
        if self._drag_start is None: return
        delta      = self._drag_start - y
        max_scroll = max(0,
            len(self.items) * self.item_h - self.h)
        self.scroll = max(0, min(
            self._drag_y + delta, max_scroll))

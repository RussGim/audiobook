import pygame
import time

class BaseScreen:
    def __init__(self, app):
        self.app     = app
        self.screen  = app.screen
        self.w       = app.screen.get_width()
        self.h       = app.screen.get_height()
        self.content_h = self.h - 80
        self._swipe_start_x = 0
        self._swipe_start_y = 0
        self._swipe_start_t = 0
        self._touch_down_pos = None

    def on_enter(self): pass
    def on_exit(self):  pass
    def draw(self):     pass
    def update(self):   pass

    def handle_touch_down(self, x, y):
        self._swipe_start_x  = x
        self._swipe_start_y  = y
        self._touch_down_pos = (x, y)
        self._swipe_start_t  = time.time()

    def handle_touch_up(self, x, y):
        if self._touch_down_pos is None:
            return None
        dx = x - self._swipe_start_x
        dy = y - self._swipe_start_y
        dt = time.time() - self._swipe_start_t
        if (abs(dx) > 100 and
                abs(dx) > abs(dy) * 2 and
                dt < 0.5):
            return "swipe_left" if dx < 0 \
                   else "swipe_right"
        return None

    def handle_touch_move(self, x, y): pass

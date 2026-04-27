import pygame
import os
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets

class BooksScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self.list = widgets.ScrollList(
            20, 90, 1240, 530)
        self._books        = []
        self._touch_start  = None
        self._pending_idx  = -1

    def on_enter(self):
        self._refresh()
        self._pending_idx = -1
        cur = self.app.mpd.book
        if cur and cur in self._books:
            self.list.set_selected(
                self._books.index(cur))

    def _refresh(self):
        self._books = self.app.mpd.get_books()
        display = []
        for b in self._books:
            n    = len(self.app.mpd.get_chapters(b))
            name = os.path.basename(b)
            display.append(f"{name}  ({n} chapters)")
        self.list.set_items(display)
        self._pending_idx = -1

    def _open_book(self, idx):
        from utils.speech import beep, speak_and_wait
        beep()
        book = self._books[idx]
        self.list.set_selected(idx)
        name = os.path.basename(book)
        # Stop MPD, speak, then play
        speak_and_wait(f"Playing {name}")
        self.app.mpd.play_book(book)
        self.app.state["book"]     = book
        self.app.state["chapter"]  = None
        self.app.state["position"] = 0.0
        from utils.state import save
        save(self.app.state)
        self._pending_idx = -1
        return "go_player"

    def draw(self):
        self.screen.fill(BLACK)
        widgets.draw_text(self.screen, "Select Book",
                          "large", YELLOW, 640, 28)
        pygame.draw.line(self.screen, WHITE,
                         (20, 75), (1260, 75), 1)
        self.list.draw(self.screen)

        if not self._books:
            widgets.draw_text(
                self.screen,
                "No books found — insert USB stick",
                "medium", GREY, 640, 350)

        if self._pending_idx >= 0 and \
           self.app.state.get("confirm_tap", False):
            widgets.draw_text(
                self.screen,
                "Tap again to play",
                "normal", ORANGE, 640, 600)

    def handle_touch_down(self, x, y):
        super().handle_touch_down(x, y)
        self._touch_start = (x, y)
        self.list.handle_touch_down(x, y)

    def handle_touch_up(self, x, y):
        direction = super().handle_touch_up(x, y)
        if direction: return direction

        if self._touch_start:
            sx, sy = self._touch_start
            idx = self.list.handle_touch_up(
                x, y, sx, sy)

            if 0 <= idx < len(self._books):
                confirm = self.app.state.get(
                    "confirm_tap", False)

                if not confirm:
                    return self._open_book(idx)

                if idx == self._pending_idx:
                    return self._open_book(idx)
                else:
                    from utils.speech import (beep,
                        speak_and_wait)
                    beep()
                    self._pending_idx = idx
                    self.list.set_selected(idx)
                    name = os.path.basename(
                        self._books[idx])
                    chapters = len(
                        self.app.mpd.get_chapters(
                            self._books[idx]))
                    speak_and_wait(
                        f"{name}, "
                        f"{chapters} chapters, "
                        f"press again to play",
                        stop_mpd=True)

        return None

    def handle_touch_move(self, x, y):
        self.list.handle_touch_move(x, y)
        self._pending_idx = -1

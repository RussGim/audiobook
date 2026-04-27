BaseScreenimport pygame
import os
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets

class ChaptersScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self.list = widgets.ScrollList(
            20, 90, 1240, 530)
        self._chapters    = []
        self._book        = None
        self._touch_start = None

    def on_enter(self):
        book = self.app.mpd.book
        if book != self._book:
            self._book     = book
            self._chapters = \
                self.app.mpd.get_chapters(book) \
                if book else []
            display = [c.rsplit(".", 1)[0]
                       for c in self._chapters]
            self.list.set_items(display)
        cur = self.app.mpd.title
        for i, c in enumerate(self._chapters):
            if c.rsplit(".", 1)[0] == cur:
                self.list.set_selected(i)
                break

    def draw(self):
        self.screen.fill(BLACK)
        book = os.path.basename(self._book) \
               if self._book else "No book"
        widgets.draw_text(
            self.screen,
            f"Chapters — {book}",
            "medium", YELLOW, 640, 28)
        pygame.draw.line(self.screen, WHITE,
                         (20, 75), (1260, 75), 1)
        self.list.draw(self.screen)
        if not self._chapters:
            widgets.draw_text(self.screen,
                              "No chapters found",
                              "medium", GREY,
                              640, 350)

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
            if 0 <= idx < len(self._chapters):
                chapter = self._chapters[idx]
                self.list.set_selected(idx)
                name = chapter.rsplit(".", 1)[0]
                from utils.speech import speak_and_wait
                speak_and_wait(f"Playing {name}",
                            stop_mpd=True)
                self.app.mpd.play_chapter(
                    self._book, chapter)
return "go_player"
        return None

    def handle_touch_move(self, x, y):
        self.list.handle_touch_move(x, y)

import pygame
import os
import subprocess
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets
from constants import SCREEN_PLAYER_HUGE

VISIBLE_BOOKS = 2
PAD           = 10
ARROW_W       = 180
BOOK_H        = (720 - PAD * 3) // 2
BOOK_X        = PAD
BOOK_W        = 1280 - BOOK_X - ARROW_W - PAD * 2
FONT_SIZE     = 92
CH_FONT_SIZE  = 42

class BooksHugeScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self._books             = []
        self._chapters          = {}
        self._scroll            = 0
        self._selected          = -1
        self._pending_idx       = -1
        self._touch_start       = None
        self._arrow_pressed     = None
        self._font              = None
        self._ch_font           = None
        self._last_usb_mounted  = False
        self._last_refresh_tick = 0
        self._usb_loading       = False

        ax = BOOK_X + BOOK_W + PAD * 2
        self.btn_up   = pygame.Rect(
            ax, PAD, ARROW_W, BOOK_H)
        self.btn_down = pygame.Rect(
            ax, PAD * 2 + BOOK_H, ARROW_W, BOOK_H)

    def on_enter(self):
        self._font    = pygame.font.SysFont(
            "sans", FONT_SIZE, bold=True)
        self._ch_font = pygame.font.SysFont(
            "sans", CH_FONT_SIZE)
        self._last_usb_mounted = os.path.ismount(
            "/home/pi/music/usb0")
        self._refresh()

    def _refresh(self):
        if not os.path.ismount(
                "/home/pi/music/usb0"):
            self._books       = []
            self._chapters    = {}
            self._scroll      = 0
            self._selected    = -1
            self._usb_loading = False
            return
        self._books    = self.app.mpd.get_books()
        self._chapters = {}
        for b in self._books:
            self._chapters[b] = len(
                self.app.mpd.get_chapters(b))
        self._scroll      = 0
        self._selected    = -1
        self._pending_idx = -1
        self._usb_loading = False
        cur = self.app.mpd.book
        if cur and cur in self._books:
            idx = self._books.index(cur)
            self._scroll   = idx
            self._selected = idx

    def _is_mpd_updating(self):
        try:
            r = subprocess.run(
                ["mpc", "status"],
                capture_output=True, text=True,
                timeout=2)
            return "Updating DB" in r.stdout
        except:
            return False

    def _check_usb(self):
        mounted = os.path.ismount(
            "/home/pi/music/usb0")
        if mounted != self._last_usb_mounted:
            self._last_usb_mounted = mounted
            if mounted:
                self._usb_loading = True
                self.app.mpd.update_library()
            else:
                self._usb_loading = False
                self._refresh()

    def _book_rect(self, slot):
        y = PAD + slot * (BOOK_H + PAD)
        return pygame.Rect(BOOK_X, y,
                           BOOK_W, BOOK_H)

    def _visible_books(self):
        result = []
        for slot in range(VISIBLE_BOOKS):
            idx = self._scroll + slot
            if idx < len(self._books):
                result.append((slot, idx,
                               self._books[idx]))
        return result

    def _draw_book_text(self, book, rect):
        if not self._font:
            return
        name = os.path.basename(book)
        n_ch = self._chapters.get(book, 0)

        words = name.split()
        lines = []
        line  = ""
        for word in words:
            test = (line + " " + word).strip()
            if self._font.size(test)[0] \
                    > rect.w - 40:
                if line:
                    lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)

        if len(lines) > 2:
            lines    = lines[:2]
            lines[1] = lines[1][:16] + "…"

        ch_text = f"{n_ch} chapters"
        line_h  = self._font.get_linesize()
        ch_h    = self._ch_font.get_linesize()
        total_h = len(lines) * line_h + PAD + ch_h
        start_y = rect.centery - total_h // 2

        for i, ln in enumerate(lines):
            surf = self._font.render(
                ln, True, WHITE)
            r    = surf.get_rect(
                centerx=rect.centerx,
                y=start_y + i * line_h)
            self.screen.blit(surf, r)

        ch_surf = self._ch_font.render(
            ch_text, True, CYAN)
        ch_r    = ch_surf.get_rect(
            centerx=rect.centerx,
            y=start_y + len(lines) * line_h + PAD)
        self.screen.blit(ch_surf, ch_r)

    def _redraw_now(self):
        self.draw()
        pygame.display.flip()

    def draw(self):
        self.screen.fill(BLACK)

        if self._usb_loading:
            dots = "." * (
                int(pygame.time.get_ticks()
                    / 400) % 4)
            widgets.draw_text(
                self.screen,
                f"Reading audio files{dots}",
                "large", ORANGE, 640, 300)
            widgets.draw_text(
                self.screen,
                "Please wait",
                "medium", GREY, 640, 380)
            return

        if not self._books:
            msg = "Insert USB stick" \
                  if not os.path.ismount(
                      "/home/pi/music/usb0") \
                  else "No books found"
            widgets.draw_text(
                self.screen, msg,
                "large", GREY, 640, 360)
            return

        for slot, idx, book in \
                self._visible_books():
            r        = self._book_rect(slot)
            selected = (idx == self._selected)
            pending  = (idx == self._pending_idx)

            col    = BLUE if selected \
                     else (40, 40, 80) \
                     if pending else DARK_GREY
            border = WHITE if selected \
                     else ORANGE if pending \
                     else GREY

            pygame.draw.rect(self.screen, col,
                             r, border_radius=24)
            pygame.draw.rect(self.screen, border,
                             r, 3,
                             border_radius=24)
            self._draw_book_text(book, r)

        # Up arrow
        can_up   = self._scroll > 0
        up_press = self._arrow_pressed == "up"
        up_col   = YELLOW if up_press \
                   else WHITE if can_up \
                   else DARK_GREY
        up_bg    = (80, 80, 20) if up_press \
                   else (30, 30, 50) if can_up \
                   else (20, 20, 20)
        pygame.draw.rect(
            self.screen, up_bg,
            self.btn_up, border_radius=20)
        pygame.draw.rect(
            self.screen, up_col,
            self.btn_up, 3, border_radius=20)
        cx = self.btn_up.centerx
        cy = self.btn_up.centery
        widgets.draw_triangle(
            self.screen, up_col, [
            (cx,      cy - 60),
            (cx - 60, cy + 50),
            (cx + 60, cy + 50)])

        # Down arrow
        can_down = self._scroll + VISIBLE_BOOKS \
                   < len(self._books)
        dn_press = self._arrow_pressed == "down"
        dn_col   = YELLOW if dn_press \
                   else WHITE if can_down \
                   else DARK_GREY
        dn_bg    = (80, 80, 20) if dn_press \
                   else (30, 30, 50) if can_down \
                   else (20, 20, 20)
        pygame.draw.rect(
            self.screen, dn_bg,
            self.btn_down, border_radius=20)
        pygame.draw.rect(
            self.screen, dn_col,
            self.btn_down, 3, border_radius=20)
        cx = self.btn_down.centerx
        cy = self.btn_down.centery
        widgets.draw_triangle(
            self.screen, dn_col, [
            (cx,      cy + 60),
            (cx - 60, cy - 50),
            (cx + 60, cy - 50)])

        # Counter between arrows
        mid_y = (self.btn_up.bottom +
                 self.btn_down.top) // 2
        widgets.draw_text(
            self.screen,
            f"{self._scroll + 1}–"
            f"{min(self._scroll + VISIBLE_BOOKS, len(self._books))}"
            f"/{len(self._books)}",
            "small", GREY,
            self.btn_up.centerx, mid_y)

    def handle_touch_down(self, x, y):
        self._touch_start = (x, y)

    def handle_touch_up(self, x, y):
        from utils.speech import beep
        if not self._touch_start:
            return None
        sx, sy = self._touch_start
        self._touch_start = None

        if self._usb_loading:
            return None

        if abs(y - sy) > 30 or \
           abs(x - sx) > 30:
            return None

        if self.btn_up.collidepoint(x, y):
            if self._scroll > 0:
                self._arrow_pressed = "up"
                self._redraw_now()
                beep()
                self._scroll       -= 1
                self._pending_idx   = -1
                self._arrow_pressed = None
            return None

        if self.btn_down.collidepoint(x, y):
            if self._scroll + VISIBLE_BOOKS \
                    < len(self._books):
                self._arrow_pressed = "down"
                self._redraw_now()
                beep()
                self._scroll       += 1
                self._pending_idx   = -1
                self._arrow_pressed = None
            return None

        for slot, idx, book in \
                self._visible_books():
            r = self._book_rect(slot)
            if r.collidepoint(x, y):
                self._handle_book_tap(idx, book)
                return None

        return None

    def _handle_book_tap(self, idx, book):
        from utils.speech import beep, speak_and_wait

        confirm = self.app.state.get(
            "confirm_tap", False)

        if not confirm:
            self._play_book(idx, book)
            return

        if idx == self._pending_idx:
            self._play_book(idx, book)
        else:
            self._pending_idx = idx
            self._selected    = idx
            self._redraw_now()
            self.app.mpd.pause()
            beep()
            name = os.path.basename(book)
            n_ch = self._chapters.get(book, 0)
            speak_and_wait(
                f"{name}, "
                f"{n_ch} chapters, "
                f"press again to play",
                stop_mpd=False)

    def _play_book(self, idx, book):
        from utils.speech import beep, speak_and_wait
        from utils.state import save

        self._selected    = idx
        self._pending_idx = -1
        self._redraw_now()
        self.app.mpd.pause()
        beep()
        name = os.path.basename(book)
        speak_and_wait(f"Playing {name}",
                       stop_mpd=False)

        ok = self.app.mpd.play_book(book)
        if not ok:
            speak_and_wait("Could not play",
                           stop_mpd=False)
            return

        self.app.state["book"]     = book
        self.app.state["chapter"]  = None
        self.app.state["position"] = 0.0
        save(self.app.state)
        self.app._go_to(SCREEN_PLAYER_HUGE)

    def handle_touch_move(self, x, y):
        pass

    def update(self):
        now = pygame.time.get_ticks()
        if now - self._last_refresh_tick > 2000:
            self._last_refresh_tick = now
            if self._usb_loading:
                if not self._is_mpd_updating():
                    self._usb_loading = False
                    self._refresh()
            else:
                self._check_usb()

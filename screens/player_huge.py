import pygame
import time
import os
import mpd as mpd_lib
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets
from constants import SCREEN_PLAYER_HUGE, \
                      SCREEN_BOOKS_HUGE

class PlayerHugeScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self.mpd             = app.mpd
        self._pressed        = None
        self._press_time     = 0
        self._long_fired     = False
        self._last_long      = 0
        self._drag_vol       = False
        self._drag_chapter   = False
        self._drag_track     = False
        self._current_chapter_idx = 0
        self._books_long_fired = False

        space_top = 190
        space_bot = 620
        bh        = 400
        cy        = space_top + \
                    (space_bot - space_top) // 2

        self.btn_prev = pygame.Rect(
            10,  cy - bh//2, 390, bh)
        self.btn_play = pygame.Rect(
            430, cy - bh//2, 420, bh)
        self.btn_next = pygame.Rect(
            880, cy - bh//2, 390, bh)

        sx = self.btn_prev.x
        sw = self.btn_next.right - self.btn_prev.x

        self.ch_bar  = pygame.Rect(sx,  20, sw, 70)
        self.tr_bar  = pygame.Rect(sx, 110, sw, 70)
        self.vol_bar = pygame.Rect(sx, 630, sw, 70)

        self.all_btns = [
            self.btn_prev, self.btn_play,
            self.btn_next
        ]

        self._swipe_start_x = 0
        self._swipe_start_y = 0
        self._swipe_start_t = 0

    def on_enter(self):
        pass

    def _draw_slider(self, surface, rect,
                     value, maximum, col):
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        r = h // 2
        pygame.draw.rect(surface, WHITE,
                         rect, border_radius=r)
        if maximum > 0:
            fill = int((value / maximum) * w)
            fill = max(0, min(fill, w))
            if fill > 0:
                pygame.draw.rect(
                    surface, col,
                    pygame.Rect(x, y, fill, h),
                    border_radius=r)
        pygame.draw.rect(surface, GREY,
                         rect, 2,
                         border_radius=r)
        if maximum > 0:
            thumb_x = x + int(
                (value / maximum) * w)
            thumb_x = max(x + r,
                          min(thumb_x, x + w - r))
            pygame.draw.circle(
                surface, WHITE,
                (thumb_x, y + h//2),
                h//2 + 6)
            pygame.draw.circle(
                surface, col,
                (thumb_x, y + h//2),
                h//2)

    def _draw_volume_slider(self):
        self._draw_slider(
            self.screen, self.vol_bar,
            self.mpd.volume, 100, GREEN)
        widgets.draw_text(
            self.screen, "VOL",
            "small", GREY,
            self.vol_bar.x - 36,
            self.vol_bar.centery)

    def _draw_btn_bg(self, rect, pressed):
        col = (200, 200, 200) if pressed else WHITE
        pygame.draw.rect(self.screen, col,
                         rect, border_radius=30)

    def _draw_prev(self, pressed):
        r  = self.btn_prev
        self._draw_btn_bg(r, pressed)
        cx = r.centerx
        cy = r.centery
        s  = 110
        pygame.draw.rect(self.screen, BLACK,
            (cx-s-12, cy-s+16, 22, (s-16)*2))
        widgets.draw_triangle(self.screen, BLACK, [
            (cx-s+22, cy),
            (cx+s,    cy-s+16),
            (cx+s,    cy+s-16)])

    def _draw_next(self, pressed):
        r  = self.btn_next
        self._draw_btn_bg(r, pressed)
        cx = r.centerx
        cy = r.centery
        s  = 110
        widgets.draw_triangle(self.screen, BLACK, [
            (cx+s-22, cy),
            (cx-s,    cy-s+16),
            (cx-s,    cy+s-16)])
        pygame.draw.rect(self.screen, BLACK,
            (cx+s-10, cy-s+16, 22, (s-16)*2))

    def _draw_play(self, pressed):
        r   = self.btn_play
        # Orange tint when long-press books
        # is ready
        col = (200, 200, 200) if pressed else \
              (255, 200, 100) \
              if self._books_long_fired else \
              (200, 255, 200) \
              if self.mpd.state == "play" \
              else WHITE
        pygame.draw.rect(self.screen, col,
                         r, border_radius=30)
        cx = r.centerx
        cy = r.centery
        s  = 145
        if self.mpd.state == "play":
            bw, bh = 46, s*2-28
            pygame.draw.rect(self.screen, BLACK,
                (cx-bw*2+8, cy-bh//2, bw, bh))
            pygame.draw.rect(self.screen, BLACK,
                (cx+bw-8,   cy-bh//2, bw, bh))
        else:
            widgets.draw_triangle(
                self.screen, BLACK, [
                (cx-s+28, cy-s+28),
                (cx-s+28, cy+s-28),
                (cx+s,    cy)])

    def _is_pressed(self, btn):
        return self._pressed == btn

    def _is_seeking(self, btn):
        return self._pressed == btn and \
               self._long_fired

    def draw(self):
        self.screen.fill(BLACK)
        mpd = self.mpd

        self._draw_slider(
            self.screen, self.ch_bar,
            mpd.track_num or 0,
            mpd.track_total or 1,
            (200, 100, 0))

        self._draw_slider(
            self.screen, self.tr_bar,
            mpd.elapsed,
            mpd.duration or 1,
            ORANGE)

        self._draw_prev(
            self._is_pressed(self.btn_prev))
        self._draw_play(
            self._is_pressed(self.btn_play))
        self._draw_next(
            self._is_pressed(self.btn_next))

        if self._is_seeking(self.btn_prev) or \
           self._is_seeking(self.btn_next):
            widgets.draw_text(
                self.screen, "SEEKING",
                "large", ORANGE, 640, 560)

        if self._books_long_fired:
            widgets.draw_text(
                self.screen,
                "Release for books",
                "normal", ORANGE, 640, 560)

        self._draw_volume_slider()

        widgets.draw_text(
            self.screen,
            "swipe down for menu",
            "tiny", (40, 40, 40),
            640, 708)

    def _jump_chapter(self, x):
        total = self.mpd.track_total or 1
        pct   = (x - self.ch_bar.x) / self.ch_bar.w
        idx   = int(pct * total)
        idx   = max(0, min(idx, total - 1))
        self._current_chapter_idx = idx
        try:
            c = mpd_lib.MPDClient()
            c.connect("localhost", 6600)
            c.timeout = 3
            c.play(idx)
            c.disconnect()
        except Exception as e:
            print(f"Chapter jump error: {e}")

    def _seek_track(self, x):
        dur = self.mpd.duration or 1
        pct = (x - self.tr_bar.x) / self.tr_bar.w
        pos = pct * dur
        self.mpd.seek_to(max(0, min(pos, dur)))

    def _set_vol(self, x):
        pct = (x - self.vol_bar.x) / self.vol_bar.w
        vol = int(pct * 100)
        self.mpd.set_volume(max(0, min(100, vol)))

    def handle_touch_down(self, x, y):
        self._swipe_start_x = x
        self._swipe_start_y = y
        self._swipe_start_t = time.time()
        self._drag_vol          = False
        self._drag_chapter      = False
        self._drag_track        = False
        self._books_long_fired  = False

        if self.ch_bar.collidepoint(x, y):
            self._drag_chapter = True
            self._jump_chapter(x)
            return

        if self.tr_bar.collidepoint(x, y):
            self._drag_track = True
            self._seek_track(x)
            return

        if self.vol_bar.collidepoint(x, y):
            self._drag_vol = True
            self._set_vol(x)
            return

        for btn in self.all_btns:
            if btn.collidepoint(x, y):
                self._pressed    = btn
                self._press_time = time.time()
                self._long_fired = False
                return

    def handle_touch_move(self, x, y):
        if self._drag_chapter:
            self._jump_chapter(x)
        elif self._drag_track:
            self._seek_track(x)
        elif self._drag_vol:
            self._set_vol(x)

    def handle_touch_up(self, x, y):
        from utils.speech import speak_and_wait

        if self._drag_chapter:
            from utils.speech import beep, \
                speak_and_wait
            beep()
            was_playing = self.mpd.state == "play"
            speak_and_wait(
                f"Chapter "
                f"{self._current_chapter_idx + 1}",
                stop_mpd=True)
            if was_playing:
                self.mpd.resume()

        self._drag_vol     = False
        self._drag_chapter = False
        self._drag_track   = False

        dx = x - self._swipe_start_x
        dy = y - self._swipe_start_y
        dt = time.time() - self._swipe_start_t

        if (dy > 80 and
                abs(dy) > abs(dx) * 1.5 and
                dt < 0.6):
            speak_and_wait("Player",
                           stop_mpd=True)
            self._pressed          = None
            self._long_fired       = False
            self._books_long_fired = False
            return "go_normal_player"

        btn = self._pressed
        self._pressed = None

        # Long press on play → books huge
        if btn == self.btn_play and \
                self._books_long_fired:
            self._books_long_fired = False
            self._long_fired       = False
            self.app._go_to(SCREEN_BOOKS_HUGE)
            return None

        if btn and not self._long_fired:
            self._do_short_press(btn)
        self._long_fired       = False
        self._books_long_fired = False
        return None

    def _do_short_press(self, btn):
        from utils.speech import beep, speak_and_wait
        beep()
        mpd = self.mpd
        if btn == self.btn_play:
            if mpd.state != "play":
                speak_and_wait("Playing",
                               stop_mpd=False)
                mpd.resume() if \
                    mpd.state == "pause" \
                    else mpd.play()
            else:
                mpd.pause()
                speak_and_wait("Paused",
                               stop_mpd=False)
        elif btn == self.btn_next:
            speak_and_wait(
                f"Chapter {mpd.track_num + 1}",
                stop_mpd=True)
            mpd.next_track()
        elif btn == self.btn_prev:
            speak_and_wait(
                f"Chapter "
                f"{max(1, mpd.track_num - 1)}",
                stop_mpd=True)
            mpd.prev_track()

    def update(self):
        btn = self._pressed
        if not btn: return
        held = time.time() - self._press_time

        if btn in (self.btn_prev, self.btn_next):
            if held >= 0.6:
                if not self._long_fired:
                    self._long_fired = True
                    self._last_long  = time.time()
                    self.app.speech.speak(
                        "Seeking forward"
                        if btn == self.btn_next
                        else "Seeking back",
                        pause_mpd=False)
                if time.time() - \
                        self._last_long >= 0.4:
                    self._last_long = time.time()
                    if btn == self.btn_next:
                        self.mpd.seek_forward(30)
                    else:
                        self.mpd.seek_back(30)

        elif btn == self.btn_play:
            if held >= 1.5 and \
                    not self._books_long_fired:
                self._books_long_fired = True
                self.app.speech.speak(
                    "Select book",
                    pause_mpd=False)

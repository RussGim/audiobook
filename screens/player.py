import pygame
import os
import time
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets
from constants import SCREEN_HUGE

class PlayerScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self.mpd           = app.mpd
        self._pressed      = None
        self._press_time   = 0
        self._long_fired   = False
        self._last_long    = 0
        self._dragging_vol = False

        cy = 370
        self.btn_prev = pygame.Rect(60,  cy-100, 280, 200)
        self.btn_play = pygame.Rect(500, cy-110, 280, 220)
        self.btn_next = pygame.Rect(940, cy-100, 280, 200)
        self.vol_bar  = pygame.Rect(60,  555,   1160,  40)

        self.all_btns = [
            self.btn_prev, self.btn_play, self.btn_next
        ]

    def _draw_prev(self, col, seeking=False):
        cx, cy = self.btn_prev.centerx, \
                 self.btn_prev.centery
        s, sm = 72, 40
        if seeking:
            widgets.draw_triangle(self.screen, col,
                [(cx-sm,   cy), (cx+sm, cy-sm),
                 (cx+sm,   cy+sm)])
            widgets.draw_triangle(self.screen, col,
                [(cx-sm*2, cy), (cx,    cy-sm),
                 (cx,      cy+sm)])
            widgets.draw_text(self.screen, "SEEK",
                              "small", col,
                              cx, cy+sm+18)
        else:
            pygame.draw.rect(self.screen, col,
                (cx-s-8, cy-s+12, 14, (s-12)*2))
            widgets.draw_triangle(self.screen, col, [
                (cx-s+16, cy),
                (cx+s,    cy-s+12),
                (cx+s,    cy+s-12)])
            widgets.draw_text(self.screen,
                              "hold to seek",
                              "tiny", GREY,
                              cx, cy+s+12)

    def _draw_next(self, col, seeking=False):
        cx, cy = self.btn_next.centerx, \
                 self.btn_next.centery
        s, sm = 72, 40
        if seeking:
            widgets.draw_triangle(self.screen, col,
                [(cx+sm,   cy), (cx-sm, cy-sm),
                 (cx-sm,   cy+sm)])
            widgets.draw_triangle(self.screen, col,
                [(cx+sm*2, cy), (cx,    cy-sm),
                 (cx,      cy+sm)])
            widgets.draw_text(self.screen, "SEEK",
                              "small", col,
                              cx, cy+sm+18)
        else:
            widgets.draw_triangle(self.screen, col, [
                (cx+s-16, cy),
                (cx-s,    cy-s+12),
                (cx-s,    cy+s-12)])
            pygame.draw.rect(self.screen, col,
                (cx+s-6, cy-s+12, 14, (s-12)*2))
            widgets.draw_text(self.screen,
                              "hold to seek",
                              "tiny", GREY,
                              cx, cy+s+12)

    def _draw_play(self, col):
        cx, cy = self.btn_play.centerx, \
                 self.btn_play.centery
        s = 85
        if self.mpd.state == "play":
            bw, bh = 30, s*2-16
            pygame.draw.rect(self.screen, col,
                (cx-bw*2+5, cy-bh//2, bw, bh))
            pygame.draw.rect(self.screen, col,
                (cx+bw-5,   cy-bh//2, bw, bh))
        else:
            widgets.draw_triangle(self.screen, col, [
                (cx-s+18, cy-s+18),
                (cx-s+18, cy+s-18),
                (cx+s,    cy)])

    def _draw_volume_slider(self):
        x, y, w, h = (self.vol_bar.x, self.vol_bar.y,
                      self.vol_bar.w, self.vol_bar.h)
        vol  = self.mpd.volume
        fill = int((vol / 100) * w)
        pygame.draw.rect(self.screen, DARK_GREY,
                         (x, y, w, h),
                         border_radius=h//2)
        if fill > 0:
            pygame.draw.rect(self.screen, GREEN,
                             (x, y, fill, h),
                             border_radius=h//2)
        pygame.draw.rect(self.screen, GREY,
                         (x, y, w, h), 2,
                         border_radius=h//2)
        thumb_x = x + fill
        pygame.draw.circle(self.screen, WHITE,
                           (thumb_x, y + h//2),
                           h//2 + 4)
        pygame.draw.circle(self.screen, GREEN,
                           (thumb_x, y + h//2),
                           h//2)
        widgets.draw_text(self.screen, "VOL",
                          "tiny", GREY,
                          x - 32, y + h//2)

    def _col(self, btn):
        if btn == self._pressed:
            return YELLOW_DIM
        if btn == self.btn_play:
            return GREEN if self.mpd.state == "play" \
                   else YELLOW
        return WHITE

    def _is_seeking(self, btn):
        return (self._pressed == btn and
                self._long_fired)

    def draw(self):
        self.screen.fill(BLACK)
        mpd = self.mpd

        def fmt(s):
            if s <= 0: return "--:--"
            return f"{int(s)//60:02d}:{int(s)%60:02d}"

        book = os.path.basename(mpd.book) \
               if mpd.book else "No book loaded"
        widgets.draw_text(self.screen, book,
                          "large", YELLOW, 640, 38)

        chapter = mpd.title or "---"
        if len(chapter) > 40:
            chapter = chapter[:37] + "..."
        widgets.draw_text(self.screen, chapter,
                          "medium", WHITE, 640, 100)

        tn = (f"Chapter {mpd.track_num}"
              f" of {mpd.track_total}"
              if mpd.track_num > 0 else "---")
        widgets.draw_text(self.screen, tn,
                          "normal", CYAN, 640, 158)

        widgets.draw_text(
            self.screen,
            f"{fmt(mpd.elapsed)}  /  "
            f"{fmt(mpd.duration)}",
            "mono", ORANGE, 640, 210)

        widgets.draw_progress_bar(
            self.screen, 60, 250, 1160, 42,
            mpd.elapsed, mpd.duration)

        self._draw_prev(
            self._col(self.btn_prev),
            seeking=self._is_seeking(self.btn_prev))
        self._draw_play(self._col(self.btn_play))
        self._draw_next(
            self._col(self.btn_next),
            seeking=self._is_seeking(self.btn_next))

        self._draw_volume_slider()

        widgets.draw_text(
            self.screen,
            "swipe up for large screen",
            "tiny", (40, 40, 40), 640, 635)

        if not mpd.connected:
            widgets.draw_text(
                self.screen, "MPD not connected",
                "small", RED, 640, 608)

        bt = self.app.bluetooth
        if bt.connected_name:
            widgets.draw_text(
                self.screen,
                f"BT: {bt.connected_name}",
                "small", CYAN, 1240, 18,
                align="right")

    def handle_touch_down(self, x, y):
        super().handle_touch_down(x, y)
        self._dragging_vol = False

        pb = pygame.Rect(60, 250, 1160, 42)
        if pb.collidepoint(x, y) and \
           self.mpd.duration > 0:
            pos = ((x - 60) / 1160
                   * self.mpd.duration)
            self.mpd.seek_to(pos)
            m = int(pos) // 60
            s = int(pos) % 60
            self.app.speech.speak(
                f"Seeking to {m} minutes "
                f"{s} seconds")
            return

        if self.vol_bar.collidepoint(x, y):
            vol = int((x - self.vol_bar.x) /
                      self.vol_bar.w * 100)
            self.mpd.set_volume(
                max(0, min(100, vol)))
            self._dragging_vol = True
            return

        for btn in self.all_btns:
            if btn.collidepoint(x, y):
                self._pressed    = btn
                self._press_time = time.time()
                self._long_fired = False
                return

    def handle_touch_move(self, x, y):
        if self._dragging_vol:
            vol = int((x - self.vol_bar.x) /
                      self.vol_bar.w * 100)
            self.mpd.set_volume(
                max(0, min(100, vol)))

    def handle_touch_up(self, x, y):
        self._dragging_vol = False
        direction = super().handle_touch_up(x, y)
        btn = self._pressed
        self._pressed = None

        if self._touch_down_pos:
            dx = x - self._touch_down_pos[0]
            dy = y - self._touch_down_pos[1]
            if (dy < -80 and
                    abs(dy) > abs(dx) * 1.5):
                from utils.speech import speak_and_wait
                speak_and_wait("Large screen")
                self._long_fired = False
                return SCREEN_HUGE

        if direction in ("swipe_left",
                         "swipe_right"):
            self._long_fired = False
            return direction

        if btn and not self._long_fired:
            self._do_short_press(btn)
        self._long_fired = False
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

import pygame
import os
import time
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets

BG         = (10,  10,  18)
CARD_BG    = (22,  22,  40)
CARD_BDR   = (40,  40,  62)
TITLE_COL  = (200, 184, 255)
SUB_COL    = (136, 136, 160)
CH_COL     = (106,  95, 192)
TIME_COL   = (100, 100, 128)
PROG_BG    = (30,  30,  48)
PROG_FG    = (74,  63, 160)
BTN_BIG    = (74,  63, 160)
BTN_BIG_P  = (100,  88, 210)
BTN_SM_BG  = (22,  22,  40)
BTN_SM_BDR = (42,  42,  65)
BTN_ICON   = (153, 153, 178)
VOL_FG     = (48, 192,  96)
VOL_BG     = (30,  30,  48)

class PlayerScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self.mpd           = app.mpd
        self._dragging_vol = False
        self._pressed      = None

        cy   = 400
        gap  = 28
        r_sk = 58
        r_ch = 70
        r_pl = 92

        # Total width: seek*2 + ch*2 + play + ch*2
        # + seek*2 + gaps*4
        total = (r_sk*2*2 + r_ch*2*2 +
                 r_pl*2 + gap*4)
        x0    = (1280 - total) // 2

        self.btn_seek_back = pygame.Rect(
            x0,
            cy - r_sk, r_sk*2, r_sk*2)
        self.btn_prev      = pygame.Rect(
            x0 + r_sk*2 + gap,
            cy - r_ch, r_ch*2, r_ch*2)
        self.btn_play      = pygame.Rect(
            x0 + r_sk*2 + r_ch*2 + gap*2,
            cy - r_pl, r_pl*2, r_pl*2)
        self.btn_next      = pygame.Rect(
            x0 + r_sk*2 + r_ch*2 + r_pl*2 + gap*3,
            cy - r_ch, r_ch*2, r_ch*2)
        self.btn_seek_fwd  = pygame.Rect(
            x0 + r_sk*2 + r_ch*2*2 + r_pl*2 + gap*4,
            cy - r_sk, r_sk*2, r_sk*2)

        self.vol_bar  = pygame.Rect(80, 535, 1100, 8)
        self.prog_bar = pygame.Rect(60, 265, 1160, 8)

        self.all_btns = [
            self.btn_seek_back, self.btn_prev,
            self.btn_play,
            self.btn_next, self.btn_seek_fwd]

    def _fmt(self, s):
        if s <= 0: return "--:--"
        return f"{int(s)//60:02d}:{int(s)%60:02d}"

    def _circle_btn(self, rect, bg, border,
                    pressed=False):
        cx, cy = rect.centerx, rect.centery
        r = rect.w // 2
        col = (min(bg[0]+30, 255),
               min(bg[1]+30, 255),
               min(bg[2]+30, 255)) \
              if pressed else bg
        pygame.draw.circle(self.screen, col,
                           (cx, cy), r)
        pygame.draw.circle(self.screen, border,
                           (cx, cy), r, 1)

    def _draw_seek_icon(self, rect, forward):
        cx, cy = rect.centerx, rect.centery
        col = BTN_ICON
        off = 7
        for i in range(2):
            ox = (off * i) if forward \
                 else (-off * i)
            if forward:
                pts = [(cx - 10 + ox, cy - 10),
                       (cx + 2  + ox, cy),
                       (cx - 10 + ox, cy + 10)]
            else:
                pts = [(cx + 10 + ox, cy - 10),
                       (cx - 2  + ox, cy),
                       (cx + 10 + ox, cy + 10)]
            pygame.draw.lines(self.screen, col,
                              False, pts, 2)
        f = pygame.font.SysFont("sans", 18)
        s = f.render("30s", True, (80, 80, 110))
        sr = s.get_rect(centerx=cx, top=cy + 12)
        self.screen.blit(s, sr)

    def _draw_ch_icon(self, rect, forward):
        cx, cy = rect.centerx, rect.centery
        col    = BTN_ICON
        bar_w, bar_h = 5, 26
        tri_w  = 18
        if forward:
            pygame.draw.rect(self.screen, col,
                (cx + tri_w - 4, cy - bar_h//2,
                 bar_w, bar_h), border_radius=2)
            widgets.draw_triangle(
                self.screen, col, [
                (cx - tri_w, cy - tri_w + 4),
                (cx - tri_w, cy + tri_w - 4),
                (cx + tri_w - 4, cy)])
        else:
            pygame.draw.rect(self.screen, col,
                (cx - tri_w - bar_w + 4,
                 cy - bar_h//2,
                 bar_w, bar_h), border_radius=2)
            widgets.draw_triangle(
                self.screen, col, [
                (cx + tri_w, cy - tri_w + 4),
                (cx + tri_w, cy + tri_w - 4),
                (cx - tri_w + 4, cy)])

    def _draw_play_icon(self, rect):
        cx, cy = rect.centerx, rect.centery
        if self.mpd.state == "play":
            bw, bh = 10, 36
            pygame.draw.rect(self.screen, WHITE,
                (cx - bw - 4, cy - bh//2,
                 bw, bh), border_radius=3)
            pygame.draw.rect(self.screen, WHITE,
                (cx + 4, cy - bh//2,
                 bw, bh), border_radius=3)
        else:
            widgets.draw_triangle(
                self.screen, WHITE, [
                (cx - 16, cy - 26),
                (cx - 16, cy + 26),
                (cx + 22, cy)])

    def draw(self):
        self.screen.fill(BG)
        mpd = self.mpd

        # Book title
        book = os.path.basename(mpd.book) \
               if mpd.book else "No book loaded"
        if len(book) > 45:
            book = book[:42] + "..."
        widgets.draw_text(self.screen, book,
            "large", TITLE_COL, 640, 52)

        # Chapter title
        ch = mpd.title or "---"
        if len(ch) > 48:
            ch = ch[:45] + "..."
        widgets.draw_text(self.screen, ch,
            "medium", SUB_COL, 640, 110)

        # Chapter number
        if mpd.track_num > 0:
            tn = (f"Chapter {mpd.track_num}"
                  f" of {mpd.track_total}")
        else:
            tn = "---"
        widgets.draw_text(self.screen, tn,
            "normal", CH_COL, 640, 158)

        # Time
        t_str = (f"{self._fmt(mpd.elapsed)}"
                 f"  /  "
                 f"{self._fmt(mpd.duration)}")
        widgets.draw_text(self.screen, t_str,
            "mono", TIME_COL, 640, 208)

        # Progress bar
        px = self.prog_bar.x
        py = self.prog_bar.y
        pw = self.prog_bar.w
        ph = self.prog_bar.h
        pygame.draw.rect(self.screen, PROG_BG,
            (px, py, pw, ph), border_radius=3)
        if mpd.duration > 0:
            fw = int((mpd.elapsed / mpd.duration)
                     * pw)
            fw = max(0, min(fw, pw))
            if fw > 0:
                pygame.draw.rect(self.screen,
                    PROG_FG,
                    (px, py, fw, ph),
                    border_radius=3)
            tx = px + fw
            pygame.draw.circle(self.screen, WHITE,
                (tx, py + ph//2), 14)
            pygame.draw.circle(self.screen, PROG_FG,
                (tx, py + ph//2), 10)

        # Buttons
        for btn in self.all_btns:
            pressed = (self._pressed == btn)
            if btn == self.btn_play:
                self._circle_btn(btn, BTN_BIG,
                    BTN_BIG, pressed)
                self._draw_play_icon(btn)
            elif btn in (self.btn_seek_back,
                         self.btn_seek_fwd):
                self._circle_btn(btn, BTN_SM_BG,
                    BTN_SM_BDR, pressed)
                self._draw_seek_icon(
                    btn, btn == self.btn_seek_fwd)
            else:
                self._circle_btn(btn, BTN_SM_BG,
                    BTN_SM_BDR, pressed)
                self._draw_ch_icon(
                    btn, btn == self.btn_next)

        # Button labels
        lf = pygame.font.SysFont("sans", 20)
        for btn, lbl in [
                (self.btn_seek_back, "seek"),
                (self.btn_prev,      "prev"),
                (self.btn_next,      "next"),
                (self.btn_seek_fwd,  "seek")]:
            s = lf.render(lbl, True, (60, 60, 85))
            r = s.get_rect(
                centerx=btn.centerx,
                top=btn.bottom + 6)
            self.screen.blit(s, r)

        # Volume slider
        vx = self.vol_bar.x
        vy = self.vol_bar.y
        vw = self.vol_bar.w
        vh = self.vol_bar.h
        vol   = mpd.volume
        vfill = int((vol / 100) * vw)
        pygame.draw.rect(self.screen, VOL_BG,
            (vx, vy, vw, vh), border_radius=4)
        if vfill > 0:
            pygame.draw.rect(self.screen, VOL_FG,
                (vx, vy, vfill, vh),
                border_radius=4)
        pygame.draw.circle(self.screen, WHITE,
            (vx + vfill, vy + vh//2), 14)
        pygame.draw.circle(self.screen, VOL_FG,
            (vx + vfill, vy + vh//2), 10)
        f_vol = pygame.font.SysFont("sans", 22)
        sv = f_vol.render("VOL", True,
                          (60, 60, 85))
        self.screen.blit(sv, (vx - 58, vy - 8))
        sp = f_vol.render(f"{vol}%", True,
                          (80, 80, 110))
        self.screen.blit(sp,
            (vx + vw + 12, vy - 8))

        # BT badge
        bt = self.app.bluetooth
        if bt.connected_name:
            bf = pygame.font.SysFont("sans", 20)
            bs = bf.render(
                f"BT  {bt.connected_name}",
                True, (48, 192, 96))
            bx = 1270 - bs.get_width()
            pygame.draw.rect(self.screen,
                (10, 40, 20),
                (bx - 10, 10,
                 bs.get_width() + 20, 30),
                border_radius=15)
            self.screen.blit(bs, (bx, 15))

        if not mpd.connected:
            widgets.draw_text(
                self.screen, "MPD not connected",
                "small", RED, 640, 590)

    def handle_touch_down(self, x, y):
        super().handle_touch_down(x, y)
        self._dragging_vol = False

        # Progress bar
        pb = pygame.Rect(
            self.prog_bar.x - 10,
            self.prog_bar.y - 20,
            self.prog_bar.w + 20,
            self.prog_bar.h + 40)
        if pb.collidepoint(x, y) and \
           self.mpd.duration > 0:
            pos = ((x - self.prog_bar.x) /
                   self.prog_bar.w *
                   self.mpd.duration)
            pos = max(0, min(pos,
                             self.mpd.duration))
            self.mpd.seek_to(pos)
            m = int(pos) // 60
            s = int(pos) % 60
            self.app.speech.speak(
                f"Seeking to {m} minutes "
                f"{s} seconds")
            return

        # Volume
        vb = pygame.Rect(
            self.vol_bar.x - 10,
            self.vol_bar.y - 20,
            self.vol_bar.w + 20,
            self.vol_bar.h + 40)
        if vb.collidepoint(x, y):
            vol = int((x - self.vol_bar.x) /
                      self.vol_bar.w * 100)
            self.mpd.set_volume(
                max(0, min(100, vol)))
            self._dragging_vol = True
            return

        for btn in self.all_btns:
            if btn.collidepoint(x, y):
                self._pressed = btn
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

        if direction in ("swipe_left",
                         "swipe_right"):
            return direction

        if btn:
            self._do_press(btn)
        return None

    def _do_press(self, btn):
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

        elif btn == self.btn_seek_back:
            self.app._suppress_chapter_announce \
                = True
            mpd.seek_back(30)
            speak_and_wait("Seeking back",
                           stop_mpd=False)

        elif btn == self.btn_seek_fwd:
            self.app._suppress_chapter_announce \
                = True
            mpd.seek_forward(30)
            speak_and_wait("Seeking forward",
                           stop_mpd=False)

        elif btn == self.btn_next:
            if mpd.track_num < mpd.track_total:
                self.app._suppress_chapter_announce\
                    = True
                speak_and_wait(
                    f"Chapter {mpd.track_num + 1}",
                    stop_mpd=True)
                mpd.next_track()
            else:
                speak_and_wait("End of book",
                               stop_mpd=False)

        elif btn == self.btn_prev:
            if mpd.track_num > 1:
                self.app._suppress_chapter_announce\
                    = True
                speak_and_wait(
                    f"Chapter "
                    f"{max(1, mpd.track_num - 1)}",
                    stop_mpd=True)
                mpd.prev_track()
            else:
                speak_and_wait(
                    "Returning to chapter one",
                    stop_mpd=True)
                mpd.prev_track()

    def update(self):
        pass

import pygame
import subprocess
import threading
import time
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets

STATIONS = [
    {
        "name": "BBC Radio 1",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_radio_one"
                "&bitrate=320000",
    },
    {
        "name": "BBC Radio 2",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_radio_two"
                "&bitrate=320000",
    },
    {
        "name": "BBC Radio 3",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_radio_three"
                "&bitrate=320000",
    },
    {
        "name": "BBC Radio 4",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_radio_fourfm"
                "&bitrate=320000",
    },
    {
        "name": "BBC Radio 4 Extra",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_radio_four_extra"
                "&bitrate=320000",
    },
    {
        "name": "BBC Radio 5 Live",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_radio_five_live"
                "&bitrate=320000",
    },
    {
        "name": "BBC Radio 6 Music",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_6music"
                "&bitrate=320000",
    },
    {
        "name": "BBC World Service",
        "url":  "https://lsn.lv/bbcradio.m3u8"
                "?station=bbc_world_service"
                "&bitrate=320000",
    },
]

class RadioScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self._selected    = -1
        self._status      = "Select a station"
        self._vlc_proc    = None
        self._touch_start = None
        self._stop_btn    = pygame.Rect(
            490, 570, 300, 55)
        self._build_btns()

    def _build_btns(self):
        self._btns = []
        bw, bh     = 580, 70
        xpad, ypad = 40, 8
        x0, y0     = 30, 90
        cols       = 2
        for i in range(len(STATIONS)):
            col = i % cols
            row = i // cols
            x   = x0 + col * (bw + xpad)
            y   = y0 + row * (bh + ypad)
            self._btns.append(
                pygame.Rect(x, y, bw, bh))

    def on_enter(self): pass

    def on_exit(self):
        self._stop()

    def _stop(self):
        if self._vlc_proc and \
           self._vlc_proc.poll() is None:
            self._vlc_proc.terminate()
            self._vlc_proc = None

    def _play(self, idx):
        self._stop()
        mpd = self.app.mpd
        if mpd.state == "play":
            mpd.pause()
        self._selected = idx
        self._status   = "Connecting..."
        station = STATIONS[idx]
        self.app.speech.speak(
            station["name"], resume=False)

        def _start():
            try:
                self._vlc_proc = subprocess.Popen(
                    ["cvlc", "--no-video",
                     "--aout=alsa",
                     "--alsa-audio-device="
                     "hw:Headphones,0",
                     station["url"]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
                self._status = "Playing"
            except Exception as e:
                self._status = f"Error: {e}"
                print(f"Radio error: {e}")

        threading.Thread(
            target=_start, daemon=True).start()

    def draw(self):
        self.screen.fill(BLACK)
        widgets.draw_text(
            self.screen, "BBC Radio",
            "large", YELLOW, 640, 28)
        pygame.draw.line(
            self.screen, WHITE,
            (20, 75), (1260, 75), 1)

        for i, (st, rect) in enumerate(
                zip(STATIONS, self._btns)):
            is_playing = (i == self._selected)
            col    = BLUE     if is_playing \
                     else DARK_GREY
            border = WHITE    if is_playing \
                     else GREY
            pygame.draw.rect(
                self.screen, col, rect,
                border_radius=12)
            pygame.draw.rect(
                self.screen, border, rect,
                2, border_radius=12)
            prefix = "▶  " if is_playing else "    "
            widgets.draw_text(
                self.screen,
                prefix + st["name"],
                "medium", WHITE,
                rect.x + 20, rect.centery,
                align="left")

        pygame.draw.line(
            self.screen, GREY,
            (20, 515), (1260, 515), 1)
        status_col = (
            GREEN  if self._status == "Playing"
            else ORANGE
            if self._status == "Connecting..."
            else WHITE)
        widgets.draw_text(
            self.screen, self._status,
            "normal", status_col, 640, 535)

        col = RED if self._selected >= 0 \
              else DARK_GREY
        pygame.draw.rect(
            self.screen, col,
            self._stop_btn, border_radius=12)
        pygame.draw.rect(
            self.screen, WHITE,
            self._stop_btn, 2, border_radius=12)
        widgets.draw_text(
            self.screen, "■  Stop",
            "normal", WHITE,
            self._stop_btn.centerx,
            self._stop_btn.centery)

    def handle_touch_down(self, x, y):
        super().handle_touch_down(x, y)
        self._touch_start = (x, y)

    def handle_touch_up(self, x, y):
        direction = super().handle_touch_up(x, y)
        if direction: return direction
        if not self._touch_start: return None
        sx, sy = self._touch_start
        if abs(y - sy) > 15: return None

        if self._stop_btn.collidepoint(x, y):
            self._stop()
            self._selected = -1
            self._status   = "Stopped"
            self.app.speech.speak(
                "Radio stopped", resume=False)
            return None

        for i, rect in enumerate(self._btns):
            if rect.collidepoint(x, y):
                if i == self._selected:
                    self._stop()
                    self._selected = -1
                    self._status   = "Stopped"
                    self.app.speech.speak(
                        "Stopped", resume=False)
                else:
                    self._play(i)
                return None
        return None

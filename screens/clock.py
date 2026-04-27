import pygame
import time
import math
from screens.base import BaseScreen
from ui.colours import *

# Cache fonts so we don't rebuild every frame
_time_font_cache  = {}
_date_font_cache  = {}

def _get_time_font(size):
    if size not in _time_font_cache:
        _time_font_cache[size] = \
            pygame.font.SysFont("sans", size,
                                bold=True)
    return _time_font_cache[size]

def _get_date_font(size):
    if size not in _date_font_cache:
        _date_font_cache[size] = \
            pygame.font.SysFont("sans", size,
                                bold=False)
    return _date_font_cache[size]

class ClockScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self._offset_x      = 0
        self._offset_y      = 0
        self._last_drift    = 0
        self._drift_range   = 20
        self._time_font_sz  = None
        self._date_font_sz  = None
        self._hint_font     = None
        self._layout_cached = False

    def on_enter(self):
        self._set_brightness(20)
        self._drift()
        self._layout_cached = False

    def on_exit(self):
        self._set_brightness(
            self.app.state.get("brightness", 80))

    def _set_brightness(self, val):
        try:
            bl = int(val * 255 / 100)
            with open(
                "/sys/class/backlight/"
                "rpi_backlight/brightness", "w"
            ) as f:
                f.write(str(bl))
        except:
            pass

    def _drift(self):
        t = time.time()
        self._offset_x = int(
            math.sin(t / 60) * self._drift_range)
        self._offset_y = int(
            math.cos(t / 47) *
            self._drift_range // 2)
        self._last_drift = t

    def _calc_layout(self, timestr, datestr):
        """Calculate font sizes once and cache"""
        W, H, pad = 1280, 720, 5

        # Find largest time font
        time_sz = 10
        for size in range(10, 600, 2):
            f = _get_time_font(size)
            if f.size(timestr)[0] > W - pad * 2:
                break
            time_sz = size

        # Find largest date font
        date_sz = 10
        for size in range(10, 400, 2):
            f = _get_date_font(size)
            if f.size(datestr)[0] > W - pad * 2:
                break
            date_sz = size

        # Scale down until total fits
        gap = 20
        while True:
            ft = _get_time_font(time_sz)
            fd = _get_date_font(date_sz)
            th = ft.size(timestr)[1]
            dh = fd.size(datestr)[1]
            if th + gap + dh <= H - pad * 2:
                break
            time_sz = max(10, time_sz - 2)
            date_sz = max(10, date_sz - 1)
            if time_sz <= 10 and date_sz <= 10:
                break

        self._time_font_sz = time_sz
        self._date_font_sz = date_sz
        self._layout_cached = True

    def draw(self):
        self.screen.fill(BLACK)

        if time.time() - self._last_drift > 30:
            self._drift()

        now = time.localtime()
        W, H, pad = 1280, 720, 5

        timestr = (f"{now.tm_hour:02d}:"
                   f"{now.tm_min:02d}")

        days   = ["Monday", "Tuesday", "Wednesday",
                  "Thursday", "Friday",
                  "Saturday", "Sunday"]
        months = ["January", "February", "March",
                  "April", "May", "June", "July",
                  "August", "September", "October",
                  "November", "December"]
        datestr = (f"{days[now.tm_wday]}  "
                   f"{now.tm_mday} "
                   f"{months[now.tm_mon - 1]}")

        if not self._layout_cached:
            self._calc_layout(timestr, datestr)

        ft = _get_time_font(self._time_font_sz)
        fd = _get_date_font(self._date_font_sz)
        th = ft.size(timestr)[1]
        dh = fd.size(datestr)[1]

        gap     = 20
        total_h = th + gap + dh
        cx      = W // 2 + self._offset_x
        start_y = ((H - total_h) // 2 +
                   self._offset_y)

        # Time
        ts = ft.render(timestr, True,
                       (210, 210, 210))
        tr = ts.get_rect(
            center=(cx, start_y + th // 2))
        self.screen.blit(ts, tr)

        # Date
        ds = fd.render(datestr, True,
                       (160, 160, 160))
        dr = ds.get_rect(
            center=(cx,
                    start_y + th + gap + dh // 2))
        self.screen.blit(ds, dr)

        # Tap hint — cached
        if not self._hint_font:
            self._hint_font = \
                pygame.font.SysFont(
                    "sans", 20, bold=False)
        hs = self._hint_font.render(
            "tap to wake", True, (50, 50, 50))
        hr = hs.get_rect(center=(W // 2, H - 20))
        self.screen.blit(hs, hr)

    def handle_touch_up(self, x, y):
        return "wake"

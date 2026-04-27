import pygame
import time
import threading
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets
from utils.state import save as save_state
from constants import SCREEN_RADIO

SPEEDS        = [0.75, 1.0, 1.25, 1.5, 2.0]
SLEEP_OPTIONS = [0, 15, 30, 45, 60]

# Total virtual height of settings content
CONTENT_TOP  = 80   # below header
SECTION_H    = 130  # height per section
NAV_Y        = 640  # nav bar top
VISIBLE_H    = NAV_Y - CONTENT_TOP

class SettingsScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self._bt_panel    = False
        self._bt_status   = "Checking..."
        self._bt_devices  = []
        self._bt_busy     = False
        self._touch_start = None
        self._sleep_end   = None
        self._sleep_idx   = 0
        self._scroll      = 0
        self._drag_start  = None
        self._drag_scroll = 0
        sp = app.state.get("speed", 1.0)
        self._speed_idx   = SPEEDS.index(sp) \
                            if sp in SPEEDS else 1
        self._brightness  = app.state.get(
            "brightness", 80)
        self._build_sections()

    def _build_sections(self):
        """
        Define sections with their y positions
        in virtual space (below CONTENT_TOP).
        Each section is SECTION_H tall.
        """
        # Section y values in virtual coords
        # (0 = top of scrollable area)
        self._sections = {
            "bluetooth": 0,
            "speed":     130,
            "sleep":     260,
            "brightness":390,
            "clock":     520,
            "player":    650,
            "confirm":   780,
        }
        self._total_h = 780 + SECTION_H

        # Build all button rects in virtual coords
        bw = 175
        self.btn_bt     = pygame.Rect(
            40, 30, 500, 75)
        self.btn_radio  = pygame.Rect(
            700, 30, 280, 75)
        self.speed_btns = [
            pygame.Rect(40 + i*(bw+10), 160, bw, 65)
            for i in range(len(SPEEDS))]
        sw = 185
        self.sleep_btns = [
            pygame.Rect(40 + i*(sw+8), 290, sw, 65)
            for i in range(len(SLEEP_OPTIONS))]
        self.bright_bar   = pygame.Rect(
            40, 420, 900, 44)
        self.bright_minus = pygame.Rect(
            965, 410, 80, 65)
        self.bright_plus  = pygame.Rect(
            1060, 410, 80, 65)
        self.btn_12h    = pygame.Rect(40,  550, 200, 55)
        self.btn_24h    = pygame.Rect(260, 550, 200, 55)
        self.btn_normal = pygame.Rect(40,  680, 200, 55)
        self.btn_large  = pygame.Rect(260, 680, 200, 55)
        self.btn_confirm_on  = pygame.Rect(
            40, 810, 200, 55)
        self.btn_confirm_off = pygame.Rect(
            260, 810, 200, 55)

    def on_enter(self):
        self._update_bt_status()

    def _update_bt_status(self):
        def _check():
            connected = \
                self.app.bluetooth.get_status()
            self._bt_status = (
                f"Connected: "
                f"{self.app.bluetooth.connected_name}"
                if connected
                else "Not connected")
        threading.Thread(
            target=_check, daemon=True).start()

    def _vy(self, virtual_y):
        """Convert virtual y to screen y"""
        return CONTENT_TOP + virtual_y - self._scroll

    def _line(self, vy):
        sy = self._vy(vy)
        if CONTENT_TOP <= sy <= NAV_Y:
            pygame.draw.line(
                self.screen, GREY,
                (20, sy), (1240, sy), 1)

    def _label(self, text, vy):
        sy = self._vy(vy)
        if CONTENT_TOP - 40 <= sy <= NAV_Y:
            widgets.draw_text(
                self.screen, text,
                "normal", CYAN, 40, sy,
                align="left")

    def _btn_rect(self, rect):
        """Convert virtual rect to screen rect"""
        return pygame.Rect(
            rect.x,
            self._vy(rect.y),
            rect.w, rect.h)

    def _draw_btn(self, rect, col,
                  text, text_col=WHITE,
                  font="normal"):
        sr = self._btn_rect(rect)
        if sr.bottom < CONTENT_TOP or \
           sr.top > NAV_Y:
            return
        widgets.draw_button_rect(
            self.screen, sr, col)
        widgets.draw_text(
            self.screen, text, font,
            text_col, sr.centerx, sr.centery)

    def draw(self):
        
        self.screen.fill(DARK_BLUE)

        # Clip to content area
        clip = pygame.Rect(
            0, CONTENT_TOP,
            1280, VISIBLE_H)
        self.screen.set_clip(clip)

        # Bluetooth section
        self._line(0)
        self._label("Bluetooth", 15)
        sr = self._btn_rect(self.btn_bt)
        if CONTENT_TOP <= sr.bottom and \
           sr.top <= NAV_Y:
            bt_col = GREEN if "Connected" in \
                     self._bt_status else GREY
            widgets.draw_button_rect(
                self.screen, sr, DARK_GREY)
            widgets.draw_text(
                self.screen, self._bt_status,
                "small", bt_col,
                sr.centerx, sr.centery)
        sr2 = self._btn_rect(self.btn_radio)
        if CONTENT_TOP <= sr2.bottom and \
           sr2.top <= NAV_Y:
            widgets.draw_button_rect(
                self.screen, sr2, PURPLE)
            widgets.draw_text(
                self.screen, "Radio",
                "normal", WHITE,
                sr2.centerx, sr2.centery)

        # Speed section
        self._line(130)
        self._label("Playback Speed", 145)
        for i, (r, spd) in enumerate(
                zip(self.speed_btns, SPEEDS)):
            self._draw_btn(
                r,
                BLUE if i == self._speed_idx
                else DARK_GREY,
                f"{spd}x")

        # Sleep section
        self._line(260)
        self._label("Sleep Timer", 275)
        if self._sleep_end:
            remaining = max(
                0, self._sleep_end - time.time())
            m = int(remaining) // 60
            s = int(remaining) % 60
            sy = self._vy(275)
            if CONTENT_TOP <= sy <= NAV_Y:
                widgets.draw_text(
                    self.screen,
                    f"Sleeping in {m}:{s:02d}",
                    "small", ORANGE, 700, sy)
        for i, (r, opt) in enumerate(
                zip(self.sleep_btns,
                    SLEEP_OPTIONS)):
            active = (
                (i == self._sleep_idx and
                 self._sleep_end is not None) or
                (i == 0 and
                 self._sleep_end is None))
            self._draw_btn(
                r,
                BLUE if active else DARK_GREY,
                "Off" if opt == 0 else f"{opt}m")

        # Brightness section
        self._line(390)
        sy = self._vy(405)
        if CONTENT_TOP <= sy <= NAV_Y:
            widgets.draw_text(
                self.screen,
                f"Brightness  {self._brightness}%",
                "normal", CYAN, 40, sy,
                align="left")
        br = self._btn_rect(self.bright_bar)
        if CONTENT_TOP <= br.bottom and \
           br.top <= NAV_Y:
            widgets.draw_progress_bar(
                self.screen,
                br.x, br.y, br.w, br.h,
                self._brightness, 100,
                col=YELLOW, bg=DARK_GREY)
        self._draw_btn(
            self.bright_minus, DARK_GREY,
            "-", YELLOW, "large")
        self._draw_btn(
            self.bright_plus, DARK_GREY,
            "+", YELLOW, "large")

        # Clock section
        self._line(520)
        self._label("Clock Format", 535)
        use_12h = self.app.state.get(
            "clock_12h", False)
        self._draw_btn(
            self.btn_12h,
            BLUE if use_12h else DARK_GREY,
            "12hr")
        self._draw_btn(
            self.btn_24h,
            BLUE if not use_12h else DARK_GREY,
            "24hr")

        # Player section
        self._line(650)
        self._label("Player Size", 665)
        use_large = self.app.state.get(
            "large_screen", False)
        self._draw_btn(
            self.btn_normal,
            BLUE if not use_large else DARK_GREY,
            "Normal")
        self._draw_btn(
            self.btn_large,
            BLUE if use_large else DARK_GREY,
            "Large")

        # Confirm tap section
        self._line(780)
        self._label("Confirm Tap", 795)
        confirm = self.app.state.get(
            "confirm_tap", False)
        self._draw_btn(
            self.btn_confirm_on,
            BLUE if confirm else DARK_GREY,
            "On")
        self._draw_btn(
            self.btn_confirm_off,
            BLUE if not confirm else DARK_GREY,
            "Off")

        self.screen.set_clip(None)

        # Header
        widgets.draw_text(
            self.screen, "Settings",
            "large", WHITE, 640, 38)
        pygame.draw.line(
            self.screen, GREY,
            (20, CONTENT_TOP - 5),
            (1240, CONTENT_TOP - 5), 1)

        # Scrollbar
        total = self._total_h
        if total > VISIBLE_H:
            bar_h = max(40, int(
                VISIBLE_H * VISIBLE_H / total))
            bar_y = CONTENT_TOP + int(
                self._scroll / total * VISIBLE_H)
            pygame.draw.rect(
                self.screen, GREY,
                (1265, bar_y, 8, bar_h),
                border_radius=4)

        if self._bt_panel:
            self.screen.set_clip(None)
            self._draw_bt_panel()

    def _draw_bt_panel(self):
        overlay = pygame.Surface(
            (self.w, self.content_h),
            pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 220))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(60, 60, 1160, 550)
        pygame.draw.rect(
            self.screen, (15, 15, 50),
            panel, border_radius=20)
        pygame.draw.rect(
            self.screen, BLUE, panel,
            2, border_radius=20)
        widgets.draw_text(
            self.screen, "Bluetooth Devices",
            "large", WHITE, 640, 105)
        if self._bt_busy:
            dots = "." * (int(time.time()*2) % 4)
            widgets.draw_text(
                self.screen,
                "Scanning" + dots,
                "medium", YELLOW, 640, 260)
        elif not self._bt_devices:
            widgets.draw_text(
                self.screen, "No devices found",
                "medium", GREY, 640, 260)
            widgets.draw_text(
                self.screen,
                "Put headphones in pairing mode",
                "small", GREY, 640, 320)
        else:
            self._bt_device_rects = []
            for i, dev in enumerate(
                    self._bt_devices[:4]):
                r = pygame.Rect(
                    100, 150+i*88, 1080, 75)
                self._bt_device_rects.append(r)
                is_con = (dev.get("mac") ==
                    self.app.bluetooth.connected_mac)
                widgets.draw_button_rect(
                    self.screen, r,
                    BLUE if is_con else DARK_GREY)
                name = dev.get(
                    "name", dev.get("mac", "?"))
                widgets.draw_text(
                    self.screen,
                    name + (" (connected)"
                            if is_con else ""),
                    "medium", WHITE,
                    r.centerx, r.centery)
        self._bt_scan_btn  = pygame.Rect(
            100, 540, 450, 60)
        self._bt_close_btn = pygame.Rect(
            730, 540, 450, 60)
        widgets.draw_button_rect(
            self.screen, self._bt_scan_btn, BLUE)
        widgets.draw_text(
            self.screen, "Scan Again", "normal",
            WHITE, self._bt_scan_btn.centerx,
            self._bt_scan_btn.centery)
        widgets.draw_button_rect(
            self.screen, self._bt_close_btn,
            DARK_GREY)
        widgets.draw_text(
            self.screen, "Close", "normal", WHITE,
            self._bt_close_btn.centerx,
            self._bt_close_btn.centery)

    def _start_scan(self):
        self._bt_busy    = True
        self._bt_devices = []
        self.app.speech.speak(
            "Scanning for Bluetooth devices")
        self.app.bluetooth.scan(
            callback=self._scan_done)

    def _scan_done(self, devices):
        self._bt_busy    = False
        self._bt_devices = devices
        self.app.speech.speak(
            f"Found {len(devices)} devices"
            if devices else "No devices found")

    def _set_sleep(self, idx):
        self._sleep_idx = idx
        mins = SLEEP_OPTIONS[idx]
        if mins == 0:
            self._sleep_end = None
            self.app.speech.speak("Sleep timer off")
        else:
            self._sleep_end = \
                time.time() + mins * 60
            self.app.speech.speak(
                f"Sleep timer, {mins} minutes")

    def _set_speed(self, idx):
        self._speed_idx         = idx
        self.app.state["speed"] = SPEEDS[idx]
        self.app.speech.speak(
            f"Speed {SPEEDS[idx]} times")
        save_state(self.app.state)

    def _set_brightness(self, val):
        self._brightness = max(10, min(100, val))
        self.app.state["brightness"] = \
            self._brightness
        try:
            bl = int(self._brightness * 255 / 100)
            with open(
                "/sys/class/backlight/"
                "rpi_backlight/brightness", "w"
            ) as f:
                f.write(str(bl))
        except: pass
        save_state(self.app.state)

    def _hit(self, rect, x, y):
        """Check if screen x,y hits virtual rect"""
        sr = self._btn_rect(rect)
        return (sr.collidepoint(x, y) and
                CONTENT_TOP <= y <= NAV_Y)

    def handle_touch_down(self, x, y):
        super().handle_touch_down(x, y)
        self._touch_start = (x, y)
        if not self._bt_panel:
            self._drag_start  = y
            self._drag_scroll = self._scroll

    def handle_touch_move(self, x, y):
        if self._bt_panel: return
        if self._drag_start is not None:
            delta = self._drag_start - y
            max_s = max(0,
                self._total_h - VISIBLE_H)
            self._scroll = max(
                0, min(self._drag_scroll + delta,
                       max_s))

    def handle_touch_up(self, x, y):
        direction = super().handle_touch_up(x, y)
        if direction and not self._bt_panel:
            return direction

        # Only register as tap if minimal scroll
        if self._touch_start:
            _, sy = self._touch_start
            if abs(y - sy) > 15:
                return None

        if self._bt_panel:
            if hasattr(self, "_bt_close_btn") and \
               self._bt_close_btn.collidepoint(x, y):
                self._bt_panel = False
                return None
            if hasattr(self, "_bt_scan_btn") and \
               self._bt_scan_btn.collidepoint(x, y):
                self._start_scan()
                return None
            if hasattr(self, "_bt_device_rects"):
                for i, r in enumerate(
                        self._bt_device_rects):
                    if r.collidepoint(x, y) and \
                       i < len(self._bt_devices):
                        dev  = self._bt_devices[i]
                        mac  = dev["mac"]
                        name = dev.get("name", mac)
                        self.app.speech.speak(
                            f"Connecting to {name}")
                        def _connected(ok, n=name):
                            if ok:
                                self.app.speech\
                                    .speak(
                                    f"Connected"
                                    f" to {n}")
                                self._bt_panel = False
                                self._update_bt_status()
                            else:
                                self.app.speech\
                                    .speak(
                                    "Connection"
                                    " failed")
                        def _paired(ok, m=mac,
                                    cb=_connected):
                            if ok:
                                self.app.bluetooth\
                                    .connect(m, cb)
                            else:
                                self.app.speech\
                                    .speak(
                                    "Pairing failed")
                        self.app.bluetooth.pair(
                            mac, callback=_paired)
                        return None
            return None

        if self._hit(self.btn_bt, x, y):
            self._bt_panel = True
            self._start_scan()
            return None

        if self._hit(self.btn_radio, x, y):
            self.app.speech.speak(
                "BBC Radio", resume=False)
            return SCREEN_RADIO

        for i, r in enumerate(self.speed_btns):
            if self._hit(r, x, y):
                self._set_speed(i)
                return None

        for i, r in enumerate(self.sleep_btns):
            if self._hit(r, x, y):
                self._set_sleep(i)
                return None

        if self._hit(self.bright_minus, x, y):
            self._set_brightness(
                self._brightness - 5)
            self.app.speech.speak(
                f"Brightness {self._brightness}")
            return None

        if self._hit(self.bright_plus, x, y):
            self._set_brightness(
                self._brightness + 5)
            self.app.speech.speak(
                f"Brightness {self._brightness}")
            return None

        if self._hit(self.bright_bar, x, y):
            pct = int(
                (x - self.bright_bar.x) /
                self.bright_bar.w * 100)
            self._set_brightness(pct)
            return None

        if self._hit(self.btn_12h, x, y):
            self.app.state["clock_12h"] = True
            self.app.speech.speak("12 hour clock")
            save_state(self.app.state)
            return None

        if self._hit(self.btn_24h, x, y):
            self.app.state["clock_12h"] = False
            self.app.speech.speak("24 hour clock")
            save_state(self.app.state)
            return None

        if self._hit(self.btn_normal, x, y):
            self.app.state["large_screen"] = False
            self.app.speech.speak("Normal screen")
            save_state(self.app.state)
            return None

        if self._hit(self.btn_large, x, y):
            self.app.state["large_screen"] = True
            self.app.speech.speak("Large screen")
            save_state(self.app.state)
            return None

        if self._hit(self.btn_confirm_on, x, y):
            self.app.state["confirm_tap"] = True
            self.app.speech.speak("Confirm tap on")
            save_state(self.app.state)
            return None

        if self._hit(self.btn_confirm_off, x, y):
            self.app.state["confirm_tap"] = False
            self.app.speech.speak("Confirm tap off")
            save_state(self.app.state)
            return None

        return None

    def update(self):
        if (self._sleep_end and
                time.time() >= self._sleep_end):
            self._sleep_end = None
            self._sleep_idx = 0
            self._fade_out()

    def _fade_out(self):
        self.app.speech.speak("Good night")
        def _do():
            start_vol = self.app.mpd.volume
            for i in range(60):
                vol = int(start_vol * (1 - i/60))
                self.app.mpd.set_volume(vol)
                time.sleep(0.5)
            self.app.mpd.pause()
            self.app.mpd.set_volume(start_vol)
        threading.Thread(
            target=_do, daemon=True).start()

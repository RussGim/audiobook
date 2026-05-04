import pygame
import time
import threading
from screens.base import BaseScreen
from ui.colours import *
from ui import widgets
from utils.state import save as save_state
from utils.speech import set_voice_prompts
from constants import (SCREEN_RADIO, SCREEN_PLAYER,
                       SCREEN_PLAYER_LARGE,
                       SCREEN_PLAYER_LARGEST)

SPEEDS        = [0.75, 1.0, 1.25, 1.5, 2.0]
SLEEP_OPTIONS = [0, 15, 30, 45, 60]
SLEEP_LABELS  = ["Off", "15m", "30m", "45m", "60m"]

BACKLIGHT     = "/sys/class/backlight/10-0045/brightness"
BACKLIGHT_MAX = 31

NAV_Y      = 640
CONT_TOP   = 80
VISIBLE_H  = NAV_Y - CONT_TOP

SCREEN_BG  = (10,  10,  18)
CARD_BG    = (22,  22,  40)
CARD_BDR   = (40,  40,  62)
SEC_LBL    = (90,  90, 115)
ROW_TXT    = (210, 210, 225)
ROW_SUB    = (90,  90, 115)
DIVIDER    = (35,  35,  55)
TOG_ON     = (48, 192,  96)
TOG_OFF    = (50,  50,  75)
PILL_ON    = (74,  63, 160)
PILL_OFF   = (38,  38,  60)
ARROW_C    = (70,  70,  95)

ROW_H      = 80
SLD_ROW_H  = 100
PIL_ROW_H  = 90
SEC_LBL_H  = 40
SEC_GAP    = 16
CPAD       = 20
TOG_W      = 80
TOG_H      = 44
PIL_W      = 110
PIL_H      = 48
PIL_GAP    = 8

_DLY  = 0
_DBY  = 40
_DSY  = 140
_CLY  = 236
_C24  = 276
_PLY  = 372
_PSY  = 412
_PSL  = 502
_ALY  = 608
_AVY  = 648
_AAY  = 728
_ACY  = 808
_NLY  = 904
_NBT  = 944
_NRD  = 1024
TOTAL_H = 1124

class SettingsScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self._bt_panel    = False
        self._bt_status   = "Not connected"
        self._bt_devices  = []
        self._bt_busy     = False
        self._touch_start = None
        self._sleep_end   = None
        self._sleep_idx   = 0
        self._scroll      = 0
        self._drag_start  = None
        self._drag_scroll = 0
        self._drag_bright = False
        sp = app.state.get("speed", 1.0)
        self._speed_idx   = SPEEDS.index(sp) \
                            if sp in SPEEDS else 1
        self._brightness  = app.state.get(
            "brightness", 80)
        self._build_rects()

    def _build_rects(self):
        tw = len(SPEEDS)*(PIL_W+PIL_GAP) - PIL_GAP
        px = 1280 - CPAD - tw
        self.speed_rects = [
            pygame.Rect(px + i*(PIL_W+PIL_GAP),
                        _PSY + (PIL_ROW_H-PIL_H)//2,
                        PIL_W, PIL_H)
            for i in range(len(SPEEDS))]

        sw = len(SLEEP_OPTIONS)*(PIL_W+PIL_GAP) \
             - PIL_GAP
        sx = 1280 - CPAD - sw
        self.sleep_rects = [
            pygame.Rect(sx + i*(PIL_W+PIL_GAP),
                        _PSL + (PIL_ROW_H-PIL_H)//2,
                        PIL_W, PIL_H)
            for i in range(len(SLEEP_OPTIONS))]

        # Three size pills
        sw2 = 3*(PIL_W+PIL_GAP) - PIL_GAP
        sx2 = 1280 - CPAD - sw2
        self.size_rects = [
            pygame.Rect(sx2 + i*(PIL_W+PIL_GAP),
                        _DSY + (ROW_H-PIL_H)//2,
                        PIL_W, PIL_H)
            for i in range(3)]

        self.row_24h      = pygame.Rect(
            0, _C24, 1280, ROW_H)
        self.row_voice    = pygame.Rect(
            0, _AVY, 1280, ROW_H)
        self.row_announce = pygame.Rect(
            0, _AAY, 1280, ROW_H)
        self.row_confirm  = pygame.Rect(
            0, _ACY, 1280, ROW_H)
        self.row_bt       = pygame.Rect(
            0, _NBT, 1280, ROW_H)
        self.row_radio    = pygame.Rect(
            0, _NRD, 1280, ROW_H)
        self.bright_rect  = pygame.Rect(
            CPAD + 30, _DBY + 62,
            1280 - CPAD*2 - 60, 8)

    def on_enter(self):
        self._update_bt_status()
        set_voice_prompts(
            self.app.state.get(
                "voice_prompts", True))

    def _update_bt_status(self):
        def _check():
            connected = \
                self.app.bluetooth.get_status()
            self._bt_status = (
                f"Connected: "
                f"{self.app.bluetooth.connected_name}"
                if connected else "Not connected")
        threading.Thread(
            target=_check, daemon=True).start()

    def _vy(self, vy):
        return CONT_TOP + vy - self._scroll

    def _hit(self, vr, x, y):
        sr = pygame.Rect(vr.x, self._vy(vr.y),
                         vr.w, vr.h)
        return (sr.collidepoint(x, y) and
                CONT_TOP <= y <= NAV_Y)

    def _draw_card(self, vy0, vy1):
        sy = max(self._vy(vy0), CONT_TOP)
        ey = min(self._vy(vy1), NAV_Y)
        if sy >= ey:
            return
        r = pygame.Rect(CPAD, sy,
                        1280 - CPAD*2, ey - sy)
        pygame.draw.rect(self.screen, CARD_BG, r,
                         border_radius=20)
        pygame.draw.rect(self.screen, CARD_BDR, r,
                         1, border_radius=20)

    def _sec_label(self, text, vy):
        sy = self._vy(vy + 24)
        if CONT_TOP <= sy <= NAV_Y:
            f = pygame.font.SysFont("sans", 22)
            s = f.render(text.upper(), True,
                         SEC_LBL)
            self.screen.blit(
                s, (CPAD + 8, sy - 11))

    def _toggle(self, vx, vy, is_on):
        sy = self._vy(vy)
        if not (CONT_TOP - TOG_H <= sy <= NAV_Y):
            return
        col = TOG_ON if is_on else TOG_OFF
        r = pygame.Rect(vx, sy, TOG_W, TOG_H)
        pygame.draw.rect(self.screen, col, r,
                         border_radius=TOG_H//2)
        cx = vx + TOG_W - TOG_H//2 if is_on \
             else vx + TOG_H//2
        pygame.draw.circle(self.screen, WHITE,
            (cx, sy + TOG_H//2), TOG_H//2 - 4)

    def _row_text(self, label, sub, vy, h=ROW_H):
        sy = self._vy(vy)
        if not (CONT_TOP - h <= sy <= NAV_Y):
            return
        cy = sy + h//2
        lx = CPAD + 30
        if sub:
            widgets.draw_text(self.screen, label,
                "normal", ROW_TXT, lx, cy - 13,
                align="left")
            f = pygame.font.SysFont("sans", 24)
            s = f.render(sub, True, ROW_SUB)
            self.screen.blit(s, (lx, cy + 7))
        else:
            widgets.draw_text(self.screen, label,
                "normal", ROW_TXT, lx, cy,
                align="left")

    def _divider(self, vy):
        sy = self._vy(vy)
        if CONT_TOP <= sy <= NAV_Y:
            pygame.draw.line(self.screen, DIVIDER,
                (CPAD + 20, sy),
                (1280 - CPAD - 20, sy), 1)

    def _pill(self, vr, label, active):
        sr = pygame.Rect(vr.x, self._vy(vr.y),
                         vr.w, vr.h)
        if sr.bottom < CONT_TOP or \
           sr.top > NAV_Y:
            return
        col = PILL_ON if active else PILL_OFF
        pygame.draw.rect(self.screen, col, sr,
                         border_radius=sr.h//2)
        tc = WHITE if active else (120, 120, 140)
        widgets.draw_text(self.screen, label,
            "small", tc, sr.centerx, sr.centery)

    def draw(self):
        self.screen.fill(SCREEN_BG)
        clip = pygame.Rect(
            0, CONT_TOP, 1280, VISIBLE_H)
        self.screen.set_clip(clip)

        tx = 1280 - CPAD - TOG_W - 10

        # Display
        self._sec_label("Display", _DLY)
        self._draw_card(_DLY + SEC_LBL_H - 4,
                        _DSY + ROW_H)

        sy_b = self._vy(_DBY)
        if CONT_TOP - SLD_ROW_H <= sy_b <= NAV_Y:
            widgets.draw_text(self.screen,
                f"Brightness  {self._brightness}%",
                "normal", ROW_TXT,
                CPAD + 30, sy_b + 28, align="left")
            bx  = CPAD + 30
            bw  = 1280 - CPAD*2 - 60
            bty = sy_b + 68
            fw  = int(self._brightness / 100 * bw)
            pygame.draw.rect(self.screen, PILL_OFF,
                (bx, bty-4, bw, 8), border_radius=4)
            if fw > 0:
                pygame.draw.rect(self.screen,
                    PILL_ON,
                    (bx, bty-4, fw, 8),
                    border_radius=4)
            pygame.draw.circle(self.screen, WHITE,
                (bx + fw, bty), 18)
            pygame.draw.circle(self.screen, PILL_ON,
                (bx + fw, bty), 13)

        self._divider(_DSY)
        self._row_text("Player size", None, _DSY)
        psize = self.app.state.get(
            "player_size", "normal")
        for i, lbl in enumerate(
                ["Normal", "Large", "Largest"]):
            self._pill(self.size_rects[i], lbl,
                       psize == lbl.lower())

        # Clock
        self._sec_label("Clock", _CLY)
        self._draw_card(_CLY + SEC_LBL_H - 4,
                        _C24 + ROW_H)
        self._row_text("24 hour clock", None, _C24)
        use_24 = not self.app.state.get(
            "clock_12h", False)
        self._toggle(tx,
                     _C24 + (ROW_H-TOG_H)//2,
                     use_24)

        # Playback
        self._sec_label("Playback", _PLY)
        self._draw_card(_PLY + SEC_LBL_H - 4,
                        _PSL + PIL_ROW_H)
        self._row_text("Speed", None,
                       _PSY, PIL_ROW_H)
        for i, spd in enumerate(SPEEDS):
            self._pill(self.speed_rects[i],
                f"{spd}x", i == self._speed_idx)

        self._divider(_PSL)
        self._row_text("Sleep timer", None,
                       _PSL, PIL_ROW_H)
        if self._sleep_end:
            rem = max(
                0, self._sleep_end - time.time())
            m = int(rem) // 60
            s = int(rem) % 60
            sy = self._vy(_PSL + PIL_ROW_H//2)
            if CONT_TOP <= sy <= NAV_Y:
                widgets.draw_text(self.screen,
                    f"{m}:{s:02d}", "small",
                    ORANGE, CPAD + 260, sy)
        for i, lbl in enumerate(SLEEP_LABELS):
            active = (
                i == self._sleep_idx and
                self._sleep_end is not None) or \
                (i == 0 and
                 self._sleep_end is None)
            self._pill(self.sleep_rects[i],
                       lbl, active)

        # Accessibility
        self._sec_label("Accessibility", _ALY)
        self._draw_card(_ALY + SEC_LBL_H - 4,
                        _ACY + ROW_H)
        voice    = self.app.state.get(
            "voice_prompts", True)
        announce = self.app.state.get(
            "chapter_announce", True)
        confirm  = self.app.state.get(
            "confirm_tap", False)

        self._row_text("Voice prompts",
            "Spoken feedback on actions", _AVY)
        self._toggle(tx,
            _AVY + (ROW_H-TOG_H)//2, voice)
        self._divider(_AAY)

        self._row_text("Chapter announce",
            "Speak chapter on change", _AAY)
        self._toggle(tx,
            _AAY + (ROW_H-TOG_H)//2, announce)
        self._divider(_ACY)

        self._row_text("Confirm tap",
            "Double tap to play books", _ACY)
        self._toggle(tx,
            _ACY + (ROW_H-TOG_H)//2, confirm)

        # Connections
        self._sec_label("Connections", _NLY)
        self._draw_card(_NLY + SEC_LBL_H - 4,
                        _NRD + ROW_H)
        self._row_text("Bluetooth",
                       self._bt_status, _NBT)
        sy_bt = self._vy(_NBT + ROW_H//2)
        if CONT_TOP <= sy_bt <= NAV_Y:
            widgets.draw_text(self.screen, "›",
                "large", ARROW_C,
                1280 - CPAD - 16, sy_bt)

        self._divider(_NRD)
        self._row_text("BBC Radio",
            "Stream live radio", _NRD)
        sy_rd = self._vy(_NRD + ROW_H//2)
        if CONT_TOP <= sy_rd <= NAV_Y:
            widgets.draw_text(self.screen, "›",
                "large", ARROW_C,
                1280 - CPAD - 16, sy_rd)

        self.screen.set_clip(None)

        pygame.draw.rect(self.screen, SCREEN_BG,
            (0, 0, 1280, CONT_TOP))
        widgets.draw_text(self.screen, "Settings",
            "large", WHITE, 640, CONT_TOP//2)
        pygame.draw.line(self.screen, CARD_BDR,
            (0, CONT_TOP), (1280, CONT_TOP), 1)

        if TOTAL_H > VISIBLE_H:
            bar_h = max(40, int(
                VISIBLE_H * VISIBLE_H / TOTAL_H))
            bar_y = CONT_TOP + int(
                self._scroll / TOTAL_H * VISIBLE_H)
            pygame.draw.rect(self.screen,
                (50, 50, 75),
                (1272, bar_y, 6, bar_h),
                border_radius=3)

        if self._bt_panel:
            self._draw_bt_panel()

    def _draw_bt_panel(self):
        overlay = pygame.Surface(
            (self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(60, 60, 1160, 550)
        pygame.draw.rect(self.screen, CARD_BG,
            panel, border_radius=24)
        pygame.draw.rect(self.screen, CARD_BDR,
            panel, 1, border_radius=24)
        widgets.draw_text(self.screen,
            "Bluetooth Devices",
            "large", WHITE, 640, 110)
        if self._bt_busy:
            dots = "." * (int(time.time()*2) % 4)
            widgets.draw_text(self.screen,
                "Scanning" + dots,
                "medium", YELLOW, 640, 260)
        elif not self._bt_devices:
            widgets.draw_text(self.screen,
                "No devices found",
                "medium", ROW_SUB, 640, 260)
            widgets.draw_text(self.screen,
                "Put headphones in pairing mode",
                "small", ROW_SUB, 640, 320)
        else:
            self._bt_device_rects = []
            for i, dev in enumerate(
                    self._bt_devices[:4]):
                r = pygame.Rect(
                    100, 150+i*88, 1080, 75)
                self._bt_device_rects.append(r)
                is_con = (dev.get("mac") ==
                    self.app.bluetooth.connected_mac)
                pygame.draw.rect(self.screen,
                    PILL_ON if is_con else PILL_OFF,
                    r, border_radius=16)
                name = dev.get(
                    "name", dev.get("mac", "?"))
                widgets.draw_text(self.screen,
                    name + (" (connected)"
                            if is_con else ""),
                    "medium", WHITE,
                    r.centerx, r.centery)
        self._bt_scan_btn  = pygame.Rect(
            100, 540, 450, 60)
        self._bt_close_btn = pygame.Rect(
            730, 540, 450, 60)
        pygame.draw.rect(self.screen, PILL_ON,
            self._bt_scan_btn, border_radius=16)
        widgets.draw_text(self.screen,
            "Scan again", "normal", WHITE,
            self._bt_scan_btn.centerx,
            self._bt_scan_btn.centery)
        pygame.draw.rect(self.screen, PILL_OFF,
            self._bt_close_btn, border_radius=16)
        widgets.draw_text(self.screen, "Close",
            "normal", WHITE,
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
        speed = SPEEDS[idx]
        self.app.state["speed"] = speed
        self.app.speech.speak(
            f"Speed {speed} times")
        save_state(self.app.state)

    def _set_brightness(self, val):
        self._brightness = max(10, min(100, val))
        self.app.state["brightness"] = \
            self._brightness
        try:
            bl = int(
                self._brightness * BACKLIGHT_MAX
                / 100)
            with open(BACKLIGHT, "w") as f:
                f.write(str(bl))
        except Exception as e:
            print(f"Brightness error: {e}")
        save_state(self.app.state)

    def _hit(self, vr, x, y):
        sr = pygame.Rect(vr.x, self._vy(vr.y),
                         vr.w, vr.h)
        return (sr.collidepoint(x, y) and
                CONT_TOP <= y <= NAV_Y)

    def handle_touch_down(self, x, y):
        super().handle_touch_down(x, y)
        self._touch_start = (x, y)
        self._drag_bright = False
        if not self._bt_panel:
            self._drag_start  = y
            self._drag_scroll = self._scroll
            bx  = CPAD + 30
            bw  = 1280 - CPAD*2 - 60
            bty = self._vy(_DBY + 68)
            if (bx <= x <= bx + bw and
                    bty - 24 <= y <= bty + 24 and
                    CONT_TOP <= y <= NAV_Y):
                self._drag_bright = True

    def handle_touch_move(self, x, y):
        if self._bt_panel:
            return
        if self._drag_bright:
            bx = CPAD + 30
            bw = 1280 - CPAD*2 - 60
            pct = max(0, min(1, (x - bx) / bw))
            self._set_brightness(int(pct * 100))
            return
        if self._drag_start is not None:
            delta = self._drag_start - y
            max_s = max(0, TOTAL_H - VISIBLE_H)
            self._scroll = max(
                0, min(self._drag_scroll + delta,
                       max_s))

    def handle_touch_up(self, x, y):
        self._drag_bright = False
        direction = super().handle_touch_up(x, y)
        if direction and not self._bt_panel:
            return direction

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
                                    "Connection failed")
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

        for i, r in enumerate(self.speed_rects):
            if self._hit(r, x, y):
                self._set_speed(i)
                return None

        for i, r in enumerate(self.sleep_rects):
            if self._hit(r, x, y):
                self._set_sleep(i)
                return None

        if self._hit(self.size_rects[0], x, y):
            self.app.state["player_size"] = "normal"
            self.app.speech.speak("Normal screen")
            save_state(self.app.state)
            self.app._go_to(SCREEN_PLAYER)
            return None
        if self._hit(self.size_rects[1], x, y):
            self.app.state["player_size"] = "large"
            self.app.speech.speak("Large screen")
            save_state(self.app.state)
            self.app._go_to(SCREEN_PLAYER_LARGE)
            return None
        if self._hit(self.size_rects[2], x, y):
            self.app.state["player_size"] = "largest"
            self.app.speech.speak("Largest screen")
            save_state(self.app.state)
            self.app._go_to(SCREEN_PLAYER_LARGEST)
            return None

        if self._hit(self.row_24h, x, y):
            clock_12h = self.app.state.get(
                "clock_12h", False)
            new_12h = not clock_12h
            self.app.state["clock_12h"] = new_12h
            self.app.speech.speak(
                "12 hour clock" if new_12h
                else "24 hour clock")
            save_state(self.app.state)
            return None

        if self._hit(self.row_voice, x, y):
            cur = self.app.state.get(
                "voice_prompts", True)
            self.app.state["voice_prompts"] = \
                not cur
            set_voice_prompts(not cur)
            if not cur:
                self.app.speech.speak(
                    "Voice prompts on")
            save_state(self.app.state)
            return None

        if self._hit(self.row_announce, x, y):
            cur = self.app.state.get(
                "chapter_announce", True)
            self.app.state["chapter_announce"] = \
                not cur
            self.app.speech.speak(
                "Chapter announce " +
                ("off" if cur else "on"))
            save_state(self.app.state)
            return None

        if self._hit(self.row_confirm, x, y):
            cur = self.app.state.get(
                "confirm_tap", False)
            self.app.state["confirm_tap"] = not cur
            self.app.speech.speak(
                "Confirm tap " +
                ("off" if cur else "on"))
            save_state(self.app.state)
            return None

        if self._hit(self.row_bt, x, y):
            self._bt_panel = True
            self._start_scan()
            return None

        if self._hit(self.row_radio, x, y):
            self.app.speech.speak(
                "BBC Radio", resume=False)
            return SCREEN_RADIO

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

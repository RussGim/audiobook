#!/usr/bin/env python3
import pygame
import sys
import os
import time

SCREEN_W   = 1280
SCREEN_H   = 720
FPS        = 30
FULLSCREEN = False  # Set True on Pi

from ui               import fonts
from ui.colours       import *
from ui.nav_bar       import NavBar
from constants        import (SCREEN_BOOKS,
                               SCREEN_PLAYER,
                               SCREEN_CHAPTERS,
                               SCREEN_SETTINGS,
                               SCREEN_CLOCK,
                               SCREEN_RADIO,
                               SCREEN_PLAYER_LARGE,
                               SCREEN_PLAYER_LARGEST,
                               SCREEN_BOOKS_HUGE)
from ui               import widgets
from mpd_client       import MPDClient
from bluetooth        import BluetoothManager
from utils            import speech as speech_module
from utils.speech     import speak, set_mpd, \
                               set_voice_prompts
from utils.state      import (load as load_state,
                               save as save_state)
from utils.usb_manager import USBManager
from screens.books         import BooksScreen
from screens.player        import PlayerScreen
from screens.player_large  import PlayerLargeScreen
from screens.player_largest import PlayerLargestScreen
from screens.chapters      import ChaptersScreen
from screens.settings      import SettingsScreen
from screens.clock         import ClockScreen
from screens.radio         import RadioScreen
from screens.books_huge    import BooksHugeScreen

class App:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self.screen = pygame.display.set_mode(
            (SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption(
            "Audiobook Player")
        self.clock  = pygame.time.Clock()
        fonts.init()

        self.mpd       = MPDClient()
        set_mpd(self.mpd)
        self.bluetooth = BluetoothManager()
        self.speech    = speech_module
        self.state     = load_state()
        set_voice_prompts(
            self.state.get("voice_prompts", True))
        self.nav       = NavBar(SCREEN_W, SCREEN_H)

        self.screens = {
            SCREEN_BOOKS:          BooksScreen(self),
            SCREEN_PLAYER:         PlayerScreen(self),
            SCREEN_PLAYER_LARGE:   PlayerLargeScreen(self),
            SCREEN_PLAYER_LARGEST: PlayerLargestScreen(self),
            SCREEN_CHAPTERS:       ChaptersScreen(self),
            SCREEN_SETTINGS:       SettingsScreen(self),
            SCREEN_CLOCK:          ClockScreen(self),
            SCREEN_RADIO:          RadioScreen(self),
            SCREEN_BOOKS_HUGE:     BooksHugeScreen(self),
        }

        self._idle_timeout              = 60
        self._last_touch                = time.time()
        self._clock_active              = False
        self._pre_clock_screen          = SCREEN_PLAYER
        self._last_eof                  = False
        self._last_save                 = time.time()
        self._last_track_num            = 0
        self._suppress_chapter_announce = False

        self._fswipe_x            = 0
        self._fswipe_y            = 0
        self._fswipe_t            = 0
        self._pre_settings_screen = None

        if self.state.get("book"):
            self._go_to(self._player_screen())
            self._resume_last()
        else:
            self._go_to(SCREEN_BOOKS)

        self.usb = USBManager(self.mpd)
        self.usb.set_callback(self._on_usb_change)
        self.usb.scan_once()
        self.usb.start_monitor()

    def _player_screen(self):
        return {
            "normal":  SCREEN_PLAYER,
            "large":   SCREEN_PLAYER_LARGE,
            "largest": SCREEN_PLAYER_LARGEST,
        }.get(self.state.get(
            "player_size", "normal"), SCREEN_PLAYER)

    def _resume_last(self):
        book     = self.state.get("book")
        chapter  = self.state.get("chapter")
        position = self.state.get("position", 0.0)
        if book:
            success = self.mpd.play_book(
                book, chapter, position)
            if success:
                speak(f"Resuming "
                      f"{os.path.basename(book)}")
            else:
                self.state["book"]     = None
                self.state["chapter"]  = None
                self.state["position"] = 0.0
                save_state(self.state)
                self._go_to(SCREEN_BOOKS)

    def _go_to(self, screen_idx):
        if hasattr(self, "_current_screen"):
            self.screens[
                self._current_screen].on_exit()
        self._current_screen = screen_idx
        if screen_idx not in (
                SCREEN_CLOCK, SCREEN_RADIO,
                SCREEN_PLAYER_LARGE,
                SCREEN_PLAYER_LARGEST,
                SCREEN_BOOKS_HUGE):
            self.nav.current = screen_idx
        elif screen_idx in (
                SCREEN_PLAYER_LARGE,
                SCREEN_PLAYER_LARGEST):
            self.nav.current = SCREEN_PLAYER
        self.screens[screen_idx].on_enter()

    def _nav_go(self, nav_r):
        if nav_r == SCREEN_PLAYER:
            self._go_to(self._player_screen())
        else:
            self._go_to(nav_r)

    def _handle_nav_result(self, result):
        if result is None or result == -1:
            return
        if isinstance(result, int):
            self._go_to(result)
        elif result == "go_player":
            self._go_to(self._player_screen())
        elif result == "go_normal_player":
            self._go_to(SCREEN_PLAYER)
        elif result == "swipe_left":
            self._go_to(
                (self._current_screen + 1) % 4)
        elif result == "swipe_right":
            self._go_to(
                (self._current_screen - 1) % 4)

    def _check_fast_swipe(self, x, y):
        dx = x - self._fswipe_x
        dy = y - self._fswipe_y
        dt = time.time() - self._fswipe_t
        if (dt > 0.4 or
                abs(dy) < 400 or
                abs(dy) < abs(dx) * 2):
            return None
        return "swipe_down" if dy > 0 \
               else "swipe_up"

    def _on_usb_change(self, drives):
        if not hasattr(self, "_current_screen"):
            return
        if drives:
            self.speech.speak(
                "USB stick inserted",
                resume=False)
        else:
            self.speech.speak(
                "USB stick removed",
                resume=False)
            self.mpd.pause()
        self.screens[SCREEN_BOOKS]._refresh()
        if (self._current_screen in (
                SCREEN_PLAYER,
                SCREEN_PLAYER_LARGE,
                SCREEN_PLAYER_LARGEST)
                and self.mpd.state == "stop"):
            self._go_to(SCREEN_BOOKS)

    def _save_position(self):
        if self.mpd.state == "play":
            self.state["book"]     = self.mpd.book
            self.state["chapter"]  = \
                self.mpd.title + ".mp3"
            self.state["position"] = self.mpd.elapsed
            self.state["volume"]   = self.mpd.volume
            save_state(self.state)

    def _check_end_of_book(self):
        is_stopped = (
            self.mpd.state == "stop" and
            self.mpd.track_num ==
            self.mpd.track_total and
            self.mpd.track_total > 0)
        if is_stopped and not self._last_eof:
            self._last_eof = True
            speak("End of book")
            self.state["position"] = 0.0
            self.state["chapter"]  = None
            save_state(self.state)
            pygame.time.set_timer(
                pygame.USEREVENT + 1, 3000, True)
        elif not is_stopped:
            self._last_eof = False

    def _check_chapter_change(self):
        num = self.mpd.track_num
        if num > 0 and \
                num != self._last_track_num:
            if self._last_track_num > 0 and \
               not self._suppress_chapter_announce \
               and self.state.get(
                   "chapter_announce", True):
                speak(f"Chapter {num}")
            self._last_track_num            = num
            self._suppress_chapter_announce = False

    def _check_idle(self):
        idle = time.time() - self._last_touch
        radio = self.screens.get(SCREEN_RADIO)
        radio_playing = (radio and
                         radio._selected >= 0)
        audio_playing = self.mpd.state == "play"
        if (idle >= self._idle_timeout and
                not self._clock_active and
                not radio_playing and
                not audio_playing):
            self._clock_active     = True
            self._pre_clock_screen = \
                self._current_screen
            self._go_to(SCREEN_CLOCK)

    def _wake_from_clock(self):
        self.screens[SCREEN_CLOCK].on_exit()
        self._clock_active   = False
        self._last_touch     = time.time()
        self._current_screen = \
            self._pre_clock_screen
        if self._pre_clock_screen not in (
                SCREEN_CLOCK, SCREEN_RADIO,
                SCREEN_PLAYER_LARGE,
                SCREEN_PLAYER_LARGEST,
                SCREEN_BOOKS_HUGE):
            self.nav.current = self._pre_clock_screen
        self.screens[
            self._current_screen].on_enter()

    def _is_huge(self):
        return self._current_screen in (
            SCREEN_PLAYER_LARGEST,
            SCREEN_BOOKS_HUGE)

    def run(self):
        while True:
            current = self.screens[
                self._current_screen]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._save_position()
                    pygame.quit()
                    sys.exit()

                if event.type == \
                        pygame.USEREVENT + 1:
                    if not self._clock_active:
                        self._go_to(SCREEN_BOOKS)

                if event.type == pygame.KEYDOWN:
                    self._last_touch = time.time()
                    if self._clock_active:
                        self._wake_from_clock()
                        continue
                    if event.key == pygame.K_ESCAPE:
                        self._save_position()
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_SPACE:
                        self.mpd.toggle()
                    elif event.key == pygame.K_LEFT:
                        self.mpd.seek_back(30)
                    elif event.key == pygame.K_RIGHT:
                        self.mpd.seek_forward(30)
                    elif event.key == pygame.K_n:
                        self.mpd.next_track()
                    elif event.key == pygame.K_p:
                        self.mpd.prev_track()
                    elif event.key == pygame.K_UP:
                        self.mpd.set_volume(
                            self.mpd.volume + 5)
                    elif event.key == pygame.K_DOWN:
                        self.mpd.set_volume(
                            self.mpd.volume - 5)
                    elif event.key == pygame.K_1:
                        self._go_to(SCREEN_BOOKS)
                    elif event.key == pygame.K_2:
                        self._nav_go(SCREEN_PLAYER)
                    elif event.key == pygame.K_3:
                        self._go_to(SCREEN_CHAPTERS)
                    elif event.key == pygame.K_4:
                        self._go_to(SCREEN_SETTINGS)
                    elif event.key == pygame.K_5:
                        self._go_to(SCREEN_RADIO)
                    elif event.key == pygame.K_6:
                        self._go_to(
                            SCREEN_PLAYER_LARGE)
                    elif event.key == pygame.K_7:
                        self._go_to(
                            SCREEN_PLAYER_LARGEST)
                    elif event.key == pygame.K_8:
                        self._go_to(
                            SCREEN_BOOKS_HUGE)
                    elif event.key == pygame.K_c:
                        if self._clock_active:
                            self._wake_from_clock()
                        else:
                            self._clock_active = True
                            self._pre_clock_screen =\
                                self._current_screen
                            self._go_to(SCREEN_CLOCK)

                elif event.type == \
                        pygame.FINGERDOWN:
                    self._last_touch = time.time()
                    x = int(event.x * SCREEN_W)
                    y = int(event.y * SCREEN_H)
                    self._fswipe_x = x
                    self._fswipe_y = y
                    self._fswipe_t = time.time()
                    if self._clock_active:
                        pass
                    elif self._is_huge():
                        current.handle_touch_down(
                            x, y)
                    else:
                        nav_r = \
                            self.nav.handle_touch(
                                x, y)
                        if nav_r == -1:
                            current.handle_touch_down(
                                x, y)
                        else:
                            self._nav_go(nav_r)

                elif event.type == pygame.FINGERUP:
                    self._last_touch = time.time()
                    x = int(event.x * SCREEN_W)
                    y = int(event.y * SCREEN_H)
                    if self._clock_active:
                        self._wake_from_clock()
                    else:
                        fswipe = \
                            self._check_fast_swipe(
                                x, y)
                        if fswipe == "swipe_down" \
                           and self._current_screen \
                           != SCREEN_SETTINGS:
                            self._pre_settings_screen \
                                = self._current_screen
                            self._go_to(
                                SCREEN_SETTINGS)
                        elif fswipe == "swipe_up" \
                           and self._current_screen \
                           == SCREEN_SETTINGS \
                           and self._pre_settings_screen \
                           is not None:
                            self._go_to(
                                self._pre_settings_screen)
                            self._pre_settings_screen \
                                = None
                        else:
                            result = \
                                current.handle_touch_up(
                                    x, y)
                            self._handle_nav_result(
                                result)

                elif event.type == \
                        pygame.FINGERMOTION:
                    if not self._clock_active:
                        x = int(event.x * SCREEN_W)
                        y = int(event.y * SCREEN_H)
                        current.handle_touch_move(
                            x, y)

            current.update()
            self.screens[SCREEN_SETTINGS].update()
            current.draw()
            if not self._clock_active and \
               not self._is_huge():
                self.nav.draw(self.screen)
            pygame.display.flip()

            if time.time() - self._last_save >= 10:
                self._last_save = time.time()
                self._save_position()

            self._check_end_of_book()
            self._check_chapter_change()
            self._check_idle()

            if self._clock_active:
                self.clock.tick(2)
            else:
                self.clock.tick(FPS)


if __name__ == "__main__":
    app = App()
    app.run()

import subprocess
import threading
import time
import pygame

_current  = None
_mpd_ref  = None

def set_mpd(mpd_client):
    global _mpd_ref
    _mpd_ref = mpd_client

def beep(freq=800, ms=40):
    try:
        import numpy as np
        vol_scale = (_mpd_ref.volume / 100) \
                    if _mpd_ref else 0.3
        vol_scale = max(0.05, vol_scale * 0.4)
        sample_rate = 22050
        samples     = int(sample_rate * ms / 1000)
        t           = np.linspace(
            0, ms/1000, samples, False)
        wave        = np.sin(
            freq * 2 * np.pi * t) * vol_scale
        wave        = (wave * 32767).astype(
            np.int16)
        stereo      = np.column_stack((wave, wave))
        sound       = pygame.sndarray.make_sound(
            stereo)
        sound.play()
    except Exception as e:
        print(f"Beep error: {e}")

def _do_speak(text):
    """Speak using espeak-ng, scaled from current MPD volume."""
    try:
        import shlex
        import re

        vol = 70

        # Prefer live MPD volume
        try:
            out = subprocess.check_output(
                ["mpc", "status"],
                text=True,
                stderr=subprocess.DEVNULL
            )
            m = re.search(r"volume:\s*(\d+)%", out)
            if m:
                vol = int(m.group(1))
        except Exception:
            pass

        # espeak amplitude is 0-200
        amp = int(max(10, min(100, vol)) * 1.5)
        amp = max(15, min(180, amp))

        cmd = f'espeak-ng -a {amp} {shlex.quote(text)}'
        subprocess.run(cmd, shell=True)

    except Exception as e:
        print(f"Speech error: {e}")

def speak_and_wait(text, stop_mpd=True):
    """
    Pause MPD if needed, speak, return.
    Caller responsible for resuming playback.
    """
    mpd = _mpd_ref
    if stop_mpd and mpd and \
       mpd.state == "play":
        mpd.pause()
        time.sleep(1.5)
    _do_speak(text)

def speak(text, interrupt=True, resume=True,
          pause_mpd=True):
    """
    Non-blocking speak. Pauses MPD if playing
    and pause_mpd=True, resumes after if resume=True.
    """
    global _current
    if interrupt and _current and \
       _current.poll() is None:
        _current.terminate()
        time.sleep(0.1)

    def _run():
        global _current
        mpd         = _mpd_ref
        was_playing = False

        if pause_mpd and mpd and \
           mpd.state == "play":
            was_playing = True
            mpd.pause()
            time.sleep(1.5)

        _do_speak(text)

        if was_playing and resume and mpd and \
           mpd.state == "pause":
            time.sleep(0.2)
            mpd.resume()

    threading.Thread(target=_run, daemon=True).start()

def stop():
    global _current
    if _current and _current.poll() is None:
        _current.terminate()

def preload():
    pass

import os
import subprocess
import threading
import time
import glob

MUSIC_DIR    = "/home/pi/music"
MPD_USB_NAME = "usb0"
MPD_USB_PATH = os.path.join(MUSIC_DIR, MPD_USB_NAME)

AUDIO_EXTS   = {".mp3", ".wav", ".flac",
                ".aac", ".ogg", ".m4a", ".m4b",
                ".mp4"}

class USBManager:
    def __init__(self, mpd_client):
        self.mpd          = mpd_client
        self.current_path = None
        self.drives       = []
        self._running     = True
        self._lock        = threading.Lock()
        self._on_change   = None

    def set_callback(self, fn):
        self._on_change = fn

    def _get_media_paths(self):
        """Dynamically find all /media/usbX paths"""
        paths = []
        # Check /media/usbX
        for path in sorted(glob.glob("/media/usb*")):
            paths.append(path)
        # Check /media/pi/X
        pi_media = "/media/pi"
        if os.path.isdir(pi_media):
            try:
                for sub in sorted(
                        os.listdir(pi_media)):
                    paths.append(
                        os.path.join(pi_media, sub))
            except: pass
        return paths

    def _find_audio_mount(self):
        """Find mounted path containing audio"""
        for path in self._get_media_paths():
            if not os.path.isdir(path): continue
            if not os.path.ismount(path): continue
            if self._has_audio(path):
                return path
        return None

    def _has_audio(self, path, depth=0):
        if depth > 4: return False
        try:
            for entry in os.listdir(path):
                if entry.startswith("."): continue
                if entry == \
                   "System Volume Information":
                    continue
                full = os.path.join(path, entry)
                if os.path.isfile(full):
                    ext = os.path.splitext(
                        entry)[1].lower()
                    if ext in AUDIO_EXTS:
                        return True
                elif os.path.isdir(full):
                    if self._has_audio(
                            full, depth+1):
                        return True
        except: pass
        return False

    def _current_symlink_target(self):
        if os.path.islink(MPD_USB_PATH):
            return os.readlink(MPD_USB_PATH)
        return None

    def _link_to_mpd(self, mount_path):
        try:
            current = self._current_symlink_target()
            if current == mount_path:
                return True

            # Remove whatever is there
            if os.path.islink(MPD_USB_PATH):
                os.unlink(MPD_USB_PATH)
            elif os.path.ismount(MPD_USB_PATH):
                subprocess.run(
                    ["sudo", "umount",
                     MPD_USB_PATH],
                    capture_output=True)
            elif os.path.isdir(MPD_USB_PATH):
                try: os.rmdir(MPD_USB_PATH)
                except: pass

            os.symlink(mount_path, MPD_USB_PATH)
            print(f"Linked {mount_path} -> "
                  f"{MPD_USB_PATH}")
            return True
        except Exception as e:
            print(f"Link error: {e}")
            return False

    def _unlink_mpd(self):
        try:
            if os.path.islink(MPD_USB_PATH):
                os.unlink(MPD_USB_PATH)
                print("Symlink removed")
        except Exception as e:
            print(f"Unlink error: {e}")

    def _update_mpd(self):
        try:
            time.sleep(1)
            self.mpd.update_library()
            time.sleep(3)
        except: pass

    def _get_label(self, mount_path):
        try:
            r = subprocess.run(
                ["lsblk", "-o",
                 "MOUNTPOINT,LABEL"],
                capture_output=True, text=True,
                timeout=2)
            for line in r.stdout.split("\n"):
                if mount_path in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
        except: pass
        return os.path.basename(mount_path)

    def scan_once(self):
        mount = self._find_audio_mount()
        drives = [{
            "path":  mount,
            "label": self._get_label(mount),
            "rel":   MPD_USB_NAME,
        }] if mount else []

        with self._lock:
            self.drives = drives
            if mount != self.current_path:
                self.current_path = mount
                if mount:
                    print(f"USB found: {mount}")
                    self._link_to_mpd(mount)
                    self._update_mpd()
                else:
                    print("USB not found")
                    self._unlink_mpd()
                    self._update_mpd()
                if self._on_change:
                    self._on_change(drives)
            else:
                if mount:
                    self._link_to_mpd(mount)
        return drives

    def update_mpd(self):
        self._update_mpd()

    def start_monitor(self):
        def _monitor():
            last_mount = self.current_path
            while self._running:
                try:
                    mount = self._find_audio_mount()
                    symlink_wrong = (
                        mount and
                        self._current_symlink_target()
                        != mount)

                    if mount != last_mount or \
                       symlink_wrong:
                        print(f"USB: "
                              f"{last_mount} -> "
                              f"{mount}")
                        prev_mount = last_mount
                        last_mount = mount
                        with self._lock:
                            self.current_path = mount
                        if mount:
                            self._link_to_mpd(mount)
                            self._update_mpd()
                            drives = [{
                                "path":  mount,
                                "label": self._get_label(mount),
                                "rel":   MPD_USB_NAME,
                            }]
                        else:
                            self._unlink_mpd()
                            self._update_mpd()
                            drives = []
                        with self._lock:
                            self.drives = drives
                        # Only callback on actual
                        # mount change not relinks
                        if mount != prev_mount:
                            if self._on_change:
                                self._on_change(
                                    drives)
                except Exception as e:
                    print(f"USB error: {e}")
                time.sleep(3)

        threading.Thread(
            target=_monitor, daemon=True).start()

    def stop(self):
        self._running = False

import mpd
import threading
import time
import os

class MPDClient:
    def __init__(self):
        self.client       = mpd.MPDClient()
        self.lock         = threading.Lock()
        self.connected    = False
        self.state        = "stop"
        self.elapsed      = 0.0
        self.duration     = 0.0
        self.volume       = 80
        self.track_num    = 0
        self.track_total  = 0
        self.current_file = ""
        self.title        = "---"
        self.book         = "---"
        self._connect()
        self._start_poll()

    def _connect(self):
        try:
            self.client.connect("localhost", 6600)
            self.client.timeout = 3
            self.connected = True
            print("MPD connected")
        except mpd.base.ConnectionError:
            self.connected = True
        except Exception as e:
            print(f"MPD connect failed: {e}")
            self.connected = False

    def _poll(self):
        while True:
            try:
                with self.lock:
                    if not self.connected:
                        try:
                            self.client.connect(
                                "localhost", 6600)
                            self.client.timeout = 3
                            self.connected = True
                            print("MPD reconnected")
                        except mpd.base.ConnectionError:
                            self.connected = True
                        except Exception as e:
                            print(f"Reconnect: {e}")
                            time.sleep(5)
                            continue

                    status  = self.client.status()
                    current = self.client.currentsong()
                    self.state    = status.get(
                        "state", "stop")
                    self.elapsed  = float(
                        status.get("elapsed", 0))
                    self.duration = float(
                        status.get("duration", 0))
                    self.volume   = int(
                        status.get("volume", 80))
                    pos  = status.get("song")
                    plen = status.get(
                        "playlistlength", "0")
                    self.track_num   = \
                        int(pos) + 1 if pos else 0
                    self.track_total = int(plen)
                    cf = current.get("file", "")
                    self.current_file = cf
                    parts = cf.split("/")
                    if len(parts) >= 2:
                        self.book = \
                            "/".join(parts[:-1])
                    else:
                        self.book = ""
                    fname = os.path.splitext(
                        os.path.basename(cf))[0]
                    self.title = \
                        current.get("title") or fname

            except mpd.base.ConnectionError:
                self.connected = True
            except Exception as e:
                print(f"Poll error: {e}")
                self.connected = False
                try:    self.client.disconnect()
                except: pass

            time.sleep(1)

    def _start_poll(self):
        threading.Thread(
            target=self._poll, daemon=True).start()

    def _cmd(self, fn, *args):
        try:
            with self.lock:
                if not self.connected: return None
                return fn(*args)
        except mpd.base.CommandError as e:
            print(f"MPD cmd error: {e}")
            return None
        except Exception as e:
            print(f"MPD cmd error: {e}")
            self.connected = False
            return None

    def play(self):
        self._cmd(self.client.play)
    def pause(self):
        self._cmd(self.client.pause, 1)
    def resume(self):
        self._cmd(self.client.pause, 0)
    def next_track(self):
        self._cmd(self.client.next)
    def prev_track(self):
        self._cmd(self.client.previous)
    def update_library(self):
        self._cmd(self.client.update)

    def toggle(self):
        if self.state == "play":
            self.pause()
        elif self.state == "pause":
            self.resume()
        else:
            self.play()

    def seek_forward(self, secs=30):
        if self.state not in ("play", "pause"):
            return
        target = min(self.elapsed + secs,
                     self.duration - 1)
        self._cmd(self.client.seekcur, str(target))

    def seek_back(self, secs=30):
        if self.state not in ("play", "pause"):
            return
        target = max(self.elapsed - secs, 0)
        self._cmd(self.client.seekcur, str(target))

    def seek_to(self, secs):
        if self.state not in ("play", "pause"):
            return
        self._cmd(self.client.seekcur,
                  str(max(0, secs)))

    def set_volume(self, vol):
        vol = max(0, min(100, vol))
        self._cmd(self.client.setvol, vol)

    def get_books(self):
        try:
            with self.lock:
                if not self.connected: return []
                books = []

                def scan(path, depth):
                    try:
                        contents = \
                            self.client.lsinfo(path) \
                            if path else \
                            self.client.lsinfo()
                        subdirs = [
                            x for x in contents
                            if "directory" in x]
                        audiofiles = [
                            x for x in contents
                            if "file" in x]
                        if audiofiles:
                            books.append(
                                path if path else "")
                        elif subdirs and depth < 3:
                            for sub in subdirs:
                                scan(
                                    sub["directory"],
                                    depth + 1)
                    except: pass

                scan("", 0)
                books = [b for b in books
                         if "System Volume"
                         not in b]
                return sorted(books)
        except Exception as e:
            print(f"get_books error: {e}")
            return []

    def get_chapters(self, book):
        try:
            c = mpd.MPDClient()
            c.connect("localhost", 6600)
            c.timeout = 5
            files    = c.lsinfo(book)
            chapters = []
            for item in files:
                if "file" in item:
                    fname = os.path.basename(
                        item["file"])
                    ext = fname.rsplit(
                        ".", 1)[-1].lower()
                    if ext in ("mp3", "wav", "flac",
                               "aac", "ogg",
                               "m4a", "m4b"):
                        chapters.append(fname)
            c.disconnect()
            return sorted(chapters)
        except Exception as e:
            print(f"get_chapters error: {e}")
            return []

    def play_book(self, book,
                  chapter=None, position=0.0):
        try:
            c = mpd.MPDClient()
            c.connect("localhost", 6600)
            c.timeout = 5
            c.clear()
            c.add(book)
            if chapter:
                playlist = c.playlistinfo()
                for i, item in enumerate(playlist):
                    if os.path.basename(
                            item["file"]) == chapter:
                        c.play(i)
                        if position > 0:
                            c.seekcur(str(position))
                        c.disconnect()
                        return True
            c.play()
            if position > 0:
                c.seekcur(str(position))
            c.disconnect()
            return True
        except Exception as e:
            print(f"play_book error: {e}")
            return False

    def play_chapter(self, book, chapter):
        try:
            c = mpd.MPDClient()
            c.connect("localhost", 6600)
            c.timeout = 5
            playlist = c.playlistinfo()
            for i, item in enumerate(playlist):
                if os.path.basename(
                        item["file"]) == chapter:
                    c.play(i)
                    c.disconnect()
                    return
            c.clear()
            c.add(book)
            c.play()
            playlist = c.playlistinfo()
            for i, item in enumerate(playlist):
                if os.path.basename(
                        item["file"]) == chapter:
                    c.play(i)
                    break
            c.disconnect()
        except Exception as e:
            print(f"play_chapter error: {e}")

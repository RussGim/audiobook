import subprocess
import threading
import time

class BluetoothManager:
    def __init__(self):
        self.devices        = []
        self.scanning       = False
        self.connected_mac  = None
        self.connected_name = None

    def get_status(self):
        try:
            r = subprocess.run(
                ["bluetoothctl", "info"],
                capture_output=True, text=True,
                timeout=3)
            if "Connected: yes" in r.stdout:
                name = "Unknown"
                for line in r.stdout.split("\n"):
                    if "Name:" in line:
                        name = line.split(
                            "Name:")[1].strip()
                self.connected_name = name
                return True
            self.connected_mac  = None
            self.connected_name = None
            return False
        except:
            return False

    def scan(self, callback=None):
        def _scan():
            self.scanning = True
            self.devices  = []
            try:
                subprocess.run(
                    ["bluetoothctl", "scan", "on"],
                    capture_output=True, timeout=2)
                time.sleep(8)
                subprocess.run(
                    ["bluetoothctl", "scan", "off"],
                    capture_output=True, timeout=2)
                r = subprocess.run(
                    ["bluetoothctl", "devices"],
                    capture_output=True, text=True,
                    timeout=3)
                devices = []
                for line in r.stdout.strip().split("\n"):
                    if "Device" in line:
                        parts = line.split(" ", 2)
                        if len(parts) >= 3:
                            devices.append({
                                "mac":  parts[1],
                                "name": parts[2]
                            })
                self.devices = devices
            except Exception as e:
                print(f"BT scan error: {e}")
            finally:
                self.scanning = False
                if callback: callback(self.devices)
        threading.Thread(
            target=_scan, daemon=True).start()

    def pair(self, mac, callback=None):
        def _pair():
            try:
                r = subprocess.run(
                    ["bluetoothctl", "pair", mac],
                    capture_output=True, text=True,
                    timeout=15)
                success = (
                    "Pairing successful" in r.stdout or
                    "Already paired" in r.stdout)
                if success:
                    subprocess.run(
                        ["bluetoothctl", "trust", mac],
                        capture_output=True, timeout=5)
                if callback: callback(success)
            except Exception as e:
                print(f"BT pair error: {e}")
                if callback: callback(False)
        threading.Thread(
            target=_pair, daemon=True).start()

    def connect(self, mac, callback=None):
        def _connect():
            try:
                r = subprocess.run(
                    ["bluetoothctl", "connect", mac],
                    capture_output=True, text=True,
                    timeout=10)
                success = (
                    "Connection successful" in r.stdout
                    or "Already connected" in r.stdout)
                if success:
                    self.connected_mac = mac
                    r2 = subprocess.run(
                        ["bluetoothctl", "info", mac],
                        capture_output=True, text=True,
                        timeout=3)
                    for line in r2.stdout.split("\n"):
                        if "Name:" in line:
                            self.connected_name = \
                                line.split(
                                    "Name:")[1].strip()
                if callback: callback(success)
            except Exception as e:
                print(f"BT connect error: {e}")
                if callback: callback(False)
        threading.Thread(
            target=_connect, daemon=True).start()

    def disconnect(self, callback=None):
        def _disconnect():
            try:
                if self.connected_mac:
                    subprocess.run(
                        ["bluetoothctl", "disconnect",
                         self.connected_mac],
                        capture_output=True, timeout=5)
                self.connected_mac  = None
                self.connected_name = None
                if callback: callback(True)
            except Exception as e:
                print(f"BT disconnect error: {e}")
                if callback: callback(False)
        threading.Thread(
            target=_disconnect, daemon=True).start()

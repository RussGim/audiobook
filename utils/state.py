import json
import os

STATE_FILE = "/home/pi/audiobook/.state.json"

_defaults = {
    "book":             None,
    "chapter":          None,
    "position":         0.0,
    "volume":           80,
    "speed":            1.0,
    "brightness":       80,
    "clock_12h":        False,
    "player_size":      "normal",
    "confirm_tap":      False,
    "bt_device":        None,
    "bt_name":          None,
    "chapter_announce": True,
    "voice_prompts":    True,
}

def load():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                # migrate old large_screen bool
                if "large_screen" in data and \
                   "player_size" not in data:
                    data["player_size"] = \
                        "large" if data["large_screen"] \
                        else "normal"
                return {**_defaults, **data}
        except:
            pass
    return dict(_defaults)

def save(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"State save error: {e}")

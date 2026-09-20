import json
import os
import sys


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(_base_dir(), "config.json")

DEFAULT_CONFIG = {
    "window_width": 900,
    "window_height": 650,
    "board_size": 10,
    "ship_count": 10,
    "difficulty": "medium",
    "cell_size": 32,
    "font_family": "Arial",
    "font_size": 11,
    "bg_color": "#002a71",
    "ship_color": "#2d2d2d",
    "hit_color": "#e52636",
    "miss_color": "#dfe7f5",
    "player_name": "Игрок",
}

STANDARD_FLEET = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
        except (json.JSONDecodeError, OSError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def fleet_for_count(ship_count):
    ship_count = max(1, min(ship_count, len(STANDARD_FLEET)))
    return STANDARD_FLEET[:ship_count]

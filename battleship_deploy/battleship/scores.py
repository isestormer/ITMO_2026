import json
import os
from datetime import datetime

from config import _base_dir

SCORES_PATH = os.path.join(_base_dir(), "scores.json")


def load_scores():
    if os.path.exists(SCORES_PATH):
        try:
            with open(SCORES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_scores(scores):
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)


def add_result(name, result, moves):
    scores = load_scores()
    scores.append({
        "name": name,
        "result": result,
        "moves": moves,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_scores(scores)


def best_scores(limit=10):
    scores = load_scores()
    wins = [s for s in scores if s["result"] == "win"]
    wins.sort(key=lambda s: s["moves"])
    return wins[:limit]

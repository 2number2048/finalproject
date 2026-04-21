import os

HIGHSCORE_FILE = 'highscore.txt'

def load_high_score():
    try:
        if not os.path.exists(HIGHSCORE_FILE):
            return 0
        with open(HIGHSCORE_FILE, 'r') as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0

def save_high_score(score):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(int(score)))
    except Exception:
        pass

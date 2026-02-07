import os

WIDTH, HEIGHT = 800, 600
FPS = 60
TITLE = "Galaxy Fury"

BASE_DIR = os.path.dirname(__file__)
ASSET_DIR = os.path.join(BASE_DIR, "assets")
HISCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

DEFAULT_SFX_VOLUME = 0.45
DEFAULT_MUSIC_VOLUME = 0.35

HUD_COLOR = (245, 235, 200)
ENEMY_BULLET_COLOR = (255, 90, 60)
PLAYER_BULLET_COLOR = (255, 230, 120)

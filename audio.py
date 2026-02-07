import os
import math
from array import array
import random
import pygame

from config import ASSET_DIR, DEFAULT_SFX_VOLUME, DEFAULT_MUSIC_VOLUME
from utils import make_beep, make_melody


def load_sound(name):
    path = os.path.join(ASSET_DIR, name)
    try:
        sfx = pygame.mixer.Sound(path)
        return sfx
    except Exception:
        return None


def load_music(name):
    path = os.path.join(ASSET_DIR, name)
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            return True
        except Exception:
            return False
    return False


def make_engine_loop(freq=70, duration=0.6, volume=0.22, sample_rate=22050):
    n = int(duration * sample_rate)
    buf = array("h")
    amp = int(32767 * volume)
    for i in range(n):
        t = i / sample_rate
        wobble = 1.0 + 0.15 * math.sin(2 * math.pi * 2.2 * t)
        val = math.sin(2 * math.pi * freq * t) * 0.65
        val += math.sin(2 * math.pi * (freq * 2.1) * t) * 0.25
        val += (random.random() * 2 - 1) * 0.08
        val *= wobble
        buf.append(int(val * amp))
    return pygame.mixer.Sound(buffer=buf)


def make_gun_burst():
    return make_beep(820, 0.06, 0.35, waveform="square")


def make_explosion():
    return make_beep(120, 0.22, 0.38, waveform="triangle")


class AudioManager:
    def __init__(self, audio_ok):
        self.audio_ok = audio_ok
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.music_volume = DEFAULT_MUSIC_VOLUME
        self.sfx_pew = None
        self.sfx_boom = None
        self.sfx_power = None
        self.sfx_boss = None
        self.sfx_gameover = None
        self.engine_loop = None
        self.bgm_sound = None

    def init(self):
        if not self.audio_ok:
            return
        sr = pygame.mixer.get_init()[0] if pygame.mixer.get_init() else 22050
        self.sfx_pew = load_sound("pew.ogg") or make_gun_burst()
        self.sfx_boom = load_sound("boom.ogg") or make_explosion()
        self.sfx_power = load_sound("powerup.ogg") or make_beep(520, 0.12, 0.30, sample_rate=sr)
        self.sfx_boss = load_sound("boss_enter.ogg") or make_beep(180, 0.45, 0.30, sample_rate=sr)
        self.sfx_gameover = load_sound("gameover.ogg") or make_beep(110, 0.60, 0.30, sample_rate=sr)
        self.engine_loop = load_sound("engine_loop.ogg")
        self.apply_volumes()

    def apply_volumes(self):
        for sfx in (self.sfx_pew, self.sfx_boom, self.sfx_power, self.sfx_boss, self.sfx_gameover, self.engine_loop):
            if sfx:
                sfx.set_volume(self.sfx_volume)

    def play_bgm(self, level):
        track = f"level{level}_bgm.ogg"
        if self.audio_ok and load_music(track):
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.bgm_sound = None
            return
        if not self.audio_ok:
            return
        if level == 1:
            seq = [(392, 1), (0, 0.5), (494, 0.5), (587, 1), (740, 0.5), (0, 0.5)]
        elif level == 2:
            seq = [(330, 1), (392, 0.5), (440, 0.5), (392, 1), (330, 0.5), (0, 0.5)]
        else:
            seq = [(262, 1), (330, 0.5), (392, 0.5), (523, 1), (392, 0.5), (0, 0.5)]
        self.bgm_sound = make_melody(seq, bpm=135, volume=0.20, waveform="square")
        self.bgm_sound.set_volume(self.music_volume)
        self.bgm_sound.play(-1)

    def stop_bgm(self):
        if self.audio_ok:
            pygame.mixer.music.stop()
        if self.bgm_sound:
            self.bgm_sound.stop()
            self.bgm_sound = None

    def start_engine(self):
        if self.engine_loop:
            self.engine_loop.set_volume(self.sfx_volume)
            self.engine_loop.play(-1)

    def stop_engine(self):
        if self.engine_loop:
            self.engine_loop.stop()

    def set_sfx_volume(self, value):
        self.sfx_volume = max(0.0, min(1.0, value))
        self.apply_volumes()

    def set_music_volume(self, value):
        self.music_volume = max(0.0, min(1.0, value))
        if self.bgm_sound:
            self.bgm_sound.set_volume(self.music_volume)
        pygame.mixer.music.set_volume(self.music_volume)

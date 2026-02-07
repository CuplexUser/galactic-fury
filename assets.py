import os
import math
import random
import wave
import struct
import pygame

from config import ASSET_DIR
from sprites import SpriteFactory


def _write_wav(path, samples, sample_rate=22050):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(struct.pack("<h", s) for s in samples))


def _sine_samples(freq, duration, volume=0.5, sample_rate=22050):
    n = int(duration * sample_rate)
    amp = int(32767 * volume)
    return [int(math.sin(2 * math.pi * freq * (i / sample_rate)) * amp) for i in range(n)]


def _noise_samples(duration, volume=0.5, sample_rate=22050):
    n = int(duration * sample_rate)
    amp = int(32767 * volume)
    return [int((random.random() * 2 - 1) * amp) for _ in range(n)]


def _engine_samples(duration=0.6, sample_rate=22050):
    n = int(duration * sample_rate)
    amp = int(32767 * 0.35)
    samples = []
    for i in range(n):
        t = i / sample_rate
        wobble = 1.0 + 0.15 * math.sin(2 * math.pi * 2.2 * t)
        val = math.sin(2 * math.pi * 70 * t) * 0.65
        val += math.sin(2 * math.pi * 145 * t) * 0.25
        val += (random.random() * 2 - 1) * 0.08
        val *= wobble
        samples.append(int(val * amp))
    return samples


def _save_png(path, surface):
    pygame.image.save(surface, path)


def ensure_assets():
    os.makedirs(ASSET_DIR, exist_ok=True)

    # Sprites
    sprite_map = {
        "player.png": SpriteFactory.player_frames()[0],
        "enemy_basic.png": SpriteFactory.enemy_sprite("basic"),
        "enemy_kamikaze.png": SpriteFactory.enemy_sprite("kamikaze"),
        "enemy_shielded.png": SpriteFactory.enemy_sprite("shielded"),
        "boss.png": SpriteFactory.boss_sprite(1),
    }
    for name, surf in sprite_map.items():
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            _save_png(path, surf)

    # Basic powerup icons
    powerups = {
        "powerup_speed.png": ("speed", (255, 140, 0)),
        "powerup_triple.png": ("triple", (100, 200, 255)),
        "powerup_shield.png": ("shield", (120, 255, 120)),
    }
    for name, (_, color) in powerups.items():
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (10, 10), 9)
            pygame.draw.circle(surf, (30, 30, 30), (10, 10), 9, 2)
            _save_png(path, surf)

    # Audio
    wavs = {
        "pew.wav": _sine_samples(860, 0.08, 0.4),
        "boom.wav": _noise_samples(0.25, 0.45),
        "powerup.wav": _sine_samples(640, 0.12, 0.35),
        "boss_enter.wav": _sine_samples(180, 0.45, 0.35),
        "gameover.wav": _sine_samples(120, 0.7, 0.35),
        "engine_loop.wav": _engine_samples(),
    }
    for name, samples in wavs.items():
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            _write_wav(path, samples)

    # Simple BGM stubs
    for level, freq in [(1, 392), (2, 330), (3, 262)]:
        path = os.path.join(ASSET_DIR, f"level{level}_bgm.wav")
        if not os.path.exists(path):
            samples = _sine_samples(freq, 1.2, 0.25)
            _write_wav(path, samples)

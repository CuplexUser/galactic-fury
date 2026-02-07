import math
from array import array
import pygame

from config import HISCORE_FILE


def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))


def sprite_from_map(map_data, palette, scale=3):
    width = max(len(row) for row in map_data)
    height = len(map_data)
    surf = pygame.Surface((width * scale, height * scale), pygame.SRCALPHA)
    for y, row in enumerate(map_data):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            color = palette.get(ch, (255, 255, 255))
            pygame.draw.rect(surf, color, (x * scale, y * scale, scale, scale))
    return surf


def read_hiscore():
    try:
        with open(HISCORE_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def write_hiscore(score):
    try:
        with open(HISCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(score))
    except Exception:
        pass


def make_beep(freq, duration=0.12, volume=0.5, waveform="sine", sample_rate=22050):
    n = int(duration * sample_rate)
    buf = array("h")
    amp = int(32767 * volume)
    for i in range(n):
        t = i / sample_rate
        val = math.sin(2 * math.pi * freq * t)
        if waveform == "triangle":
            val = 2.0 * abs(2 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
        if waveform == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        env = 1.0
        if t < 0.01:
            env = t / 0.01
        elif t > duration - 0.04:
            env = max(0.0, (duration - t) / 0.04)
        val *= env
        buf.append(int(val * amp))
    return pygame.mixer.Sound(buffer=buf)


def make_melody(sequence, bpm=120, volume=0.25, sample_rate=22050, waveform="sine"):
    beat = 60 / bpm
    buf = array("h")
    amp = int(32767 * volume)
    for freq, beats in sequence:
        n = int(beat * beats * sample_rate)
        for i in range(n):
            if freq == 0:
                buf.append(0)
                continue
            t = i / sample_rate
            if waveform == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            else:
                val = math.sin(2 * math.pi * freq * t)
            buf.append(int(val * amp))
    return pygame.mixer.Sound(buffer=buf)

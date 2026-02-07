import random
import os
import pygame

from config import WIDTH, HEIGHT
from config import ASSET_DIR


class Background:
    def __init__(self):
        self.bg_image = None
        bg_path = os.path.join(ASSET_DIR, "background.png")
        if os.path.exists(bg_path):
            try:
                img = pygame.image.load(bg_path).convert()
                if img.get_width() != WIDTH or img.get_height() != HEIGHT:
                    img = pygame.transform.scale(img, (WIDTH, HEIGHT))
                self.bg_image = img
            except Exception:
                self.bg_image = None
        self.wave_offset = 0
        self.clouds = [
            [random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(40, 90), random.uniform(10, 30)]
            for _ in range(6)
        ]
        self.islands = [
            [random.randint(40, WIDTH - 60), random.randint(-HEIGHT, HEIGHT), random.randint(30, 80)]
            for _ in range(5)
        ]

    def update(self, dt):
        self.wave_offset = (self.wave_offset + 80 * dt) % 20
        for cloud in self.clouds:
            cloud[1] += cloud[3] * dt
            if cloud[1] > HEIGHT + 80:
                cloud[0] = random.randint(0, WIDTH)
                cloud[1] = -80
        for island in self.islands:
            island[1] += 40 * dt
            if island[1] > HEIGHT + 60:
                island[0] = random.randint(40, WIDTH - 60)
                island[1] = random.randint(-HEIGHT, -40)

    def draw(self, surface, level):
        if self.bg_image:
            img_h = self.bg_image.get_height()
            scroll = int(self.wave_offset * 4) % img_h
            for y in (-img_h + scroll, scroll, img_h + scroll):
                surface.blit(self.bg_image, (0, y))
        else:
            if level == 1:
                surface.fill((12, 12, 24))
            elif level == 2:
                surface.fill((10, 10, 26))
            else:
                surface.fill((8, 8, 22))

        if not self.bg_image:
            for y in range(-20, HEIGHT + 20, 20):
                offset = int(self.wave_offset + (y % 40) * 0.2)
                pygame.draw.line(surface, (40, 60, 120), (0, y + offset), (WIDTH, y + offset), 1)

        if not self.bg_image:
            for x, y, r in self.islands:
                pygame.draw.circle(surface, (30, 40, 80), (x, int(y)), r)
                pygame.draw.circle(surface, (50, 60, 110), (x + int(r * 0.2), int(y - r * 0.1)), int(r * 0.7))

        if not self.bg_image:
            for x, y, r, _ in self.clouds:
                pygame.draw.circle(surface, (140, 150, 190), (int(x), int(y)), int(r * 0.7))
                pygame.draw.circle(surface, (170, 180, 210), (int(x + r * 0.5), int(y)), int(r * 0.55))

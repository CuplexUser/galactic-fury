import random
import pygame

from config import WIDTH, HEIGHT


class Background:
    def __init__(self):
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
        if level == 1:
            surface.fill((20, 80, 150))
        elif level == 2:
            surface.fill((18, 60, 120))
        else:
            surface.fill((16, 50, 90))

        for y in range(-20, HEIGHT + 20, 20):
            offset = int(self.wave_offset + (y % 40) * 0.2)
            pygame.draw.line(surface, (40, 110, 180), (0, y + offset), (WIDTH, y + offset), 2)

        for x, y, r in self.islands:
            pygame.draw.circle(surface, (40, 90, 50), (x, int(y)), r)
            pygame.draw.circle(surface, (60, 120, 70), (x + int(r * 0.2), int(y - r * 0.1)), int(r * 0.7))

        for x, y, r, _ in self.clouds:
            pygame.draw.circle(surface, (220, 230, 240), (int(x), int(y)), int(r * 0.7))
            pygame.draw.circle(surface, (240, 245, 250), (int(x + r * 0.5), int(y)), int(r * 0.55))

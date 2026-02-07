import math
import random
import os
import pygame

from config import WIDTH, HEIGHT, PLAYER_BULLET_COLOR, ASSET_DIR
from utils import clamp
from sprites import SpriteFactory


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=-520, color=PLAYER_BULLET_COLOR, damage=1, vx=0, vy=None):
        super().__init__()
        self.image = pygame.Surface((4, 12))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.damage = damage
        self.vx = vx
        self.vy = vy

    def update(self, dt):
        if self.vy is None:
            self.rect.y += int(self.speed * dt)
        else:
            self.rect.x += int(self.vx * dt)
            self.rect.y += int(self.vy * dt)
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, lifespan=0.6):
        super().__init__()
        self.image = pygame.Surface((3, 3), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-90, 90)
        self.vy = random.uniform(-140, 140)
        self.lifespan = lifespan

    def update(self, dt):
        self.lifespan -= dt
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)
        if self.lifespan <= 0:
            self.kill()


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, x, y, size=26):
        super().__init__()
        self.size = size
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (110, 85, 60), (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, (90, 70, 50), (size // 3, size // 3), size // 6)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = random.randint(90, 150)
        self.drift = random.randint(-40, 40)

    def update(self, dt):
        self.rect.y += int(self.speed * dt)
        self.rect.x += int(self.drift * dt)
        if self.rect.top > HEIGHT + 40:
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    TYPES = ["speed", "triple", "shield"]

    def __init__(self, x, y, ptype):
        super().__init__()
        self.ptype = ptype
        png_path = os.path.join(ASSET_DIR, f"powerup_{ptype}.png")
        if os.path.exists(png_path):
            try:
                self.image = pygame.image.load(png_path).convert_alpha()
            except Exception:
                self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        else:
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        if self.image.get_width() == 20:
            color = (255, 215, 0)
            if ptype == "speed":
                color = (255, 140, 0)
            elif ptype == "triple":
                color = (100, 200, 255)
            elif ptype == "shield":
                color = (120, 255, 120)
            pygame.draw.circle(self.image, color, (10, 10), 9)
            pygame.draw.circle(self.image, (30, 30, 30), (10, 10), 9, 2)
            if ptype == "speed":
                pygame.draw.polygon(self.image, (30, 30, 30), [(7, 6), (14, 10), (7, 14)])
            elif ptype == "triple":
                for dx in (-4, 0, 4):
                    pygame.draw.line(self.image, (30, 30, 30), (10 + dx, 5), (10 + dx, 15), 2)
            elif ptype == "shield":
                pygame.draw.rect(self.image, (30, 30, 30), (7, 6, 6, 10), 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 160

    def update(self, dt):
        self.rect.y += int(self.speed * dt)
        if self.rect.top > HEIGHT:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.frames = SpriteFactory.player_frames()
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        self.speed = 300
        self.lives = 3
        self.shield = 0
        self.shoot_cooldown = 0
        self.triple_shot = 0
        self.invuln = 0
        self.anim_timer = 0

    def update(self, dt, keys):
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed
        self.rect.x += int(dx * dt)
        self.rect.y += int(dy * dt)
        self.rect.x = clamp(self.rect.x, 0, WIDTH - self.rect.width)
        self.rect.y = clamp(self.rect.y, 0, HEIGHT - self.rect.height)
        self.shoot_cooldown = max(0, self.shoot_cooldown - dt)
        self.triple_shot = max(0, self.triple_shot - dt)
        self.invuln = max(0, self.invuln - dt)
        self.shield = max(0, self.shield - dt)
        self.anim_timer += dt
        if self.anim_timer > 0.12:
            self.anim_timer = 0
            self.image = self.frames[1] if self.image == self.frames[0] else self.frames[0]

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self):
        self.shoot_cooldown = 0.14

    def hit(self):
        if self.invuln > 0:
            return False
        if self.shield > 0:
            self.shield = 0
            self.invuln = 1.0
            return False
        self.lives -= 1
        self.invuln = 1.6
        return True


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, etype, level):
        super().__init__()
        self.etype = etype
        self.level = level
        self.hp = 1
        self.speed = 95 + level * 8
        self.zig_phase = random.uniform(0, math.tau)
        self.kamikaze = False
        self.score_value = 10

        if etype == "basic":
            self.image = SpriteFactory.enemy_sprite("basic")
            self.hp = 1
            self.score_value = 10
        elif etype == "kamikaze":
            self.image = SpriteFactory.enemy_sprite("kamikaze")
            self.hp = 1
            self.kamikaze = True
            self.score_value = 20
        elif etype == "shielded":
            self.image = SpriteFactory.enemy_sprite("shielded")
            self.hp = 3
            self.score_value = 20

        self.rect = self.image.get_rect(center=(x, y))
        self.dive_target = None
        self.pattern = None
        self.pattern_data = {}
        self.age = 0.0

    def set_pattern(self, pattern, **kwargs):
        self.pattern = pattern
        self.pattern_data = kwargs

    def update(self, dt, player=None):
        self.age += dt
        if self.etype == "kamikaze" and player:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            self.rect.x += int((dx / dist) * self.speed * 1.05 * dt)
            self.rect.y += int((dy / dist) * self.speed * 1.05 * dt)
        elif self.pattern == "arc":
            start_x = self.pattern_data.get("start_x", self.rect.x)
            amp = self.pattern_data.get("amp", 120)
            freq = self.pattern_data.get("freq", 1.2)
            phase = self.pattern_data.get("phase", 0.0)
            self.rect.y += int(self.speed * dt)
            self.rect.x = int(start_x + math.sin(self.age * freq + phase) * amp)
        elif self.pattern == "zig":
            start_x = self.pattern_data.get("start_x", self.rect.x)
            amp = self.pattern_data.get("amp", 140)
            freq = self.pattern_data.get("freq", 2.4)
            phase = self.pattern_data.get("phase", 0.0)
            self.rect.y += int(self.speed * dt)
            self.rect.x = int(start_x + math.sin(self.age * freq + phase) * amp)
        elif self.pattern == "v":
            direction = self.pattern_data.get("direction", 1)
            vx = self.pattern_data.get("vx", 90)
            self.rect.y += int(self.speed * dt)
            self.rect.x += int(direction * vx * dt)
        elif self.pattern == "stagger":
            delay = self.pattern_data.get("delay", 0.0)
            speed_mul = 0.3 if self.age < delay else 1.0
            self.rect.y += int(self.speed * speed_mul * dt)
        elif self.pattern == "escort_lead":
            start_x = self.pattern_data.get("start_x", self.rect.x)
            phase = self.pattern_data.get("phase", 0.0)
            self.rect.y += int(self.speed * dt)
            self.rect.x = int(start_x + math.sin(self.age * 1.2 + phase) * 20)
        elif self.pattern == "escort_wing":
            start_x = self.pattern_data.get("start_x", self.rect.x)
            offset = self.pattern_data.get("offset", 0)
            phase = self.pattern_data.get("phase", 0.0)
            self.rect.y += int(self.speed * dt)
            self.rect.x = int(start_x + offset + math.sin(self.age * 1.5 + phase) * 15)
        elif self.etype == "shielded":
            self.rect.y += int(self.speed * 0.6 * dt)
            self.rect.x += int(math.sin(pygame.time.get_ticks() / 180 + self.zig_phase) * 60 * dt)
        else:
            self.rect.y += int(self.speed * dt)

        if self.rect.top > HEIGHT + 40:
            self.kill()


class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.image = SpriteFactory.boss_sprite(level)
        self.rect = self.image.get_rect(center=(WIDTH // 2, -120))
        self.hp = 200 + (level - 1) * 120
        self.max_hp = self.hp
        self.speed = 70 + level * 20
        self.entering = True
        self.fire_timer = 0
        self.minion_timer = 0
        self.phase = 1
        self.weakpoints = []
        if self.level == 3:
            w, h = self.image.get_width(), self.image.get_height()
            wp_w = int(w * 0.12)
            wp_h = int(h * 0.18)
            self.weakpoints = [
                pygame.Rect(int(w * 0.28), int(h * 0.28), wp_w, wp_h),
                pygame.Rect(int(w * 0.60), int(h * 0.28), wp_w, wp_h),
            ]

    def update(self, dt):
        if self.entering:
            self.rect.y += int(self.speed * dt)
            if self.rect.top >= 40:
                self.entering = False
            return

        self.rect.x += int(math.sin(pygame.time.get_ticks() / 600) * self.speed * dt)

        if self.hp < self.max_hp * 0.5:
            self.phase = 2

    def should_fire(self, dt):
        self.fire_timer += dt
        if self.fire_timer >= (0.4 if self.phase == 2 else 0.6):
            self.fire_timer = 0
            return True
        return False

    def should_spawn_minion(self, dt):
        self.minion_timer += dt
        if self.minion_timer >= (3.0 if self.phase == 1 else 2.0):
            self.minion_timer = 0
            return True
        return False

import sys
import math
import random
import pygame

from config import WIDTH, HEIGHT, FPS, TITLE, HUD_COLOR, ENEMY_BULLET_COLOR
from background import Background
from audio import AudioManager
from utils import read_hiscore, write_hiscore
from entities import Bullet, Particle, Asteroid, PowerUp, Player, Enemy, Boss
from assets import ensure_assets


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.audio_ok = True
        try:
            pygame.mixer.init()
        except Exception:
            self.audio_ok = False
        ensure_assets()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)
        self.big_font = pygame.font.SysFont("Consolas", 40)
        self.scanlines = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 6):
            pygame.draw.line(self.scanlines, (0, 0, 0, 22), (0, y), (WIDTH, y))

        self.audio = AudioManager(self.audio_ok)
        self.audio.init()

        self.state = "MENU"
        self.menu_index = 0
        self.options_index = 0
        self.score = 0
        self.level = 1
        self.level_time = 0
        self.level_duration = 150
        self.hiscore = read_hiscore()
        self.shake = 0

        self.player = Player()
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.life_icon = pygame.transform.scale(self.player.frames[0], (20, 14))
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()

        self.spawn_timer = 0
        self.asteroid_timer = 0
        self.background = Background()
        self.level_transition_timer = 0

    def reset_game(self):
        self.score = 0
        self.level = 1
        self.level_time = 0
        self.player = Player()
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.life_icon = pygame.transform.scale(self.player.frames[0], (20, 14))
        self.enemies.empty()
        self.enemy_bullets.empty()
        self.player_bullets.empty()
        self.powerups.empty()
        self.particles.empty()
        self.asteroids.empty()
        self.boss_group.empty()
        self.spawn_timer = 0
        self.asteroid_timer = 0
        self.background = Background()
        self.level_transition_timer = 0
        self.player.shield = 3
        self.player.triple_shot = 3
        self.state = "PLAYING"
        self.audio.play_bgm(self.level)
        self.audio.start_engine()

    def spawn_formation(self):
        patterns = ["line", "zig", "v", "arc", "stagger", "escort"]
        pattern = random.choice(patterns)
        count = 4 + self.level * 2
        if pattern == "line":
            for i in range(count):
                x = 60 + i * 60 % (WIDTH - 120)
                y = random.randint(-220, -60)
                enemy = Enemy(x, y, "basic", self.level)
                enemy.set_pattern("line")
                self.enemies.add(enemy)
            return
        if pattern == "zig":
            for i in range(count):
                x = 80 + (i % 2) * (WIDTH - 160)
                y = -60 - i * 40
                etype = "kamikaze" if i % 3 == 0 else "basic"
                enemy = Enemy(x, y, etype, self.level)
                enemy.set_pattern("zig", start_x=x, amp=140, freq=2.2, phase=i * 0.6)
                self.enemies.add(enemy)
            return
        if pattern == "v":
            for i in range(count):
                x = WIDTH // 2 + (i - (count // 2)) * 40
                y = -60 - abs(i - (count // 2)) * 20
                direction = -1 if i < (count // 2) else 1
                enemy = Enemy(x, y, "basic", self.level)
                enemy.set_pattern("v", direction=direction, vx=90)
                self.enemies.add(enemy)
            return
        if pattern == "arc":
            for i in range(count):
                t = i / max(1, count - 1)
                x = int(WIDTH * 0.15 + t * WIDTH * 0.7 + math.sin(t * math.pi) * 120)
                y = -80 - int(math.cos(t * math.pi) * 50)
                etype = "basic" if i % 2 == 0 else "shielded"
                enemy = Enemy(x, y, etype, self.level)
                enemy.set_pattern("arc", start_x=x, amp=100, freq=1.1, phase=t * 1.6)
                self.enemies.add(enemy)
            return
        if pattern == "stagger":
            for i in range(count):
                x = random.randint(80, WIDTH - 80)
                y = -80 - i * 45
                etype = "kamikaze" if i % 2 == 0 else "basic"
                enemy = Enemy(x, y, etype, self.level)
                enemy.set_pattern("stagger", delay=i * 0.15)
                self.enemies.add(enemy)
            return
        if pattern == "escort":
            x = random.randint(180, WIDTH - 180)
            y = random.randint(-200, -80)
            lead = Enemy(x, y, "shielded", self.level)
            lead.set_pattern("escort_lead", start_x=x, phase=random.random() * 2)
            left = Enemy(x - 70, y + 40, "basic", self.level)
            left.set_pattern("escort_wing", start_x=x, offset=-70, phase=random.random() * 2)
            right = Enemy(x + 70, y + 40, "basic", self.level)
            right.set_pattern("escort_wing", start_x=x, offset=70, phase=random.random() * 2)
            self.enemies.add(lead, left, right)

    def spawn_enemy_wave(self):
        if self.level_time < 18:
            weights = [0.78, 0.18, 0.04]
        elif self.level_time < 45:
            weights = [0.65, 0.22, 0.13]
        else:
            weights = [0.55, 0.25, 0.20]
        if random.random() < 0.55:
            self.spawn_formation()
            return
        count = 4 + self.level * 2
        types = ["basic", "kamikaze", "shielded"]
        for _ in range(count):
            etype = random.choices(types, weights=weights)[0]
            x = random.randint(40, WIDTH - 40)
            y = random.randint(-200, -40)
            self.enemies.add(Enemy(x, y, etype, self.level))

    def spawn_asteroid(self):
        size = random.randint(20, 40)
        x = random.randint(40, WIDTH - 40)
        y = random.randint(-120, -40)
        self.asteroids.add(Asteroid(x, y, size=size))

    def spawn_boss(self):
        boss = Boss(self.level)
        self.boss_group.add(boss)
        if self.audio.sfx_boss:
            self.audio.sfx_boss.play()

    def spawn_powerup(self, x, y):
        if random.random() < 0.22:
            ptype = random.choice(PowerUp.TYPES)
            self.powerups.add(PowerUp(x, y, ptype))

    def fire_player_bullets(self):
        if not self.player.can_shoot():
            return
        self.player.shoot()
        if self.audio.sfx_pew:
            self.audio.sfx_pew.play()
        x, y = self.player.rect.center
        if self.player.triple_shot > 0:
            for dx in (-14, 0, 14):
                self.player_bullets.add(Bullet(x + dx, y - 15))
        else:
            self.player_bullets.add(Bullet(x, y - 15))

    def fire_enemy_bullet(self, enemy):
        if len(self.enemy_bullets) > 12 + self.level * 6:
            return
        difficulty = min(1.0, self.level_time / 45)
        chance = 0.003 + difficulty * 0.004 + self.level * 0.0015
        if random.random() < chance:
            bullet = Bullet(enemy.rect.centerx, enemy.rect.bottom + 6, speed=190 + self.level * 18, color=ENEMY_BULLET_COLOR)
            self.enemy_bullets.add(bullet)

    def fire_boss_bullets(self, boss):
        if not boss.should_fire(1 / FPS):
            return
        if self.level == 1:
            px, py = self.player.rect.center
            for offset in (-30, 0, 30):
                bx = boss.rect.centerx + offset
                by = boss.rect.bottom + 10
                dx = px - bx
                dy = py - by
                dist = max(1, math.hypot(dx, dy))
                speed = 220
                bullet = Bullet(bx, by, color=ENEMY_BULLET_COLOR, damage=2, vx=(dx / dist) * speed, vy=(dy / dist) * speed)
                self.enemy_bullets.add(bullet)
        else:
            for offset in (-40, 0, 40):
                bullet = Bullet(boss.rect.centerx + offset, boss.rect.bottom + 10, speed=220 + self.level * 24, color=ENEMY_BULLET_COLOR, damage=2)
                self.enemy_bullets.add(bullet)

    def handle_collisions(self):
        for bullet in self.player_bullets:
            hit_list = pygame.sprite.spritecollide(bullet, self.enemies, False)
            for enemy in hit_list:
                enemy.hp -= bullet.damage
                bullet.kill()
                if enemy.hp <= 0:
                    self.score += enemy.score_value
                    self.spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                    self.explode(enemy.rect.centerx, enemy.rect.centery, (255, 120, 120))
                    enemy.kill()
                    if self.audio.sfx_boom:
                        self.audio.sfx_boom.play()

        boss = self.boss_group.sprite
        if boss:
            for bullet in self.player_bullets:
                if boss.rect.colliderect(bullet.rect):
                    if self.level == 3 and boss.phase == 2:
                        hit_weak = False
                        for wp in boss.weakpoints:
                            wp_rect = pygame.Rect(boss.rect.x + wp.x, boss.rect.y + wp.y, wp.w, wp.h)
                            if wp_rect.colliderect(bullet.rect):
                                hit_weak = True
                                break
                        if hit_weak:
                            boss.hp -= bullet.damage * 2
                    else:
                        boss.hp -= bullet.damage
                    bullet.kill()
                    self.shake = 6
                    if boss.hp <= 0:
                        self.score += 200
                        self.explode(boss.rect.centerx, boss.rect.centery, (200, 150, 255))
                        boss.kill()
                        self.level_complete()

        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
            self.on_player_hit()

        if pygame.sprite.spritecollide(self.player, self.enemies, True):
            self.on_player_hit()

        if pygame.sprite.spritecollide(self.player, self.asteroids, True):
            self.on_player_hit()
        for bullet in self.player_bullets:
            if pygame.sprite.spritecollide(bullet, self.asteroids, True):
                bullet.kill()
                self.explode(bullet.rect.centerx, bullet.rect.centery, (150, 120, 90))

        for p in pygame.sprite.spritecollide(self.player, self.powerups, True):
            self.score += 50
            if self.audio.sfx_power:
                self.audio.sfx_power.play()
            if p.ptype == "speed":
                self.player.speed = min(400, self.player.speed + 60)
            elif p.ptype == "triple":
                self.player.triple_shot = 8
            elif p.ptype == "shield":
                self.player.shield = 6

    def on_player_hit(self):
        hit = self.player.hit()
        self.shake = 10
        self.explode(self.player.rect.centerx, self.player.rect.centery, (80, 200, 255))
        if hit and self.player.lives <= 0:
            self.game_over()

    def explode(self, x, y, color):
        for _ in range(20):
            self.particles.add(Particle(x, y, color))

    def level_complete(self):
        self.state = "LEVEL_COMPLETE"
        self.level_transition_timer = 2.2
        self.audio.stop_bgm()
        self.audio.stop_engine()

    def game_over(self):
        self.state = "GAME_OVER"
        self.audio.stop_bgm()
        self.audio.stop_engine()
        if self.audio.sfx_gameover:
            self.audio.sfx_gameover.play()
        if self.score > self.hiscore:
            self.hiscore = self.score
            write_hiscore(self.hiscore)

    def update_background(self, dt):
        self.background.update(dt)

    def draw_background(self, surface):
        self.background.draw(surface, self.level)

    def draw_hud(self):
        score_text = self.font.render(f"Score: {self.score}", True, HUD_COLOR)
        lives_text = self.font.render(f"Lives: {self.player.lives}", True, HUD_COLOR)
        level_text = self.font.render(f"Level: {self.level}", True, HUD_COLOR)
        self.screen.blit(score_text, (10, 8))
        self.screen.blit(lives_text, (WIDTH // 2 - 60, 8))
        self.screen.blit(level_text, (WIDTH - 130, 8))
        for i in range(self.player.lives):
            self.screen.blit(self.life_icon, (10 + i * 22, 30))

        boss = self.boss_group.sprite
        if boss:
            bar_w = 300
            bar_h = 12
            x = WIDTH // 2 - bar_w // 2
            y = 30
            pygame.draw.rect(self.screen, (60, 30, 30), (x, y, bar_w, bar_h))
            hp_w = int(bar_w * (boss.hp / boss.max_hp))
            pygame.draw.rect(self.screen, (255, 120, 80), (x, y, hp_w, bar_h))

    def draw_menu(self, surface):
        surface.fill((8, 20, 40))
        title = self.big_font.render(TITLE, True, (250, 220, 130))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
        options = ["Play", "Options", "High Scores", "Quit"]
        for i, opt in enumerate(options):
            color = (255, 160, 80) if i == self.menu_index else (230, 235, 240)
            text = self.font.render(opt, True, color)
            surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 250 + i * 36))
        surface.blit(self.scanlines, (0, 0))

    def draw_highscores(self, surface):
        surface.fill((8, 20, 40))
        title = self.big_font.render("High Scores", True, (250, 220, 130))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
        hs = self.font.render(f"Best: {self.hiscore}", True, (230, 235, 240))
        surface.blit(hs, (WIDTH // 2 - hs.get_width() // 2, 220))
        tip = self.font.render("Press ESC to return", True, (200, 210, 220))
        surface.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 320))
        surface.blit(self.scanlines, (0, 0))

    def draw_options(self, surface):
        surface.fill((8, 20, 40))
        title = self.big_font.render("Options", True, (250, 220, 130))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 90))

        items = [
            ("SFX Volume", self.audio.sfx_volume),
            ("Music Volume", self.audio.music_volume),
        ]
        for i, (label, val) in enumerate(items):
            color = (255, 160, 80) if i == self.options_index else (230, 235, 240)
            text = self.font.render(f"{label}: {int(val * 100):3d}%", True, color)
            surface.blit(text, (WIDTH // 2 - 140, 200 + i * 36))
            bar_x = WIDTH // 2 + 30
            bar_y = 205 + i * 36
            pygame.draw.rect(surface, (40, 60, 80), (bar_x, bar_y, 160, 12))
            pygame.draw.rect(surface, (255, 160, 80), (bar_x, bar_y, int(160 * val), 12))

        controls = [
            "Controls:",
            "Arrows - Move",
            "Space - Fire",
            "P - Pause",
            "ESC - Back",
        ]
        for i, line in enumerate(controls):
            text = self.font.render(line, True, (200, 210, 220))
            surface.blit(text, (WIDTH // 2 - 140, 320 + i * 22))
        surface.blit(self.scanlines, (0, 0))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        text = self.big_font.render("PAUSED", True, (255, 200, 120))
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 20))

    def draw_level_complete(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))
        text = self.big_font.render("LEVEL COMPLETE!", True, (255, 220, 140))
        surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 30))

    def draw_game_over(self, surface):
        surface.fill((0, 0, 0))
        text = self.big_font.render("GAME OVER", True, (255, 120, 90))
        surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
        score = self.font.render(f"Final Score: {self.score}", True, (230, 235, 240))
        surface.blit(score, (WIDTH // 2 - score.get_width() // 2, HEIGHT // 2 + 10))
        tip = self.font.render("Press ENTER to return to menu", True, (200, 210, 220))
        surface.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT // 2 + 50))
        surface.blit(self.scanlines, (0, 0))

    def draw_ending(self, surface):
        surface.fill((0, 0, 0))
        text = self.big_font.render("YOU WIN!", True, (255, 220, 140))
        surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 140))
        score = self.font.render(f"Final Score: {self.score}", True, (230, 235, 240))
        surface.blit(score, (WIDTH // 2 - score.get_width() // 2, 220))
        credits = self.font.render("Thanks for playing Sky Fury 1945", True, (200, 210, 220))
        surface.blit(credits, (WIDTH // 2 - credits.get_width() // 2, 280))
        tip = self.font.render("Press ENTER to return to menu", True, (200, 210, 220))
        surface.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 340))
        surface.blit(self.scanlines, (0, 0))

    def update(self, dt):
        if self.state == "PLAYING":
            keys = pygame.key.get_pressed()
            self.player.update(dt, keys)
            self.update_background(dt)

            self.spawn_timer += dt
            self.level_time += dt

            if self.level_time < self.level_duration:
                difficulty = min(1.0, self.level_time / 45)
                spawn_interval = 2.6 - difficulty * 0.8 - (self.level - 1) * 0.2
                spawn_interval = max(1.6, spawn_interval)
                if self.spawn_timer > spawn_interval and len(self.enemies) < 16 + self.level * 4:
                    self.spawn_timer = 0
                    self.spawn_enemy_wave()

            for enemy in self.enemies:
                enemy.update(dt, self.player)
                self.fire_enemy_bullet(enemy)

            if self.level_time >= self.level_duration and not self.boss_group.sprite:
                self.spawn_boss()

            boss = self.boss_group.sprite
            if boss:
                boss.update(dt)
                self.fire_boss_bullets(boss)
                if self.level == 2 and boss.should_spawn_minion(dt):
                    for _ in range(2):
                        x = boss.rect.centerx + random.randint(-60, 60)
                        y = boss.rect.bottom + random.randint(10, 40)
                        self.enemies.add(Enemy(x, y, "basic", self.level))

            if self.level == 2 and not self.boss_group.sprite:
                self.asteroid_timer += dt
                if self.asteroid_timer > 0.9:
                    self.asteroid_timer = 0
                    self.spawn_asteroid()

            self.player_bullets.update(dt)
            self.enemy_bullets.update(dt)
            self.powerups.update(dt)
            self.particles.update(dt)
            self.asteroids.update(dt)

            self.handle_collisions()

        elif self.state == "LEVEL_COMPLETE":
            self.level_transition_timer -= dt
            if self.level_transition_timer <= 0:
                self.level += 1
                if self.level > 3:
                    self.state = "ENDING"
                    self.audio.stop_bgm()
                    self.audio.stop_engine()
                else:
                    self.level_time = 0
                    self.enemies.empty()
                    self.enemy_bullets.empty()
                    self.player_bullets.empty()
                    self.boss_group.empty()
                    self.powerups.empty()
                    self.asteroids.empty()
                    self.player.shield = max(self.player.shield, 2)
                    self.player.triple_shot = max(self.player.triple_shot, 2)
                    self.state = "PLAYING"
                    self.audio.play_bgm(self.level)
                    self.audio.start_engine()

        self.shake = max(0, self.shake - dt * 10)

    def draw(self, target=None):
        surface = target or self.screen
        if self.state == "MENU":
            self.draw_menu(surface)
            return
        if self.state == "HIGHSCORES":
            self.draw_highscores(surface)
            return
        if self.state == "OPTIONS":
            self.draw_options(surface)
            return
        if self.state == "GAME_OVER":
            self.draw_game_over(surface)
            return
        if self.state == "ENDING":
            self.draw_ending(surface)
            return

        self.draw_background(surface)
        if not (self.player.invuln > 0 and int(pygame.time.get_ticks() / 120) % 2 == 0):
            self.player_group.draw(surface)
        self.enemies.draw(surface)
        self.player_bullets.draw(surface)
        self.enemy_bullets.draw(surface)
        self.powerups.draw(surface)
        self.particles.draw(surface)
        self.asteroids.draw(surface)
        if self.boss_group.sprite:
            self.boss_group.draw(surface)
            boss = self.boss_group.sprite
            if self.level == 3 and boss.phase == 2:
                for wp in boss.weakpoints:
                    pygame.draw.rect(surface, (80, 255, 160), (boss.rect.x + wp.x, boss.rect.y + wp.y, wp.w, wp.h), 2)
        self.draw_hud()

        if self.state == "LEVEL_COMPLETE":
            self.draw_level_complete(surface)

        surface.blit(self.scanlines, (0, 0))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == "MENU":
                        if event.key == pygame.K_UP:
                            self.menu_index = (self.menu_index - 1) % 4
                        if event.key == pygame.K_DOWN:
                            self.menu_index = (self.menu_index + 1) % 4
                        if event.key == pygame.K_RETURN:
                            if self.menu_index == 0:
                                self.reset_game()
                            elif self.menu_index == 1:
                                self.state = "OPTIONS"
                            elif self.menu_index == 2:
                                self.state = "HIGHSCORES"
                            elif self.menu_index == 3:
                                running = False
                    elif self.state == "HIGHSCORES":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "MENU"
                    elif self.state == "OPTIONS":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "MENU"
                        if event.key == pygame.K_UP:
                            self.options_index = (self.options_index - 1) % 2
                        if event.key == pygame.K_DOWN:
                            self.options_index = (self.options_index + 1) % 2
                        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            delta = -0.05 if event.key == pygame.K_LEFT else 0.05
                            if self.options_index == 0:
                                self.audio.set_sfx_volume(self.audio.sfx_volume + delta)
                            elif self.options_index == 1:
                                self.audio.set_music_volume(self.audio.music_volume + delta)
                    elif self.state == "PLAYING":
                        if event.key == pygame.K_SPACE:
                            self.fire_player_bullets()
                        if event.key == pygame.K_p:
                            self.state = "PAUSED"
                            self.audio.stop_engine()
                    elif self.state == "PAUSED":
                        if event.key == pygame.K_p:
                            self.state = "PLAYING"
                            self.audio.start_engine()
                    elif self.state in ("GAME_OVER", "ENDING"):
                        if event.key == pygame.K_RETURN:
                            self.state = "MENU"

            if self.state == "PAUSED":
                self.draw()
                self.draw_pause()
                pygame.display.flip()
                continue

            self.update(dt)

            scene = pygame.Surface((WIDTH, HEIGHT))
            self.draw(scene)
            if self.shake > 0:
                offset_x = random.randint(-int(self.shake), int(self.shake))
                offset_y = random.randint(-int(self.shake), int(self.shake))
                self.screen.blit(scene, (offset_x, offset_y))
            else:
                self.screen.blit(scene, (0, 0))

            pygame.display.flip()

        pygame.quit()
        sys.exit()

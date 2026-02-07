import os
import pygame

from config import ASSET_DIR
from utils import sprite_from_map


def _load_png(name):
    path = os.path.join(ASSET_DIR, name)
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            return None
    return None


class SpriteFactory:
    @staticmethod
    def player_frames():
        png = _load_png("player.png")
        if png:
            return [png, png]
        palette = {
            "1": (220, 240, 255),
            "2": (80, 120, 180),
            "3": (200, 60, 60),
            "4": (255, 210, 80),
        }
        base_map = [
            "...1111...",
            "..112211..",
            ".11222211.",
            "1122222211",
            "1123343211",
            ".11222211.",
            "..112211..",
            "...1111...",
        ]
        thrust_map = [
            "...1111...",
            "..112211..",
            ".11222211.",
            "1122222211",
            "1123343211",
            ".11222211.",
            "..112211..",
            "...1411...",
        ]
        return [
            sprite_from_map(base_map, palette, scale=4),
            sprite_from_map(thrust_map, palette, scale=4),
        ]

    @staticmethod
    def enemy_sprite(etype):
        if etype == "basic":
            png = _load_png("enemy_basic.png")
            if png:
                return png
        if etype == "kamikaze":
            png = _load_png("enemy_kamikaze.png")
            if png:
                return png
        if etype == "shielded":
            png = _load_png("enemy_shielded.png")
            if png:
                return png
        if etype == "basic":
            palette = {"1": (140, 200, 255), "2": (50, 80, 120), "3": (240, 180, 60)}
            fighter_map = [
                "..111..",
                ".12221.",
                "1223221",
                "1222221",
                ".12221.",
                "..111..",
            ]
            return sprite_from_map(fighter_map, palette, scale=4)
        if etype == "kamikaze":
            palette = {"1": (220, 140, 80), "2": (120, 60, 30), "3": (255, 220, 160)}
            dive_map = [
                "...1...",
                "..121..",
                ".12321.",
                "1233321",
                ".12221.",
                "..111..",
            ]
            return sprite_from_map(dive_map, palette, scale=4)
        palette = {"1": (170, 210, 120), "2": (80, 110, 50), "3": (230, 240, 200), "4": (120, 150, 80)}
        bomber_map = [
            ".111111.",
            "12222221",
            "12333321",
            "12344321",
            "12333321",
            "12222221",
            ".111111.",
        ]
        return sprite_from_map(bomber_map, palette, scale=4)

    @staticmethod
    def boss_sprite(level):
        png = _load_png("boss.png")
        if png:
            return png
        palette = {
            "1": (200, 210, 230),
            "2": (90, 110, 140),
            "3": (240, 200, 90),
            "4": (160, 80, 60),
        }
        boss_map = [
            ".......111111.......",
            ".....1122222211.....",
            "...11222222222211...",
            "..1222233333322221..",
            ".122233333443333221.",
            ".122233344444333221.",
            "..12223333344333221..",
            "...122223333332221...",
            ".....1122222211.....",
            ".......111111.......",
        ]
        scale = 8 if level >= 2 else 7
        return sprite_from_map(boss_map, palette, scale=scale)

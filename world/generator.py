# world/generator.py
from .sector import Sector
import random


class WorldGenerator:
    def __init__(self):
        self.sectors = {}

    @staticmethod
    def calculate_mass(size_px, type_key=""):
        base_mass = (size_px ** 2) / 128.0
        return base_mass

    def get_sector(self, x, y, asteroid_sprites, wreck_sprite=None, planet_sprite=None):
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            # Определяем тип генерации
            if x == 0 and y == 0:
                # Стартовая зона: плотный пояс с фиксированным количеством
                sector.generate_belt(
                    asteroid_sprites=asteroid_sprites,
                    inner_radius=400,      # было min_x
                    outer_radius=800,     # было max_x
                    counts={              # было distribution
                        "ast_mod01_s16": 35,
                        "ast_mod01_s32": 25,
                        "ast_mod01_s64": 20
                    },
                    wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite
                )
            else:
                # Остальные зоны: случайное скопление
                sector.generate_clustered_field(
                    asteroid_sprites=asteroid_sprites,
                    wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite
                )

            self.sectors[key] = sector

        return self.sectors[key]

    def preload_neighbors(self, cx, cy, asteroid_sprites, wreck_sprite=None, planet_sprite=None):
        offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]

        for dx, dy in offsets:
            nx, ny = cx + dx, cy + dy
            self.get_sector(nx, ny, asteroid_sprites,
                            wreck_sprite=wreck_sprite,
                            planet_sprite=planet_sprite)

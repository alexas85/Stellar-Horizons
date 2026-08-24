# world/generator.py
from .sector import Sector


class WorldGenerator:
    def __init__(self):
        self.sectors = {}

    def get_sector(self, x, y, asteroid_sprites, wreck_sprite=None, planet_sprite=None):
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            if x == 0 and y == 0:
                sector.generate_belt(
                    asteroid_sprites,
                    400, 700,
                    {
                        "ast_mod01_s16": 75,
                        "ast_mod01_s32": 45,
                        "ast_mod01_s64": 50
                    },
                    wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite  # <--- Передаем планету
                )
            else:
                sector.generate_clustered_field(
                    asteroid_sprites,
                    wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite  # <--- Передаем планету
                )

            self.sectors[key] = sector

        return self.sectors[key]

    def preload_neighbors(self, cx, cy, asteroid_sprites, wreck_sprite=None, planet_sprite=None):
        offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (0, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]

        for dx, dy in offsets:
            nx, ny = cx + dx, cy + dy
            # Передаем все спрайты дальше
            self.get_sector(nx, ny, asteroid_sprites, wreck_sprite=wreck_sprite, planet_sprite=planet_sprite)

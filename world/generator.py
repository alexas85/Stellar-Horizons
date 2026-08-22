# world/generator.py
from .sector import Sector

class WorldGenerator:
    def __init__(self):
        self.sectors = {}

    def get_sector(self, x, y, asteroid_sprites):
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            # Логика генерации: центр (0,0) — пояс, остальные — пучки
            if x == 0 and y == 0:
                sector.generate_belt(asteroid_sprites, 400, 700, {
                    "ast_mod01_s16": 75,
                    "ast_mod01_s32": 45,
                    "ast_mod01_s64": 50
                })
            else:
                sector.generate_clustered_field(asteroid_sprites, total_count=50)

            self.sectors[key] = sector

        return self.sectors[key]

    def preload_neighbors(self, cx, cy, asteroid_sprites):
        """Загружает текущую комнату и всех 8 соседей заранее."""
        offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (0, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]
        for dx, dy in offsets:
            nx, ny = cx + dx, cy + dy
            self.get_sector(nx, ny, asteroid_sprites)

# world/generator.py
from .sector import Sector


class WorldGenerator:
    def __init__(self):
        self.sectors = {}

    def get_sector(self, x, y, asteroid_sprites):
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            # Логика генерации для разных комнат (пример)
            if x == 99 and y == 100:
                # Комната с обычным полем
                sector.generate_random_field(asteroid_sprites, {
                    "ast_mod01_s16": 25,
                    "ast_mod01_s32": 12,
                    "ast_mod01_s64": 10
                })
            elif x == 101 and y == 101:
                # Комната с поясом астероидов
                sector.generate_belt(asteroid_sprites, 400, 700, {
                    "ast_mod01_s16": 75,
                    "ast_mod01_s32": 45,
                    "ast_mod01_s64": 50
                })
            else:
                # Пустая комната или дефолтная генерация
                sector.generate_random_field(asteroid_sprites, {
                    "ast_mod01_s16": 5,
                    "ast_mod01_s32": 3,
                    "ast_mod01_s64": 2
                })

            self.sectors[key] = sector
        return self.sectors[key]

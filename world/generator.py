# world/generator.py
from .sector import Sector


class WorldGenerator:
    def __init__(self):
        self.sectors = {}

    def get_sector(self, x, y, asteroid_sprites, wreck_sprite=None):
        """
        Получает сектор. Если его нет — генерирует.
        wreck_sprite: спрайт корабля-обломка (передается для генерации спец-объектов)
        """
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            # Логика генерации: центр (0,0) — пояс, остальные — пучки
            if x == 0 and y == 0:
                # Передаем wreck_sprite в generate_belt, чтобы он мог создать корабль,
                # если вдруг комната (1,0) будет сгенерирована как пояс (хотя у нас она обычная)
                sector.generate_belt(
                    asteroid_sprites,
                    400, 700,
                    {
                        "ast_mod01_s16": 75,
                        "ast_mod01_s32": 45,
                        "ast_mod01_s64": 50
                    },
                    wreck_sprite=wreck_sprite
                )
            else:
                # Передаем wreck_sprite в generate_clustered_field
                sector.generate_clustered_field(
                    asteroid_sprites,
                    wreck_sprite=wreck_sprite
                )

            self.sectors[key] = sector

        return self.sectors[key]

    def preload_neighbors(self, cx, cy, asteroid_sprites, wreck_sprite=None):
        """
        Загружает текущую комнату и всех 8 соседей заранее.
        ВАЖНО: Теперь корректно передает wreck_sprite во все соседние сектора.
        """
        offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (0, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]

        for dx, dy in offsets:
            nx, ny = cx + dx, cy + dy
            # ИСПРАВЛЕНИЕ: Передаем wreck_sprite дальше в get_sector
            self.get_sector(nx, ny, asteroid_sprites, wreck_sprite=wreck_sprite)

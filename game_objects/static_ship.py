import pygame
import random


class StaticShip:
    # Кэш спрайтов стадий ремонта — загружается один раз
    _repair_sprites_cache = None

    @classmethod
    def _get_repair_sprites(cls):
        if cls._repair_sprites_cache is None:
            from sprites import get_wreck_repair_sprites
            cls._repair_sprites_cache = get_wreck_repair_sprites()
        return cls._repair_sprites_cache

    def __init__(self, sprite, x, y, angle=0.0):
        # Сразу грузим спрайт 20% — обломок изначально выглядит повреждённым
        repair_sprites = self._get_repair_sprites()
        self.sprite = repair_sprites.get(20, sprite)
        self._original_sprite = sprite  # На случай, если спрайты не найдутся
        self.x = x
        self.y = y
        self.angle = angle
        self.highlight_radius = 128
        self.highlight_thickness = 1
        self.highlight_alpha = 70
        self.highlight_color = (211, 211, 211)

        self._is_scanned = False
        self.is_disassembled = False
        self.ship_name = "Destroyer Wreck"
        self.modules = {}
        self.resources = {
            "metal": 15,
            "mineral": 5,
            "energy": 3
        }

        # Склад (доступен после ремонта Корпуса до 100%)
        self.storage = {
            "metal": 0,
            "precious": 0,
            "crystal": 0,
            "energy": 0,
            "mineral": 0,
            "uranium": 0
        }
        self.storage_max = 500

    @property
    def is_scanned(self):
        return self._is_scanned

    @is_scanned.setter
    def is_scanned(self, value):
        self._is_scanned = value
        if value and not self.modules:
            self.modules = {
                "Броня": random.randint(0, 100),
                "Корпус": 20,
                "Двигатель": random.randint(0, 100),
                "Вооружение": random.randint(0, 100),
            }
        self._update_sprite_by_hull()

    @property
    def is_habitable(self):
        """True, если Корпус отремонтирован до 100%."""
        return self._is_scanned and self.modules.get("Корпус", 0) >= 100

    def _update_sprite_by_hull(self):
        """Меняет спрайт в зависимости от целостности Корпуса."""
        repair_sprites = self._get_repair_sprites()

        # До сканирования — Корпус считаем равным 20%
        if not self._is_scanned or not self.modules:
            hull = 20
        else:
            hull = int(self.modules.get("Корпус", 0))

        if hull >= 100:
            new_sprite = repair_sprites.get(100, self._original_sprite)
        else:
            # Округляем вниз до ближайшего десятка: 20-29 → 20, 30-39 → 30, ...
            tier = max(20, (hull // 10) * 10)
            if tier in repair_sprites:
                new_sprite = repair_sprites[tier]
            else:
                new_sprite = self._original_sprite

        if new_sprite is not None and new_sprite is not self.sprite:
            self.sprite = new_sprite

    def deposit_resource(self, name, amount):
        """Помещает ресурс на склад. Возвращает фактически помещённое количество."""
        space_left = self.storage_max - self.storage.get(name, 0)
        if space_left <= 0:
            return 0
        actual = min(amount, space_left)
        self.storage[name] = self.storage.get(name, 0) + actual
        return actual

    def withdraw_resource(self, name, amount):
        """Забирает ресурс со склада. Возвращает фактически забранное количество."""
        stored = self.storage.get(name, 0)
        actual = min(amount, stored)
        self.storage[name] = stored - actual
        return actual

    def update(self):
        self._update_sprite_by_hull()

    def draw(self, screen, camera, show_highlight=False):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        rect = self.sprite.get_rect(center=(screen_x, screen_y))
        screen.blit(self.sprite, rect)

        if show_highlight:
            cx, cy = rect.center
            surf_size = self.highlight_radius * 2 + self.highlight_thickness * 2
            highlight_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            draw_color = (*self.highlight_color, self.highlight_alpha)

            pygame.draw.circle(
                highlight_surf,
                draw_color,
                (surf_size // 2, surf_size // 2),
                self.highlight_radius,
                self.highlight_thickness
            )
            screen.blit(highlight_surf, (cx - surf_size // 2, cy - surf_size // 2))

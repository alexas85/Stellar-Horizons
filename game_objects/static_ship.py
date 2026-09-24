# game_objects/static_ship.py
import pygame
import random
import math


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
        self._base_sprite = repair_sprites.get(20, sprite)
        self._original_sprite = sprite
        self.sprite = self._base_sprite
        self.x = x
        self.y = y

        # Случайный поворот 25–75 градусов
        if angle == 0.0:
            self.angle = random.uniform(25, 75)
        else:
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

        self.storage = {
            "metal": 0,
            "precious": 0,
            "crystal": 0,
            "energy": 0,
            "mineral": 0,
            "uranium": 0
        }
        self.storage_max = 500
        # --- ДОБАВЛЯЕМ ФИЗИКУ ДЛЯ УПРАВЛЕНИЯ ---
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0
        self.max_speed = 6.0  # Чуть медленнее игрока
        self.friction = 0.98  # Трение в космосе
        self.acceleration = 0.2  # Сила тяги
        self.turn_speed = 0.15  # Скорость поворота
        self.max_angular_velocity = 3.0

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
        return self._is_scanned and self.modules.get("Корпус", 0) >= 100

    def _update_sprite_by_hull(self):
        """Меняет базовый спрайт в зависимости от целостности Корпуса."""
        repair_sprites = self._get_repair_sprites()

        if not self._is_scanned or not self.modules:
            hull = 20
        else:
            hull = int(self.modules.get("Корпус", 0))

        if hull >= 100:
            new_sprite = repair_sprites.get(100, self._original_sprite)
        else:
            tier = max(20, (hull // 10) * 10)
            if tier in repair_sprites:
                new_sprite = repair_sprites[tier]
            else:
                new_sprite = self._original_sprite

        if new_sprite is not None and new_sprite is not self._base_sprite:
            self._base_sprite = new_sprite

    def rotate(self, direction):
        """Вращение корабля (вызывается из main.py при нажатии клавиш)"""
        target_angular_velocity = direction * self.max_angular_velocity

        if abs(self.angular_velocity - target_angular_velocity) < self.turn_speed:
            self.angular_velocity = target_angular_velocity
        else:
            if self.angular_velocity < target_angular_velocity:
                self.angular_velocity += self.turn_speed
            else:
                self.angular_velocity -= self.turn_speed

    def accelerate(self):
        """Ускорение корабля вперед по текущему углу"""
        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * self.acceleration

        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

    def deposit_resource(self, name, amount):
        space_left = self.storage_max - self.storage.get(name, 0)
        if space_left <= 0:
            return 0
        actual = min(amount, space_left)
        self.storage[name] = self.storage.get(name, 0) + actual
        return actual

    def withdraw_resource(self, name, amount):
        stored = self.storage.get(name, 0)
        actual = min(amount, stored)
        self.storage[name] = stored - actual
        return actual

    def update(self):
        self._update_sprite_by_hull()
        # 1. Обновляем спрайт в зависимости от ремонта (твоя старая логика)
        self._update_sprite_by_hull()

        # 2. Применяем физику вращения
        self.angular_velocity *= 0.95  # Трение вращения
        self.angle += self.angular_velocity

        # Нормализация угла (чтобы не улетал в бесконечность)
        if self.angle >= 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        # 3. Применяем физику движения
        self.velocity *= self.friction
        self.x += self.velocity.x
        self.y += self.velocity.y

        # Примечание: rect в draw() пересчитывается на лету, поэтому здесь его обновлять не обязательно,
        # если только ты не используешь rect для коллизий.

    def draw(self, screen, camera, show_highlight=False):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y

        # Поворачиваем базовый спрайт на self.angle
        rotated = pygame.transform.rotate(self._base_sprite, -self.angle)
        rect = rotated.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated, rect)

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

# game_objects/asteroid.py
import math
import pygame
import random


class Asteroid:
    def __init__(self, sprite, x, y, angle, rotation_speed, orbit_center, orbit_radius, orbit_speed, size_px=64, type_key=""):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.rotation_speed = rotation_speed
        self.orbit_center = orbit_center
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.size_px = size_px  # размер астероида: 16, 32, 64 и т.д.
        self.type_key = type_key  # теперь параметр есть в сигнатуре

        # Инерция (для отскока)
        self.velocity_x = 0.0
        self.velocity_y = 0.0

        # Размеры для коллизий
        try:
            self.width = sprite.get_width()
            self.height = sprite.get_height()
        except AttributeError:
            # Если передали не Surface, а что-то другое — ставим заглушки
            self.width = 64
            self.height = 64

    def apply_knockback(self, push_x, push_y):
        """Добавляет импульс к астероиду (для отскока)."""
        # Базовое отталкивание
        self.velocity_x += push_x
        self.velocity_y += push_y

        # Случайный разброс, чтобы траектории не были одинаковыми
        random_factor = random.uniform(-0.5, 0.5)
        self.velocity_x += random_factor
        self.velocity_y += random_factor

    def update(self):
        # Если у астероида есть орбита — двигаем по орбите
        if self.orbit_center is not None:
            cx, cy = self.orbit_center
            angle_delta = self.orbit_speed
            self.angle += angle_delta
            self.x = cx + math.cos(self.angle) * self.orbit_radius
            self.y = cy + math.sin(self.angle) * self.orbit_radius
        else:
            # Если нет орбиты (например, после удара) — двигаем по инерции
            self.x += self.velocity_x
            self.y += self.velocity_y

            # Лёгкое затухание скорости, чтобы астероид не улетал бесконечно
            decay = 0.98
            self.velocity_x *= decay
            self.velocity_y *= decay

        self.angle += self.rotation_speed

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera):
        """Отрисовка астероида с учётом камеры."""
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        rect = rotated_sprite.get_rect(center=(draw_x, draw_y))
        screen.blit(rotated_sprite, rect)

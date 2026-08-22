# game_objects/asteroid.py
import math
import pygame


class Asteroid:
    def __init__(self, sprite, x, y, angle, rotation_speed,
                 orbit_center=None, orbit_radius=0, orbit_speed=0):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.rotation_speed = rotation_speed

        # Параметры орбиты
        self.orbit_center = orbit_center
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.current_orbit_angle = angle

        # Храним оригинальный размер спрайта для корректного центрирования
        self.original_rect = sprite.get_rect()

    def update(self):
        # 1. Вращение самого астероида
        self.angle += self.rotation_speed

        # 2. Движение по орбите
        if self.orbit_center and self.orbit_radius > 0:
            self.current_orbit_angle += self.orbit_speed

            cx, cy = self.orbit_center
            self.x = cx + math.cos(self.current_orbit_angle) * self.orbit_radius
            self.y = cy + math.sin(self.current_orbit_angle) * self.orbit_radius

    def draw(self, screen, camera):
        # 1. Переводим мировые координаты в экранные
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y

        # 2. Поворачиваем спрайт
        angle_deg = math.degrees(self.angle)
        rotated_image = pygame.transform.rotate(self.sprite, angle_deg)

        # 3. Получаем rect повернутого изображения и центрируем его
        new_rect = rotated_image.get_rect(center=(screen_x, screen_y))

        # 4. ПРОВЕРКА ВИДИМОСТИ
        # Если весь прямоугольник находится за пределами экрана — не рисуем
        if (new_rect.right < 0 or new_rect.left > camera.width or
                new_rect.bottom < 0 or new_rect.top > camera.height):
            return

        screen.blit(rotated_image, new_rect.topleft)

    def get_rect(self):
        """Возвращает прямоугольник для коллизий в мировых координатах."""
        # Для коллизий лучше использовать оригинальный размер, смещенный на мировые координаты
        rect = self.original_rect.copy()
        rect.center = (self.x, self.y)
        return rect

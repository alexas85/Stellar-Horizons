# game_objects/bullet.py
import pygame
import math

class Bullet:
    def __init__(self, x, y, angle, speed=12, max_distance=300, base_velocity=None):
        """
        x, y: стартовые координаты
        angle: угол выстрела в градусах (как у корабля)
        speed: собственная скорость пули вперёд (относительно корабля)
        max_distance: максимальная дистанция полёта (в условных единицах)
        base_velocity: pygame.math.Vector2 — скорость корабля в момент выстрела (чтобы пуля «унаследовала» её)
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.max_distance = max_distance
        self.distance_traveled = 0
        self.sprite = None
        self.damage = 10

        # Прямоугольник для коллизий
        self.rect = pygame.Rect(0, 0, 16, 16)

        # Вычисляем вектор направления по углу
        rad = math.radians(self.angle)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)

        # Базовая скорость пули (вперёд по направлению выстрела)
        self.velocity = pygame.math.Vector2(dir_x * speed, dir_y * speed)

        # Если передана скорость корабля — прибавляем её (векторное сложение)
        if base_velocity is not None:
            self.velocity += base_velocity

        # Для подсчёта дистанции используем реальную длину вектора скорости
        self.speed_magnitude = self.velocity.length()
        # Защита от деления на ноль или странных случаев
        if self.speed_magnitude == 0:
            self.speed_magnitude = speed

    def set_sprite(self, surface):
        """Устанавливает спрайт и подгоняет rect под его размер"""
        self.sprite = surface
        if self.sprite:
            self.rect.width = self.sprite.get_width()
            self.rect.height = self.sprite.get_height()

    def update(self):
        """Двигает пулю по её текущей скорости и считает пройденное расстояние"""
        # Двигаем по вектору velocity (уже включает скорость корабля)
        self.x += self.velocity.x
        self.y += self.velocity.y

        # Добавляем пройденное расстояние за этот кадр
        self.distance_traveled += self.speed_magnitude

        # Обновляем rect для коллизий
        if self.sprite:
            w = self.sprite.get_width()
            h = self.sprite.get_height()
            self.rect = pygame.Rect(0, 0, w, h)
            self.rect.center = (self.x, self.y)

    def is_active(self):
        """Возвращает True, пока пуля не пролетела лимит дистанции"""
        return self.distance_traveled < self.max_distance

    def draw(self, surface, camera):
        """Рисует пулю с поворотом на её угол"""
        cam_x, cam_y = camera.x, camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        if not self.sprite:
            # Если спрайта нет — рисуем красный квадрат (для отладки)
            rect = pygame.Rect(draw_x - 8, draw_y - 8, 16, 16)
            pygame.draw.rect(surface, (255, 0, 0), rect)
            return

        # Поворот спрайта на self.angle
        rotated = pygame.transform.rotate(self.sprite, -self.angle)  # минус, потому что Y вниз
        rect = rotated.get_rect(center=(draw_x, draw_y))

        surface.blit(rotated, rect)

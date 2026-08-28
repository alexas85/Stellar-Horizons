import pygame
import math


class Bullet:
    def __init__(self, x, y, angle, speed=15, max_distance=300):
        self.x = x
        self.y = y
        self.angle = angle  # Угол в радианах
        self.speed = speed
        self.max_distance = max_distance

        # Пройденное расстояние
        self.distance_traveled = 0

        # Вектор движения (dx, dy)
        rad = math.radians(angle)
        self.dx = math.cos(rad) * speed
        self.dy = math.sin(rad) * speed

        # Спрайт (загрузим позже в main.py, чтобы не тормозить инициализацию)
        self.sprite = None
        self.size = 16

    def set_sprite(self, sprite):
        """Устанавливает спрайт и подгоняет его под размер"""
        if sprite:
            self.sprite = pygame.transform.smoothscale(sprite, (self.size, self.size))
        else:
            # Заглушка, если спрайт не найден
            self.sprite = pygame.Surface((self.size, self.size))
            self.sprite.fill((255, 0, 0))

    def update(self):
        """Двигает пулю и считает дистанцию"""
        self.x += self.dx
        self.y += self.dy
        self.distance_traveled += self.speed

    def is_active(self):
        """Возвращает True, если пуля еще в игре (не пролетела лимит)"""
        return self.distance_traveled < self.max_distance

    def draw(self, screen, camera):
        if not self.sprite:
            return

        screen_x = self.x - camera.x
        screen_y = self.y - camera.y

        # Рисуем от центра
        rect = self.sprite.get_rect(center=(screen_x, screen_y))
        screen.blit(self.sprite, rect)

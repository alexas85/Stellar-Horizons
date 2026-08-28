import pygame
import math

class Bullet:
    def __init__(self, x, y, angle, speed=12, max_distance=300):
        self.x = x
        self.y = y
        self.angle = angle          # угол в градусах (как у корабля)
        self.speed = speed
        self.max_distance = max_distance
        self.distance_traveled = 0
        self.sprite = None           # сюда запишется спрайт из player.shoot()

        # Прямоугольник для коллизий (пока заглушка, будет обновляться)
        self.rect = pygame.Rect(0, 0, 16, 16)

    def set_sprite(self, surface):
        """Устанавливает спрайт и сразу подгоняет rect под его размер"""
        self.sprite = surface
        if self.sprite:
            self.rect.width = self.sprite.get_width()
            self.rect.height = self.sprite.get_height()

    def update(self):
        """Двигает пулю вперёд по её углу и считает пройденное расстояние"""
        rad = math.radians(self.angle)
        dx = math.cos(rad) * self.speed
        dy = math.sin(rad) * self.speed

        self.x += dx
        self.y += dy
        self.distance_traveled += math.hypot(dx, dy)

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

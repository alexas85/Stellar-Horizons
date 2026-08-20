import pygame
import math
from config import SHIP_ACCELERATION


class PlayerShip:
    def __init__(self, x, y, idle_sprite, movement_sprites):
        self.x = x
        self.y = y
        self.angle = 0  # 0 градусов = смотрит вверх
        self.velocity = pygame.math.Vector2(0, 0)

        # Храним оригинал для вращения
        self.original_image = idle_sprite
        self.image = self.original_image

        # rect нужен только для получения размера картинки и коллизий
        # Инициализируем его размером картинки, центр пока не важен
        self.rect = self.image.get_rect()

        self.rotation_speed = 4
        self.max_speed = 8

        # Анимация
        self.movement_sprites = movement_sprites
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 100

    def rotate(self, direction):
        """direction: 1 (по часовой), -1 (против часовой)"""
        self.angle += direction * self.rotation_speed

        # Вращаем от оригинала
        self.image = pygame.transform.rotate(self.original_image, -self.angle)

        # Обновляем rect под новый размер повернутой картинки
        # Центр пока ставим в (0,0), реальные координаты будем считать в draw
        self.rect = self.image.get_rect()

    def accelerate(self):
        """Тяга строго по направлению носа"""
        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * SHIP_ACCELERATION

        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

    def update(self):
        # Трение
        self.velocity *= 0.98

        self.x += self.velocity.x
        self.y += self.velocity.y

        # Примечание: мы НЕ обновляем self.rect.center здесь.
        # self.rect используется только для получения размера картинки (width, height)
        # и для коллизий (если реализуешь позже). Позиция для отрисовки считается в draw.

    def draw(self, surface, camera_offset):
        cam_x, cam_y = camera_offset

        # Позиция на экране = Мировая позиция - Смещение камеры
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Создаем прямоугольник для отрисовки
        draw_rect = self.rect.copy()
        draw_rect.topleft = (draw_x, draw_y)

        surface.blit(self.image, draw_rect)

import pygame
import math
from config import SHIP_ACCELERATION


class PlayerShip:
    def __init__(self, x, y, idle_sprite, movement_sprites):
        self.x = x
        self.y = y
        self.angle = 0
        self.velocity = pygame.math.Vector2(0, 0)

        self.original_image = idle_sprite
        self.image = self.original_image
        self.rect = self.image.get_rect()

        # Физика вращения
        self.angular_velocity = 0.0  # текущая угловая скорость (градусы в кадр)
        self.max_angular_velocity = 3.0  # максимальная скорость поворота
        self.turn_acceleration = 0.2  # насколько быстро набирается поворот (как «газ» руля)

        self.max_speed = 8

        self.movement_sprites = movement_sprites
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 100

    def rotate(self, direction):
        """direction: 1 (по часовой), -1 (против часовой)"""
        # Плавно ускоряем/замедляем вращение
        target_angular_velocity = direction * self.max_angular_velocity

        # Линейная интерполяция к целевой скорости (проще, чем PID)
        if abs(self.angular_velocity - target_angular_velocity) < self.turn_acceleration:
            self.angular_velocity = target_angular_velocity
        else:
            if self.angular_velocity < target_angular_velocity:
                self.angular_velocity += self.turn_acceleration
            else:
                self.angular_velocity -= self.turn_acceleration

    def accelerate(self):
        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * SHIP_ACCELERATION
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

    def update(self):
        # Применяем поворот
        self.angle += self.angular_velocity

        # Трение вращения (чтобы корабль не крутился вечно)
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        # Движение
        self.velocity *= 0.98
        self.x += self.velocity.x
        self.y += self.velocity.y

    def draw(self, surface, camera_offset):
        cam_x, cam_y = camera_offset
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Вращаем от оригинала
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=(draw_x, draw_y))

        surface.blit(self.image, self.rect.topleft)

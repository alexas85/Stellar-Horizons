# game_objects/asteroid.py
import math
import pygame

class Asteroid:
    def __init__(self, sprite, x, y, angle, rotation_speed):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.rotation_speed = rotation_speed

    def update(self):
        self.angle += self.rotation_speed

    def draw(self, screen, camera):
        # Поворачиваем спрайт
        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        # Вычисляем позицию на экране с учетом камеры
        rect = rotated_sprite.get_rect(center=(self.x - camera.left, self.y - camera.top))
        screen.blit(rotated_sprite, rect.topleft)

    def get_rect(self):
        w, h = self.sprite.get_size()
        return pygame.Rect(self.x - w/2, self.y - h/2, w, h)

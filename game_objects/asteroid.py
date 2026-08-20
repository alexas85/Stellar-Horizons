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

        # Параметры орбиты (для пояса астероидов)
        self.orbit_center = orbit_center  # (cx, cy)
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed  # скорость движения по орбите (в радианах за кадр)
        self.current_orbit_angle = angle  # текущий угол на орбите

    def update(self):
        # 1. Вращение самого астероида (кувыркание)
        self.angle += self.rotation_speed

        # 2. Движение по орбите (если параметры заданы)
        if self.orbit_center and self.orbit_radius > 0:
            self.current_orbit_angle += self.orbit_speed

            cx, cy = self.orbit_center
            self.x = cx + math.cos(self.current_orbit_angle) * self.orbit_radius
            self.y = cy + math.sin(self.current_orbit_angle) * self.orbit_radius

    def draw(self, screen, camera):
        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        rect = rotated_sprite.get_rect(center=(self.x - camera.left, self.y - camera.top))
        screen.blit(rotated_sprite, rect.topleft)

    def get_rect(self):
        w, h = self.sprite.get_size()
        return pygame.Rect(self.x - w / 2, self.y - h / 2, w, h)

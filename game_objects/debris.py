import pygame
import math
import random


class ShipDebris:
    """Осколок разрушенного корабля — летит, вращается, тормозит и затухает."""

    def __init__(self, x, y, sprite, speed_min=2.0, speed_max=6.0):
        self.x = x
        self.y = y
        self.sprite = sprite

        # Случайное направление и скорость
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_min, speed_max)
        self.velocity = pygame.math.Vector2(
            math.cos(angle) * speed,
            math.sin(angle) * speed
        )

        # Вращение
        self.angle = random.uniform(0, 360)
        self.angular_velocity = random.uniform(-5.0, 5.0)

        # Физика
        self.friction = 0.97
        self.angular_friction = 0.96

        # Жизненный цикл
        self.lifetime = 0
        self.max_lifetime = 360       # 6 секунд при 60 FPS
        self.fade_start = 240         # затухание с 4-й секунды
        self.is_expired = False
        self.alpha = 255

        self._update_rect()

    def _update_rect(self):
        w = self.sprite.get_width()
        h = self.sprite.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

    def update(self):
        if self.is_expired:
            return

        self.lifetime += 1

        self.velocity *= self.friction
        self.angular_velocity *= self.angular_friction
        self.x += self.velocity.x
        self.y += self.velocity.y
        self.angle += self.angular_velocity

        # Плавное затухание
        if self.lifetime >= self.fade_start:
            progress = (self.lifetime - self.fade_start) / max(1, self.max_lifetime - self.fade_start)
            self.alpha = max(0, int(255 * (1 - progress)))

        if self.lifetime >= self.max_lifetime or self.alpha <= 0:
            self.is_expired = True

        self._update_rect()

    def draw(self, surface, camera):
        if self.is_expired:
            return

        if isinstance(camera, tuple):
            cam_x, cam_y = camera
        else:
            cam_x, cam_y = camera.x, camera.y

        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        rotated = pygame.transform.rotate(self.sprite, -self.angle)

        if self.alpha < 255:
            fade_surf = pygame.Surface(rotated.get_size(), pygame.SRCALPHA)
            fade_surf.fill((255, 255, 255, self.alpha))
            rotated = rotated.copy()
            rotated.blit(fade_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
        surface.blit(rotated, rect)

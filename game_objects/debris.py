import pygame
import math
import random


class ShipDebris:
    """Осколок разрушенного корабля — летит, вращается, тормозит. Можно разобрать на ресурсы."""

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

        # Интерфейс для сбора (совместим с asteroid)
        self.type_key = "destroyer_debris"
        self.size_px = 128
        self.is_collecting = False
        self.collection_start_time = 0.0
        self.marked_for_removal = False

        self._update_rect()

    @property
    def velocity_x(self):
        return self.velocity.x

    @property
    def velocity_y(self):
        return self.velocity.y

    def _update_rect(self):
        w = self.sprite.get_width()
        h = self.sprite.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

    def update(self):
        # --- ЛОГИКА СБОРА (как у астероида) ---
        if self.is_collecting:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.collection_start_time
            if elapsed >= 3000:
                self.marked_for_removal = True
                self.is_collecting = False
                self.collection_start_time = 0.0
            return  # во время сбора осколок замерает

        # Обычное движение
        self.velocity *= self.friction
        self.angular_velocity *= self.angular_friction
        self.x += self.velocity.x
        self.y += self.velocity.y
        self.angle += self.angular_velocity

        self._update_rect()

    def draw(self, surface, camera):
        if isinstance(camera, tuple):
            cam_x, cam_y = camera
        else:
            cam_x, cam_y = camera.x, camera.y

        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        rotated = pygame.transform.rotate(self.sprite, -self.angle)
        rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
        surface.blit(rotated, rect)

import pygame
import math
import random


class Crystal:
    """Кристалл, выпадающий из амёбы. Собирается за 1 секунду, даёт 5-10 кристаллов."""

    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.size_px = sprite.get_width()
        self.type_key = "crystal"
        self.angle = 0.0
        self.rotation_speed = random.uniform(-0.02, 0.02)
        self.velocity_x = random.uniform(-2.5, 2.5)
        self.velocity_y = random.uniform(-2.5, 2.5)

        self.is_collecting = False
        self.collection_start_time = 0.0
        self.marked_for_removal = False

        self.width = self.size_px
        self.height = self.size_px
        self.mass = 1.0

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.width, self.height)
        r.center = (int(self.x), int(self.y))
        return r

    def apply_knockback(self, px, py):
        self.velocity_x += px
        self.velocity_y += py

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_x *= 0.98
        self.velocity_y *= 0.98
        self.angle += self.rotation_speed

        if self.is_collecting:
            elapsed = pygame.time.get_ticks() - self.collection_start_time
            if elapsed >= 1000:  # 1 секунда
                self.marked_for_removal = True
                self.is_collecting = False
                self.collection_start_time = 0.0

    def draw(self, screen, camera):
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        rotated = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        rect = rotated.get_rect(center=(draw_x, draw_y))
        screen.blit(rotated, rect)

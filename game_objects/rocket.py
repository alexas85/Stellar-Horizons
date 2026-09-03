import pygame
import math


class Rocket:
    def __init__(self, x, y, angle, target=None, max_distance=2000):
        self.x = x
        self.y = y
        self.angle = angle
        self.target = target
        self.max_distance = max_distance
        self.distance_traveled = 0
        self.speed = 8.0
        self.turn_speed = 4.0  # градусов за кадр
        self.sprites = None
        self.animation_index = 0
        self.animation_timer = 0
        self.rect = pygame.Rect(0, 0, 16, 16)
        self.rect.center = (int(self.x), int(self.y))

    def set_sprites(self, sprites):
        self.sprites = sprites
        if sprites and len(sprites) > 0:
            w = sprites[0].get_width()
            h = sprites[0].get_height()
            self.rect = pygame.Rect(0, 0, w, h)
            self.rect.center = (int(self.x), int(self.y))

    def update(self):
        # Самонаведение
        if self.target is not None and not self.target.is_destroyed:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))

            diff = target_angle - self.angle
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360

            if abs(diff) <= self.turn_speed:
                self.angle = target_angle
            elif diff > 0:
                self.angle += self.turn_speed
            else:
                self.angle -= self.turn_speed

        # Движение
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed

        # Rect
        if self.sprites and len(self.sprites) > 0:
            w = self.sprites[0].get_width()
            h = self.sprites[0].get_height()
            self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

        # Анимация
        if self.sprites:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_index = (self.animation_index + 1) % len(self.sprites)
                self.animation_timer = 0

    def is_active(self):
        return self.distance_traveled < self.max_distance

    def check_hit(self):
        """Возвращает True, если ракета попала в цель."""
        if self.target is not None and not self.target.is_destroyed:
            # Проверка по дистанции — надёжнее, чем rect при быстром полёте
            dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if dist < 30:
                return True
            # Двойная проверка через rect — на всякий случай
            if self.rect.colliderect(self.target.rect):
                return True
        return False

    def draw(self, surface, camera):
        cam_x, cam_y = camera.x, camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        if self.sprites and len(self.sprites) > 0:
            sprite = self.sprites[self.animation_index]
            rotated = pygame.transform.rotate(sprite, -self.angle)
            rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
            surface.blit(rotated, rect)
        else:
            pygame.draw.circle(surface, (255, 100, 0), (int(draw_x), int(draw_y)), 4)

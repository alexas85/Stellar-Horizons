# game_objects/rocket.py
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
        self.turn_speed = 4.0

        self.sprites = None
        self.animation_index = 0
        self.animation_timer = 0

        # --- Параметры шлейфа ---
        self.trail_max_length =20  # длина хвоста в сегментах
        self.trail_fade_step = 15  # шаг затухания прозрачности
        self.trail = []  # теперь храним: (x, y, age)
        # age = 0 это самый свежий (крупный), max_length-1 это старый (мелкий)

        self.trail_sprite = None
        # НАСТРОЙКИ РАЗМЕРА:
        self.trail_start_scale = 1.1  # старт: в 1.5 раза крупнее оригинала
        self.trail_end_scale = 0.6  # конец: сжимаем до 60% оригинала

        self.rect = pygame.Rect(0, 0, 16, 16)
        self.rect.center = (int(self.x), int(self.y))

    def set_sprites(self, sprites):
        self.sprites = sprites
        if sprites and len(sprites) > 0:
            w = sprites[0].get_width()
            h = sprites[0].get_height()
            self.rect = pygame.Rect(0, 0, w, h)
            self.rect.center = (int(self.x), int(self.y))

    def set_trail_sprite(self, sprite):
        """Передаем спрайт для сегмента хвоста"""
        # Сохраняем оригинал как есть, масштабировать будем при отрисовке
        self.trail_sprite = sprite

    def update(self):
        # --- Самонаведение и движение (без изменений) ---
        if self.target is not None and not self.target.is_destroyed:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))

            diff = target_angle - self.angle
            while diff > 180: diff -= 360
            while diff < -180: diff += 360

            if abs(diff) <= self.turn_speed:
                self.angle = target_angle
            elif diff > 0:
                self.angle += self.turn_speed
            else:
                self.angle -= self.turn_speed

        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed

        # Обновляем rect и анимацию (без изменений)
        if self.sprites and len(self.sprites) > 0:
            w = self.sprites[0].get_width()
            h = self.sprites[0].get_height()
            self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

        if self.sprites:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_index = (self.animation_index + 1) % len(self.sprites)
                self.animation_timer = 0

        # --- ЛОГИКА ШЛЕЙФА С ИЗМЕНЕНИЕМ РАЗМЕРА ---
        # Добавляем текущую позицию. Возраст нового сегмента всегда 0 (самый свежий)
        # Мы не храним alpha отдельно, считаем его по возрасту
        self.trail.append((self.x, self.y, 0))

        if len(self.trail) > self.trail_max_length:
            self.trail.pop(0)

        # Увеличиваем возраст всех старых сегментов
        # Самый первый в списке (индекс 0) — самый старый, ему даем максимальный возраст
        # Последний в списке — самый новый, возраст 0
        for i in range(len(self.trail)):
            x, y, age = self.trail[i]
            # Пересчитываем возраст:
            # Если в списке 10 элементов, то индекс 0 имеет возраст 9, индекс 9 имеет возраст 0
            new_age = len(self.trail) - 1 - i
            self.trail[i] = (x, y, new_age)

    def is_active(self):
        return self.distance_traveled < self.max_distance

    def check_hit(self):
        if self.target is not None and not self.target.is_destroyed:
            dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if dist < 30:
                return True
            if self.rect.colliderect(self.target.rect):
                return True
        return False

    def draw(self, surface, camera):
        cam_x, cam_y = camera.x, camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Рисуем хвост (сначала, чтобы ракета была поверх)
        if self.trail_sprite:
            for x, y, age in self.trail:
                # 1. Считаем прозрачность по возрасту
                # Чем старше сегмент (больше age), тем прозрачнее
                alpha = max(0, 255 - (age * self.trail_fade_step))

                # 2. Считаем масштаб по возрасту
                # Интерполяция между start_scale и end_scale
                # Если age=0 -> scale=start_scale, если age=max -> scale=end_scale
                max_age = self.trail_max_length - 1
                if max_age == 0: max_age = 1  # защита от деления на 0

                progress = age / max_age
                current_scale = self.trail_start_scale + (self.trail_end_scale - self.trail_start_scale) * progress

                # Округляем размеры до целых
                w_orig, h_orig = self.trail_sprite.get_size()
                new_w = int(w_orig * current_scale)
                new_h = int(h_orig * current_scale)

                # Создаем уменьшенную копию спрайта
                scaled_sprite = pygame.transform.smoothscale(self.trail_sprite, (new_w, new_h))
                scaled_sprite.set_alpha(alpha)

                # Центрируем сегмент на точке
                sx = int(x - cam_x)
                sy = int(y - cam_y)
                trail_rect = scaled_sprite.get_rect(center=(sx, sy))
                surface.blit(scaled_sprite, trail_rect)

        # Рисуем саму ракету (без изменений)
        if self.sprites and len(self.sprites) > 0:
            sprite = self.sprites[self.animation_index]
            rotated = pygame.transform.rotate(sprite, -self.angle)
            rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
            surface.blit(rotated, rect)
        else:
            pygame.draw.circle(surface, (255, 100, 0), (int(draw_x), int(draw_y)), 4)

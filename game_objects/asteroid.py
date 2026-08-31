# asteroid.py
import math
import pygame
import random

# --- НАСТРОЙКА ОТЛАДКИ ---
DEBUG_HITBOX = True

# --- НАСТРОЙКИ ФИЗИКИ ---
MAX_ASTEROID_SPEED = 3.0  # Максимальная скорость астероида (подбирай под баланс)
ASTEROID_DECAY = 0.98    # Затухание скорости (трение)


class Asteroid:
    @staticmethod
    def calculate_mass_from_size(size_px):
        """
        Единая формула расчёта массы по размеру.
        Используй её везде (в sector.py, main.py и т.д.), чтобы баланс был стабильным.

        16px  -> ~2.0
        32px  -> ~8.0
        64px  -> ~32.0
        124px -> ~119.0 (почти неподвижный)
        """
        return (size_px ** 2) / 128.0

    def __init__(self, sprite, x, y, angle, rotation_speed, orbit_center, orbit_radius, orbit_speed,
                 size_px=64, type_key="", mass=None):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.rotation_speed = rotation_speed
        self.orbit_center = orbit_center
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.size_px = size_px
        self.type_key = type_key

        # Масса: если не передали — считаем по размеру
        if mass is None:
            mass = self.calculate_mass_from_size(size_px)
        self.mass = mass

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        try:
            self.width = sprite.get_width()
            self.height = sprite.get_height()
        except AttributeError:
            self.width = size_px
            self.height = size_px

        self.hitbox_offset_x = -2
        self.hitbox_offset_y = -1

        # --- НОВЫЕ ПОЛЯ ДЛЯ МЕХАНИКИ СБОРА ---
        self.is_collecting = False          # идёт ли сейчас сбор этого астероида
        self.collection_start_time = 0.0   # время начала сбора (в мс)
        self.collected_resources = None    # словарь с ресурсами, которые будут начислены (или None)
        self.marked_for_removal = False     # флаг: объект нужно удалить из сектора

    def apply_knockback(self, push_x, push_y):
        """Добавляет импульс к астероиду (для отскока)."""
        self.velocity_x += push_x
        self.velocity_y += push_y

    def update(self):
        # Если у астероида есть орбита — двигаем по орбите
        if self.orbit_center is not None:
            cx, cy = self.orbit_center
            angle_delta = self.orbit_speed
            self.angle += angle_delta
            self.x = cx + math.cos(self.angle) * self.orbit_radius
            self.y = cy + math.sin(self.angle) * self.orbit_radius
        else:
            # Если нет орбиты (например, после удара) — двигаем по инерции
            self.x += self.velocity_x
            self.y += self.velocity_y

            # Затухание скорости (трение/сопротивление среды)
            self.velocity_x *= ASTEROID_DECAY
            self.velocity_y *= ASTEROID_DECAY

            # Ограничение максимальной скорости (чтобы астероид не улетал за экран)
            speed = math.hypot(self.velocity_x, self.velocity_y)
            if speed > MAX_ASTEROID_SPEED:
                ratio = MAX_ASTEROID_SPEED / speed
                self.velocity_x *= ratio
                self.velocity_y *= ratio

        self.angle += self.rotation_speed

        # --- ЛОГИКА СБОРА РЕСУРСОВ ---
        if self.is_collecting:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.collection_start_time

            # Сбор длится 3000 мс (3 секунды)
            if elapsed >= 3000:
                # Сбор завершён: помечаем на удаление, сбрасываем флаги
                self.marked_for_removal = True
                self.is_collecting = False
                self.collection_start_time = 0.0
            # Если сбор идёт — ничего не делаем, ждём таймера

    @property
    def rect(self):
        """Возвращает прямоугольник хитбокса со смещением."""
        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.center = (self.x, self.y)
        rect.move_ip(self.hitbox_offset_x, self.hitbox_offset_y)
        return rect

    def draw(self, screen, camera):
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y

        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        rect = rotated_sprite.get_rect(center=(draw_x, draw_y))
        screen.blit(rotated_sprite, rect)

        if DEBUG_HITBOX:
            hitbox = self.rect
            screen_hitbox = hitbox.copy()
            screen_hitbox.x -= camera.x
            screen_hitbox.y -= camera.y
            pygame.draw.rect(screen, (0, 255, 0), screen_hitbox, 2)
            center_x = screen_hitbox.centerx
            center_y = screen_hitbox.centery
            pygame.draw.circle(screen, (255, 0, 0), (int(center_x), int(center_y)), 4)

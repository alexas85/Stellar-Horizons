# game_objects/asteroid.py
import math
import pygame
import random

# --- НАСТРОЙКА ОТЛАДКИ ---
# Поставь True, чтобы видеть хитбоксы (зелёный контур) на экране.
# Когда всё настроишь — поставь False, чтобы не засорять экран.
DEBUG_HITBOX = False


class Asteroid:
    def __init__(self, sprite, x, y, angle, rotation_speed, orbit_center, orbit_radius, orbit_speed, size_px=64,
                 type_key=""):
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

        # Инерция (для отскока)
        self.velocity_x = 0.0
        self.velocity_y = 0.0

        # Размеры для коллизий
        try:
            self.width = sprite.get_width()
            self.height = sprite.get_height()
        except AttributeError:
            self.width = 64
            self.height = 64

        # ============================================================
        # ЗДЕСЬ ПОДКРУЧИВАЕМ СМЕЩЕНИЕ ХИТБОКСА ВРУЧНУЮ
        # ------------------------------------------------------------
        # Подбери эти значения экспериментально.
        # Пример: (-10, -5) сдвинет хитбокс на 10 пикселей влево и на 5 вверх.
        # Положительные значения: вправо/вниз, отрицательные: влево/вверх.
        self.hitbox_offset_x = -2  # <-- МЕНЯЙ ЭТО ЗНАЧЕНИЕ
        self.hitbox_offset_y = -1  # <-- МЕНЯЙ ЭТО ЗНАЧЕНИЕ
        # ============================================================

    def apply_knockback(self, push_x, push_y):
        """Добавляет импульс к астероиду (для отскока)."""
        self.velocity_x += push_x
        self.velocity_y += push_y

        random_factor = random.uniform(-0.5, 0.5)
        self.velocity_x += random_factor
        self.velocity_y += random_factor

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

            decay = 0.98
            self.velocity_x *= decay
            self.velocity_y *= decay

        self.angle += self.rotation_speed

    @property
    def rect(self):
        """
        Возвращает прямоугольник хитбокса.
        Хитбокс центрируется по координатам (self.x, self.y),
        а затем сдвигается на заданное смещение.
        """
        # Создаём базовый прямоугольник по размеру спрайта
        rect = pygame.Rect(0, 0, self.width, self.height)

        # Центрируем его по логическим координатам астероида
        rect.center = (self.x, self.y)

        # Применяем ручное смещение
        rect.move_ip(self.hitbox_offset_x, self.hitbox_offset_y)

        return rect

    def draw(self, screen, camera):
        """Отрисовка астероида с учётом камеры."""
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y

        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        rect = rotated_sprite.get_rect(center=(draw_x, draw_y))
        screen.blit(rotated_sprite, rect)

        # ============================================================
        # ОТЛАДКА: Визуализация хитбокса
        # ------------------------------------------------------------
        if DEBUG_HITBOX:
            # Получаем хитбокс (уже со смещением!)
            hitbox = self.rect

            # Переводим координаты хитбокса в экранные (учитывая камеру)
            screen_hitbox = hitbox.copy()
            screen_hitbox.x -= camera.x
            screen_hitbox.y -= camera.y

            # Рисуем зелёный контур хитбокса
            pygame.draw.rect(screen, (0, 255, 0), screen_hitbox, 2)

            # Опционально: рисуем центр хитбокса красной точкой
            center_x = screen_hitbox.centerx
            center_y = screen_hitbox.centery
            pygame.draw.circle(screen, (255, 0, 0), (int(center_x), int(center_y)), 4)
        # ============================================================

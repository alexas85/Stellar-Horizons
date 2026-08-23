# game_objects/static_ship.py
import math
import pygame


class StaticShip:
    def __init__(self, sprite, x, y, angle):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle

        # Сохраняем оригинальный rect для центрирования
        self.original_rect = sprite.get_rect()

    def update(self):
        # Статичный объект не двигается, но метод нужен для единообразия цикла отрисовки
        pass

    def draw(self, screen, camera):
        # 1. Переводим мировые координаты в экранные
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y

        # 2. Поворачиваем спрайт
        angle_deg = math.degrees(self.angle)
        rotated_image = pygame.transform.rotate(self.sprite, angle_deg)

        # 3. Получаем rect повернутого изображения и центрируем его
        new_rect = rotated_image.get_rect(center=(screen_x, screen_y))

        # 4. Проверка видимости (чтобы не рисовать, если объект далеко за экраном)
        if (new_rect.right < 0 or new_rect.left > camera.width or
                new_rect.bottom < 0 or new_rect.top > camera.height):
            return

        screen.blit(rotated_image, new_rect.topleft)

    def get_rect(self):
        """Возвращает прямоугольник для коллизий в мировых координатах."""
        rect = self.original_rect.copy()
        rect.center = (self.x, self.y)
        return rect

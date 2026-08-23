# game_objects/static_ship.py
import pygame
import math

class StaticShip:
    def __init__(self, sprite, x, y, angle=0.0):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.rect = self.sprite.get_rect(center=(x, y))

    def update(self):
        pass

    def draw(self, screen, camera, show_highlight=False):
        # Экранные координаты центра объекта
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y

        # Поворот спрайта
        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(-self.angle))
        rect = rotated_sprite.get_rect(center=(screen_x, screen_y))

        screen.blit(rotated_sprite, rect)

        if show_highlight:
            cx, cy = rect.center
            radius = 128  # Новый радиус
            thickness = 2  # Толщина линии
            alpha = 128    # 50% прозрачности (0–255)
            color = (128, 128, 128)  # Серый

            # Создаём поверхность для полупрозрачного круга
            # Размер поверхности: диаметр + толщина по краям, чтобы контур не обрезался
            surf_size = radius * 2 + thickness * 2
            highlight_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            highlight_surf.fill((0, 0, 0, 0))  # Полностью прозрачный фон

            # Рисуем полупрозрачный круг на этой поверхности
            pygame.draw.circle(
                highlight_surf,
                (*color, alpha),  # Цвет с альфа-каналом
                (surf_size // 2, surf_size // 2),
                radius,
                thickness
            )

            # Вычисляем позицию поверхности на экране
            draw_x = cx - surf_size // 2
            draw_y = cy - surf_size // 2

            screen.blit(highlight_surf, (draw_x, draw_y))

# game_objects/static_planet.py
import pygame


class StaticPlanet:
    def __init__(self, sprite, x, y, parallax_factor=1):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.parallax_factor = parallax_factor
        # Радиус подсветки для планеты
        self.highlight_radius = 350
        self.highlight_thickness = 2
        self.highlight_alpha = 50  # 50% прозрачности
        self.highlight_color = (0, 255, 0)  # Ярко-зелёный для обитаемой планеты

    def update(self):
        pass

    def draw(self, screen, camera, show_highlight=False):
        # Применяем параллакс
        screen_x = self.x - (camera.x * self.parallax_factor)
        screen_y = self.y - (camera.y * self.parallax_factor)

        rect = self.sprite.get_rect(center=(screen_x, screen_y))
        screen.blit(self.sprite, rect)

        # Рисуем подсветку, если нужно
        if show_highlight:
            cx, cy = rect.center

            # Создаём поверхность для полупрозрачного круга
            surf_size = self.highlight_radius * 2 + self.highlight_thickness * 2
            highlight_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

            # Рисуем на поверхности полупрозрачный круг (используем цвет с альфа-каналом)
            # Цвет: (R, G, B, Alpha)
            draw_color = (*self.highlight_color, self.highlight_alpha)

            pygame.draw.circle(
                highlight_surf,
                draw_color,
                (surf_size // 2, surf_size // 2),
                self.highlight_radius,
                self.highlight_thickness
            )

            # Копируем на экран со смещением
            screen.blit(highlight_surf, (cx - surf_size // 2, cy - surf_size // 2))

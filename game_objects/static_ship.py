# game_objects/static_ship.py
import pygame


class StaticShip:
    def __init__(self, sprite, x, y, angle=0.0):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        # Радиус подсветки для корабля — 128 пикселей
        self.highlight_radius = 128
        self.highlight_thickness = 1
        self.highlight_alpha = 70
        self.highlight_color = (211, 211, 211)  # Жёлтый для корабля

    def update(self):
        pass

    def draw(self, screen, camera, show_highlight=False):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        rect = self.sprite.get_rect(center=(screen_x, screen_y))
        screen.blit(self.sprite, rect)

        if show_highlight:
            cx, cy = rect.center
            surf_size = self.highlight_radius * 2 + self.highlight_thickness * 2
            highlight_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            draw_color = (*self.highlight_color, self.highlight_alpha)

            pygame.draw.circle(
                highlight_surf,
                draw_color,
                (surf_size // 2, surf_size // 2),
                self.highlight_radius,
                self.highlight_thickness
            )
            screen.blit(highlight_surf, (cx - surf_size // 2, cy - surf_size // 2))

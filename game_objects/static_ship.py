# game_objects/static_ship.py
import pygame
import random


class StaticShip:
    def __init__(self, sprite, x, y, angle=0.0):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.highlight_radius = 128
        self.highlight_thickness = 1
        self.highlight_alpha = 70
        self.highlight_color = (211, 211, 211)

        # --- СОСТОЯНИЕ ---
        self._is_scanned = False
        self.is_disassembled = False
        self.ship_name = "Destroyer Wreck"
        self.modules = {}  # Заполняется при сканировании
        self.resources = {
            "metal": 15,
            "mineral": 5,
            "energy": 3
        }

    @property
    def is_scanned(self):
        return self._is_scanned

    @is_scanned.setter
    def is_scanned(self, value):
        """Когда дрон завершает сканирование и ставит True —
        автоматически генерируются проценты целостности модулей."""
        self._is_scanned = value
        if value and not self.modules:
            self.modules = {
                "Броня": random.randint(0, 100),
                "Корпус": random.randint(0, 100),
                "Двигатель": random.randint(0, 100),
                "Вооружение": random.randint(0, 100),
            }

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

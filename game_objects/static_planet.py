# game_objects/static_planet.py
import pygame

class StaticPlanet:
    def __init__(self, sprite, x, y, parallax_factor=1):
        """
        parallax_factor: 1.0 — двигается как обычный объект (рядом).
                         0.5 — двигается в 2 раза медленнее (дальше).
                         0.3 — ещё дальше.
        """
        self.sprite = sprite
        self.x = x
        self.y = y
        self.parallax_factor = parallax_factor
        self.rect = self.sprite.get_rect(center=(x, y))

    def update(self):
        pass

    def draw(self, screen, camera):
        # Применяем параллакс: планета двигается медленнее камеры
        # Формула: позиция на экране = (реальная позиция - камера * фактор)
        screen_x = self.x - (camera.x * self.parallax_factor)
        screen_y = self.y - (camera.y * self.parallax_factor)

        rect = self.sprite.get_rect(center=(screen_x, screen_y))
        screen.blit(self.sprite, rect)

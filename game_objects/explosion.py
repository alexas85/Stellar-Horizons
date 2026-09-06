import pygame


class Explosion:
    """Анимация взрыва. Проигрывается один раз и удаляется."""
    def __init__(self, x, y, sprites, frame_delay=3):
        self.x = x
        self.y = y
        self.sprites = sprites
        self.frame_delay = frame_delay   # кадров между сменой спрайта
        self.timer = 0
        self.index = 0
        self.done = False

    def update(self):
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.timer = 0
            self.index += 1
            if self.index >= len(self.sprites):
                self.done = True

    def draw(self, surface, camera):
        if self.done or not self.sprites:
            return
        if isinstance(camera, tuple):
            cam_x, cam_y = camera
        else:
            cam_x, cam_y = camera.x, camera.y
        sprite = self.sprites[self.index]
        draw_x = int(self.x - cam_x)
        draw_y = int(self.y - cam_y)
        rect = sprite.get_rect(center=(draw_x, draw_y))
        surface.blit(sprite, rect)

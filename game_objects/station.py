# game_objects/station.py
import pygame


class Station:
    """Космическая станция — вращающийся объект с подсветкой при приближении игрока."""
    def __init__(self, sprite, x, y, rotation_speed=0.3):
        self.sprite = sprite
        self.original_sprite = sprite
        self.x = x
        self.y = y
        self.angle = 0.0
        self.rotation_speed = rotation_speed  # градусов за кадр
        self.highlight_radius = 150
        self.highlight_thickness = 1
        self.highlight_alpha = 70
        self.highlight_color = (100, 200, 255)  # голубой

    def update(self):
        self.angle += self.rotation_speed
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

    def draw(self, screen, camera, show_highlight=False):
        if isinstance(camera, tuple):
            cam_x, cam_y = camera
        else:
            cam_x, cam_y = camera.x, camera.y

        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)

        rotated = pygame.transform.rotate(self.original_sprite, -self.angle)
        rect = rotated.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated, rect)

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

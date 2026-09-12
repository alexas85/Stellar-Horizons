import pygame
import math


class ScanDrone:
    """Дрон-сканер: вылетает к обломку, выходит на орбиту, сканирует, исчезает."""

    def __init__(self, start_x, start_y, target_ship, drone_sprite, scan_sprites, return_target=None):

        self.x = start_x
        self.y = start_y
        self.target_ship = target_ship
        self.return_target = return_target
        self.drone_sprite = drone_sprite
        self.scan_sprites = scan_sprites

        # Состояния: "flying" → "scanning" → "done"
        self.state = "flying"

        # Начальный угол орбиты — по направлению подлёта
        dx = target_ship.x - start_x
        dy = target_ship.y - start_y
        self.orbit_angle = math.degrees(math.atan2(dy, dx))

        self.orbit_radius = 90
        self.orbit_speed = 0.5      # градусов за кадр
        self.fly_speed = 3.0

        # Анимация сканирования
        self.scan_frame = 0
        self.scan_timer = 0
        self.scan_frame_delay = 4
        self.scan_duration = 0
        self.max_scan_duration = 1800  # 3 секунды при 60 fps

        # Затухание
        self.done = False
        self.fade_timer = 0
        self.fade_duration = 30

    def update(self):
        target = self.target_ship

        # Если обломок разобран — дрон исчезает
        if target is None or getattr(target, 'is_disassembled', False):
            self.state = "done"

        if self.state == "flying":
            rad = math.radians(self.orbit_angle)
            target_x = target.x + self.orbit_radius * math.cos(rad)
            target_y = target.y + self.orbit_radius * math.sin(rad)

            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)

            if dist < self.fly_speed:
                self.x = target_x
                self.y = target_y
                self.state = "scanning"
            else:
                self.x += dx / dist * self.fly_speed
                self.y += dy / dist * self.fly_speed

        elif self.state == "scanning":
            # Вращение по орбите
            self.orbit_angle += self.orbit_speed
            if self.orbit_angle > 360:
                self.orbit_angle -= 360
            rad = math.radians(self.orbit_angle)
            self.x = target.x + self.orbit_radius * math.cos(rad)
            self.y = target.y + self.orbit_radius * math.sin(rad)

            # Анимация сканирования
            self.scan_timer += 1
            if self.scan_timer >= self.scan_frame_delay:
                self.scan_timer = 0
                self.scan_frame = (self.scan_frame + 1) % len(self.scan_sprites)

            self.scan_duration += 1
            if self.scan_duration >= self.max_scan_duration:
                target.is_scanned = True
                if self.return_target is not None:
                    self.state = "returning"
                else:
                    self.state = "done"

        elif self.state == "returning":
            dx = self.return_target.x - self.x
            dy = self.return_target.y - self.y
            dist = math.hypot(dx, dy)

            if dist < self.fly_speed:
                self.x = self.return_target.x
                self.y = self.return_target.y
                self.state = "done"
            else:
                self.x += dx / dist * self.fly_speed
                self.y += dy / dist * self.fly_speed


        elif self.state == "done":
            self.fade_timer += 1
            if self.fade_timer >= self.fade_duration:
                self.done = True

    def draw(self, surface, camera):
        cam_x, cam_y = camera.x, camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Угол поворота: при сканировании смотрит на обломок, при возвращении — на игрока
        if self.state == "returning" and self.return_target is not None:
            angle_to_wreck = math.degrees(math.atan2(
                self.return_target.y - self.y,
                self.return_target.x - self.x
            ))
        else:
            angle_to_wreck = math.degrees(math.atan2(
                self.target_ship.y - self.y,
                self.target_ship.x - self.x
            ))

        # --- НОВЫЙ ЭФФЕКТ СКАНИРОВАНИЯ (градиент + размер) ---
        if self.state == "scanning":
            scan_radius = 100  # радиус эффекта (было ~32px, теперь крупнее)
            scan_thickness = 1
            scan_alpha_center = 180
            scan_alpha_edge = 0

            # Создаём поверхность для эффекта
            surf_size = (scan_radius + scan_thickness) * 2
            scan_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

            # Рисуем круг с градиентом вручную (через концентрические кольца)
            rings = 12
            for i in range(rings):
                r_current = int((i / rings) * scan_radius)
                r_next = int(((i + 1) / rings) * scan_radius)
                alpha = int(scan_alpha_center - (i / rings) * (scan_alpha_center - scan_alpha_edge))
                color = (0, 255, 200, alpha)  # голубой сканирующий цвет

                pygame.draw.circle(scan_surf, color, (surf_size // 2, surf_size // 2), r_next, scan_thickness)

            # Позиционируем эффект между дроном и обломком (чуть ближе к обломку)
            offset_dist = 40
            scan_x = self.x + math.cos(math.radians(angle_to_wreck)) * offset_dist
            scan_y = self.y + math.sin(math.radians(angle_to_wreck)) * offset_dist

            rect = scan_surf.get_rect(center=(int(scan_x - cam_x), int(scan_y - cam_y)))
            surface.blit(scan_surf, rect)

        # Дрон (с затуханием в конце)
        alpha = 255
        if self.state == "done":
            alpha = max(0, 255 - int(255 * self.fade_timer / self.fade_duration))

        if alpha > 0:
            drone_surf = self.drone_sprite.copy()
            drone_surf.set_alpha(alpha)
            rotated = pygame.transform.rotate(drone_surf, -angle_to_wreck)
            rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
            surface.blit(rotated, rect)

# game_objects/drone.py
import pygame
import math
import random


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
        self.max_scan_duration = 100  # 3 секунды при 60 fps

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


class RepairDrone:
    """
    Дрон-ремонтник: подлетает, зависает, пускает луч сварки, чинит модуль,
    затем возвращается к кораблю игрока.
    Состояния: FLYING_AROUND -> LOCKED_ON -> REPAIRING -> RETURNING -> DONE
    """
    BASE_REPAIR_TIME = 3600 # 30 секунд при 60 FPS на 100% ремонта

    def __init__(self, start_x, start_y, target_ship, module_name, drone_sprite, return_target=None):
        self.x = start_x
        self.y = start_y
        self.target_ship = target_ship
        self.module_name = module_name
        self.return_target = return_target
        self.drone_sprite = drone_sprite

        # Состояния
        self.state = "FLYING_AROUND"

        # Параметры движения
        self.orbit_radius = 120
        self.fly_speed = 4.0
        self.locked_pos = None

        # Таймеры
        self.total_duration = 0
        self.elapsed_time = 0
        self.state_timer = 0

        # Параметры ремонта
        current_integrity = target_ship.modules.get(module_name, 0)
        needed_percent = 100 - current_integrity
        self.total_duration = max(30, int((needed_percent / 100.0) * self.BASE_REPAIR_TIME))

        # Эффект луча
        self.spark_timer = 0
        self.spark_interval = 5

        # Флаг завершения
        self.done = False
        self.fade_timer = 0
        self.fade_duration = 30

    def update(self):
        self.state_timer += 1

        if self.state == "DONE":
            self.fade_timer += 1
            if self.fade_timer >= self.fade_duration:
                self.done = True
            return

        # Проверка: если цель уничтожена или разобрана — летим обратно
        if self.target_ship is None or getattr(self.target_ship, 'is_disassembled', False):
            if self.return_target is not None:
                self.state = "RETURNING"
                self.state_timer = 0
            else:
                self.state = "DONE"
            return

        # 1. FLYING_AROUND: хаотичное движение вокруг цели
        if self.state == "FLYING_AROUND":
            angle = math.radians(self.state_timer * 0.1)
            rand_offset = random.uniform(-20, 20)

            target_x = self.target_ship.x + (self.orbit_radius + rand_offset) * math.cos(angle)
            target_y = self.target_ship.y + (self.orbit_radius + rand_offset) * math.sin(angle)

            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)

            if dist < self.fly_speed or self.state_timer > 120:
                self.state = "LOCKED_ON"
                self.locked_pos = (self.x, self.y)
                self.state_timer = 0
            else:
                self.x += dx / dist * self.fly_speed
                self.y += dy / dist * self.fly_speed

        # 2. LOCKED_ON: зависание перед началом сварки
        elif self.state == "LOCKED_ON":
            vibrate_x = random.uniform(-2, 2)
            vibrate_y = random.uniform(-2, 2)
            self.x = self.locked_pos[0] + vibrate_x
            self.y = self.locked_pos[1] + vibrate_y

            if self.state_timer > 30:
                self.state = "REPAIRING"
                self.state_timer = 0

        # 3. REPAIRING: основной процесс ремонта
        elif self.state == "REPAIRING":
            self.elapsed_time += 1

            # Плавно увеличиваем целостность
            repair_per_frame = 100.0 / self.total_duration
            current_integrity = self.target_ship.modules.get(self.module_name, 0)
            new_integrity = min(100, current_integrity + repair_per_frame)
            self.target_ship.modules[self.module_name] = new_integrity

            # Если ремонт завершён — летим обратно
            if new_integrity >= 100 or self.elapsed_time >= self.total_duration:
                self.target_ship.modules[self.module_name] = 100
                print(f"[SUCCESS] Модуль '{self.module_name}' отремонтирован! Дрон возвращается.")
                self.state = "RETURNING"
                self.state_timer = 0

        # 4. RETURNING: летим к кораблю игрока
        elif self.state == "RETURNING":
            if self.return_target is None:
                self.state = "DONE"
                self.state_timer = 0
                return

            dx = self.return_target.x - self.x
            dy = self.return_target.y - self.y
            dist = math.hypot(dx, dy)

            if dist < self.fly_speed:
                # Достигли игрока — затухаем
                self.state = "DONE"
                self.state_timer = 0
            else:
                self.x += dx / dist * self.fly_speed
                self.y += dy / dist * self.fly_speed

    def draw(self, surface, camera):
        cam_x, cam_y = camera.x, camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Угол поворота: при возвращении смотрим на игрока, иначе — на обломок
        if self.state == "RETURNING" and self.return_target is not None:
            angle_to_target = math.degrees(math.atan2(
                self.return_target.y - self.y,
                self.return_target.x - self.x
            ))
        else:
            angle_to_target = math.degrees(math.atan2(
                self.target_ship.y - self.y,
                self.target_ship.x - self.x
            ))

        # Отрисовка дрона с затуханием
        alpha = 255
        if self.state == "DONE":
            alpha = max(0, 255 - int(255 * self.fade_timer / self.fade_duration))

        if alpha > 0:
            drone_surf = self.drone_sprite.copy()
            drone_surf.set_alpha(alpha)
            rotated = pygame.transform.rotate(drone_surf, -angle_to_target)
            rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
            surface.blit(rotated, rect)

        # Отрисовка луча сварки (ТОЛЬКО в состоянии REPAIRING)
        if self.state == "REPAIRING":
            target_w = self.target_ship.sprite.get_width() / 2
            target_h = self.target_ship.sprite.get_height() / 2
            hit_x = self.target_ship.x + random.uniform(-target_w, target_w)
            hit_y = self.target_ship.y + random.uniform(-target_h, target_h)

            start_pos = (draw_x, draw_y)
            end_pos = (hit_x - cam_x, hit_y - cam_y)

            # Эффект мерцания
            self.spark_timer += 1
            if self.spark_timer >= self.spark_interval:
                self.spark_timer = 0
                color_var = random.randint(200, 255)
                line_color = (color_var, color_var - 50, 0)
                line_width = random.randint(2, 4)
            else:
                line_color = (255, 200, 50)
                line_width = 3

            pygame.draw.line(surface, line_color, start_pos, end_pos, line_width)

            # Искры
            if self.spark_timer == 0:
                spark_count = random.randint(1, 3)
                for _ in range(spark_count):
                    sx = end_pos[0] + random.randint(-10, 10)
                    sy = end_pos[1] + random.randint(-10, 10)
                    pygame.draw.circle(surface, (255, 255, 200), (int(sx), int(sy)), random.randint(2, 4))

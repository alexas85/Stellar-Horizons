import pygame
import math
import random


class SpaceAmoeba:
    """
    Космическая амёба: тёмно-серая, тянется к цели псевдоподией.
    Отросток постепенно вырастает из центра и плавно меняет направление.
    Отрисовка полностью процедурная — без спрайтов.
    """

    def __init__(self, x, y, room_left, room_top, room_right, room_bottom):
        self.x = x
        self.y = y

        # Границы сектора
        self.room_left = room_left
        self.room_top = room_top
        self.room_right = room_right
        self.room_bottom = room_bottom

        # Размеры
        self.base_radius = 80
        self.absorb_radius = 65
        self.detection_radius = 300

        # Движение
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.max_speed = 1.2
        self.aggressive_speed = 2.0
        self.acceleration = 0.04
        self.friction = 0.98

        # Блуждание и агрессия
        self.target_pos = None
        self.state = "WANDER"
        self.current_target = None
        self.target_angle = 0.0
        self.target_dist = 0.0

        # --- ПЛАВНОЕ ВЫТЯГИВАНИЕ И ПОВОРОТ ЩУПАЛЬЦА ---
        self.tentacle_growth = 0.0        # 0 = втянут, 1 = полностью вытянут
        self.tentacle_growth_speed = 0.012  # скорость роста за кадр (~5 сек до полной длины)
        self.tentacle_retract_speed = 0.015  # медленное втягивание (~5.5 сек)
        self.tentacle_angle = 0.0          # текущий угол щупальца (плавный)
        self.tentacle_angle_speed = 0.03   # скорость поворота к новому углу

        # Анимация формы
        self.time = 0.0
        self.num_points = 28
        self.point_phases = [random.uniform(0, 2 * math.pi) for _ in range(self.num_points)]
        self.point_speeds = [random.uniform(0.8, 1.6) for _ in range(self.num_points)]
        self.point_amps = [random.uniform(8, 22) for _ in range(self.num_points)]

        # Внутренние ядра
        self.nuclei = []
        for _ in range(random.randint(3, 6)):
            self.nuclei.append({
                "offset_x": random.uniform(-35, 35),
                "offset_y": random.uniform(-35, 35),
                "radius": random.uniform(6, 16),
                "phase": random.uniform(0, 2 * math.pi),
                "speed": random.uniform(0.4, 1.0),
            })

        # Поглощение
        self.absorbing = False
        self.absorb_target = None
        self.absorb_damage = 0.15
        self.absorb_slow_factor = 0.85
        self.absorb_pull = 0.2

        # Прочность
        self.hp = 300
        self.max_hp = 300
        self.is_destroyed = False

        # Для совместимости с main.py
        self.angle = 0
        self.is_disassembled = False
        self.sector = None

    def set_sector(self, sector):
        self.sector = sector

    @property
    def rect(self):
        size = int(self.base_radius * 2)
        r = pygame.Rect(0, 0, size, size)
        r.center = (int(self.x), int(self.y))
        return r

    def _pick_new_target(self):
        margin = 200
        self.target_pos = (
            random.randint(self.room_left + margin, self.room_right - margin),
            random.randint(self.room_top + margin, self.room_bottom - margin),
        )

    @staticmethod
    def _lerp_angle(current, target, t):
        """Плавная интерполяция между двумя углами (с учётом перехода через ±π)."""
        diff = target - current
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return current + diff * t

    def update(self, target=None):
        if self.is_destroyed:
            return

        self.time += 0.016

        # --- ОПРЕДЕЛЕНИЕ ЦЕЛИ И АГРЕССИИ ---
        self.current_target = None
        self.state = "WANDER"
        self.target_dist = 0.0

        candidates = []
        if target is not None and not getattr(target, "is_destroyed", False):
            if hasattr(target, "velocity") and hasattr(target, "take_damage"):
                candidates.append(target)

        if self.sector and hasattr(self.sector, "objects"):
            for obj in self.sector.objects:
                if obj is self:
                    continue
                if hasattr(obj, "velocity") and hasattr(obj, "take_damage"):
                    if not getattr(obj, "is_destroyed", False):
                        candidates.append(obj)

        nearest_dist_sq = float("inf")
        for t in candidates:
            tdx = t.x - self.x
            tdy = t.y - self.y
            tdist_sq = tdx * tdx + tdy * tdy

            if tdist_sq < nearest_dist_sq and tdist_sq < self.detection_radius ** 2:
                nearest_dist_sq = tdist_sq
                self.current_target = t

        if self.current_target is not None:
            self.state = "AGGRESSIVE"
            tdx = self.current_target.x - self.x
            tdy = self.current_target.y - self.y
            self.target_dist = math.hypot(tdx, tdy)
            self.target_angle = math.atan2(tdy, tdx)

        # --- ПЛАВНЫЙ ПОВОРОТ И ВЫТЯГИВАНИЕ ЩУПАЛЬЦА ---
        if self.state == "AGGRESSIVE":
            # Плавно поворачиваем щупальце к цели
            self.tentacle_angle = self._lerp_angle(
                self.tentacle_angle, self.target_angle, self.tentacle_angle_speed
            )
            # Постепенно вытягиваем
            if self.target_dist > self.absorb_radius:
                self.tentacle_growth = min(1.0, self.tentacle_growth + self.tentacle_growth_speed)
            else:
                # Цель в зоне поглощения — втягиваем щупальце
                self.tentacle_growth = max(0.0, self.tentacle_growth - self.tentacle_retract_speed)
        else:
            # Нет цели — втягиваем щупальце
            self.tentacle_growth = max(0.0, self.tentacle_growth - self.tentacle_retract_speed)

        # --- ДВИЖЕНИЕ ---
        if self.state == "AGGRESSIVE":
            dx = self.current_target.x - self.x
            dy = self.current_target.y - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                self.velocity_x += (dx / dist) * self.acceleration
                self.velocity_y += (dy / dist) * self.acceleration

                cur_speed = math.hypot(self.velocity_x, self.velocity_y)
                if cur_speed > self.aggressive_speed:
                    self.velocity_x = (self.velocity_x / cur_speed) * self.aggressive_speed
                    self.velocity_y = (self.velocity_y / cur_speed) * self.aggressive_speed
        else:
            if self.target_pos is None:
                self._pick_new_target()

            dx = self.target_pos[0] - self.x
            dy = self.target_pos[1] - self.y
            dist = math.hypot(dx, dy)

            if dist < 60:
                self._pick_new_target()
            elif dist > 0:
                self.velocity_x += (dx / dist) * self.acceleration
                self.velocity_y += (dy / dist) * self.acceleration

            speed = math.hypot(self.velocity_x, self.velocity_y)
            if speed > self.max_speed:
                self.velocity_x = (self.velocity_x / speed) * self.max_speed
                self.velocity_y = (self.velocity_y / speed) * self.max_speed

        # Трение
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction

        # Органическое покачивание
        self.x += self.velocity_x + math.sin(self.time * 0.5) * 0.3
        self.y += self.velocity_y + math.cos(self.time * 0.7) * 0.3

        # Ограничение по сектору
        self.x = max(self.room_left + self.base_radius,
                     min(self.x, self.room_right - self.base_radius))
        self.y = max(self.room_top + self.base_radius,
                     min(self.y, self.room_bottom - self.base_radius))

        # --- ПОГЛОЩЕНИЕ ---
        self.absorbing = False
        self.absorb_target = None

        if self.current_target and not getattr(self.current_target, "is_destroyed", False):
            tdx = self.current_target.x - self.x
            tdy = self.current_target.y - self.y
            tdist = math.hypot(tdx, tdy)

            if tdist < self.absorb_radius:
                self.absorbing = True
                self.absorb_target = self.current_target

                if hasattr(self.current_target, "velocity"):
                    vx = getattr(self.current_target.velocity, "x", 0)
                    vy = getattr(self.current_target.velocity, "y", 0)
                    setattr(self.current_target.velocity, "x", vx * self.absorb_slow_factor)
                    setattr(self.current_target.velocity, "y", vy * self.absorb_slow_factor)

                self.current_target.take_damage(self.absorb_damage)

                if tdist > 0:
                    pull_x = (tdx / tdist) * self.absorb_pull
                    pull_y = (tdy / tdist) * self.absorb_pull
                    self.current_target.x -= pull_x
                    self.current_target.y -= pull_y

    def take_damage(self, amount):
        if self.is_destroyed:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.is_destroyed = True
            print("[SUCCESS] Космическая амёба уничтожена!")

    def draw(self, surface, camera):
        if self.is_destroyed:
            return

        cam_x = camera.x
        cam_y = camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # --- ПСЕВДОПОДИЯ (ПОСТЕПЕННО ВЫТЯГИВАЕТСЯ) ---
        # Рисуем только если growth > 0.01 и цель за пределами радиуса поглощения
        # --- ПСЕВДОПОДИЯ (ВЫТЯГИВАЕТСЯ И МЕДЛЕННО ВТЯГИВАЕТСЯ) ---
        if self.tentacle_growth > 0.01:

            # Если цель ещё видна — тянемся к ней; если нет — щупальце втягивается с последним углом
            if self.current_target and self.target_dist > self.absorb_radius:
                max_len = min(self.target_dist * 0.8, 250)
            else:
                max_len = 250  # фиксированная длина при втягивании
            stretch_len = max_len * self.tentacle_growth

            # Количество сегментов тоже зависит от growth — растёт вместе с длиной
            num_segments = max(3, int(16 * self.tentacle_growth))

            for i in range(num_segments):
                t = i / max(1, num_segments - 1)
                seg_dist = t * stretch_len

                # Органическое волнообразное искривление
                wave = math.sin(self.time * 2.5 + t * 5) * 6 * t
                perp_x = -math.sin(self.tentacle_angle) * wave
                perp_y = math.cos(self.tentacle_angle) * wave

                seg_x = int(draw_x + math.cos(self.tentacle_angle) * seg_dist + perp_x)
                seg_y = int(draw_y + math.sin(self.tentacle_angle) * seg_dist + perp_y)

                # Радиус сужается от 34 (у основания) до 5 (на кончике)
                seg_r = int(34 * (1 - t * 0.85) + 5)

                shade = max(28, 48 - int(t * 18))
                if self.absorbing:
                    color = (shade, shade - 5, shade - 8)
                else:
                    color = (shade, shade, shade + 5)

                pygame.draw.circle(surface, color, (seg_x, seg_y), seg_r)

        # --- ТЕЛО АМЁБЫ (С ДЕФОРМАЦИЕЙ В СТОРОНУ ЦЕЛИ) ---
        surf_size = int(self.base_radius * 3.6)
        amoeba_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        cx = surf_size // 2
        cy = surf_size // 2

        points = []
        for i in range(self.num_points):
            angle = (i / self.num_points) * 2 * math.pi
            r = self.base_radius
            r += math.sin(self.time * self.point_speeds[i] + self.point_phases[i]) * self.point_amps[i]

            # Деформация тела в сторону щупальца (используем плавный угол)
            if self.state == "AGGRESSIVE" and self.tentacle_growth > 0.1:
                angle_diff = angle - self.tentacle_angle
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                bulge = max(0, math.cos(angle_diff)) * 25 * self.tentacle_growth
                r += bulge

            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            points.append((px, py))

        # Цвета: тёмно-серый
        if self.absorbing:
            body_color = (60, 60, 70, 90)
            edge_color = (100, 100, 120, 180)
        elif self.state == "AGGRESSIVE":
            body_color = (50, 50, 60, 80)
            edge_color = (90, 90, 110, 170)
        else:
            body_color = (45, 45, 55, 75)
            edge_color = (80, 80, 100, 150)

        pygame.draw.polygon(amoeba_surf, body_color, points)
        pygame.draw.polygon(amoeba_surf, edge_color, points, 2)

        # --- ВНУТРЕННИЕ ЯДРА ---
        for nuc in self.nuclei:
            nx = cx + nuc["offset_x"] + math.sin(self.time * nuc["speed"] + nuc["phase"]) * 6
            ny = cy + nuc["offset_y"] + math.cos(self.time * nuc["speed"] + nuc["phase"]) * 6
            nr = nuc["radius"] + math.sin(self.time * nuc["speed"] * 1.3 + nuc["phase"]) * 3

            nuc_color = (120, 80, 40, 160) if not self.absorbing else (180, 60, 40, 200)
            pygame.draw.circle(amoeba_surf, nuc_color, (int(nx), int(ny)), max(2, int(nr)))

        # --- МЕМБРАНА ПОГЛОЩЕНИЯ ---
        if self.absorbing:
            pulse = math.sin(self.time * 5) * 0.5 + 0.5
            membrane_r = int(self.absorb_radius * (0.7 + pulse * 0.15))
            membrane_color = (200, 40, 40, int(60 + pulse * 60))
            pygame.draw.circle(amoeba_surf, membrane_color, (cx, cy), membrane_r, 3)

        surface.blit(amoeba_surf, (draw_x - cx, draw_y - cy))

        # --- HP БАР ---
        if self.hp < self.max_hp:
            bar_w = 100
            bar_h = 5
            bar_x = int(draw_x - bar_w // 2)
            bar_y = int(draw_y - self.base_radius - 25)

            pygame.draw.rect(surface, (30, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            if fill_w > 0:
                pygame.draw.rect(surface, (80, 200, 100), (bar_x, bar_y, fill_w, bar_h))
            pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h), 1)

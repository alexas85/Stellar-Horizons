# game_objects/amoeba.py
import pygame
import math
import random


class SpaceAmoeba:
    """
    Космическая амёба: тёмно-серая, тянется к цели псевдоподией.
    Отросток постепенно вырастает из центра и плавно меняет направление.
    Отрисовка полностью процедурная — без спрайтов.
    """

    def __init__(self, x, y, room_left, room_top, room_right, room_bottom,
                 scale_factor=1.0, has_tentacles=True):
        self.x = x
        self.y = y

        # Границы сектора
        self.room_left = room_left
        self.room_top = room_top
        self.room_right = room_right
        self.room_bottom = room_bottom

        # Размеры (с масштабированием)
        self.base_radius = 80 * scale_factor
        self.absorb_radius = 65 * scale_factor
        self.detection_radius = 300 * scale_factor
        self.scale_factor = scale_factor
        self.has_tentacles = has_tentacles

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
        self.tentacle_growth = 0.0  # 0 = втянут, 1 = полностью вытянут
        self.tentacle_growth_speed = 0.012  # скорость роста за кадр
        self.tentacle_retract_speed = 0.015  # медленное втягивание
        self.tentacle_alpha = 0.0  # 0 = невидимо, 1 = полностью проявлено
        self.tentacle_fade_speed = 0.015  # скорость проявления/затухания
        self.tentacle_angle = 0.0          # текущий угол щупальца (плавный)
        self.tentacle_angle_speed = 0.03   # скорость поворота к новому углу

        # Анимация формы
        self.time = 0.0
        self.num_points = 28
        self.point_phases = [random.uniform(0, 2 * math.pi) for _ in range(self.num_points)]
        self.point_speeds = [random.uniform(0.8, 1.6) for _ in range(self.num_points)]
        self.point_amps = [random.uniform(8, 22) * scale_factor for _ in range(self.num_points)]

        # Внутренние ядра
        self.nuclei = []
        for _ in range(random.randint(3, 6)):
            self.nuclei.append({
                "offset_x": random.uniform(-35, 35) * scale_factor,
                "offset_y": random.uniform(-35, 35) * scale_factor,
                "radius": random.uniform(6, 16) * scale_factor,
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
        self.hp = 100 # позже будет 300
        self.max_hp = 100  # позже будет 300
        self.is_destroyed = False
        self.hp_bar_alpha = 0
        self._frames_since_damage = 0
        # --- ЛОГИКА СМЕРТИ ---
        self.death_state = "ALIVE"    # ALIVE → DYING → BURST
        self.death_timer = 0.0
        self.death_scale = 1.0
        self.death_pulse_boost = 1.0
        self.fully_destroyed = False
        self.pending_crystal_count = 0
        self.death_circles = []


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
        if self.fully_destroyed:
            return
        if self.death_state != "ALIVE":
            self._update_death()
            return

        self.time += 0.016

        self._frames_since_damage += 1
        if self._frames_since_damage > 180:  # 3 сек без урона
            self.hp_bar_alpha = max(0, self.hp_bar_alpha - 255 / 60)  # затухание за 1 сек

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

        # --- ЩУПАЛЬЦА (только если разрешены) ---
        if self.has_tentacles:
            if self.state == "AGGRESSIVE":
                self.tentacle_angle = self._lerp_angle(
                    self.tentacle_angle, self.target_angle, self.tentacle_angle_speed
                )
                if self.target_dist > self.absorb_radius:
                    if self.tentacle_alpha < 1.0:
                        self.tentacle_alpha = min(1.0, self.tentacle_alpha + self.tentacle_fade_speed)
                    else:
                        self.tentacle_growth = min(1.0, self.tentacle_growth + self.tentacle_growth_speed)
                else:
                    self.tentacle_growth = max(0.0, self.tentacle_growth - self.tentacle_retract_speed)
            else:
                if self.tentacle_growth > 0.01:
                    self.tentacle_growth = max(0.0, self.tentacle_growth - self.tentacle_retract_speed)
                else:
                    self.tentacle_alpha = max(0.0, self.tentacle_alpha - self.tentacle_fade_speed)
        else:
            self.tentacle_alpha = 0.0
            self.tentacle_growth = 0.0

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

    def _update_death(self):
        self.death_timer += 0.016

        if self.death_state == "DYING":
            self.death_scale = max(0.33, 1.0 - self.death_timer * 0.1675)
            self.death_pulse_boost = min(2.0, 1.0 + self.death_timer * 0.25)

            if self.death_timer >= 4.0:
                self.death_state = "BURST"
                self.death_timer = 0.0
                self.pending_crystal_count = random.randint(1, 5)
                self._spawn_death_circles()
                print("[DEBUG] Амёба распадается на кристаллы и осколки")

        elif self.death_state == "BURST":
            # Обновляем прозрачность и позицию осколков
            dt = 0.016
            to_remove = []
            for c in self.death_circles:
                c['alpha'] -= c['fade_speed'] * dt
                c['x'] += c['drift_x'] * dt
                c['y'] += c['drift_y'] * dt
                if c['alpha'] <= 0:
                    to_remove.append(c)

            # Удаляем полностью исчезнувшие осколки
            for c in to_remove:
                self.death_circles.remove(c)

            # Если все осколки исчезли — помечаем объект как полностью уничтоженный
            if not self.death_circles:
                self.fully_destroyed = True

    def _spawn_death_circles(self):
        self.death_circles = []
        count = random.randint(12, 20)  # чуть больше осколков
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, self.base_radius * 0.2)  # стартуем ближе к центру
            speed = random.uniform(8.0, 14.0)  # быстрее разлёт
            self.death_circles.append({
                'x': self.x + math.cos(angle) * dist,
                'y': self.y + math.sin(angle) * dist,
                'radius': random.uniform(6, 12),  # в ~4 раза меньше
                'alpha': 255.0,
                'fade_speed': 50.0, #  random.uniform(1.0, 3.0),  # исчезают за ~1 сек
                'drift_x': math.cos(angle) * speed,
                'drift_y': math.sin(angle) * speed,
            })

    def take_damage(self, amount):
        if self.death_state != "ALIVE":
            return
        self.hp -= amount
        self.hp_bar_alpha = 255
        self._frames_since_damage = 0
        if self.hp <= 0:
            self.hp = 0
            self.death_state = "DYING"
            self.death_timer = 0.0
            self.is_destroyed = True  # для совместимости
            print("[SUCCESS] Космическая амёба начинает распадаться!")

    def draw(self, surface, camera):
        if self.fully_destroyed:
            return

        cam_x = camera.x
        cam_y = camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        if self.death_state == "BURST":
            # Убрали вспышку — теперь только осколки
            for c in self.death_circles:
                if c['alpha'] <= 0:
                    continue
                sx = int(c['x'] - cam_x)
                sy = int(c['y'] - cam_y)
                r = max(1, int(c['radius']))
                alpha = max(0, int(c['alpha']))
                circ_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                # Цвет осколков: светло-серый с прозрачностью
                pygame.draw.circle(circ_surf, (140, 150, 160, alpha), (r + 2, r + 2), r)
                surface.blit(circ_surf, (sx - r - 2, sy - r - 2))
            return

        # --- DYING и ALIVE: тело амёбы ---

        # Псевдоподия — только когда живы
        if self.tentacle_alpha > 0.01 and self.death_state == "ALIVE" and self.has_tentacles:
            if self.current_target and self.target_dist > self.absorb_radius:
                max_len = min(self.target_dist * 0.8, 250)
            else:
                max_len = 250
            stretch_len = max_len * self.tentacle_growth
            num_segments = max(3, int(16 * self.tentacle_growth))

            tentacle_surf_size = int(max_len + self.base_radius * 2 + 60)
            tentacle_surf = pygame.Surface((tentacle_surf_size, tentacle_surf_size), pygame.SRCALPHA)
            tcx = tentacle_surf_size // 2
            tcy = tentacle_surf_size // 2

            for i in range(num_segments):
                t = i / max(1, num_segments - 1)
                seg_dist = t * stretch_len
                wave = math.sin(self.time * 2.5 + t * 5) * 6 * t
                perp_x = -math.sin(self.tentacle_angle) * wave
                perp_y = math.cos(self.tentacle_angle) * wave
                seg_x = int(tcx + math.cos(self.tentacle_angle) * seg_dist + perp_x)
                seg_y = int(tcy + math.sin(self.tentacle_angle) * seg_dist + perp_y)
                seg_r = int(34 * (1 - t * 0.85) + 5)
                shade = max(28, 48 - int(t * 18))
                if self.absorbing:
                    color = (shade, shade - 5, shade - 8)
                else:
                    color = (shade, shade, shade + 5)
                pygame.draw.circle(tentacle_surf, color, (seg_x, seg_y), seg_r)

            tentacle_surf.set_alpha(int(255 * self.tentacle_alpha))
            surface.blit(tentacle_surf, (int(draw_x - tcx), int(draw_y - tcy)))

        # --- ТЕЛО АМЁБЫ ---
        effective_radius = self.base_radius * self.death_scale
        surf_size = int(self.base_radius * 3.6)
        amoeba_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        cx = surf_size // 2
        cy = surf_size // 2

        points = []
        for i in range(self.num_points):
            angle = (i / self.num_points) * 2 * math.pi
            r = effective_radius
            r += math.sin(self.time * self.point_speeds[i] * self.death_pulse_boost
                          + self.point_phases[i]) * self.point_amps[i] * self.death_pulse_boost

            if self.state == "AGGRESSIVE" and self.tentacle_growth > 0.1 and self.death_state == "ALIVE":
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

        # Внутренние ядра
        for nuc in self.nuclei:
            nx = cx + nuc["offset_x"] * self.death_scale + math.sin(
                self.time * nuc["speed"] + nuc["phase"]) * 6 * self.death_scale
            ny = cy + nuc["offset_y"] * self.death_scale + math.cos(
                self.time * nuc["speed"] + nuc["phase"]) * 6 * self.death_scale
            nr = (nuc["radius"] + math.sin(self.time * nuc["speed"] * 1.3 + nuc["phase"]) * 3) * self.death_scale
            nuc_color = (120, 80, 40, 160) if not self.absorbing else (180, 60, 40, 200)
            pygame.draw.circle(amoeba_surf, nuc_color, (int(nx), int(ny)), max(2, int(nr)))

        # Мембрана поглощения — только когда живы
        if self.absorbing and self.death_state == "ALIVE":
            pulse = math.sin(self.time * 5) * 0.5 + 0.5
            membrane_r = int(self.absorb_radius * (0.7 + pulse * 0.15))
            membrane_color = (200, 40, 40, int(60 + pulse * 60))
            pygame.draw.circle(amoeba_surf, membrane_color, (cx, cy), membrane_r, 3)

        surface.blit(amoeba_surf, (draw_x - cx, draw_y - cy))

        # HP бар — с затуханием
        if self.hp_bar_alpha > 0 and self.death_state == "ALIVE":
            bar_w = 100
            bar_h = 5
            bar_x = int(draw_x - bar_w // 2)
            bar_y = int(draw_y - self.base_radius - 25)
            alpha = int(self.hp_bar_alpha)
            bar_surf = pygame.Surface((bar_w + 2, bar_h + 2), pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, (30, 0, 0, alpha), (1, 1, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            if fill_w > 0:
                pygame.draw.rect(bar_surf, (80, 200, 100, alpha), (1, 1, fill_w, bar_h))
            pygame.draw.rect(bar_surf, (80, 80, 80, alpha), (1, 1, bar_w, bar_h), 1)
            surface.blit(bar_surf, (bar_x - 1, bar_y - 1))


import pygame
import math

# --- DEBUG ---
DEBUG_WARDEN = False  # True — рисует капсулу, safety-радиусы и границы кластеров

# --- НАСТРОЙКИ КЛАСТЕРИЗАЦИИ ---
SAFETY_RADIUS = 120
BELT_MARGIN = 150

# --- НАСТРОЙКИ КАПСУЛЫ ---
CAPSULE_LEN = 140
CAPSULE_RAD = 47

# --- НАСТРОЙКИ HP И УРОНА ---
WARDEN_MAX_HP = 100
RAM_DAMAGE = 20              # урон стражу за одно столкновение с large-астероидом
DAMAGE_COOLDOWN_FRAMES = 30  # 0.5 сек неуязвимости после удара (60 FPS)


class WardenShip:
    """Орбитальный страж — NPC, пролетающий через комнату по прямой с обходом препятствий."""

    def __init__(self, x, y, idle_sprite, movement_sprites, direction_angle):
        self.x = x
        self.y = y
        self.angle = direction_angle
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0

        # Спрайты
        self.idle_sprite = idle_sprite
        self.movement_sprites = movement_sprites
        self.original_image = idle_sprite

        # Физика — медленный, тяжёлый корабль
        self.max_speed = 2.5
        self.acceleration = 0.05
        self.max_angular_velocity = 0.8
        self.turn_step = 0.08
        self.mass = 500.0

        # Базовый курс (прямая траектория)
        self.base_direction_angle = direction_angle

        # Облёт препятствий
        self.avoidance_angle = 0.0
        self.avoidance_decay = 0.96
        self.obstacle_scan_range = 1650
        self.avoidance_deadzone = 2.0

        # Логика исчезновения
        self.out_of_view_timer = 0.0
        self.despawn_delay = 15000
        self.should_despawn = False

        # HP и урон
        self.hp = WARDEN_MAX_HP
        self.max_hp = WARDEN_MAX_HP
        self.is_destroyed = False
        self.damage_cooldown = 0

        # Спрайты астероидов для спавна осколков
        self.asteroid_sprites = None

        # Осколки, ждущие добавления в сектор
        self.pending_fragments = []

        # Анимация
        self.animation_index = 0
        self.animation_timer = 0
        self.is_thrusting = True

        # Сектор
        self.sector = None

        # Кэш кластеров для отрисовки DEBUG
        self._cached_clusters = []
        self._cached_belt = None

        self._update_rect()

    def set_sector(self, sector):
        self.sector = sector

    def set_asteroid_sprites(self, sprites):
        self.asteroid_sprites = sprites

    def _update_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

    # -------------------------------------------------------
    #  HP / УРОН
    # -------------------------------------------------------

    def take_damage(self, amount):
        """Страж получает урон. Неуязвим во время cooldown."""
        if self.is_destroyed:
            return
        if self.damage_cooldown > 0:
            return
        self.hp -= amount
        self.damage_cooldown = DAMAGE_COOLDOWN_FRAMES
        if self.hp <= 0:
            self.hp = 0
            self.is_destroyed = True
            self.should_despawn = True
            print("[DEBUG] Орбитальный страж уничтожен при таране!")

    # -------------------------------------------------------
    #  КАПСУЛЬНАЯ КОЛЛИЗИЯ
    # -------------------------------------------------------

    def _capsule_circle_collide(self, ast_x, ast_y, ast_radius):
        dx = ast_x - self.x
        dy = ast_y - self.y

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        local_x = dx * cos_a + dy * sin_a
        local_y = -dx * sin_a + dy * cos_a

        half_len = CAPSULE_LEN / 2
        clamped_x = max(-half_len, min(half_len, local_x))

        diff_x = local_x - clamped_x
        diff_y = local_y
        dist = math.sqrt(diff_x * diff_x + diff_y * diff_y)

        return dist <= (CAPSULE_RAD + ast_radius)

    # -------------------------------------------------------
    #  КЛАСТЕРИЗАЦИЯ
    # -------------------------------------------------------

    def _build_clusters(self):
        clusters = []
        belt_obstacle = None

        if self.sector is None or not hasattr(self.sector, 'asteroids'):
            return clusters, belt_obstacle

        if not self.sector.asteroids:
            return clusters, belt_obstacle

        large_asteroids = []
        belt_asteroids = []

        for ast in self.sector.asteroids:
            if getattr(ast, 'marked_for_removal', False):
                continue
            if ast.size_px < 64:
                continue

            if ast.orbit_center is not None:
                belt_asteroids.append(ast)
            else:
                large_asteroids.append(ast)

        n = len(large_asteroids)
        if n > 0:
            parent = list(range(n))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(a, b):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb

            for i in range(n):
                for j in range(i + 1, n):
                    dist = math.hypot(
                        large_asteroids[i].x - large_asteroids[j].x,
                        large_asteroids[i].y - large_asteroids[j].y
                    )
                    if dist < SAFETY_RADIUS * 2:
                        union(i, j)

            groups = {}
            for i in range(n):
                root = find(i)
                if root not in groups:
                    groups[root] = []
                groups[root].append(large_asteroids[i])

            for group in groups.values():
                cx = sum(a.x for a in group) / len(group)
                cy = sum(a.y for a in group) / len(group)
                max_dist = 0
                for a in group:
                    d = math.hypot(a.x - cx, a.y - cy) + SAFETY_RADIUS
                    if d > max_dist:
                        max_dist = d
                clusters.append((cx, cy, max_dist))

        if belt_asteroids:
            orbit_cx, orbit_cy = belt_asteroids[0].orbit_center
            max_orbit_r = max(a.orbit_radius for a in belt_asteroids)
            belt_radius = max_orbit_r + BELT_MARGIN
            belt_obstacle = (orbit_cx, orbit_cy, belt_radius)

        return clusters, belt_obstacle

    # -------------------------------------------------------
    #  УКЛОНЕНИЕ
    # -------------------------------------------------------

    def _check_obstacles_ahead(self):
        clusters, belt_obstacle = self._build_clusters()
        self._cached_clusters = clusters
        self._cached_belt = belt_obstacle

        obstacles = list(clusters)
        if belt_obstacle:
            obstacles.append(belt_obstacle)

        if not obstacles:
            self.avoidance_angle *= self.avoidance_decay
            if abs(self.avoidance_angle) < self.avoidance_deadzone:
                self.avoidance_angle = 0.0
            return

        rad = math.radians(self.angle)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)

        total_pressure = 0.0

        for obs_cx, obs_cy, obs_radius in obstacles:
            dx = obs_cx - self.x
            dy = obs_cy - self.y
            dist = math.hypot(dx, dy)

            if dist > self.obstacle_scan_range or dist < 1:
                continue

            forward_proj = dx * dir_x + dy * dir_y
            if forward_proj < 0:
                continue

            perp_x = -dir_y
            perp_y = dir_x
            side_offset = dx * perp_x + dy * perp_y

            corridor_width = obs_radius + 80

            if abs(side_offset) < corridor_width:
                proximity = 1.0 - (forward_proj / self.obstacle_scan_range)
                lateral_factor = 1.0 - (abs(side_offset) / corridor_width)

                sign = -1 if side_offset > 0 else 1
                total_pressure += sign * proximity * lateral_factor

        if abs(total_pressure) > 0.01:
            target_avoidance = max(-70, min(70, total_pressure * 40))
            self.avoidance_angle += (target_avoidance - self.avoidance_angle) * 0.08
        else:
            self.avoidance_angle *= self.avoidance_decay
            if abs(self.avoidance_angle) < self.avoidance_deadzone:
                self.avoidance_angle = 0.0

    # -------------------------------------------------------
    #  СТОЛКНОВЕНИЯ
    # -------------------------------------------------------

    def _handle_asteroid_collisions(self):
        """
        Мелкие/средние (<=32px) — отскок.
        Крупные (>=64px) — отскок + разрушение на осколки + урон стражу.
        """
        if self.sector is None or not hasattr(self.sector, 'asteroids'):
            return

        speed = self.velocity.length()

        for ast in self.sector.asteroids:
            if getattr(ast, 'marked_for_removal', False):
                continue

            ast_radius = ast.size_px / 2

            if not self._capsule_circle_collide(ast.x, ast.y, ast_radius):
                continue

            dx = ast.x - self.x
            dy = ast.y - self.y
            dist = math.hypot(dx, dy)

            if dist <= 0:
                continue

            dx /= dist
            dy /= dist

            if ast.size_px <= 32:
                # Мелкие и средние — только отскок
                push_force = 3.0 + speed * 2.0
                ast.apply_knockback(dx * push_force, dy * push_force)
            else:
                # Крупные — отскок + разрушение + урон стражу
                push_force = 0.8 + speed * 0.5
                ast.apply_knockback(dx * push_force, dy * push_force)

                # Разрушаем астероид (логика как при обстреле)
                ast.take_damage(9999)
                if ast.hp <= 0:
                    ast.marked_for_removal = True
                    if self.asteroid_sprites:
                        fragments = ast.spawn_fragments(self.asteroid_sprites)
                        for frag in fragments:
                            if frag is not None:
                                self.pending_fragments.append(frag)

                # Страж получает урон от тарана
                self.take_damage(RAM_DAMAGE)

    # -------------------------------------------------------
    #  ДВИЖЕНИЕ
    # -------------------------------------------------------

    def _rotate_towards(self, target_angle):
        diff = target_angle - self.angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        target_angular = math.copysign(self.max_angular_velocity, diff)

        if abs(self.angular_velocity - target_angular) < self.turn_step:
            self.angular_velocity = target_angular
        else:
            if self.angular_velocity < target_angular:
                self.angular_velocity += self.turn_step
            else:
                self.angular_velocity -= self.turn_step

    def update(self, camera_rect=None):
        self._check_obstacles_ahead()
        self._handle_asteroid_collisions()

        # Кулдаун урона
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

        effective_angle = self.base_direction_angle + self.avoidance_angle
        self._rotate_towards(effective_angle)

        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * self.acceleration

        speed = self.velocity.length()
        if speed > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.velocity *= 0.99
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        self.x += self.velocity.x
        self.y += self.velocity.y

        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        # Логика исчезновения
        if camera_rect is not None and not self.is_destroyed:
            in_view = camera_rect.collidepoint(self.x, self.y)
            if in_view:
                self.out_of_view_timer = 0.0
            else:
                self.out_of_view_timer += 16
                if self.out_of_view_timer >= self.despawn_delay:
                    self.should_despawn = True

        self._update_animation()
        self._update_rect()

    # -------------------------------------------------------
    #  АНИМАЦИЯ И ОТРИСОВКА
    # -------------------------------------------------------

    def _update_animation(self):
        speed = self.velocity.length()
        if self.is_thrusting and speed > 0.1 and self.movement_sprites:
            self.animation_timer += 1
            if self.animation_timer >= 6:
                self.animation_index = (self.animation_index + 1) % len(self.movement_sprites)
                self.animation_timer = 0
            self.original_image = self.movement_sprites[self.animation_index]
        else:
            self.original_image = self.idle_sprite

    def _draw_capsule_debug(self, surface, cam_x, cam_y):
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        half_len = CAPSULE_LEN / 2

        corners_local = [
            ( half_len,  CAPSULE_RAD),
            ( half_len, -CAPSULE_RAD),
            (-half_len, -CAPSULE_RAD),
            (-half_len,  CAPSULE_RAD),
        ]

        corners_world = []
        for lx, ly in corners_local:
            wx = self.x + lx * cos_a - ly * sin_a
            wy = self.y + lx * sin_a + ly * cos_a
            corners_world.append((wx - cam_x, wy - cam_y))

        pygame.draw.polygon(surface, (255, 255, 0), corners_world, 2)

        for end_x in (-half_len, half_len):
            cx = self.x + end_x * cos_a
            cy = self.y + end_x * sin_a
            pygame.draw.circle(surface, (255, 255, 0),
                               (int(cx - cam_x), int(cy - cam_y)),
                               CAPSULE_RAD, 2)

        pygame.draw.circle(surface, (255, 100, 100),
                           (int(self.x - cam_x), int(self.y - cam_y)), 3)

    def draw(self, surface, camera):
        if isinstance(camera, tuple):
            cam_x, cam_y = camera
        else:
            cam_x, cam_y = camera.x, camera.y

        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        rotated = pygame.transform.rotate(self.original_image, -self.angle)
        rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
        surface.blit(rotated, rect)

        # --- HP бар (как у амёбы) ---
        if self.hp < self.max_hp and not self.is_destroyed:
            bar_w = 100
            bar_h = 5
            bar_x = int(draw_x - bar_w // 2)
            bar_y = int(draw_y - rect.height // 2 - 12)
            pygame.draw.rect(surface, (30, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            if fill_w > 0:
                pygame.draw.rect(surface, (80, 200, 100), (bar_x, bar_y, fill_w, bar_h))
            pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h), 1)

        # --- DEBUG ---
        if DEBUG_WARDEN:
            self._draw_capsule_debug(surface, cam_x, cam_y)

            if self.sector and hasattr(self.sector, 'asteroids'):
                for ast in self.sector.asteroids:
                    if getattr(ast, 'marked_for_removal', False):
                        continue
                    if ast.size_px >= 64 and ast.orbit_center is None:
                        sx = int(ast.x - cam_x)
                        sy = int(ast.y - cam_y)
                        pygame.draw.circle(surface, (255, 80, 80), (sx, sy), SAFETY_RADIUS, 1)

            for cx, cy, r in self._cached_clusters:
                sx = int(cx - cam_x)
                sy = int(cy - cam_y)
                pygame.draw.circle(surface, (80, 255, 80), (sx, sy), int(r), 2)

            if self._cached_belt:
                bx, by, br = self._cached_belt
                sx = int(bx - cam_x)
                sy = int(by - cam_y)
                pygame.draw.circle(surface, (80, 80, 255), (sx, sy), int(br), 2)

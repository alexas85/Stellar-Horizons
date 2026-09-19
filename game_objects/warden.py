import pygame
import math


class WardenShip:
    """Орбитальный страж — NPC, пролетающий через комнату по прямой с обходом крупных астероидов."""

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
        self.mass = 500.0  # Очень тяжёлый — мелкие астероиды его не сдвинут

        # Базовый курс (прямая траектория)
        self.base_direction_angle = direction_angle

        # Облёт препятствий — только крупные астероиды (64px+)
        self.avoidance_angle = 0.0
        self.avoidance_decay = 0.96
        self.obstacle_scan_range = 1650
        self.avoidance_deadzone = 2.0

        # Логика исчезновения
        self.out_of_view_timer = 0.0
        self.despawn_delay = 15000
        self.should_despawn = False

        # Анимация
        self.animation_index = 0
        self.animation_timer = 0
        self.is_thrusting = True

        # Сектор для проверки астероидов
        self.sector = None

        self._update_rect()

    def set_sector(self, sector):
        self.sector = sector

    def _update_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

    def _check_obstacles_ahead(self):
        """
        Суммарное давление от всех крупных астероидов (64px+) в коридоре.
        Каждый астероид толкает корабль вбок — чем ближе, тем сильнее.
        Сумма всех сил даёт стабильное направление уклонения без качания.
        """
        if self.sector is None or not hasattr(self.sector, 'asteroids'):
            self.avoidance_angle *= self.avoidance_decay
            if abs(self.avoidance_angle) < self.avoidance_deadzone:
                self.avoidance_angle = 0.0
            return

        if not self.sector.asteroids:
            self.avoidance_angle *= self.avoidance_decay
            if abs(self.avoidance_angle) < self.avoidance_deadzone:
                self.avoidance_angle = 0.0
            return

        rad = math.radians(self.angle)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)

        # Суммарное давление: + = вправо, - = влево
        total_pressure = 0.0

        for ast in self.sector.asteroids:
            if getattr(ast, 'marked_for_removal', False):
                continue

            # Игнорируем мелкие и средние — уклоняемся только от крупных
            if ast.size_px < 64:
                continue

            dx = ast.x - self.x
            dy = ast.y - self.y
            dist = math.hypot(dx, dy)

            if dist > self.obstacle_scan_range or dist < 1:
                continue

            # Проекция вперёд — астероид впереди или позади?
            forward_proj = dx * dir_x + dy * dir_y
            if forward_proj < 0:
                continue

            # Боковое смещение — справа или слева?
            perp_x = -dir_y
            perp_y = dir_x
            side_offset = dx * perp_x + dy * perp_y

            ast_radius = max(ast.rect.width, ast.rect.height) / 2 if hasattr(ast, 'rect') else 32
            corridor_width = ast_radius + 80

            if abs(side_offset) < corridor_width:
                # Сила: тем больше, чем ближе астероид (по дистанции и по боку)
                proximity = 1.0 - (forward_proj / self.obstacle_scan_range)
                lateral_factor = 1.0 - (abs(side_offset) / corridor_width)

                # Знак: астероид справа → толкаем влево (отрицательное давление)
                #       астероид слева → толкаем вправо (положительное давление)
                sign = -1 if side_offset > 0 else 1

                total_pressure += sign * proximity * lateral_factor

        if abs(total_pressure) > 0.01:
            # Превращаем давление в угол уклонения (ограничиваем 60°)
            target_avoidance = max(-60, min(60, total_pressure * 40))

            # Плавная интерполяция — никакого резкого скачка
            self.avoidance_angle += (target_avoidance - self.avoidance_angle) * 0.08
        else:
            # Препятствий нет — плавно возвращаемся к прямому курсу
            self.avoidance_angle *= self.avoidance_decay
            if abs(self.avoidance_angle) < self.avoidance_deadzone:
                self.avoidance_angle = 0.0

    def _handle_small_asteroid_collisions(self):
        """Толкает мелкие (16px) и средние (32px) астероиды при столкновении. Страж не реагирует."""
        if self.sector is None or not hasattr(self.sector, 'asteroids'):
            return

        warden_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        warden_rect.center = (int(self.x), int(self.y))

        speed = self.velocity.length()

        for ast in self.sector.asteroids:
            if getattr(ast, 'marked_for_removal', False):
                continue

            # Только мелкие и средние
            if ast.size_px > 32:
                continue

            if warden_rect.colliderect(ast.rect):
                dx = ast.x - self.x
                dy = ast.y - self.y
                dist = math.hypot(dx, dy)

                if dist > 0:
                    dx /= dist
                    dy /= dist

                    # Сила толчка: базовая + от скорости стража
                    push_force = 3.0 + speed * 2.0

                    ast.apply_knockback(dx * push_force, dy * push_force)

    def _rotate_towards(self, target_angle):
        """Плавный поворот к целевому углу."""
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
        # Облёт крупных препятствий (суммарное давление)
        self._check_obstacles_ahead()

        # Толкаем мелкие астероиды при столкновении
        self._handle_small_asteroid_collisions()

        # Целевой угол = базовый курс + уклонение
        effective_angle = self.base_direction_angle + self.avoidance_angle
        self._rotate_towards(effective_angle)

        # Движение вперёд
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
        if camera_rect is not None:
            in_view = camera_rect.collidepoint(self.x, self.y)
            if in_view:
                self.out_of_view_timer = 0.0
            else:
                self.out_of_view_timer += 16
                if self.out_of_view_timer >= self.despawn_delay:
                    self.should_despawn = True

        self._update_animation()
        self._update_rect()

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

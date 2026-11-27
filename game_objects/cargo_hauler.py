# game_objects/cargo_hauler.py
"""Транспортник 4 класса (CargoHauler) — без вооружения.

Летит в случайном направлении, облетая астероиды. Если в группе несколько
транспортников — держатся строем рядом. При обстреле слегка ускоряется.
Ракеты игрока наводятся на него как на разведчика/истребителя.
"""

import math
import random

import pygame

from config import SHIP_ACCELERATION, SHIP_FRICTION, ROOM_WIDTH, ROOM_HEIGHT


class CargoHauler:
    """Грузовой транспортник. Не стреляет, пытается уйти от игрока."""

    def __init__(self, x, y, idle_sprite, movement_sprites, sector_x, sector_y,
                 room_width, room_height, group_id=None):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0

        # Физика — в 2 раза медленнее, чтобы игрок мог догнать
        self.max_speed = 2.25
        self.boosted_speed = 3.25          # скорость после обстрела
        self.max_angular_velocity = 3.0
        self.turn_acceleration = 0.3
        self.collision_force = 8.0

        # Спрайты
        self.idle_sprite = idle_sprite
        self.movement_sprites = movement_sprites
        self.original_image = idle_sprite

        # Текущая скорость (может измениться при обстреле)
        self.current_speed = self.max_speed

        # Постоянный курс полёта (в градусах) — транспортник летит в одном
        # направлении, облетая астероиды, и не останавливается на границах.
        self.heading_angle = random.uniform(0, 360)
        self.group_heading = None          # общее направление для группы (Vector2)

        # Облёт препятствий
        self.sector = None
        self.obstacle_scan_range = 400
        self.avoidance_angle = 60
        self.avoidance_direction = 1
        self.avoidance_decay = 0.90

        # Сектор/комната, к которой принадлежит транспортник
        self.room_x = sector_x
        self.room_y = sector_y

        # Границы комнаты
        self.room_left = sector_x * room_width
        self.room_right = (sector_x + 1) * room_width
        self.room_top = sector_y * room_height
        self.room_bottom = (sector_y + 1) * room_height

        # Ссылка на генератор миров (для перелёта между комнатами).
        # Устанавливается из spawn-кода.
        self.generator = None

        # Идентификатор группы: транспортники с одним group_id держатся рядом
        self.group_id = group_id
        # Позиция в строю относительно ведущего (для 2 и 3 транспортников)
        self.formation_offset = pygame.math.Vector2(0, 0)

        # Здоровье: нужно несколько попаданий пуль
        self.hp = 220
        self.max_hp = 220
        self.is_destroyed = False
        self.destroyed_sprite = None
        self.physics_active = True
        self.combat_target = None

        # Анимация
        self.animation_index = 0
        self.animation_timer = 0
        self.is_thrusting = False

        # Флаг «был ли обстрелян» — при первом обстреле ускоряемся
        self.agitated = False

        # Состояние побега после потери товарища
        self.fleeing = False      # True, когда транспортник спасается бегством

        # --- ИСЧЕЗНОВЕНИЕ БЕЗ ВНИМАНИЯ ИГРОКА ---
        # Время последнего «контакта» с игроком (сканирование радаром или погоня).
        # Если в течение минуты не было контакта — транспортник исчезает.
        self.last_attention_time = pygame.time.get_ticks()
        self.vanishing_timeout = 60000   # мс (1 минута)

        # Комната, где игрок начал нападение (для вызова отряда истребителей)
        self.attack_room = (self.room_x, self.room_y)

        self._update_rect()

    def set_sector(self, sector):
        """Привязывает сектор для проверки коллизий с астероидами."""
        self.sector = sector

    def set_destroyed_sprite(self, sprite):
        self.destroyed_sprite = sprite

    # ------------------------------------------------------------------ утилиты
    def _update_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

    def apply_impulse_to(self, obj, force):
        dx = obj.x - self.x
        dy = obj.y - self.y
        length = math.hypot(dx, dy)
        if length == 0:
            return
        obj.apply_knockback(dx / length * force, dy / length * force)

    def _check_obstacles_ahead(self):
        """Задаёт угол уклонения от астероидов впереди."""
        if self.sector is None or not self.sector.asteroids:
            self.avoidance_angle *= self.avoidance_decay
            return

        rad = math.radians(self.angle)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)
        closest_dist = self.obstacle_scan_range
        closest_side = 1

        for ast in self.sector.asteroids:
            if getattr(ast, "marked_for_removal", False):
                continue
            dx = ast.x - self.x
            dy = ast.y - self.y
            dist = math.hypot(dx, dy)
            if dist > self.obstacle_scan_range or dist < 1:
                continue
            forward_proj = dx * dir_x + dy * dir_y
            if forward_proj < 0:
                continue
            perp_x = -dir_y
            perp_y = dir_x
            side_offset = dx * perp_x + dy * perp_y
            ast_radius = max(ast.rect.width, ast.rect.height) / 2 if hasattr(ast, "rect") else 20
            if abs(side_offset) < ast_radius + 60:
                if forward_proj < closest_dist:
                    closest_dist = forward_proj
                    closest_side = -1 if side_offset > 0 else 1

        if closest_dist < self.obstacle_scan_range:
            urgency = 1.0 - (closest_dist / self.obstacle_scan_range)
            self.avoidance_angle = closest_side * urgency * 85
            self.avoidance_direction = closest_side
        else:
            self.avoidance_angle *= self.avoidance_decay
            if abs(self.avoidance_angle) < 0.5:
                self.avoidance_angle = 0

    def rotate_towards(self, target_angle):
        diff = target_angle - self.angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        target_angular = math.copysign(self.max_angular_velocity, diff)
        if abs(self.angular_velocity - target_angular) < self.turn_acceleration:
            self.angular_velocity = target_angular
        else:
            self.angular_velocity += (self.turn_acceleration
                                      if self.angular_velocity < target_angular
                                      else -self.turn_acceleration)

    # ------------------------------------------------------------- игровой цикл
    def mark_attention(self):
        """Отмечает, что игрок проявил интерес к транспортнику
        (сканировал радаром или преследует/обстреливает) — сбрасывает таймер исчезновения."""
        self.last_attention_time = pygame.time.get_ticks()

    def update(self, dt_ms=0, target=None):
        if self.is_destroyed:
            self._drift_destroyed()
            return

        # Погоня/обстрел игроком — момент внимания (обновляем таймер)
        if target is not None and not target.is_destroyed:
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.hypot(dx, dy)
            if dist < 600:
                self.mark_attention()

        # Если цель (игрок) в поле зрения и по нам стреляли — стараемся уйти
        if target is not None and self.agitated and not target.is_destroyed:
            if dist < 600:
                # Курс прочь от игрока
                flee_angle = math.degrees(math.atan2(-dy, -dx))
                self.rotate_towards(flee_angle)
                self.current_speed = self.boosted_speed
                self._trust_move(flee_angle)
                self.is_thrusting = True
                self._finish_motion()
                return

        # Нормальное движение: летим по постоянному курсу, облетая препятствия
        self._normal_flight()

    def _normal_flight(self):
        # Базовый курс — постоянное направление (для группы — общий курс группы)
        base_angle = self.heading_angle
        if self.group_heading is not None:
            base_angle = math.degrees(math.atan2(self.group_heading.y, self.group_heading.x))

        self._check_obstacles_ahead()
        eff_angle = base_angle + self.avoidance_angle
        self.rotate_towards(eff_angle)
        self._trust_move(eff_angle)
        self.is_thrusting = True
        self._finish_motion()

    def _trust_move(self, angle):
        rad = math.radians(angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * (SHIP_ACCELERATION * 0.85)
        if self.velocity.length() > self.current_speed:
            self.velocity.scale_to_length(self.current_speed)

    def _formation_bias(self, base_angle):
        """Транспортники в группе слегка подстраивают курс, чтобы держаться рядом."""
        # Без доступа к другим — просто возвращаем курс группы целиком,
        # а позиции расходим в спавне; здесь поддерживаем дистанцию слабой
        # коррекцией, чтобы не разлетались.
        return base_angle

    def _finish_motion(self):
        self.velocity *= SHIP_FRICTION
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0
        self.x += self.velocity.x
        self.y += self.velocity.y

        # Отскок от астероидов (в текущем секторе по позиции)
        self._check_collisions_with_asteroids()

        # --- СВОБОДНЫЙ ПОЛЁТ СКВОЗЬ ГРАНИЦЫ КОМНАТ ---
        # Транспортник НЕ привязан к комнате: вылетая за её пределы, продолжает
        # лететь дальше (координаты глобальные). Он не переносится и не пропадает.
        # Сектор для поиска препятствий пересчитываем каждый кадр по позиции.
        if self.generator is not None:
            self._update_current_sector()

        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self._update_animation()
        self._update_rect()

    def _update_current_sector(self):
        """Пересчитывает текущий сектор по глобальной позиции транспортника,
        чтобы облет препятствий работал в любой комнате, а не только в стартовой."""
        if self.generator is None:
            return
        local_x = int(self.x // ROOM_WIDTH)
        local_y = int(self.y // ROOM_HEIGHT)
        # Сектор уже привязан к правильной комнате — не трогаем
        if self.sector is not None and self.sector.x == local_x and self.sector.y == local_y:
            return
        try:
            spawn_sprites = getattr(self, "spawn_sprites", None)
            if spawn_sprites is not None:
                new_sector = self.generator.get_sector(
                    local_x, local_y, spawn_sprites[0],
                    wreck_sprite=spawn_sprites[1],
                    planet_sprite=spawn_sprites[2],
                    station_sprite=spawn_sprites[3],
                )
            else:
                new_sector = self.generator.get_sector(local_x, local_y)
        except Exception:
            return
        self.sector = new_sector
        self.room_x = local_x
        self.room_y = local_y

    def _check_collisions_with_asteroids(self):
        """Проверяет столкновения с астероидами текущего сектора."""
        if self.sector is None or not getattr(self.sector, "asteroids", None):
            return
        r = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        r.center = (int(self.x), int(self.y))
        for ast in self.sector.asteroids:
            if getattr(ast, "marked_for_removal", False):
                continue
            if r.colliderect(ast.rect):
                # Отталкиваем астероид и слегка меняем курс, но не останавливаемся
                self.apply_impulse_to(ast, self.collision_force)
                self.velocity *= 0.7
                break

    def _update_animation(self):
        speed = self.velocity.length()
        if speed < 0.15:
            self.is_thrusting = False
        if self.is_thrusting and speed >= 0.15 and self.movement_sprites:
            self.animation_timer += 1
            if self.animation_timer >= 5:
                self.animation_index = (self.animation_index + 1) % len(self.movement_sprites)
                self.animation_timer = 0
            self.original_image = self.movement_sprites[self.animation_index]
        else:
            self.is_thrusting = False
            self.original_image = self.idle_sprite
            self.animation_index = 0
            self.animation_timer = 0

    def _drift_destroyed(self):
        self.velocity *= SHIP_FRICTION
        self.angular_velocity *= 0.95
        self.x += self.velocity.x
        self.y += self.velocity.y
        self.x = max(self.room_left, min(self.x, self.room_right))
        self.y = max(self.room_top, min(self.y, self.room_bottom))
        self.angle += self.angular_velocity
        self._update_animation()
        self._update_rect()

    # ---------------------------------------------------------------- урон/огонь
    def take_damage(self, amount):
        """Получает урон. При первом попадании — в панику (ускорение)."""
        if self.is_destroyed:
            return
        # Обстрел — признак интереса игрока; фиксируем комнату, где напали
        self.mark_attention()
        if not self.agitated:
            self.agitated = True
            self.current_speed = self.boosted_speed
            # Комната, где игрок начал нападение (для вызова отряда)
            self.attack_room = (int(self.x // ROOM_WIDTH), int(self.y // ROOM_HEIGHT))
        # Транспортник мог убежать — комната нападения не меняется при повторном уроне
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_destroyed = True
            self.state = "DESTROYED"
            self.is_thrusting = False
            self.combat_target = None
            if self.destroyed_sprite:
                self.idle_sprite = self.destroyed_sprite
                self.movement_sprites = [self.destroyed_sprite]
                self.original_image = self.destroyed_sprite

    # ------------------------------------------------------------------ отрисовка
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
# game_objects/enemy.py
import pygame
import math
import random
from config import SHIP_ACCELERATION, SHIP_FRICTION
from game_objects.bullet import Bullet



class ScoutShip:
    def __init__(self, x, y, idle_sprite, movement_sprites, sector_x, sector_y, room_width, room_height):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0

        # Физика
        self.max_angular_velocity = 3.0
        self.turn_acceleration = 0.25
        self.max_speed = 6.0

        # Спрайты
        self.idle_sprite = idle_sprite
        self.movement_sprites = movement_sprites
        self.original_image = idle_sprite

        # Состояние патруля
        self.state = 'PICK_NEW'
        self.target_pos = None
        self.loiter_timer = 0
        self.loiter_duration = 2500  # мс

        # Сила отскока астероидов
        self.collision_force = 8.0


        # Границы комнаты — абсолютные мировые координаты
        self.room_left = sector_x * room_width
        self.room_right = (sector_x + 1) * room_width
        self.room_top = sector_y * room_height
        self.room_bottom = (sector_y + 1) * room_height

        # Анимация
        self.animation_index = 0
        self.animation_timer = 0
        self.is_thrusting = False

        # Ссылка на сектор — для проверки коллизий с астероидами
        self.sector = None


        self._update_rect()

    def set_sector(self, sector):
        """Привязывает сектор, чтобы разведчик видел астероиды."""
        self.sector = sector

    def apply_impulse_to(self, obj, force):
        """Толкает астероид от разведчика."""
        dx = obj.x - self.x
        dy = obj.y - self.y
        length = math.hypot(dx, dy)
        if length == 0:
            return
        dx /= length
        dy /= length
        obj.apply_knockback(dx * force, dy * force)


    def _update_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

    def pick_new_target(self):
        """Выбирает новую точку патрулирования в пределах комнаты."""
        margin = 400
        min_dist = 500

        for _ in range(20):  # максимум 20 попыток
            tx = random.randint(self.room_left + margin, self.room_right - margin)
            ty = random.randint(self.room_top + margin, self.room_bottom - margin)
            dist_sq = (tx - self.x) ** 2 + (ty - self.y) ** 2
            if dist_sq >= min_dist ** 2:
                self.target_pos = pygame.math.Vector2(tx, ty)
                self.state = 'SEEK'
                return

        # Если не нашли — берём любую точку
        tx = random.randint(self.room_left + margin, self.room_right - margin)
        ty = random.randint(self.room_top + margin, self.room_bottom - margin)
        self.target_pos = pygame.math.Vector2(tx, ty)
        self.state = 'SEEK'

    def rotate_towards(self, target_angle):
        """Плавный поворот к целевому углу."""
        diff = target_angle - self.angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        target_angular = math.copysign(self.max_angular_velocity, diff)

        if abs(self.angular_velocity - target_angular) < self.turn_acceleration:
            self.angular_velocity = target_angular
        else:
            if self.angular_velocity < target_angular:
                self.angular_velocity += self.turn_acceleration
            else:
                self.angular_velocity -= self.turn_acceleration

    def update(self, dt_ms=0, target=None):
        if self.state == 'PICK_NEW':
            self.pick_new_target()
            return

        target_angle = 0.0
        dist_to_target = 99999.0

        if self.target_pos is not None:
            dx = self.target_pos.x - self.x
            dy = self.target_pos.y - self.y
            dist_to_target = math.hypot(dx, dy)
            target_angle = math.degrees(math.atan2(dy, dx))

        if self.state == 'SEEK':
            self.rotate_towards(target_angle)
            rad = math.radians(self.angle)
            direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            self.velocity += direction * SHIP_ACCELERATION
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            self.is_thrusting = True

            if dist_to_target < 120:
                self.state = 'ARRIVE'

        elif self.state == 'ARRIVE':
            self.rotate_towards(target_angle)
            self.is_thrusting = False

            if self.velocity.length() < 0.5 or dist_to_target < 60:
                self.state = 'LOITER'
                self.loiter_timer = pygame.time.get_ticks()

        elif self.state == 'LOITER':
            self.is_thrusting = False
            rand_turn = random.uniform(-0.8, 0.8)
            self.rotate_towards(self.angle + rand_turn)

            now = pygame.time.get_ticks()
            if now - self.loiter_timer >= self.loiter_duration:
                self.state = 'PICK_NEW'

        # Трение
        self.velocity *= SHIP_FRICTION
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        # Движение
        self.x += self.velocity.x
        self.y += self.velocity.y

        # --- ОТСКОКИ ОТ АСТЕРОИДОВ ---
        if self.sector is not None and hasattr(self.sector, 'asteroids'):
            scout_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
            scout_rect.center = (int(self.x), int(self.y))

            for ast in self.sector.asteroids:
                if ast.marked_for_removal:
                    continue
                if scout_rect.colliderect(ast.rect):
                    # Столкновение: обнуляем скорость, толкаем астероид
                    self.velocity = pygame.math.Vector2(0, 0)
                    self.is_thrusting = False
                    self.apply_impulse_to(ast, self.collision_force)
                    # Путь заблокирован — выбираем новую точку
                    self.state = 'PICK_NEW'
                    break

        # Ограничение по комнате
        self.x = max(self.room_left, min(self.x, self.room_right))

        # Ограничение по комнате
        self.x = max(self.room_left, min(self.x, self.room_right))
        self.y = max(self.room_top, min(self.y, self.room_bottom))

        # Угол
        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self._update_animation()
        self._update_rect()

    def _update_animation(self):
        STOP_THRESHOLD = 0.15
        speed = self.velocity.length()

        if speed < STOP_THRESHOLD:
            self.is_thrusting = False

        if self.is_thrusting and speed >= STOP_THRESHOLD and self.movement_sprites:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_index = (self.animation_index + 1) % len(self.movement_sprites)
                self.animation_timer = 0
            self.original_image = self.movement_sprites[self.animation_index]
        else:
            self.is_thrusting = False
            self.original_image = self.idle_sprite
            self.animation_index = 0
            self.animation_timer = 0

    def draw(self, surface, camera):
        """Рисует корабль. Принимает как Rect, так и кортеж (x, y)."""
        if isinstance(camera, tuple):
            cam_x, cam_y = camera
        else:
            cam_x, cam_y = camera.x, camera.y

        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        rotated = pygame.transform.rotate(self.original_image, -self.angle)
        rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
        surface.blit(rotated, rect)

class DestroyerShip(ScoutShip):
    """Истребитель — патрулирует, а при сближении игрока — преследует и стреляет."""

    # Спрайт пули — устанавливается из main.py
    bullet_sprite = None

    @classmethod
    def set_bullet_sprite(cls, sprite):
        cls.bullet_sprite = sprite

    def __init__(self, x, y, idle_sprite, movement_sprites, sector_x, sector_y, room_width, room_height):
        super().__init__(x, y, idle_sprite, movement_sprites, sector_x, sector_y, room_width, room_height)

        # Перенастройка физики
        self.max_speed = 7.5
        self.max_angular_velocity = 3.5
        self.turn_acceleration = 0.3
        self.loiter_duration = 1200
        self.collision_force = 14.0

        # Боевые параметры
        self.detect_range = 300      # дистанция обнаружения игрока
        self.keep_distance = 150     # минимальная дистанция, ближе не подлетает
        self.fire_cooldown = 0
        self.cooldown_time = 400     # мс между выстрелами
        self.bullets = []
        self.combat_target = None

    def shoot(self):
        """Стреляет пулю в текущем направлении носа корабля."""
        if self.bullet_sprite is None:
            return

        current_time = pygame.time.get_ticks()
        if self.fire_cooldown > 0 and current_time < self.fire_cooldown:
            return

        new_bullet = Bullet(
            x=self.x,
            y=self.y,
            angle=self.angle,
            speed=10,
            max_distance=400,
            base_velocity=self.velocity
        )
        new_bullet.set_sprite(self.bullet_sprite)
        self.bullets.append(new_bullet)
        self.fire_cooldown = current_time + self.cooldown_time

    def update(self, dt_ms=0, target=None):
        """Обновление с боевой логикой. target — объект игрока (или None)."""
        # Проверка: виден ли игрок?
        if target is not None:
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.hypot(dx, dy)

            if dist <= self.detect_range:
                self.state = 'COMBAT'
                self.combat_target = target
            elif self.state == 'COMBAT':
                # Игрок убежал — возвращаемся к патрулю
                self.state = 'PICK_NEW'
                self.combat_target = None

        # Боевой режим — своя логика, не вызываем родительский update
        if self.state == 'COMBAT' and self.combat_target is not None:
            self._update_combat()
            self._update_animation()
            self._update_rect()
            return

        # Обычный патруль — родительская логика
        super().update(dt_ms)

    def _update_combat(self):
        """Логика боя: преследование, удержание дистанции, стрельба."""
        target = self.combat_target
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.hypot(dx, dy)

        # Угол к игроку
        target_angle = math.degrees(math.atan2(dy, dx))
        self.rotate_towards(target_angle)

        # Движение: если далеко — ускоряемся, если близко — тормозим
        if dist > self.keep_distance:
            rad = math.radians(self.angle)
            direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            self.velocity += direction * SHIP_ACCELERATION
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            self.is_thrusting = True
        else:
            # Близко — гасим скорость
            self.is_thrusting = False

        # Трение
        self.velocity *= SHIP_FRICTION
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        # Движение
        self.x += self.velocity.x
        self.y += self.velocity.y

        # Ограничение по комнате
        self.x = max(self.room_left, min(self.x, self.room_right))
        self.y = max(self.room_top, min(self.y, self.room_bottom))

        # Угол
        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        # Стрельба (с проверкой, что нос направлен примерно к игроку)
        angle_diff = target_angle - self.angle
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        if abs(angle_diff) < 30:  # стреляем только если нос смотрит на игрока
            self.shoot()

        # Отскоки от астероидов
        if self.sector is not None and hasattr(self.sector, 'asteroids'):
            scout_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
            scout_rect.center = (int(self.x), int(self.y))

            for ast in self.sector.asteroids:
                if ast.marked_for_removal:
                    continue
                if scout_rect.colliderect(ast.rect):
                    self.velocity = pygame.math.Vector2(0, 0)
                    self.is_thrusting = False
                    self.apply_impulse_to(ast, self.collision_force)
                    break

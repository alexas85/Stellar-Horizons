# game_objects/player.py
import pygame
import math
from config import SHIP_ACCELERATION
from game_objects.bullet import Bullet


class PlayerShip:
    def __init__(self, x, y, idle_sprite, movement_sprites):
        self.x = x
        self.y = y

        # Скорости ДО обнуления (для физики удара в main.py)
        self.last_vx = 0.0
        self.last_vy = 0.0

        self.angle = 0
        self.velocity = pygame.math.Vector2(0, 0)

        # Состояния
        self.on_planet_surface = False
        self.is_landing = False
        self.landing_progress = 0.0
        self.target_scale = 1.0
        self.min_scale = 0.15
        self.landing_speed = 0.005
        self.landing_move_speed = 0.7
        self.landing_target = None

        # Физика вращения
        self.angular_velocity = 0.0
        self.max_angular_velocity = 3.0
        self.turn_acceleration = 0.2
        self.max_speed = 8

        # Спрайты
        self.idle_sprite = idle_sprite
        self.movement_sprites = movement_sprites
        self.original_image = idle_sprite

        # rect инициализируем по центру
        self.rect = self.idle_sprite.get_rect(center=(self.x, self.y))

        # Анимация двигателей
        self.animation_index = 0
        self.animation_timer = 0
        self.is_thrusting = False

        # Выстрелы
        self.bullets = []
        self.fire_cooldown = 0
        self.cooldown_time = 250  # мс между выстрелами

        # Инвентарь
        self.inventory = {
            "metal": 0,
            "precious": 0,
            "crystal": 0,
            "energy": 0,
            "mineral": 0,
            "uranium": 0
        }

    def rotate(self, direction):
        """Плавное вращение корабля"""
        target_angular_velocity = direction * self.max_angular_velocity
        if abs(self.angular_velocity - target_angular_velocity) < self.turn_acceleration:
            self.angular_velocity = target_angular_velocity
        else:
            if self.angular_velocity < target_angular_velocity:
                self.angular_velocity += self.turn_acceleration
            else:
                self.angular_velocity -= self.turn_acceleration

    def accelerate(self):
        """Ускорение в направлении носа корабля"""
        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * SHIP_ACCELERATION
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.is_thrusting = True

    def start_landing(self, planet=None):
        """Начало посадки на планету"""
        self.is_landing = True
        self.landing_progress = 0.0
        self.on_planet_surface = False
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0

        if planet is not None and hasattr(planet, 'x') and hasattr(planet, 'y'):
            self.landing_target = pygame.math.Vector2(planet.x, planet.y)
        else:
            from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
            self.landing_target = pygame.math.Vector2(
                PLANET_ROOM_WIDTH // 2,
                PLANET_ROOM_HEIGHT // 2
            )

    def exit_planet(self, return_x, return_y):
        """Выход с планеты в космос"""
        self.on_planet_surface = False
        self.is_landing = False
        self.x = return_x
        self.y = return_y
        self.velocity = pygame.math.Vector2(0, 0)
        self.landing_progress = 0.0
        self.angular_velocity = 0.0
        self.is_thrusting = False
        self.landing_target = None
        self.target_scale = 1.0
        self._update_rect()

    def shoot(self, bullet_sprite):
        current_time = pygame.time.get_ticks()
        if self.fire_cooldown > 0 and current_time < self.fire_cooldown:
            return None

        new_bullet = Bullet(
            x=self.x,
            y=self.y,
            angle=self.angle,
            speed=12,
            max_distance=300,
            base_velocity=self.velocity  # <-- важно: передаём скорость корабля
        )
        new_bullet.set_sprite(bullet_sprite)

        self.bullets.append(new_bullet)
        self.fire_cooldown = current_time + self.cooldown_time
        return new_bullet

    def apply_impulse_to(self, obj, force):
        dx = obj.x - self.x
        dy = obj.y - self.y
        length = math.hypot(dx, dy)

        if length == 0:
            return

        dx /= length
        dy /= length

        # Используем встроенный метод астероида
        obj.apply_knockback(dx * force, dy * force)

    def update(self, world_objects=None):
        """
        Основной цикл обновления физики.
        world_objects: список объектов (астероидов) для проверки коллизий.
        Возвращает объект столкновения, если оно произошло, иначе None.
        """
        # Сохраняем скорость ДО изменений для передачи в main.py (физика удара)
        self.last_vx = float(self.velocity.x)
        self.last_vy = float(self.velocity.y)

        # --- ЛОГИКА ПОСАДКИ ---
        if self.is_landing and not self.on_planet_surface:
            if self.landing_target is None:
                from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
                self.landing_target = pygame.math.Vector2(PLANET_ROOM_WIDTH // 2, PLANET_ROOM_HEIGHT // 2)

            current_pos = pygame.math.Vector2(self.x, self.y)
            direction = self.landing_target - current_pos
            dist = direction.length()

            if dist < 2.0:
                self.x = self.landing_target.x
                self.y = self.landing_target.y
                self.landing_progress = 1.0
                self.on_planet_surface = True
                self.target_scale = self.min_scale
                self.landing_target = None
            else:
                direction.scale_to_length(self.landing_move_speed)
                self.x += direction.x
                self.y += direction.y
                self.landing_progress += self.landing_speed
                if self.landing_progress > 1.0:
                    self.landing_progress = 1.0
                t = self.landing_progress
                self.target_scale = max(self.min_scale, 1.0 - t * (1.0 - self.min_scale))

            self._update_rect()
            self._update_animation_and_bullets()
            return None  # Во время посадки коллизии с астероидами не проверяем

        # --- ЛОГИКА НА ПЛАНЕТЕ ---
        if self.on_planet_surface:
            self.velocity *= 0.98
            self.x += self.velocity.x
            self.y += self.velocity.y
            self.angular_velocity *= 0.95
            if abs(self.angular_velocity) < 0.01:
                self.angular_velocity = 0.0
            self._update_rect()
            self._update_animation_and_bullets()
            return None

        # --- ЛОГИКА КОСМОСА ---

        # Вращение
        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        # Трение
        self.velocity *= 0.98

        # Предсказание столкновения
        next_x = self.x + self.velocity.x
        next_y = self.y + self.velocity.y

        w = self.original_image.get_width()
        h = self.original_image.get_height()
        if self.is_landing and not self.on_planet_surface:
            w = int(w * self.target_scale)
            h = int(h * self.target_scale)

        temp_rect = pygame.Rect(0, 0, w, h)
        temp_rect.center = (next_x, next_y)

        collision_detected = False
        hit_object = None

        if world_objects:
            for obj in world_objects:
                if not hasattr(obj, 'rect'):
                    continue
                if temp_rect.colliderect(obj.rect):
                    collision_detected = True
                    hit_object = obj
                    break

        if collision_detected and hit_object:
            # СТОЛКНОВЕНИЕ:

            # 1. Сбрасываем скорость корабля
            self.velocity = pygame.math.Vector2(0, 0)

            # 2. СРАЗУ выключаем тягу при ударе — иначе анимация может «подмигивать»
            self.is_thrusting = False

            # 3. Применяем импульс к астероиду
            self.apply_impulse_to(hit_object, 12.0)

            self._update_rect()
            self._update_animation_and_bullets()
            return hit_object

        else:
            # НЕТ СТОЛКНОВЕНИЯ: применяем движение
            self.x = next_x
            self.y = next_y
            self._update_rect()
            self._update_animation_and_bullets()
            return None

    def _update_animation_and_bullets(self):
        """Вынесенная логика анимации и пуль, чтобы не дублировать код"""
        # Считаем текущую скорость
        speed = self.velocity.length()

        # Порог, ниже которого считаем корабль «остановившимся»
        STOP_THRESHOLD = 0.15

        # Если скорость очень маленькая — принудительно выключаем тягу и сбрасываем анимацию
        if speed < STOP_THRESHOLD:
            self.is_thrusting = False

        # Анимация двигателей: только если есть тяга И скорость достаточная
        if self.is_thrusting and speed >= STOP_THRESHOLD and self.movement_sprites:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_index = (self.animation_index + 1) % len(self.movement_sprites)
                self.animation_timer = 0
            self.original_image = self.movement_sprites[self.animation_index]
        else:
            # Выключаем анимацию, возвращаем idle
            self.is_thrusting = False  # чтобы не включалась снова без нажатия
            self.original_image = self.idle_sprite
            self.animation_index = 0
            self.animation_timer = 0

        # Обновление пуль
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.is_active():
                self.bullets.remove(bullet)

    def _update_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()

        if self.is_landing and not self.on_planet_surface:
            w = int(w * self.target_scale)
            h = int(h * self.target_scale)

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (self.x, self.y)

    def draw(self, surface, camera_offset):
        cam_x, cam_y = camera_offset
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        if self.is_landing and not self.on_planet_surface:
            scale = self.target_scale
            w = int(self.original_image.get_width() * scale)
            h = int(self.original_image.get_height() * scale)
            scaled_img = pygame.transform.smoothscale(self.original_image, (w, h))
            rotated = pygame.transform.rotate(scaled_img, -self.angle)
            rect = rotated.get_rect(center=(draw_x, draw_y))
            surface.blit(rotated, rect)
            return

        rotated = pygame.transform.rotate(self.original_image, -self.angle)
        rect = rotated.get_rect(center=(draw_x, draw_y))
        surface.blit(rotated, rect)

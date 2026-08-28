import pygame
import math
from config import SHIP_ACCELERATION
from game_objects.bullet import Bullet


# Важно: убедитесь, что класс Bullet импортируется корректно.
# Если Bullet находится в game_objects.bullet, раскомментируйте строку ниже:
# from game_objects.bullet import Bullet

class PlayerShip:
    def __init__(self, x, y, idle_sprite, movement_sprites):
        self.x = x
        self.y = y
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

        # rect инициализируем по центру, чтобы сразу было корректно
        self.rect = self.idle_sprite.get_rect(center=(self.x, self.y))

        # Анимация двигателей
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 100
        self.is_thrusting = False

        # Выстрелы
        self.bullets = []
        self.fire_cooldown = 0
        self.cooldown_time = 250  # мс между выстрелами

        # Инвентарь (создаём только если ещё нет)
        if not hasattr(self, 'inventory'):
            self.inventory = {
                "metal": 1000,
                "precious": 1000,
                "crystal": 1000,
                "energy": 1000,
                "mineral": 1000,
                "uranium": 1000
            }

    def rotate(self, direction):
        target_angular_velocity = direction * self.max_angular_velocity
        if abs(self.angular_velocity - target_angular_velocity) < self.turn_acceleration:
            self.angular_velocity = target_angular_velocity
        else:
            if self.angular_velocity < target_angular_velocity:
                self.angular_velocity += self.turn_acceleration
            else:
                self.angular_velocity -= self.turn_acceleration

    def accelerate(self):
        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * SHIP_ACCELERATION
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.is_thrusting = True

    def start_landing(self, planet=None):
        self.is_landing = True
        self.landing_progress = 0.0
        self.on_planet_surface = False
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0

        if planet is not None and hasattr(planet, 'x') and hasattr(planet, 'y'):
            self.landing_target = pygame.math.Vector2(planet.x, planet.y)
        else:
            # Фолбэк: центр комнаты на планете
            from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
            self.landing_target = pygame.math.Vector2(
                PLANET_ROOM_WIDTH // 2,
                PLANET_ROOM_HEIGHT // 2
            )

    def exit_planet(self, return_x, return_y):
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
        # Обновляем rect после телепортации
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
            max_distance=300
        )
        new_bullet.set_sprite(bullet_sprite)

        self.bullets.append(new_bullet)
        self.fire_cooldown = current_time + self.cooldown_time
        return new_bullet

    def update(self):
        # 1. Посадка
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

            self._update_rect()  # Важно: обновляем rect с учётом масштаба
            return

        # 2. На планете
        if self.on_planet_surface:
            self.velocity *= 0.98
            self.x += self.velocity.x
            self.y += self.velocity.y
            self.angular_velocity *= 0.95
            if abs(self.angular_velocity) < 0.01:
                self.angular_velocity = 0.0
            self._update_rect()
            return

        # 3. Космос
        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        self.velocity *= 0.98
        self.x += self.velocity.x
        self.y += self.velocity.y

        self._update_rect()

        # Анимация двигателей
        if self.is_thrusting and self.movement_sprites:
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

        # Обновление и очистка пуль
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.is_active():
                self.bullets.remove(bullet)

    def _update_rect(self):
        """Обновляет rect по центру (x, y) и с учётом текущего масштаба."""
        # Получаем размер текущего изображения (учитывая масштаб, если нужно)
        w = self.original_image.get_width()
        h = self.original_image.get_height()

        # Если корабль уменьшается (посадка), используем target_scale для расчёта размера rect
        if self.is_landing and not self.on_planet_surface:
            w = int(w * self.target_scale)
            h = int(h * self.target_scale)

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (self.x, self.y)

    def draw(self, surface, camera_offset):
        cam_x, cam_y = camera_offset
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Посадка: уменьшаем и вращаем
        if self.is_landing and not self.on_planet_surface:
            scale = self.target_scale
            w = int(self.original_image.get_width() * scale)
            h = int(self.original_image.get_height() * scale)
            scaled_img = pygame.transform.smoothscale(self.original_image, (w, h))
            rotated = pygame.transform.rotate(scaled_img, -self.angle)
            rect = rotated.get_rect(center=(draw_x, draw_y))
            surface.blit(rotated, rect)
            return

        # Обычный режим: просто вращаем
        rotated = pygame.transform.rotate(self.original_image, -self.angle)
        rect = rotated.get_rect(center=(draw_x, draw_y))
        surface.blit(rotated, rect)

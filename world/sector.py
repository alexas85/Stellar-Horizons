import random
import math
from game_objects.asteroid import Asteroid
from config import SIGMA, ROOM_WIDTH, ROOM_HEIGHT


class Sector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.asteroids = []
        self.is_generated = False
        self.belt = None

    def generate_random_field(self, asteroid_sprites, counts):
        """Обычная генерация (случайное распределение)."""
        center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        for sprite_key, count in counts.items():
            sprite = asteroid_sprites.get(sprite_key)
            if not sprite:
                continue

            for _ in range(count):
                x = random.gauss(center_x, SIGMA)
                y = random.gauss(center_y, SIGMA)

                x = max(0, min(ROOM_WIDTH, x))
                y = max(0, min(ROOM_HEIGHT, y))

                # Простая проверка на пересечение
                collision = False
                for existing in self.asteroids:
                    if math.hypot(x - existing.x, y - existing.y) < 64:
                        collision = True
                        break

                if not collision:
                    angle = random.uniform(0, 2 * math.pi)
                    rot_speed = random.uniform(-0.05, 0.05)
                    self.asteroids.append(Asteroid(sprite, x, y, angle, rot_speed))

        self.is_generated = True

    def generate_belt(self, asteroid_sprites, inner_radius, outer_radius, counts):
        """Генерация пояса астероидов с орбитальным движением."""
        center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        belt_asteroids = []
        for sprite_key, count in counts.items():
            sprite = asteroid_sprites.get(sprite_key)
            if not sprite:
                continue

            for _ in range(count):
                # Выбираем случайный радиус между внутренним и внешним
                dist = random.uniform(inner_radius, outer_radius)

                # Начальный угол на орбите
                start_angle = random.uniform(0, 2 * math.pi)

                # Скорость движения по орбите (чтобы астероиды не стояли стеной)
                orbit_speed = random.uniform(0.005, 0.02)

                # Направление движения (по часовой или против)
                if random.random() > 0.5:
                    orbit_speed = -orbit_speed

                belt_asteroids.append(
                    Asteroid(
                        sprite=sprite,
                        x=center_x,  # Начальная позиция будет пересчитана в update
                        y=center_y,
                        angle=random.uniform(0, 2 * math.pi),  # Вращение текстуры
                        rotation_speed=random.uniform(-0.05, 0.05),  # Кувырок
                        orbit_center=(center_x, center_y),
                        orbit_radius=dist,
                        orbit_speed=orbit_speed
                    )
                )

        self.belt = belt_asteroids
        self.asteroids = belt_asteroids  # В этом секторе астероиды - это и есть пояс
        self.is_generated = True

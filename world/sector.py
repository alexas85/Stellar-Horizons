# world/sector.py
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
        self.belt = None  # Здесь может быть объект пояса астероидов

    def generate_random_field(self, asteroid_sprites, counts):
        """Генерация астероидов по нормальному распределению (как в твоем коде)."""
        center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        for sprite_key, count in counts.items():
            sprite = asteroid_sprites.get(sprite_key)
            if not sprite:
                continue

            for _ in range(count):
                # Нормальное распределение
                x = random.gauss(center_x, SIGMA)
                y = random.gauss(center_y, SIGMA)

                # Ограничение границами комнаты
                x = max(0, min(ROOM_WIDTH, x))
                y = max(0, min(ROOM_HEIGHT, y))

                # Проверка на пересечение (упрощенная)
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
        """Генерация пояса астероидов вокруг центра сектора."""
        center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        belt_asteroids = []
        for sprite_key, count in counts.items():
            sprite = asteroid_sprites.get(sprite_key)
            if not sprite:
                continue

            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(inner_radius, outer_radius)

                x = center_x + math.cos(angle) * dist
                y = center_y + math.sin(angle) * dist

                # Проверка границ комнаты (на случай если пояс вылезает за край)
                if 0 <= x <= ROOM_WIDTH and 0 <= y <= ROOM_HEIGHT:
                    a_angle = random.uniform(0, 2 * math.pi)
                    a_rot = random.uniform(-0.05, 0.05)
                    belt_asteroids.append(Asteroid(sprite, x, y, a_angle, a_rot))

        self.belt = belt_asteroids
        self.is_generated = True

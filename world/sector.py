# world/sector.py
import random
import math
from game_objects.asteroid import Asteroid
from config import ROOM_WIDTH, ROOM_HEIGHT


class Sector:
    def __init__(self, x, y):
        self.x = x  # Координаты комнаты в сетке (например, 1, 0)
        self.y = y
        self.asteroids = []
        self.is_generated = False
        self.belt = None

    def generate_clustered_field(self, asteroid_sprites, total_count=50):
        """Генерирует астероиды пучками (кластерами) в МИРОВЫХ координатах."""
        self.asteroids = []
        types = list(asteroid_sprites.keys())

        if not types:
            return

        cluster_count = random.randint(6, 8)

        # ВАЖНО: Вычисляем мировой центр текущей комнаты
        room_center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        room_center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        for _ in range(cluster_count):
            remaining = total_count - len(self.asteroids)
            if remaining <= 0:
                break

            max_cluster_size = max(1, int(remaining * 0.4))
            cluster_size = random.randint(1, max_cluster_size)

            margin = 250
            # ИСПРАВЛЕНИЕ: Генерируем центр кластера относительно МИРОВОГО центра комнаты
            # Это гарантирует, что кластер будет внутри комнаты, но с правильными глобальными координатами
            cluster_x = room_center_x + random.randint(-margin, margin)
            cluster_y = room_center_y + random.randint(-margin, margin)

            for _ in range(cluster_size):
                radius = 350
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, radius)

                # ax и ay теперь сразу МИРОВЫЕ координаты
                ax = cluster_x + math.cos(angle) * dist
                ay = cluster_y + math.sin(angle) * dist

                # Проверка на коллизии с уже созданными в этом секторе астероидами
                collision = False
                for existing in self.asteroids:
                    if math.hypot(ax - existing.x, ay - existing.y) < 64:
                        collision = True
                        break

                if not collision:
                    ast_type = random.choice(types)
                    sprite = asteroid_sprites.get(ast_type)

                    if not sprite:
                        continue

                    rot_speed = random.uniform(-0.02, 0.02)

                    new_asteroid = Asteroid(
                        sprite=sprite,
                        x=ax,
                        y=ay,
                        angle=random.uniform(0, 2 * math.pi),
                        rotation_speed=rot_speed,
                        orbit_center=None,
                        orbit_radius=0,
                        orbit_speed=0
                    )
                    self.asteroids.append(new_asteroid)

        self.is_generated = True

    def generate_belt(self, asteroid_sprites, inner_radius, outer_radius, counts):
        """Генерация пояса астероидов с орбитальным движением."""
        # Центр пояса — мировой центр комнаты
        center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        belt_asteroids = []
        for sprite_key, count in counts.items():
            sprite = asteroid_sprites.get(sprite_key)
            if not sprite:
                continue

            for _ in range(count):
                dist = random.uniform(inner_radius, outer_radius)
                orbit_speed = random.uniform(0.001, 0.009)
                if random.random() > 0.5:
                    orbit_speed = -orbit_speed

                belt_asteroids.append(
                    Asteroid(
                        sprite=sprite,
                        x=center_x,
                        y=center_y,
                        angle=random.uniform(0, 2 * math.pi),
                        rotation_speed=random.uniform(-0.05, 0.05),
                        orbit_center=(center_x, center_y),
                        orbit_radius=dist,
                        orbit_speed=orbit_speed
                    )
                )

        self.asteroids = belt_asteroids
        self.belt = belt_asteroids
        self.is_generated = True

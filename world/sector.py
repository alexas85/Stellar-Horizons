# world/sector.py
import random
import math
from game_objects.asteroid import Asteroid
from game_objects.static_ship import StaticShip
from config import ROOM_WIDTH, ROOM_HEIGHT


class Sector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.asteroids = []
        self.objects = []  # Список для статичных объектов (корабли, станции)
        self.is_generated = False
        self.belt = None

    def generate_clustered_field(self, asteroid_sprites, total_count=50, wreck_sprite=None):
        """Генерирует астероиды пучками. wreck_sprite - спрайт корабля-обломка."""
        self.asteroids = []
        self.objects = []  # Очищаем список объектов при каждой генерации
        types = list(asteroid_sprites.keys())

        if not types:
            return

        cluster_count = random.randint(6, 8)

        room_center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        room_center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        for _ in range(cluster_count):
            remaining = total_count - len(self.asteroids)
            if remaining <= 0:
                break

            max_cluster_size = max(1, int(remaining * 0.4))
            cluster_size = random.randint(1, max_cluster_size)

            margin = 250
            cluster_x = room_center_x + random.randint(-margin, margin)
            cluster_y = room_center_y + random.randint(-margin, margin)

            for _ in range(cluster_size):
                radius = 350
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, radius)

                ax = cluster_x + math.cos(angle) * dist
                ay = cluster_y + math.sin(angle) * dist

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

        # -------------------------------------------------------------
        # ЛОГИКА РАЗМЕЩЕНИЯ КОРАБЛЯ-ОБЛОМКА
        # -------------------------------------------------------------
        if wreck_sprite and self.x == 1 and self.y == 0:
            # =========================================================
            # ВАРИАНТ 1: ФИКСИРОВАННАЯ ПОЗИЦИЯ (АКТИВНЫЙ КОД)
            # Корабль в верхнем левом углу, отступ 400px от краев комнаты
            # =========================================================
            offset_from_edge = 400

            # Мировые координаты X: начало комнаты + отступ
            fixed_x = (self.x * ROOM_WIDTH) + offset_from_edge

            # Мировые координаты Y: начало комнаты + отступ
            fixed_y = (self.y * ROOM_HEIGHT) + offset_from_edge

            fixed_angle = 60.0  # Можно поставить 0 или любой другой фиксированный угол

            wrecked_ship = StaticShip(
                sprite=wreck_sprite,
                x=fixed_x,
                y=fixed_y,
                angle=fixed_angle
            )
            self.objects.append(wrecked_ship)
            print(
                f"[DEBUG] В комнате ({self.x}, {self.y}) размещен корабль-обломок в ФИКСИРОВАННОЙ позиции: X={fixed_x}, Y={fixed_y}")

            # =========================================================
            # ВАРИАНТ 2: СЛУЧАЙНАЯ ПОЗИЦИЯ (ЗАКОММЕНТИРОВАН ДЛЯ ТЕСТОВ)
            # Раскомментируйте этот блок и закомментируйте ВАРИАНТ 1 выше,
            # чтобы вернуть случайную генерацию.
            # =========================================================
            """
            margin = 150  # Отступ от стен комнаты
            rand_x = (self.x * ROOM_WIDTH) + random.randint(margin, ROOM_WIDTH - margin)
            rand_y = (self.y * ROOM_HEIGHT) + random.randint(margin, ROOM_HEIGHT - margin)
            rand_angle = random.uniform(0, 2 * math.pi)

            wrecked_ship = StaticShip(
                sprite=wreck_sprite,
                x=rand_x,
                y=rand_y,
                angle=rand_angle
            )
            self.objects.append(wrecked_ship)
            print(f"[DEBUG] В комнате ({self.x}, {self.y}) размещен корабль-обломок в СЛУЧАЙНОЙ позиции.")
            """
        # -------------------------------------------------------------

        self.is_generated = True

    def generate_belt(self, asteroid_sprites, inner_radius, outer_radius, counts, wreck_sprite=None):
        """Генерация пояса астероидов. Также принимает wreck_sprite для комнаты (1,0)."""
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

        # Дублируем логику размещения корабля и здесь, на случай если комната (1,0) будет сгенерирована как пояс
        if wreck_sprite and self.x == 1 and self.y == 0:
            offset_from_edge = 400
            fixed_x = (self.x * ROOM_WIDTH) + offset_from_edge
            fixed_y = (self.y * ROOM_HEIGHT) + offset_from_edge
            fixed_angle = 0.0

            wrecked_ship = StaticShip(
                sprite=wreck_sprite,
                x=fixed_x,
                y=fixed_y,
                angle=fixed_angle
            )

            if not hasattr(self, 'objects'):
                self.objects = []
            self.objects.append(wrecked_ship)

        self.is_generated = True

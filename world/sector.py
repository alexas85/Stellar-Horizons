# world/sector.py
import random
import math
from game_objects.asteroid import Asteroid
from game_objects.static_ship import StaticShip
from game_objects.static_planet import StaticPlanet
from config import ROOM_WIDTH, ROOM_HEIGHT

class Sector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.asteroids = []
        self.objects = []
        self.is_generated = False
        self.belt = None

    def generate_clustered_field(self, asteroid_sprites, total_count=50, wreck_sprite=None, planet_sprite=None):
        self.asteroids = []
        self.objects = []

        types = list(asteroid_sprites.keys())
        if not types:
            self.is_generated = True
            return

        # --- СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ КОМНАТЫ (1, 1): хаотичные mod04 ---
        if self.x == 1 and self.y == 1:
            # Выбираем только ключи mod04
            mod04_keys = [k for k in types if "mod04" in k]
            if not mod04_keys:
                print("[WARN] Нет спрайтов mod04 для комнаты (1,1)")
            else:
                # Хаотичный разброс по всей комнате
                for _ in range(total_count):
                    # Случайная позиция в пределах комнаты
                    ax = (self.x * ROOM_WIDTH) + random.randint(0, ROOM_WIDTH - 64)
                    ay = (self.y * ROOM_HEIGHT) + random.randint(0, ROOM_HEIGHT - 64)

                    # Простая проверка на пересечение (чтобы не накладывать один на другой)
                    collision = False
                    for existing in self.asteroids:
                        if math.hypot(ax - existing.x, ay - existing.y) < 64:
                            collision = True
                            break

                    if not collision:
                        sprite_key = random.choice(mod04_keys)
                        sprite = asteroid_sprites[sprite_key]
                        rot_speed = random.uniform(-0.02, 0.02)

                        new_asteroid = Asteroid(
                            sprite=sprite,
                            x=ax, y=ay,
                            angle=random.uniform(0, 2 * math.pi),
                            rotation_speed=rot_speed,
                            orbit_center=None, orbit_radius=0, orbit_speed=0
                        )
                        self.asteroids.append(new_asteroid)

            # Обломки/планеты для (1,1) — если нужны, добавь здесь
            # (сейчас ничего не добавляем, но можно по аналогии с (1,0))

            self.is_generated = True
            print(f"[DEBUG] Комната (1,1): сгенерировано {len(self.asteroids)} астероидов mod04")
            return  # Завершаем метод, чтобы не выполнять обычный кластерный спавн

        # --- ОБЫЧНАЯ ЛОГИКА (все остальные комнаты) ---
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
                        x=ax, y=ay,
                        angle=random.uniform(0, 2 * math.pi),
                        rotation_speed=rot_speed,
                        orbit_center=None, orbit_radius=0, orbit_speed=0
                    )
                    self.asteroids.append(new_asteroid)

        # Обломок в (1,0)
        if wreck_sprite and self.x == 1 and self.y == 0:
            offset_from_edge = 400
            fixed_x = (self.x * ROOM_WIDTH) + offset_from_edge
            fixed_y = (self.y * ROOM_HEIGHT) + offset_from_edge
            wrecked_ship = StaticShip(sprite=wreck_sprite, x=fixed_x, y=fixed_y, angle=0.0)
            self.objects.append(wrecked_ship)

        # Планета в (0,-1)
        if planet_sprite and self.x == 0 and self.y == -1:
            planet_x = (self.x * ROOM_WIDTH) + (ROOM_WIDTH // 2)
            planet_y = (self.y * ROOM_HEIGHT) + (ROOM_HEIGHT // 2)
            new_planet = StaticPlanet(sprite=planet_sprite, x=planet_x, y=planet_y)
            self.objects.append(new_planet)

        self.is_generated = True
    def generate_belt(self, asteroid_sprites, inner_radius, outer_radius, counts, wreck_sprite=None,
                      planet_sprite=None):
        """Генерация пояса астероидов (для стартовой комнаты)."""
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

        # --- Логика для комнаты (1, 0) ---
        if self.x == 1 and self.y == 0:
            if wreck_sprite:
                offset_from_edge = 400
                wrecked_ship = StaticShip(
                    sprite=wreck_sprite,
                    x=(self.x * ROOM_WIDTH) + offset_from_edge,
                    y=(self.y * ROOM_HEIGHT) + offset_from_edge
                )
                self.objects.append(wrecked_ship)

            if planet_sprite:
                margin_left = 300
                margin_bottom = 300
                planet_x = (self.x * ROOM_WIDTH) + margin_left
                planet_y = (self.y * ROOM_HEIGHT) + (ROOM_HEIGHT - margin_bottom)
                new_planet = StaticPlanet(sprite=planet_sprite, x=planet_x, y=planet_y)
                self.objects.append(new_planet)

        # --- Планета в центре комнаты (0, -1) ---
        if planet_sprite and self.x == 0 and self.y == -1:
            planet_x = (self.x * ROOM_WIDTH) + (ROOM_WIDTH // 2)
            planet_y = (self.y * ROOM_HEIGHT) + (ROOM_HEIGHT // 2)

            new_planet = StaticPlanet(
                sprite=planet_sprite,
                x=planet_x,
                y=planet_y,
                parallax_factor=0.4
            )
            self.objects.append(new_planet)
            print(f"[DEBUG] Планета добавлена в generate_belt для комнаты ({self.x}, {self.y})")

        self.is_generated = True

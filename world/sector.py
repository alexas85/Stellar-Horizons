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
            return

        # --- Генерация астероидов (без изменений) ---
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

        # --- Размещение корабля-обломка (оставляем как было для (1, 0)) ---
        if wreck_sprite and self.x == 1 and self.y == 0:
            offset_from_edge = 400
            fixed_x = (self.x * ROOM_WIDTH) + offset_from_edge
            fixed_y = (self.y * ROOM_HEIGHT) + offset_from_edge
            wrecked_ship = StaticShip(sprite=wreck_sprite, x=fixed_x, y=fixed_y, angle=0.0)
            self.objects.append(wrecked_ship)

        # --- НОВАЯ ЛОГИКА: Планета в центре комнаты (0, -1) ---
        if planet_sprite and self.x == 0 and self.y == -1:
            # Центр комнаты (0, -1)
            planet_x = (self.x * ROOM_WIDTH) + (ROOM_WIDTH // 2)
            planet_y = (self.y * ROOM_HEIGHT) + (ROOM_HEIGHT // 2)

            new_planet = StaticPlanet(sprite=planet_sprite, x=planet_x, y=planet_y)
            self.objects.append(new_planet)
            print(f"[DEBUG] Планета размещена в центре комнаты ({self.x}, {self.y}) по координатам ({planet_x}, {planet_y})")
        # -----------------------------------------------------------------

        self.is_generated = True

    # ... остальной код (generate_belt и т.д.) оставь без изменений ...

    def generate_belt(self, asteroid_sprites, inner_radius, outer_radius, counts, wreck_sprite=None,
                      planet_sprite=None):
        """Генерация пояса астероидов."""
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

        # --- ЛОГИКА ДЛЯ КОМНАТЫ (1, 0) --- (оставляем как есть)
        if self.x == 1 and self.y == 0:
            if wreck_sprite:
                offset_from_edge = 400
                wrecked_ship = StaticShip(sprite=wreck_sprite, x=(self.x * ROOM_WIDTH) + offset_from_edge,
                                          y=(self.y * ROOM_HEIGHT) + offset_from_edge)
                self.objects.append(wrecked_ship)

            # Тут у тебя была планета для (1,0) — можно оставить или убрать, если не нужна
            if planet_sprite:
                margin_left = 300
                margin_bottom = 300
                planet_x = (self.x * ROOM_WIDTH) + margin_left
                planet_y = (self.y * ROOM_HEIGHT) + (ROOM_HEIGHT - margin_bottom)
                new_planet = StaticPlanet(sprite=planet_sprite, x=planet_x, y=planet_y)
                self.objects.append(new_planet)

        # --- НОВАЯ ЛОГИКА: ПЛАНЕТА В ЦЕНТРЕ КОМНАТЫ (0, -1) ---
        if planet_sprite and self.x == 0 and self.y == -1:
            planet_x = (self.x * ROOM_WIDTH) + (ROOM_WIDTH // 2)
            planet_y = (self.y * ROOM_HEIGHT) + (ROOM_HEIGHT // 2)

            new_planet = StaticPlanet(sprite=planet_sprite, x=planet_x, y=planet_y, parallax_factor=0.4)
            self.objects.append(new_planet)
            print(f"[DEBUG] Планета добавлена в generate_belt для комнаты ({self.x}, {self.y})")
        # -------------------------------------------------------------

        self.is_generated = True

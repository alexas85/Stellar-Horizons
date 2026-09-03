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

    @staticmethod
    def calculate_mass(size_px):
        """
        Рассчитывает массу астероида на основе его размера.
        Формула: площадь / константа.
        16px -> ~2.0 (лёгкий)
        32px -> ~8.0 (средний)
        64px -> ~32.0 (тяжёлый)
        124px -> ~119.0 (очень тяжёлый, почти неподвижный)
        """
        return (size_px ** 2) / 199.0

    def generate_clustered_field(self, asteroid_sprites, total_count=50, wreck_sprite=None, planet_sprite=None):
        self.asteroids = []
        self.objects = []

        # asteroid_sprites теперь: { key: (Surface, size_px) }
        items = list(asteroid_sprites.items())
        if not items:
            self.is_generated = True
            return

        # --- СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ КОМНАТЫ (1, 1): хаотичные mod04 ---
        if self.x == 1 and self.y == 1:
            # Фильтруем только mod04
            mod04_items = [item for item in items if "mod04" in item[0]]

            if not mod04_items:
                print("[WARN] Нет спрайтов mod04 для комнаты (1,1)")
            else:
                for _ in range(total_count):
                    ax = (self.x * ROOM_WIDTH) + random.randint(0, ROOM_WIDTH - 64)
                    ay = (self.y * ROOM_HEIGHT) + random.randint(0, ROOM_HEIGHT - 64)

                    collision = False
                    for existing in self.asteroids:
                        # Используем размер существующего астероида для проверки коллизии
                        min_dist = max(existing.size_px // 2, 32)
                        if math.hypot(ax - existing.x, ay - existing.y) < min_dist * 2:
                            collision = True
                            break

                    if not collision:
                        sprite_key, (sprite, size_px) = random.choice(mod04_items)
                        rot_speed = random.uniform(-0.02, 0.02)

                        # РАССЧИТЫВАЕМ МАССУ
                        mass = self.calculate_mass(size_px)

                        new_asteroid = Asteroid(
                            sprite=sprite,
                            x=ax, y=ay,
                            angle=random.uniform(0, 2 * math.pi),
                            rotation_speed=rot_speed,
                            orbit_center=None,
                            orbit_radius=0,
                            orbit_speed=0,
                            size_px=size_px,
                            type_key=sprite_key,
                            mass=mass  # <--- ПЕРЕДАЁМ МАССУ
                        )
                        self.asteroids.append(new_asteroid)

            self.is_generated = True
            print(f"[DEBUG] Комната (1,1): сгенерировано {len(self.asteroids)} астероидов mod04")
            return

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
                    min_dist = max(existing.size_px // 2, 32)
                    if math.hypot(ax - existing.x, ay - existing.y) < min_dist * 2:
                        collision = True
                        break

                if not collision:
                    sprite_key, (sprite, size_px) = random.choice(items)
                    rot_speed = random.uniform(-0.02, 0.02)

                    # РАССЧИТЫВАЕМ МАССУ
                    mass = self.calculate_mass(size_px)

                    new_asteroid = Asteroid(
                        sprite=sprite,
                        x=ax, y=ay,
                        angle=random.uniform(0, 2 * math.pi),
                        rotation_speed=rot_speed,
                        orbit_center=None,
                        orbit_radius=0,
                        orbit_speed=0,
                        size_px=size_px,
                        type_key=sprite_key,
                        mass=mass  # <--- ПЕРЕДАЁМ МАССУ
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

        # --- РАЗВЕДЧИК В КОМНАТЕ (0, 1) ---
        if self.x == 0 and self.y == 1:
            from game_objects.enemy import ScoutShip
            from sprites import get_scout_sprites, get_scout_destroyed_sprite

            scout_idle, scout_anim = get_scout_sprites()
            scout_destroyed = get_scout_destroyed_sprite()

            start_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
            start_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

            scout = ScoutShip(
                x=start_x,
                y=start_y,
                idle_sprite=scout_idle,
                movement_sprites=scout_anim,
                sector_x=self.x,
                sector_y=self.y,
                room_width=ROOM_WIDTH,
                room_height=ROOM_HEIGHT
            )
            scout.set_sector(self)
            scout.set_sector(self)
            scout.set_destroyed_sprite(scout_destroyed)
            self.objects.append(scout)
            print(f"[DEBUG] Разведчик добавлен в комнату ({self.x}, {self.y})")

        # --- ИСТРЕБИТЕЛЬ В КОМНАТЕ (-1, 0) ---
        if self.x == -1 and self.y == 0:
            from game_objects.enemy import DestroyerShip
            from sprites import get_destroyer_sprites, get_destroyer_destroyed_sprite

            destroyer_idle, destroyer_anim = get_destroyer_sprites()
            # Сначала загружаем спрайт обломка в переменную
            destroyer_destroyed = get_destroyer_destroyed_sprite()

            start_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
            start_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

            destroyer = DestroyerShip(
                x=start_x,
                y=start_y,
                idle_sprite=destroyer_idle,
                movement_sprites=destroyer_anim,
                sector_x=self.x,
                sector_y=self.y,
                room_width=ROOM_WIDTH,
                room_height=ROOM_HEIGHT
            )
            destroyer.set_sector(self)

            # Теперь безопасно передаём переменную
            destroyer.set_destroyed_sprite(destroyer_destroyed)

            self.objects.append(destroyer)
            print(f"[DEBUG] Истребитель добавлен в комнату ({self.x}, {self.y})")

    def generate_belt(self, asteroid_sprites, inner_radius, outer_radius, counts, wreck_sprite=None,
                      planet_sprite=None):
        """Генерация пояса астероидов (для стартовой комнаты)."""
        center_x = self.x * ROOM_WIDTH + ROOM_WIDTH // 2
        center_y = self.y * ROOM_HEIGHT + ROOM_HEIGHT // 2

        belt_asteroids = []

        # counts: { "ast_mod01_s16": 10, ... }
        for sprite_key, count in counts.items():
            # Получаем кортеж (sprite, size)
            data = asteroid_sprites.get(sprite_key)

            # ВАЖНО: Проверка на существование спрайта
            if not data:
                print(f"[WARN] Не найден спрайт для ключа: {sprite_key}")
                continue

            sprite, size_px = data

            # РАССЧИТЫВАЕМ МАССУ
            mass = self.calculate_mass(size_px)

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
                        rotation_speed=random.uniform(-0.01, 0.01),
                        orbit_center=(center_x, center_y),
                        orbit_radius=dist,
                        orbit_speed=orbit_speed,
                        size_px=size_px,
                        type_key=sprite_key,
                        mass=mass  # <--- ПЕРЕДАЁМ МАССУ
                    )
                )

        self.asteroids = belt_asteroids
        self.belt = belt_asteroids

        # Логика для комнаты (1, 0)
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

        # Планета в центре комнаты (0, -1)
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

# world/generator.py
from .sector import Sector
from config import ROOM_WIDTH, ROOM_HEIGHT
from game_objects.amoeba import SpaceAmoeba
import random
import math



class WorldGenerator:
    def __init__(self):
        self.sectors = {}

    @staticmethod
    def calculate_mass(size_px, type_key=""):
        base_mass = (size_px ** 2) / 128.0
        return base_mass

    def get_sector(self, x, y, asteroid_sprites, wreck_sprite=None, planet_sprite=None, station_sprite=None):
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            if x == 0 and y == 0:
                sector.generate_belt(
                    asteroid_sprites=asteroid_sprites,
                    inner_radius=400,
                    outer_radius=800,
                    counts={
                        "ast_mod01_s16": 35,
                        "ast_mod01_s32": 25,
                        "ast_mod01_s64": 20
                    },
                    wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite,
                    station_sprite=station_sprite
                )
            else:
                sector.generate_clustered_field(
                    asteroid_sprites=asteroid_sprites,
                    wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite,
                    station_sprite=station_sprite
                )
            # Космическая амёба в секторе (0, 1) — случайная позиция
            if x == 0 and y == 1:
                margin = 80  # радиус амёбы, чтобы не появлялась вплотную к стенкам
                amoeba = SpaceAmoeba(
                    x=random.randint(0 + margin, ROOM_WIDTH - margin),
                    y=random.randint(ROOM_HEIGHT + margin, 2 * ROOM_HEIGHT - margin),
                    room_left=0,
                    room_top=ROOM_HEIGHT,
                    room_right=ROOM_WIDTH,
                    room_bottom=2 * ROOM_HEIGHT,
                )
                sector.objects.append(amoeba)
                amoeba.set_sector(sector)
            # Мелкие амёбы без щупалец в комнате (0, -2)
            if x == 0 and y == -2:
                amoeba_count = random.randint(10, 30)
                spawned = 0
                for _ in range(amoeba_count):
                    margin = 30
                    ax = random.randint(margin, ROOM_WIDTH - margin)
                    ay = random.randint(-2 * ROOM_HEIGHT + margin, -ROOM_HEIGHT - margin)

                    too_close = False
                    for obj in sector.objects:
                        if isinstance(obj, SpaceAmoeba):
                            if math.hypot(ax - obj.x, ay - obj.y) < 50:
                                too_close = True
                                break

                    if not too_close:
                        small_amoeba = SpaceAmoeba(
                            x=ax,
                            y=ay,
                            room_left=0,
                            room_top=-2 * ROOM_HEIGHT,
                            room_right=ROOM_WIDTH,
                            room_bottom=-ROOM_HEIGHT,
                            scale_factor=0.2,       # в 5 раз меньше
                            has_tentacles=False,    # без щупалец
                        )
                        small_amoeba.set_sector(sector)
                        sector.objects.append(small_amoeba)
                        spawned += 1

                print(f"[DEBUG] Комната (0,-2): заспавнено {spawned} мелких амеб (планировалось {amoeba_count})")


            self.sectors[key] = sector

        return self.sectors[key]

    def preload_neighbors(self, cx, cy, asteroid_sprites, wreck_sprite=None, planet_sprite=None, station_sprite=None):
        offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]

        for dx, dy in offsets:
            nx, ny = cx + dx, cy + dy
            self.get_sector(nx, ny, asteroid_sprites,
                            wreck_sprite=wreck_sprite,
                            planet_sprite=planet_sprite,
                            station_sprite=station_sprite)

# world/generator.py
from .sector import Sector
from config import ROOM_WIDTH, ROOM_HEIGHT
from game_objects.amoeba import SpaceAmoeba
import random



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
            # Космическая амёба в секторе (0, 1)
            if x == 0 and y == 1:
                amoeba = SpaceAmoeba(
                    x=ROOM_WIDTH // 2,
                    y=int(1.5 * ROOM_HEIGHT),
                    room_left=0,
                    room_top=ROOM_HEIGHT,
                    room_right=ROOM_WIDTH,
                    room_bottom=2 * ROOM_HEIGHT,
                )
                sector.objects.append(amoeba)
                amoeba.set_sector(sector)


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

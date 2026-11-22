# world/generator.py
from .sector import Sector
from config import ROOM_WIDTH, ROOM_HEIGHT
from game_objects.amoeba import SpaceAmoeba
import random
import math
import pygame



class WorldGenerator:
    def __init__(self):
        self.sectors = {}
        # Глобальный список транспортников (обновляются и рисуются всегда)
        self.haulers = []

        # --- ТРАНСПОРТНИКИ (тестовый спавн) ---
        # ТЕСТОВОЕ РАСПОЛОЖЕНИЕ: все транспортники в комнате (-2, -2),
        # чтобы их было легко найти. 1 + 2 + 3 = 6 штук в одной комнате.
        # Конфиг: { (x,y): count }
        self.hauler_rooms = {(-2, -2): 6}
        print(f"[HAULER] Транспортники в комнатах (тест): {self.hauler_rooms}")

    @staticmethod
    def calculate_mass(size_px, type_key=""):
        base_mass = (size_px ** 2) / 128.0
        return base_mass

    def get_sector(self, x, y, asteroid_sprites, wreck_sprite=None, planet_sprite=None, station_sprite=None):
        key = (x, y)
        if key not in self.sectors:
            sector = Sector(x, y)

            if x == 0 and y == 0:
                # Стартовая комната — пучок астероидов (не пояс), чтобы было
                # больше места и обзорнее, чем в окружении.
                sector.generate_clustered_field(
                    asteroid_sprites=asteroid_sprites,
                    total_count=40,
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

            # --- ТРАНСПОРТНИКИ (CargoHauler) ---
            # Спавнятся в комнате в момент, когда игрок залетает в неё.
            if (x, y) in self.hauler_rooms:
                from game_objects.cargo_hauler import CargoHauler
                from sprites import get_hauler_sprites, get_hauler_destroyed_sprite

                count = self.hauler_rooms[(x, y)]
                hauler_idle, hauler_anim = get_hauler_sprites()
                hauler_destroyed = get_hauler_destroyed_sprite()
                group_id = (x, y)  # все транспортники одной комнаты — одна группа

                # Общее направление группы (случайный вектор)
                heading_ang = random.uniform(0, 2 * math.pi)
                group_heading = pygame.math.Vector2(math.cos(heading_ang), math.sin(heading_ang))

                # Общая позиция старта (центр комнаты со смещением)
                start_x = x * ROOM_WIDTH + ROOM_WIDTH // 2
                start_y = y * ROOM_HEIGHT + ROOM_HEIGHT // 2

                for i in range(count):
                    # Разводим транспортники веером от центра, чтобы они не совпадали
                    off_ang = group_id[0] * 1.3 + i * (2 * math.pi / max(1, count))
                    hx = start_x + math.cos(off_ang) * (160 + i * 40)
                    hy = start_y + math.sin(off_ang) * (160 + i * 40)

                    hauler = CargoHauler(
                        x=hx, y=hy,
                        idle_sprite=hauler_idle,
                        movement_sprites=hauler_anim,
                        sector_x=x, sector_y=y,
                        room_width=ROOM_WIDTH, room_height=ROOM_HEIGHT,
                        group_id=group_id,
                    )
                    hauler.set_sector(sector)
                    hauler.set_destroyed_sprite(hauler_destroyed)
                    hauler.group_heading = group_heading
                    hauler.generator = self
                    # Запоминаем спрайты для отложенного создания соседних секторов
                    # при перелёте транспортника между комнатами.
                    hauler.spawn_sprites = (asteroid_sprites, wreck_sprite, planet_sprite, station_sprite)
                    hauler.heading_angle = math.degrees(math.atan2(group_heading.y, group_heading.x))
                    sector.objects.append(hauler)
                    # Регистрируем в глобальном списке
                    if hauler not in self.haulers:
                        self.haulers.append(hauler)

                print(f"[HAULER] {count} транспортник(а/ов) добавлено в комнату ({x}, {y})")
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

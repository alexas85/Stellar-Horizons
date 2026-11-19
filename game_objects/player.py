# game_objects/player.py
import pygame
import math
import random
from config import (SHIP_CLASSES, FUEL_CONSUMPTION_PER_SEC, ENERGY_PER_SHOT,
                    ENERGY_REGEN_PER_SEC, WRECK_PLAYER_MAX_RESOURCE)
from game_objects.bullet import Bullet


def _get_ship_stats(class_id):
    """Возвращает статы класса корабля (dict). Неизвестный класс → статы класса 4."""
    stats = SHIP_CLASSES.get(int(class_id))
    if stats is None:
        stats = SHIP_CLASSES[4]
    return stats


class PlayerShip:
    def __init__(self, x, y, idle_sprite, movement_sprites, class_id=4):
        self.x = x
        self.y = y

        # --- СТАТЫ КЛАССА КОРАБЛЯ (data-driven из config.SHIP_CLASSES) ---
        self.class_id = class_id
        self.base_stats = _get_ship_stats(class_id)

        # Скорости ДО обнуления (для физики удара в main.py)
        self.last_vx = 0.0
        self.last_vy = 0.0

        self.angle = 0
        self.velocity = pygame.math.Vector2(0, 0)

        # Состояния
        self.on_planet_surface = False
        self.is_landing = False
        self.landing_progress = 0.0
        self.target_scale = 1.0
        self.min_scale = 0.15
        self.landing_speed = 0.005
        self.landing_move_speed = 0.7
        self.landing_target = None

        # --- СТЫКОВКА СО СТАНЦИЕЙ ---
        self.is_docking = False          # анимация прилёта к станции
        self.is_docked = False           # уже пристыкован, вращается со станцией
        self.docked_station = None       # ссылка на объект Station
        self.docking_progress = 0.0      # прогресс анимации стыковки (0..1)
        self.docking_speed = 0.007      # скорость анимации стыковки
        self.dock_offset = 0             # расстояние от центра станции до корабля
        self.docking_start_pos = None    # позиция корабля в момент начала стыковки
        self.docking_start_angle = 0.0   # угол корабля в момент начала стыковки

        # Физика вращения — из статов класса
        self.angular_velocity = 0.0
        self.max_angular_velocity = self.base_stats["turn_rate"]
        self.turn_acceleration = 0.2
        self.max_speed = self.base_stats["max_speed"]

        # Спрайты
        self.idle_sprite = idle_sprite
        self.movement_sprites = movement_sprites
        self.original_image = idle_sprite
        # Оригинальные спрайты обычного корабля — для восстановления при возврате из осколка
        self.default_idle_sprite = idle_sprite
        self.default_movement_sprites = movement_sprites

        # rect инициализируем по центру
        self.rect = self.idle_sprite.get_rect(center=(self.x, self.y))

        # Анимация двигателей
        self.animation_index = 0
        self.animation_timer = 0
        self.is_thrusting = False

        # Выстрелы
        self.bullets = []
        self.fire_cooldown = 0
        self.cooldown_time = 250  # мс между выстрелами

        # Инвентарь. Свой у каждого корабля (объект), которым игрок управляет.
        # ship_inventories хранит инвентарь для каждого корабля: ключ = идентификатор корабля.
        # self.inventory всегда указывает на инвентарь активного корабля.
        self.ship_inventories = {}
        self._active_inventory_key = None  # ключ активного корабля в ship_inventories
        self._empty_inventory = {
            "metal": 0,
            "precious": 0,
            "steel": 0,
            "crystal": 0,
            "mineral": 0,
            "uranium": 0
        }
        self.inventory = dict(self._empty_inventory)
        # Здоровье
        self.hp = self.base_stats["max_hp"]
        self.max_hp = self.base_stats["max_hp"]
        # --- ЭНЕРГИЯ (батареи) ---
        self.energy = self.base_stats["max_energy"]
        self.max_energy = self.base_stats["max_energy"]
        # --- ТОПЛИВО ---
        self.fuel = self.base_stats["max_fuel"]
        self.max_fuel = self.base_stats["max_fuel"]
        # --- ВНУТРЕННИЕ ТАЙМЕРЫ ---
        self._energy_regen_accum = 0.0
        self._docking_fuel_accum = 0.0
        # --- ЛИМИТ РЕСУРСОВ (грузоподъёмность из статов класса) ---
        self.max_resource = self.base_stats["cargo"]
        self._default_max_resource = self.base_stats["cargo"]

        # --- ПЕРЕСАДКА НА ДРУГОЙ КОРАБЛЬ (осколок Destroyer и др.) ---
        self.piloted_wreck = None       # корабль, которым сейчас управляем (None = обычный корабль)
        # Активные параметры физики — стартуют из статов класса
        self.active_acceleration = self.base_stats["acceleration"]
        self.active_max_speed = self.base_stats["max_speed"]

        # --- СОСТОЯНИЕ УНИЧТОЖЕНИЯ ---
        self.is_destroyed = False
        self.destroyed_sprite = None


        # --- МЕХАНИКА СБОРА ---
        self.collecting_asteroid = None
        self.collection_start_time = 0.0
        self.is_collecting = False

        self.is_boarded = False  # Игрок сейчас внутри обломка?
        self.boarded_wreck = None  # Ссылка на объект обломка
        self.saved_idle_sprite = None  # Чтобы вернуть свой спрайт при выходе
        self.saved_movement_sprites = None

    def rotate(self, direction):
        target_angular_velocity = direction * self.max_angular_velocity
        if abs(self.angular_velocity - target_angular_velocity) < self.turn_acceleration:
            self.angular_velocity = target_angular_velocity
        else:
            if self.angular_velocity < target_angular_velocity:
                self.angular_velocity += self.turn_acceleration
            else:
                self.angular_velocity -= self.turn_acceleration

    def accelerate(self):
        if self.fuel <= 0:
            return  # нет топлива — нет ускорения
        rad = math.radians(self.angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.velocity += direction * self.active_acceleration
        if self.velocity.length() > self.active_max_speed:
            self.velocity.scale_to_length(self.active_max_speed)
        self.is_thrusting = True
        # Расход топлива (пересчёт из секунд в кадры: /60)
        self.fuel = max(0, self.fuel - FUEL_CONSUMPTION_PER_SEC / 60.0)

    # ================================================================
    #  ПЕРЕСАДКА НА ДРУГОЙ КОРАБЛЬ (осколок Destroyer)
    # ================================================================

    def _update_wreck_physics(self):
        """Пересчитывает параметры физики исходя из класса и целостности Двигателя корабля.
        Двигатель 30% → самые низкие ходовые; 100% → полные (по статам класса корабля)."""
        wreck = self.piloted_wreck
        if wreck is None:
            # Обычный корабль — статы класса игрока
            stats = SHIP_CLASSES.get(self.class_id, SHIP_CLASSES[4])
            self.active_acceleration = stats["acceleration"]
            self.active_max_speed = stats["max_speed"]
            return

        # Корабль-осколок: физика от его класса
        wreck_class = getattr(wreck, 'class_id', 3)  # осколок по умолчанию класс 3 (Эсминец)
        stats = SHIP_CLASSES.get(wreck_class, SHIP_CLASSES[3])
        max_acc = stats["acceleration"]
        max_spd = stats["max_speed"]

        engine = wreck.get_engine_integrity()
        # Нормируем целостность двигателя в диапазон 30..100 → 0..1
        t = max(0.0, min(1.0, (engine - 30.0) / 70.0))

        self.active_acceleration = max_acc * (0.45 + 0.55 * t)
        self.active_max_speed = max_spd * (0.45 + 0.55 * t)

        if self.velocity.length() > self.active_max_speed:
            self.velocity.scale_to_length(self.active_max_speed)

    def _current_ship_key(self):
        """Возвращает ключ активного корабля в ship_inventories."""
        if self._active_inventory_key is not None:
            return self._active_inventory_key
        # По умолчанию — основной корабль игрока
        return "player"

    def _load_inventory(self, key, max_resource):
        """Сохраняет инвентарь текущего корабля и подгружает инвентарь корабля с ключом key."""
        old_key = self._current_ship_key()
        if old_key != key or old_key not in self.ship_inventories:
            self.ship_inventories[old_key] = dict(self.inventory)
        else:
            self.ship_inventories[old_key] = dict(self.inventory)

        self._active_inventory_key = key
        # Подгружаем инвентарь целевого корабля (или пустой)
        if key not in self.ship_inventories:
            self.ship_inventories[key] = dict(self._empty_inventory)
        self.inventory = self.ship_inventories[key]
        self.max_resource = max_resource

    def board_wreck(self, wreck, wreck_sprite):
        """Пересаживает игрока в осколок. Инвентарь и вместимость — СВОИ у каждого корабля,
        поэтому при пересадке переключаемся на инвентарь осколка (он хранится в ship_inventories,
        а у самого осколка — как wreck.storage). Спрайт осколка для отрисовки."""
        # Сохраняем дефолтные спрайты обычного корабля для возврата
        if not self.piloted_wreck:
            self.default_idle_sprite = self.idle_sprite
            self.default_movement_sprites = self.movement_sprites
            self._default_max_resource = self.max_resource

        self.piloted_wreck = wreck

        # Перенимаем позицию и спрайт осколка
        self.x = wreck.x
        self.y = wreck.y
        self.angle = wreck.angle
        self.original_image = wreck_sprite
        self.idle_sprite = wreck_sprite
        self.movement_sprites = []
        # Грузоподъёмность — из класса корабля-осколка
        wreck_cargo = getattr(wreck, 'cargo_capacity', WRECK_PLAYER_MAX_RESOURCE)

        # Переключаемся на персональный инвентарь осколка.
        # Инвентарь осколка живёт в wreck.storage (склад), но игрок работает со своим словарём
        # ресурсов; синхронизируем через ship_inventories по ключу id(wreck).
        wreck_key = f"wreck_{id(wreck)}"
        self._load_inventory(wreck_key, wreck_cargo)
        # Переносим вчерашний склад осколка в персональный инвентарь игрока для удобства:
        # берём содержимое wreck.storage как основу, если там что-то есть.
        if not any(self.inventory.values()) and any(getattr(wreck, 'storage', {}).values()):
            for res, amt in wreck.storage.items():
                self.inventory[res] = amt

        # Сбрасываем состояния
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0
        self.is_thrusting = False
        self.stop_collection()
        self._update_wreck_physics()
        self._update_rect()

    def leave_wreck(self, old_piloted_wreck):
        """Возвращает игрока в обычный корабль. Инвентарь обычного корабля восстанавливается.
        old_piloted_wreck — осколок, из которого выходим (его инвентарь сохраняется в ship_inventories)."""
        # Сохраняем инвентарь осколка, из которого выходим
        if old_piloted_wreck is not None:
            wreck_key = f"wreck_{id(old_piloted_wreck)}"
            self.ship_inventories[wreck_key] = dict(self.inventory)
            # Синхронизируем обратно со складом осколка
            for res in old_piloted_wreck.storage:
                old_piloted_wreck.storage[res] = self.inventory.get(res, 0)

        self.piloted_wreck = None
        # Восстанавливаем спрайты и лимит обычного корабля
        self.idle_sprite = self.default_idle_sprite
        self.movement_sprites = self.default_movement_sprites
        self.original_image = self.default_idle_sprite
        self.max_resource = self._default_max_resource
        # Переключаемся на персональный инвентарь обычного корабля
        self._load_inventory("player", self._default_max_resource)
        self._update_wreck_physics()
        self._update_rect()
        # Позицию задаёт вызывающий код (рядом с осколком-складом)

    def start_landing(self, planet=None):
        self.is_landing = True
        self.landing_progress = 0.0
        self.on_planet_surface = False
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0

        if planet is not None and hasattr(planet, 'x') and hasattr(planet, 'y'):
            self.landing_target = pygame.math.Vector2(planet.x, planet.y)
        else:
            from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
            self.landing_target = pygame.math.Vector2(
                PLANET_ROOM_WIDTH // 2,
                PLANET_ROOM_HEIGHT // 2
            )

    def exit_planet(self, return_x, return_y):
        self.on_planet_surface = False
        self.is_landing = False
        self.x = return_x
        self.y = return_y
        self.velocity = pygame.math.Vector2(0, 0)
        self.landing_progress = 0.0
        self.angular_velocity = 0.0
        self.is_thrusting = False
        self.landing_target = None
        self.target_scale = 1.0
        self.stop_collection()
        self._update_rect()

    # ================================================================
    #  СТЫКОВКА
    # ================================================================

    def start_docking(self, station):
        """Запуск анимации медленной стыковки со станцией."""
        self.is_docking = True
        self.is_docked = False
        self.docked_station = station
        self.velocity = pygame.math.Vector2(0, 0)
        self.angular_velocity = 0.0
        self.is_thrusting = False
        self.stop_collection()

        # Расчёт дистанции от центра станции до корабля
        station_radius = station.original_sprite.get_width() / 2
        player_radius = self.original_image.get_width() / 2
        self.dock_offset = station_radius + player_radius + 10

        # Запоминаем стартовую позицию и угол для интерполяции
        self.docking_progress = 0.0
        self.docking_start_pos = pygame.math.Vector2(self.x, self.y)
        self.docking_start_angle = self.angle

    def stop_docking(self):
        """Отстыковка от станции."""
        self.is_docked = False
        self.is_docking = False
        self.docked_station = None
        self.angular_velocity = 0.0
        self.velocity = pygame.math.Vector2(0, -1.5)
        self._docking_fuel_accum = 0.0
        self._update_rect()

    def _get_dock_position(self):
        """Вычисляет целевую позицию и угол корабля на станции (справа)."""
        station = self.docked_station
        rad = math.radians(station.angle)
        target_x = station.x + self.dock_offset * math.cos(rad)
        target_y = station.y + self.dock_offset * math.sin(rad)
        target_angle = station.angle + 90
        if target_angle >= 360:
            target_angle -= 360
        elif target_angle < 0:
            target_angle += 360
        return target_x, target_y, target_angle

    def _update_docking(self):
        """Плавная анимация прилёта корабля к точке стыковки."""
        station = self.docked_station
        if station is None:
            return

        # Целевая позиция меняется каждый кадр — станция вращается
        target_x, target_y, target_angle = self._get_dock_position()

        self.docking_progress += self.docking_speed
        if self.docking_progress >= 1.0:
            self.docking_progress = 1.0
            self.is_docking = False
            self.is_docked = True

        t = self.docking_progress

        # Интерполяция позиции: от стартовой к целевой
        self.x = self.docking_start_pos.x + (target_x - self.docking_start_pos.x) * t
        self.y = self.docking_start_pos.y + (target_y - self.docking_start_pos.y) * t

        # Интерполяция угла (с учётом перехода через 360)
        angle_diff = target_angle - self.docking_start_angle
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        self.angle = self.docking_start_angle + angle_diff * t
        if self.angle >= 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self._update_rect()

    def _sync_docked_position(self):
        """Синхронизация с вращающейся станцией — вызывается каждый кадр."""
        target_x, target_y, target_angle = self._get_dock_position()
        self.x = target_x
        self.y = target_y
        self.angle = target_angle
        self._update_rect()

        # --- ЗАПРАВКА ТОПЛИВОМ (~3 ед/сек) ---
        if self.fuel < self.max_fuel:
            self._docking_fuel_accum += 3.0 / 60.0
            if self._docking_fuel_accum >= 1.0:
                refuel = int(self._docking_fuel_accum)
                self.fuel = min(self.max_fuel, self.fuel + refuel)
                self._docking_fuel_accum -= refuel

    # ================================================================

    def stop_collection(self):
        if self.collecting_asteroid is not None:
            self.collecting_asteroid.is_collecting = False
            self.collecting_asteroid.collection_start_time = 0.0
            self.collecting_asteroid = None
            self.is_collecting = False
            self.collection_start_time = 0.0

    def shoot(self, bullet_sprite):
        if self.energy < ENERGY_PER_SHOT:
            return None  # не хватает энергии — выстрел не происходит
        current_time = pygame.time.get_ticks()
        if self.fire_cooldown > 0 and current_time < self.fire_cooldown:
            return None

        new_bullet = Bullet(
            x=self.x,
            y=self.y,
            angle=self.angle,
            speed=12,
            max_distance=300,
            base_velocity=self.velocity
        )
        new_bullet.set_sprite(bullet_sprite)

        self.bullets.append(new_bullet)
        self.fire_cooldown = current_time + self.cooldown_time
        self.energy = max(0, self.energy - ENERGY_PER_SHOT)
        return new_bullet

    def add_resource(self, name, amount):
        """Добавляет ресурс с учётом лимита. Возвращает фактически добавленное количество."""
        if name not in self.inventory:
            self.inventory[name] = 0
        space_left = self.max_resource - self.inventory[name]
        if space_left <= 0:
            return 0
        actual = min(amount, space_left)
        self.inventory[name] += actual
        return actual


    def take_damage(self, amount):
        if self.is_destroyed:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_destroyed = True
            self.velocity = pygame.math.Vector2(0, 0)
            self.angular_velocity = 0.0
            self.is_thrusting = False
            self.stop_collection()
            print("[DESTROYED] Корабль игрока уничтожен!")
        print(f"[DAMAGE] HP: {self.hp}/{self.max_hp}")

    def set_destroyed_sprite(self, sprite):
        self.destroyed_sprite = sprite


    def apply_impulse_to(self, obj, force):
        dx = obj.x - self.x
        dy = obj.y - self.y
        length = math.hypot(dx, dy)

        if length == 0:
            return

        dx /= length
        dy /= length
        obj.apply_knockback(dx * force, dy * force)

    def try_start_collection(self, asteroid):
        if self.is_collecting or self.on_planet_surface or self.is_landing or self.is_docking or self.is_docked:
            return False

        # Проверка типа: осколок или мелкий астероид
        is_debris = hasattr(asteroid, 'type_key') and asteroid.type_key == "destroyer_debris"
        is_small_asteroid = (hasattr(asteroid, 'type_key') and
                             (asteroid.type_key.startswith("ast_mod04") or asteroid.type_key.startswith("ast_mod01"))
                             and asteroid.size_px == 16)
        is_crystal = hasattr(asteroid, 'type_key') and asteroid.type_key == "crystal"

        if not is_debris and not is_small_asteroid and not is_crystal:
            return False

        dist_sq = (asteroid.x - self.x) ** 2 + (asteroid.y - self.y) ** 2
        max_dist = 150
        if dist_sq > max_dist ** 2:
            return False

        speed = math.hypot(asteroid.velocity_x, asteroid.velocity_y)
        if speed > 0.8:
            return False

        self.collecting_asteroid = asteroid
        self.is_collecting = True
        self.collection_start_time = pygame.time.get_ticks()
        asteroid.is_collecting = True
        asteroid.collection_start_time = self.collection_start_time

        return True

    def remove_resource(self, name, amount):
        """Списывает ресурс. Возвращает True, если ресурсов хватило, иначе False."""
        if name not in self.inventory:
            return False

        if self.inventory[name] >= amount:
            self.inventory[name] -= amount
            return True
        return False

    def update(self, world_objects=None):
        """
        Основной цикл обновления физики.
        Возвращает объект столкновения, если оно произошло, иначе None."""
        # --- РЕГЕНЕРАЦИЯ ЭНЕРГИИ (от звёзд и планет) ---
        if self.energy < self.max_energy:
            self._energy_regen_accum += ENERGY_REGEN_PER_SEC / 60.0
            if self._energy_regen_accum >= 1.0:
                regen = int(self._energy_regen_accum)
                self.energy = min(self.max_energy, self.energy + regen)
                self._energy_regen_accum -= regen
        # Фоновый расход топлива: 0.5 единицы в секунду
        if self.fuel > 0 and not self.is_docked:
            self.fuel -= 0.5 / 60.0
            if self.fuel < 0:
                self.fuel = 0

                # --- УНИЧТОЖЕН: корабль не управляется, только дрейфует ---
        if self.is_destroyed:
            # Лёгкий дрейф обломка
            self.velocity *= 0.98
            self.x += self.velocity.x
            self.y += self.velocity.y
            self.angular_velocity *= 0.95
            self.angle += self.angular_velocity
            if self.angle > 360:
                self.angle -= 360
            elif self.angle < 0:
                self.angle += 360
            self._update_rect()
            self._update_animation_and_bullets()
            return None
        # --- СТЫКОВКА: анимация прилёта ---
        if self.is_docking:
            self._update_docking()
            self._update_animation_and_bullets()
            return None

        # --- СТЫКОВКА: уже пристыкован, вращаемся со станцией ---
        if self.is_docked and self.docked_station:
            self._sync_docked_position()
            self._update_animation_and_bullets()
            return None

        # Сохраняем скорость ДО изменений для передачи в main.py (физика удара)
        self.last_vx = float(self.velocity.x)
        self.last_vy = float(self.velocity.y)

        # Физика активного корабля (зависит от Двигателя осколка, если управляем им)
        self._update_wreck_physics()

        # --- ЛОГИКА ПОСАДКИ ---
        if self.is_landing and not self.on_planet_surface:
            if self.landing_target is None:
                from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
                self.landing_target = pygame.math.Vector2(PLANET_ROOM_WIDTH // 2, PLANET_ROOM_HEIGHT // 2)

            current_pos = pygame.math.Vector2(self.x, self.y)
            direction = self.landing_target - current_pos
            dist = direction.length()

            if dist < 2.0:
                self.x = self.landing_target.x
                self.y = self.landing_target.y
                self.landing_progress = 1.0
                self.on_planet_surface = True
                self.target_scale = self.min_scale
                self.landing_target = None
                self.stop_collection()
            else:
                direction.scale_to_length(self.landing_move_speed)
                self.x += direction.x
                self.y += direction.y
                self.landing_progress += self.landing_speed
                if self.landing_progress > 1.0:
                    self.landing_progress = 1.0
                t = self.landing_progress
                self.target_scale = max(self.min_scale, 1.0 - t * (1.0 - self.min_scale))

            self._update_rect()
            self._update_animation_and_bullets()
            return None

        # --- ЛОГИКА НА ПЛАНЕТЕ ---
        if self.on_planet_surface:
            self.velocity *= 0.98
            self.x += self.velocity.x
            self.y += self.velocity.y
            self.angular_velocity *= 0.95
            if abs(self.angular_velocity) < 0.01:
                self.angular_velocity = 0.0
            self._update_rect()
            self._update_animation_and_bullets()
            return None

        # --- ОБРАБОТКА СБОРА РЕСУРСОВ ---
        if self.is_collecting and self.collecting_asteroid is not None:
            asteroid = self.collecting_asteroid
            current_time = pygame.time.get_ticks()

            if asteroid.marked_for_removal:
                if hasattr(asteroid, 'type_key') and asteroid.type_key == "destroyer_debris":
                    self.add_resource("metal", random.randint(10, 15))
                    self.add_resource("steel", random.randint(8, 12))
                    self.add_resource("precious", random.randint(5, 8))
                    self.add_resource("uranium", random.randint(0, 1))
                    self.add_resource("crystal", random.randint(0, 3))
                elif hasattr(asteroid, 'type_key') and asteroid.type_key == "crystal":
                    self.add_resource("crystal", random.randint(5, 10))
                else:
                    self.add_resource("metal", random.randint(5, 16))
                    self.add_resource("mineral", random.randint(0, 3))
                self.stop_collection()
                return None

            dist_sq = (asteroid.x - self.x) ** 2 + (asteroid.y - self.y) ** 2
            max_dist = 160
            if dist_sq > max_dist ** 2:
                self.stop_collection()

        # --- ЛОГИКА КОСМОСА ---

        # Вращение
        self.angle += self.angular_velocity
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360
        self.angular_velocity *= 0.95
        if abs(self.angular_velocity) < 0.01:
            self.angular_velocity = 0.0

        # Трение
        self.velocity *= 0.98

        # Предсказание столкновения
        next_x = self.x + self.velocity.x
        next_y = self.y + self.velocity.y

        w = self.original_image.get_width()
        h = self.original_image.get_height()
        if self.is_landing and not self.on_planet_surface:
            w = int(w * self.target_scale)
            h = int(h * self.target_scale)

        temp_rect = pygame.Rect(0, 0, w, h)
        temp_rect.center = (next_x, next_y)

        collision_detected = False
        hit_object = None

        if world_objects:
            for obj in world_objects:
                if not hasattr(obj, 'rect'):
                    continue
                if temp_rect.colliderect(obj.rect):
                    collision_detected = True
                    hit_object = obj
                    break

        if collision_detected and hit_object:
            self.velocity = pygame.math.Vector2(0, 0)
            self.is_thrusting = False
            self.apply_impulse_to(hit_object, 12.0)
            self.stop_collection()
            self._update_rect()
            self._update_animation_and_bullets()
            return hit_object
        else:
            self.x = next_x
            self.y = next_y
            self._update_rect()
            self._update_animation_and_bullets()
            return None

    def _update_animation_and_bullets(self):
        speed = self.velocity.length()
        STOP_THRESHOLD = 0.15

        if speed < STOP_THRESHOLD:
            self.is_thrusting = False

        if self.is_thrusting and speed >= STOP_THRESHOLD and self.movement_sprites:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_index = (self.animation_index + 1) % len(self.movement_sprites)
                self.animation_timer = 0
            self.original_image = self.movement_sprites[self.animation_index]
        else:
            self.is_thrusting = False
            self.original_image = self.idle_sprite
            self.animation_index = 0
            self.animation_timer = 0

        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.is_active():
                self.bullets.remove(bullet)

    def _update_rect(self):
        w = self.original_image.get_width()
        h = self.original_image.get_height()

        if self.is_landing and not self.on_planet_surface:
            w = int(w * self.target_scale)
            h = int(h * self.target_scale)

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (self.x, self.y)

    def draw(self, surface, camera_offset, interaction_target=None):
        cam_x, cam_y = camera_offset
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Если корабль в процессе посадки — рисуем уменьшающийся спрайт
        if self.is_landing and not self.on_planet_surface:
            scale = self.target_scale
            w = int(self.original_image.get_width() * scale)
            h = int(self.original_image.get_height() * scale)
            scaled_img = pygame.transform.smoothscale(self.original_image, (w, h))
            rotated = pygame.transform.rotate(scaled_img, -self.angle)
            rect = rotated.get_rect(center=(draw_x, draw_y))
            surface.blit(rotated, rect)
            return

        # Выбор спрайта: обломок если уничтожен, иначе обычный
        current_sprite = self.destroyed_sprite if (self.is_destroyed and self.destroyed_sprite) else self.original_image
        rotated = pygame.transform.rotate(current_sprite, -self.angle)
        rect = rotated.get_rect(center=(draw_x, draw_y))
        surface.blit(rotated, rect)

        # Линия взаимодействия — только в космосе и не при стыковке
        if interaction_target is not None and not self.is_docking and not self.is_docked:
            tx = interaction_target.x - cam_x
            ty = interaction_target.y - cam_y

            pygame.draw.line(surface, (255, 255, 255), (draw_x, draw_y), (tx, ty), 3)
            pygame.draw.circle(surface, (255, 255, 255), (int(tx), int(ty)), 6, 2)

    def board_wreck(self, wreck_obj):
        """Игрок садится в обломок"""
        if self.is_boarded:
            return

        self.is_boarded = True
        self.boarded_wreck = wreck_obj

        # 1. Передаем текущую скорость и вращение обломку
        wreck_obj.velocity = self.velocity.copy()
        wreck_obj.angular_velocity = self.angular_velocity
        wreck_obj.angle = self.angle

        # 2. Сохраняем свои спрайты, чтобы вернуть их потом
        self.saved_idle_sprite = self.idle_sprite
        self.saved_movement_sprites = self.movement_sprites

        # 3. Визуальный трюк:
        # Мы НЕ меняем спрайты местами. Мы просто заставляем обломок выглядеть как игрок.
        # Так как в main.py мы перестанем рисовать player, а wreck будет рисовать свой спрайт,
        # нам нужно сказать wreck'у: "Рисуй спрайт игрока".
        wreck_obj._base_sprite = self.idle_sprite
        wreck_obj._original_sprite = self.idle_sprite
        wreck_obj.sprite = self.idle_sprite

        # Если у wreck есть анимация двигателей, её тоже можно подменить,
        # но для начала хватит смены _base_sprite.

        print(f"[BOARDING] Игрок сел в {wreck_obj.ship_name}")

    def leave_wreck(self):
        """Игрок покидает обломок"""
        if not self.is_boarded or self.boarded_wreck is None:
            return

        wreck = self.boarded_wreck

        # 1. Забираем физику обратно
        self.velocity = wreck.velocity.copy()
        self.angular_velocity = wreck.angular_velocity
        self.angle = wreck.angle
        self.x = wreck.x
        self.y = wreck.y

        # 2. Возвращаем свои спрайты
        self.idle_sprite = self.saved_idle_sprite
        self.movement_sprites = self.saved_movement_sprites
        self.original_image = self.idle_sprite

        # 3. Сбрасываем состояние
        self.is_boarded = False
        self.boarded_wreck = None

        # Опционально: сбросить скорость обломка, чтобы он не улетел, пока стоит пустым
        # wreck.velocity = pygame.math.Vector2(0, 0)

        print("[LEAVE] Игрок вернулся в свой корабль")

# config.py

# Размеры мира и экрана
ROOM_WIDTH = 4000
ROOM_HEIGHT = 4000
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Параметры комнаты «на поверхности планеты»
PLANET_ROOM_WIDTH = 1280
PLANET_ROOM_HEIGHT = 720

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Физика корабля
SHIP_ACCELERATION = 0.2
SHIP_FRICTION = 0.98

# Параметры генерации (сигма для нормального распределения)
# ЭТОТ ПАРАМЕТР НУЖЕН ФАЙЛУ world/sector.py
SIGMA = 300

# Классы кораблей — централизованные статы (data-driven).
# Классы от 5-го (дроны, 32px) до 1-го (колосс/крепость, 512px).
# size = (ширина, высота) спрайта; power — множитель урона (баланс оружия).
# repair_modifier — множитель сложности/длительности ремонта: чем крупнее корабль,
# тем труднее чинить его с меньшего аппарата (идея «крупный чинить маленьким трудоёмко»).
# class_id всегда ключ (int) = уровень корабля: 5 → 1 (5 самый лёгкий, 1 самый мощный).
SHIP_CLASSES = {
    5: {
        "name": "Дрон",
        "size": (32, 32), "power": 0.6,
        "max_hp": 50, "max_speed": 10.0, "acceleration": 0.30, "turn_rate": 4.0,
        "max_fuel": 60, "max_energy": 50, "cargo": 10, "repair_modifier": 0.6,
    },
    4: {
        "name": "Истребитель",
        "size": (64, 64), "power": 1.0,
        "max_hp": 100, "max_speed": 8.0, "acceleration": 0.20, "turn_rate": 3.0,
        "max_fuel": 100, "max_energy": 100, "cargo": 50, "repair_modifier": 1.0,
    },
    3: {
        "name": "Эсминец",
        "size": (128, 128), "power": 1.8,
        "max_hp": 200, "max_speed": 5.0, "acceleration": 0.10, "turn_rate": 2.0,
        "max_fuel": 150, "max_energy": 150, "cargo": 500, "repair_modifier": 1.8,
    },
    2: {
        "name": "Броненосец",
        "size": (256, 256), "power": 3.0,
        "max_hp": 400, "max_speed": 3.5, "acceleration": 0.07, "turn_rate": 1.5,
        "max_fuel": 220, "max_energy": 220, "cargo": 1200, "repair_modifier": 3.0,
    },
    1: {
        "name": "Колосс",
        "size": (512, 512), "power": 5.0,
        "max_hp": 800, "max_speed": 2.2, "acceleration": 0.04, "turn_rate": 1.0,
        "max_fuel": 400, "max_energy": 400, "cargo": 3000, "repair_modifier": 5.0,
    },
}

RESOURCE_ICONS = {
    "metal": "assets/resources/res_metal_base.png",
    "precious": "assets/resources/res_metal_noble.png",
    "steel": "assets/resources/res_steel.png",
    "crystal": "assets/resources/res_crystal.png",
    "mineral": "assets/resources/res_mineral.png",
    "uranium": "assets/resources/res_uranium.png",
}
ASTEROID_TYPES = {
    "normal": ["mod01", "mod02", "mod03"],
    "resource": ["mod04", "mod05", "mod06"]
}

ASTEROID_SIZES = {
    "small": 16,
    "medium": 32,
    "large": 64,
    "extra_large": 128
}
# Стоимость ремонта
# 1 единица ресурса восстанавливает 1% целостности модуля
REPAIR_COST_PER_PERCENT = 1.0
# Минимальная целостность Двигателя (%), при которой доступна пересадка в осколок
MIN_ENGINE_FOR_TRANSFER = 30.0
# Запасное значение грузоподъёмности игрока в случае, если у корабля-осколка нет cargo_capacity
WRECK_PLAYER_MAX_RESOURCE = 500
# Тип ресурса, требуемый для ремонта корпуса (должен совпадать с ключом в player.inventory)
REPAIR_RESOURCE_TYPE = "metal"
# Настройки ремонта обломков
# Расход топлива: 5 единиц за минуту = 5/60 за секунду
FUEL_CONSUMPTION_PER_SEC = 5.0 / 60.0
# Расход энергии на выстрел
ENERGY_PER_SHOT = 10.0
# Регенерация энергии: 1 единица в секунду
ENERGY_REGEN_PER_SEC = 5.0

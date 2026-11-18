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

# Классы кораблей (размеры и мощность)
SHIP_CLASSES = {
    1: {"size": (512, 512), "power": 5.0},
    2: {"size": (256, 256), "power": 3.5},
    3: {"size": (128, 128), "power": 2.0},
    4: {"size": (64, 64), "power": 1.2},
    5: {"size": (32, 32), "power": 0.8},
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
# Физика управляемого осколка (Destroyer). Скорость/ускорение зависят от Двигателя (30..100%).
WRECK_BASE_ACCELERATION = 0.1          # ускорение при Двигателе 100%
WRECK_BASE_MAX_SPEED = 5.0             # макс. скорость при Двигателе 100%
WRECK_ACCEL_PENALTY_RANGE = 0.55       # доля ускорения, теряемая при падении Двигателя до 30%
WRECK_MAXSPEED_PENALTY_RANGE = 0.55    # доля макс. скорости, теряемая при падении Двигателя до 30%
# Лимит инвентаря у игрока, когда он управляет осколком-складом (Destroyer)
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

# config.py

# Размеры мира и экрана
ROOM_WIDTH = 4000
ROOM_HEIGHT = 4000
CAMERA_WIDTH = 800
CAMERA_HEIGHT = 600

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
    "crystal": "assets/resources/res_crystal.png",
    "energy": "assets/resources/res_energy.png",
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

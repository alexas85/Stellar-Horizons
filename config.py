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

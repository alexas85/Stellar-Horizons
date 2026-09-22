# sprites.py
import os
import pygame
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def load_image(path, convert_alpha=True):
    """Загружает изображение или создает заглушку, если файла нет."""
    full_path = os.path.join(ASSETS_DIR, path)
    try:
        img = pygame.image.load(full_path)
        if convert_alpha:
            return img.convert_alpha()
        return img.convert()
    except FileNotFoundError:
        print(f"⚠️ Файл не найден: {path}. Используем заглушку.")

        # Создаем заглушку в зависимости от типа
        surf = pygame.Surface((64, 64))
        if convert_alpha:
            surf.set_colorkey((0, 0, 0))

        if "stars" in path:
            # Заглушка для звёзд: чёрный фон + случайные белые точки
            surf.fill((0, 0, 20))  # Почти чёрный
            for _ in range(10):
                x = random.randint(0, 63)
                y = random.randint(0, 63)
                size = random.choice([1, 2])
                pygame.draw.circle(surf, (255, 255, 255), (x, y), size)
            return surf
        elif "fog" in path:
            # Если вдруг где-то попросят туман, сделаем прозрачный
            surf.fill((0, 0, 0, 0))
            return surf.convert_alpha()
        elif "ship" in path or "trport" in path:
            surf.fill((255, 0, 0))  # Красный корабль
        elif "ast" in path:
            surf.fill((100, 100, 100))  # Серый астероид
        else:
            surf.fill((255, 255, 255))
        return surf


def get_backgrounds():
    """
    Возвращает единый фон для всех комнат: только звёзды.
    Туман убран по требованию.
    """
    return {
        "stars": load_image("backgrounds/starfields/stars.png"),
    }


def get_ship_sprites(class_id):
    folder = f"ships/class_{class_id}"

    # 1. Загружаем idle (картинка, когда стоим)
    idle_path = f"{folder}/idle.png"
    idle = load_image(idle_path)

    # 2. Загружаем анимацию (список картинок)
    movement = []
    for i in range(1, 4):  # Ищем anim1.png, anim2.png, anim3.png
        anim_path = f"{folder}/anim{i}.png"
        movement.append(load_image(anim_path))

    return idle, movement

def get_scout_sprites():
    """Загружает спрайты для корабля-разведчика из class_4."""
    folder = "ships/class_4"

    idle_path = f"{folder}/scout_idle.png"
    idle = load_image(idle_path)

    movement = []
    for i in range(1, 4):
        anim_path = f"{folder}/scout_anim{i:02d}.png"  # scout_anim01, scout_anim02, scout_anim03
        movement.append(load_image(anim_path))

    if not movement:
        movement = [idle]

    return idle, movement
def get_scout_destroyed_sprite():
    return load_image("ships/class_4/scout_destroyed.png")


def get_destroyer_sprites():
    """Загружает спрайты для истребителя из class_4."""
    folder = "ships/class_4"

    idle_path = f"{folder}/destroyer_idle.png"
    idle = load_image(idle_path)

    movement = []
    for i in range(1, 4):
        anim_path = f"{folder}/destroyer_anim{i:02d}.png"
        movement.append(load_image(anim_path))

    if not movement:
        movement = [idle]

    return idle, movement
def get_rocket_sprites():
    """Загружает 4 кадра анимации ракеты."""
    sprites = []
    for i in range(1, 5):
        path = f"projectiles/rocket_mod01_anim{i:02d}.png"
        sprites.append(load_image(path))
    return sprites

def get_explosion_sprites():
    """Загружает 10 кадров анимации взрыва."""
    sprites = []
    for i in range(1, 11):
        path = f"explosions/expl_{i:02d}.png"
        sprites.append(load_image(path))
    return sprites



def get_destroyer_destroyed_sprite():
    """Загружает спрайт уничтоженного истребителя."""
    return load_image("ships/class_4/destroyer_destroyed.png")

def get_warden_sprites():
    """Загружает спрайты для орбитального стража из class_2."""
    folder = "ships/class_2"

    idle_path = f"{folder}/orbital-warden_idle.png"
    idle = load_image(idle_path)

    movement = []
    for i in range(1, 4):
        anim_path = f"{folder}/orbital-warden_anim{i}.png"
        movement.append(load_image(anim_path))

    if not movement:
        movement = [idle]

    return idle, movement

def get_quick_shuttle_debris_sprites():
    """Загружает 10 спрайтов осколков Quick Shuttle."""
    sprites = []
    for i in range(1, 11):
        path = f"ships/debris/quickShuttle_debris_{i:02d}.png"
        sprites.append(load_image(path))
    return sprites

def get_quick_shuttle_idle_sprite():
    """Загружает idle-спрайт Quick Shuttle из class_3."""
    return load_image("ships/class_3/quickShuttle_idle.png")



def get_asteroid_sprites():
    """Загружает спрайты астероидов и возвращает словарь: key -> (sprite, size_px)"""
    return {
        "ast_mod01_s16": (load_image("asteroids/small/asteroid_mod01_16px.png"), 16),
        "ast_mod01_s32": (load_image("asteroids/medium/asteroid_mod01_32px.png"), 32),
        "ast_mod01_s64": (load_image("asteroids/large/asteroid_mod01_64px.png"), 64),
        "ast_mod04_s16": (load_image("asteroids/small/asteroid_mod04_16px.png"), 16),
        "ast_mod04_s32": (load_image("asteroids/medium/asteroid_mod04_32px.png"), 32),
        "ast_mod04_s64": (load_image("asteroids/large/asteroid_mod04_64px.png"), 64),
    }
def get_sparks_sprites():
    """Загружает 3 кадра анимации искр."""
    sprites = []
    for i in range(1, 5):
        path = f"projectiles/sparks_anim{i:02d}_16px.png"
        sprites.append(load_image(path))
    return sprites

def get_player_destroyed_sprite():
    """Загружает спрайт уничтоженного корабля игрока."""
    return load_image("ships/class_4/destroyed.png")

def get_drone_sprite():
    """Загружает спрайт скан-дрона."""
    return load_image("ships/class_5/repair_scann_drone_mod01_16px.png")


def get_scan_sprites():
    """Загружает 5 кадров анимации сканирования."""
    sprites = []
    for i in range(1, 6):
        path = f"projectiles/scan_anim{i:02d}_32px.png"
        sprites.append(load_image(path))
    return sprites
def get_destroyer_debris_sprites():
    """Загружает 3 спрайта осколков истребителя."""
    sprites = []
    for i in range(1, 4):
        path = f"ships/class_4/destroyer_debris_{i}.png"
        sprites.append(load_image(path))
    return sprites
def get_scout_debris_sprites():
    """Загружает 3 спрайта осколков разведчика."""
    sprites = []
    for i in range(1, 4):
        path = f"ships/class_4/scout_debris_{i}.png"
        sprites.append(load_image(path))
    return sprites
def get_orbital_warden_debris_sprites():
    """Загружает 19 спрайтов осколков орбитального стража."""
    sprites = []
    for i in range(1, 20):
        path = f"ships/debris/orbitalWarden_debris_{i:02d}.png"
        sprites.append(load_image(path))
    return sprites

def get_crystal_sprite():
    return load_image("resources/crystal.png")
def get_wreck_repair_sprites():
    """Загружает спрайты стадий ремонта обломка (20% → 90% → idle 100%)."""
    folder = "ships/class_3"
    sprites = {}
    for pct in [20, 30, 40, 50, 60, 70, 80, 90]:
        path = f"{folder}/destroyer_repair_128px_{pct}.png"
        sprites[pct] = load_image(path)
    sprites[100] = load_image(f"{folder}/destroyer_128px_idle.png")
    return sprites

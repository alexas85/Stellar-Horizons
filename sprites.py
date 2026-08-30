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


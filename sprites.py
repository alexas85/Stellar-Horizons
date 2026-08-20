# sprites.py
import os
import pygame

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
        # Создаем цветной квадрат 64x64 вместо картинки
        surf = pygame.Surface((64, 64))
        if convert_alpha:
            surf.set_colorkey((0, 0, 0))
        # Разные цвета для разных типов объектов для наглядности
        if "fog" in path:
            surf.fill((50, 50, 80))
        elif "stars" in path:
            surf.fill((20, 20, 40))
        elif "ship" in path or "trport" in path:
            surf.fill((255, 0, 0))  # Красный корабль
        elif "ast" in path:
            surf.fill((100, 100, 100))  # Серый астероид
        else:
            surf.fill((255, 255, 255))
        return surf


def get_backgrounds():
    """Возвращает загруженные фоновые изображения."""
    return {
        "fog": load_image("backgrounds/fog/bg_98_98_fog.png"),
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
    """Загружает спрайты астероидов разных размеров."""
    return {
        "ast_mod01_s16": load_image("asteroids/small/ast_mod01_s16.png"),
        "ast_mod01_s32": load_image("asteroids/medium/ast_mod01_s32.png"),
        "ast_mod01_s64": load_image("asteroids/large/ast_mod01_s64.png"),
    }

#!/usr/bin/env python3
"""
Процедурная генерация спрайта транспортника класса 4 (без вооружения).

Рисуем грузовой транспортник: широкий корпус-баржа с двумя грузовыми секциями,
мостовая надстройка, двигатели сзади. НЕТ орудий — гражданское судно.
Вывод: assets/ships/class_4/hauler_idle.png + hauler_anim1..3.png
"""

import os
import random
import pygame

# ------------------- Конфигурация -------------------
SIZE = 64            # целевой размер спрайта (px)
SCALE = 6            # сетка до сжатия
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "ships", "class_4")

# Палитра
COLOR_HULL = (95, 108, 122)      # основной корпус
COLOR_HULL_DARK = (60, 70, 82)   # тёмный низ/тень
COLOR_HULL_HI = (140, 155, 172)  # верхний блик
COLOR_CARGO = (150, 120, 70)     # грузовые контейнеры (песочный)
COLOR_CARGO_DARK = (110, 85, 50)
COLOR_GLASS = (140, 210, 255)    # стекло мостика
COLOR_ACCENT = (230, 150, 40)    # оранжевые акценты корпуса
COLOR_ENGINE = (255, 190, 80)    # двигатели
COLOR_DARK = (35, 42, 50)        # детали/контур


def px(surf, x, y, color, size):
    pygame.draw.rect(surf, color, (x * size, y * size, size, size))


def build_pixel_map(anim_frame):
    """
    Возвращает список (x, y, color). anim_frame 0..2 — лёгкие вариации
    (пульсация двигателя/индикаторов), чтобы анимация была заметной.
    """
    cells = []

    # --- Корпус-баржа: широкий прямоугольник со скруглением по бокам ---
    # от y=24 до y=40, ширина от x=14 до x=50
    for y in range(24, 42):
        half = 18
        if y == 24 or y == 41:
            half = 12   # скошенные углы
        elif y == 25 or y == 40:
            half = 15
        for x in range(32 - half, 32 + half):
            cells.append((x, y, COLOR_HULL))

    # --- Верхний блик корпуса ---
    for y in range(25, 29):
        for x in range(32 - 12, 32 + 12):
            cells.append((x, y, COLOR_HULL_HI))

    # --- Тёмная нижняя кромка ---
    for y in range(39, 42):
        for x in range(32 - 15, 32 + 15):
            cells.append((x, y, COLOR_HULL_DARK))

    # --- Грузовые контейнеры: две секции слева и справа от мостика ---
    # левая секция
    for y in range(28, 38):
        for x in range(17, 25):
            cells.append((x, y, COLOR_CARGO))
        # тёмные линии контейнеров
        if y in (32, 35):
            for x in range(17, 25):
                cells.append((x, y, COLOR_CARGO_DARK))
    # правая секция
    for y in range(28, 38):
        for x in range(39, 47):
            cells.append((x, y, COLOR_CARGO))
        if y in (32, 35):
            for x in range(39, 47):
                cells.append((x, y, COLOR_CARGO_DARK))

    # --- Мостик по центру ---
    for y in range(20, 29):
        for x in range(28, 37):
            cells.append((x, y, COLOR_HULL))
    # стекло мостика
    for y in range(22, 26):
        for x in range(29, 36):
            cells.append((x, y, COLOR_GLASS))

    # --- Двигатели сзади (справа) ---
    engine_x = 50
    for dy in range(28, 38):
        for dx in range(48, 53):
            cells.append((dx, dy, COLOR_ENGINE))
    # сопло тёмное
    for dy in range(30, 36):
        cells.append((49, dy, COLOR_DARK))

    # --- Носовая часть слева (обтекатель) ---
    for y in range(30, 36):
        for x in range(11, 15):
            cells.append((x, y, COLOR_HULL_HI))

    # --- Оранжевые акценты (не оружие, просто маркировка) ---
    for dy in range(27, 30):
        cells.append((26, dy, COLOR_ACCENT))
        cells.append((38, dy, COLOR_ACCENT))

    # --- Пульсация индикатора мостика по кадрам (анимация) ---
    if anim_frame == 1:
        cells.append((31, 19, COLOR_ACCENT))
        cells.append((32, 19, COLOR_ACCENT))
        cells.append((33, 19, COLOR_ACCENT))
    elif anim_frame == 2:
        # дополнительное свечение двигателя
        for dy in range(30, 36):
            cells.append((52, dy, COLOR_ACCENT))
            cells.append((53, dy, COLOR_ACCENT))

    return cells


def build_destroyed_map():
    """Разрушенный транспортник: тёмный, покорёженный корпус без целостных грузов."""
    cells = []
    # Обломок: рваные куски корпуса
    for y in range(26, 40):
        width = random.randint(8, 16)
        start_x = random.randint(22, 42 - width)
        for x in range(start_x, start_x + width):
            cells.append((x, y, COLOR_HULL_DARK))
    # пара уцелевших деталей
    for x in range(12, 16):
        for y in range(30, 34):
            cells.append((x, y, COLOR_HULL))
    for x in range(26, 30):
        for y in range(28, 32):
            cells.append((x, y, COLOR_CARGO_DARK))
    for x in range(44, 49):
        for y in range(32, 36):
            cells.append((x, y, COLOR_DARK))
    # слабое свечение двигателя
    cells.append((50, 30, COLOR_ACCENT))
    cells.append((50, 31, COLOR_ACCENT))
    return cells


def build_debris_map(idx):
    """Осколок транспортника — случайный рваный кусок корпуса."""
    cells = []
    # Разные осколки по idx
    if idx == 0:
        block = [(12, 30), (13, 29), (13, 30), (14, 30), (14, 31), (15, 31), (12, 31)]
    elif idx == 1:
        block = [(28, 34), (29, 33), (29, 34), (30, 34), (30, 35), (29, 35), (28, 35)]
    else:
        block = [(40, 28), (41, 28), (41, 29), (42, 29), (42, 30), (41, 30), (40, 29)]

    for (x, y) in block:
        cells.append((x, y, COLOR_HULL_DARK))
        cells.append((x + 1, y, COLOR_CARGO_DARK))
    return cells


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT_DIR, exist_ok=True)

    big = SIZE * SCALE
    # idle-кадр
    surf = pygame.Surface((big, big), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    for x, y, color in build_pixel_map(0):
        px(surf, x, y, color, SCALE)
    idle = pygame.transform.smoothscale(surf, (SIZE, SIZE))

    pygame.image.save(idle, os.path.join(OUT_DIR, "hauler_idle.png"))
    print(f"[OK] {os.path.join(OUT_DIR, 'hauler_idle.png')}")

    # anim1..3
    for f in (1, 2, 3):
        s = pygame.Surface((big, big), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        for x, y, color in build_pixel_map(f % 3):
            px(s, x, y, color, SCALE)
        out = pygame.transform.smoothscale(s, (SIZE, SIZE))
        pygame.image.save(out, os.path.join(OUT_DIR, f"hauler_anim{f}.png"))
        print(f"[OK] {os.path.join(OUT_DIR, f'hauler_anim{f}.png')}")

    # разрушенный спрайт
    ds = pygame.Surface((big, big), pygame.SRCALPHA)
    ds.fill((0, 0, 0, 0))
    for x, y, color in build_destroyed_map():
        px(ds, x, y, color, SCALE)
    destroyed = pygame.transform.smoothscale(ds, (SIZE, SIZE))
    pygame.image.save(destroyed, os.path.join(OUT_DIR, "hauler_destroyed.png"))
    print(f"[OK] {os.path.join(OUT_DIR, 'hauler_destroyed.png')}")

    # осколки
    for i in range(1, 4):
        bs = pygame.Surface((big, big), pygame.SRCALPHA)
        bs.fill((0, 0, 0, 0))
        for x, y, color in build_debris_map(i - 1):
            px(bs, x, y, color, SCALE)
        out = pygame.transform.smoothscale(bs, (SIZE, SIZE))
        path = os.path.join(OUT_DIR, f"hauler_debris_{i}.png")
        pygame.image.save(out, path)
        print(f"[OK] {path}")

    pygame.quit()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Процедурная генерация пиксельных спрайтов кораблей (Pygame, PNG с альфа-каналом).

Первый пробный спрайт: дрон-ремонтник класса 5 (32x32).

Всё рисуется многократно увеличенным в «пиксельной сетке» (pixel grid), затем
уменьшается до целевого размера — получается стилизованный пиксель-арт.

Запуск:  python tools/gen_sprite.py
Вывод:   assets/ships/class_5/repair_drone_gen_32px.png
"""

import os
import pygame

# ------------------- Конфигурация -------------------
SIZE = 32            # целевой размер спрайта (px)
SCALE = 8            # во сколько раз рисуем сетку до сжатия (для чётких пикселей)
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "ships",
                   "class_5", "repair_drone_gen_32px.png")

# Палитра (R, G, B)
COLOR_BODY = (70, 80, 95)       # основной корпус
COLOR_BODY_HI = (110, 125, 145) # блик/верх корпуса
COLOR_DARK = (35, 42, 50)       # тёмные детали
COLOR_ACCENT = (70, 170, 90)    # зелёный акцент (ремонтник)
COLOR_ENGINE = (255, 190, 60)   # свечение двигателя
COLOR_GLASS = (140, 200, 255)   # прозрачная "стеклянная" кабина/индикатор


def px(surf, x, y, color, size):
    """Закрашивает один «пиксель» сетки (прямоугольник size x size)."""
    pygame.draw.rect(surf, color, (x * size, y * size, size, size))


def build_pixel_map():
    """
    Возвращает список кортежей (x, y, color) для сетки 32x32 (целевое разрешение).
    Рисуем дрона-ремонтника: компактный корпус по центру, двигатель сзади,
    маленький рабочий «луч/рука» спереди и зелёный индикатор.
    """
    cells = []

    # --- Корпус (ромбовидный, верх и низ симметрично) ---
    # Верхняя половина корпуса
    for y in range(10, 20):
        # ширина ряда: с 6 (середина) до краёв 2-4
        half = max(3, 14 - abs(19 - y) * 2) // 2  # ширина половины
        if y == 15:  # самая широкая середина
            half = 8
        elif y == 16:
            half = 8
        else:
            half = 7
        for x in range(16 - half, 16 + half):
            cells.append((x, y, COLOR_BODY))
    # --- Блик (светлая полоса сверху корпуса) ---
    for y in range(12, 15):
        for x in range(16 - 5, 16 + 5):
            cells.append((x, y, COLOR_BODY_HI))

    # --- Кабина/индикатор по центру ---
    for dy in range(14, 18):
        for dx in range(-2, 3):
            cells.append((16 + dx, dy, COLOR_GLASS))

    # --- Двигатель (сзади, слева сверху от корпуса) ---
    for dx in range(-4, 0):
        for dy in range(14, 18):
            cells.append((16 + dx, dy, COLOR_ENGINE))

    # --- Зелёный акцент: зона «ремонтного» модуля спереди (справа) ---
    for dy in range(14, 18):
        cells.append((20, dy, COLOR_ACCENT))
        cells.append((21, dy, COLOR_ACCENT))

    # --- Тёмные детали: контур стыков ---
    cells.append((16, 12, COLOR_DARK))
    cells.append((16, 13, COLOR_DARK))
    cells.append((13, 19, COLOR_DARK))
    cells.append((19, 19, COLOR_DARK))

    return cells


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))  # нужно для работы Surface с альфой

    big = SIZE * SCALE
    surf = pygame.Surface((big, big), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    for x, y, color in build_pixel_map():
        px(surf, x, y, color, SCALE)

    # Уменьшаем до целевого размера с антиалиасингом
    final = pygame.transform.smoothscale(surf, (SIZE, SIZE))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(final, OUT)
    print(f"[OK] Спрайт сохранён: {OUT}")
    pygame.quit()


if __name__ == "__main__":
    main()
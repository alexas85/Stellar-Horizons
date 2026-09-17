# main.py
import pygame
import sys
import os
import math
import random

from config import ROOM_WIDTH, ROOM_HEIGHT, CAMERA_WIDTH, CAMERA_HEIGHT
from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
from game_objects.static_ship import StaticShip
from sprites import get_backgrounds, get_ship_sprites, get_asteroid_sprites, get_rocket_sprites, get_explosion_sprites, get_sparks_sprites, get_player_destroyed_sprite, get_drone_sprite, get_scan_sprites
from game_objects.player import PlayerShip
from world.generator import WorldGenerator
from game_objects.static_planet import StaticPlanet
from game_objects.station import Station
from config import RESOURCE_ICONS, REPAIR_COST_PER_PERCENT, REPAIR_RESOURCE_TYPE
from game_objects.rocket import Rocket
from game_objects.enemy import DestroyerShip, ScoutShip
from sprites import get_rocket_sprites
from game_objects.explosion import Explosion
from sprites import get_sparks_sprites
from game_objects.drone import ScanDrone, RepairDrone
from game_objects.amoeba import SpaceAmoeba
from ui_config import HUD_NEON, HUD_GLOW, HUD_TEXT, HUD_BG_ALPHA, HUD_BORDER_WIDTH, HUD_GAP, HUD_NOISE_INTENSITY, HUD_NOISE_LINE_ALPHA, HUD_GLOW_OVERLAY_ALPHA


from game_objects.bullet import Bullet


def draw_hud(screen, player, font, resource_surfaces, start_x, y_offset=20):
    x = start_x
    y = y_offset
    resource_order = ["metal", "precious", "crystal", "energy", "mineral", "uranium"]

    for name in resource_order:
        count = player.inventory.get(name, 0)
        if name not in resource_surfaces:
            continue

        icon = resource_surfaces[name]
        # Масштабируем иконку до 15x15 если нужно
        if icon.get_width() != 15 or icon.get_height() != 15:
            icon = pygame.transform.smoothscale(icon, (15, 15))

        screen.blit(icon, (x, y))
        text_x = x + icon.get_width() + 4
        text_y = y
        text_surf = font.render(str(count), True, (255, 255, 255))
        screen.blit(text_surf, (text_x, text_y))
        x += 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((CAMERA_WIDTH, CAMERA_HEIGHT))
    pygame.display.set_caption('Stellar Horizons - Asteroid Belt')
    clock = pygame.time.Clock()

    backgrounds = get_backgrounds()
    idle_sprite, movement_sprites = get_ship_sprites(4)
    asteroid_sprites = get_asteroid_sprites()

    wreck_path = "assets/ships/class_3/ship_destroyer_destroyer-01_128px_idle.png"
    wreck_sprite = None
    try:
        wreck_sprite = pygame.image.load(wreck_path).convert_alpha()
        print(f"[SUCCESS] Спрайт корабля загружен: {wreck_path}")
    except FileNotFoundError:
        print(f"[ERROR] Не удалось найти спрайт корабля по пути: {wreck_path}")

    planet_path = "assets/planets/habitable/planet_lariona_512px.png"
    planet_sprite = None
    try:
        planet_sprite = pygame.image.load(planet_path).convert_alpha()
        print(f"[SUCCESS] Спрайт планеты загружен: {planet_path}")
    except FileNotFoundError:
        print(f"[ERROR] Не удалось найти спрайт планеты: {planet_path}")

    station_path = "assets/stations/station_fuel_256px.png"
    station_sprite = None
    try:
        station_sprite = pygame.image.load(station_path).convert_alpha()
        print(f"[SUCCESS] Спрайт станции загружен: {station_path}")
    except FileNotFoundError:
        print(f"[ERROR] Не удалось найти спрайт станции по пути: {station_path}")

    bullet_path = "assets/projectiles/shot_16px_mod1.png"
    bullet_sprite = None
    try:
        bullet_sprite = pygame.image.load(bullet_path).convert_alpha()
        from game_objects.enemy import DestroyerShip
        DestroyerShip.set_bullet_sprite(bullet_sprite)
        rocket_sprites = get_rocket_sprites()
        explosion_sprites = get_explosion_sprites()
        sparks_sprites = get_sparks_sprites()

        explosions = []
        player_destroyed_sprite = get_player_destroyed_sprite()
        drone_sprite = get_drone_sprite()
        scan_sprites = get_scan_sprites()



        print(f"[SUCCESS] Спрайт выстрела загружен: {bullet_path}")
    except FileNotFoundError:
        print("[WARNING] Не удалось найти выстрел. Используется заглушка.")
        bullet_sprite = pygame.Surface((16, 16))
        bullet_sprite.fill((255, 0, 0))

    trail_path = "assets/projectiles/trail_roket01.png"
    trail_sprite = None
    try:
        trail_sprite = pygame.image.load(trail_path).convert_alpha()
        print(f"[SUCCESS] Trail sprite loaded: {trail_path}")
    except FileNotFoundError:
        print(f"[WARNING] Trail sprite not found: {trail_path}. Will use circles instead.")

    resource_surfaces = {}
    for name, path in RESOURCE_ICONS.items():
        try:
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                surf = pygame.transform.smoothscale(surf, (24, 24))
                resource_surfaces[name] = surf
            else:
                raise FileNotFoundError
        except Exception:
            placeholder = pygame.Surface((24, 24))
            placeholder.fill((150, 150, 150))
            resource_surfaces[name] = placeholder

    font_hud = pygame.font.SysFont('Arial', 15, bold=False)
    font_debug = pygame.font.SysFont('Arial', 16)
    font_ui = pygame.font.SysFont('Arial', 18, bold=True)


    player = PlayerShip(
        x=ROOM_WIDTH // 2,
        y=ROOM_HEIGHT // 2,
        idle_sprite=idle_sprite,
        movement_sprites=movement_sprites
    )
    player.set_destroyed_sprite(player_destroyed_sprite)


    generator = WorldGenerator()
    camera = pygame.Rect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
    fire_rocket = False
    rockets = []
    locked_target = None
    running = True

    trigger_distance_x = ROOM_WIDTH - 50
    trigger_distance_y = ROOM_HEIGHT - 50
    last_space_pos = (player.x, player.y)
    player_mass = 64.0  # Масса корабля для расчёта импульса

    # Константа дистанции подсветки (как ты просил)
    INTERACTION_MAX_DIST = 250
    INTERACTION_MAX_DIST_SQ = INTERACTION_MAX_DIST ** 2
    REPAIR_MENU_OFFSET_X = 240  # Смещение вправо в пикселях

    # Переменную нужно создать ДО цикла (где-нибудь рядом с running = True)
    show_scout_indicator = False
    # --- UI ОБЛОМКА ---
    ui_active = False
    ui_target_wreck = None
    ui_target_sector = None
    repair_menu_active = False  # Открыто ли окно расчета стоимости?
    repair_target_module = None  # Какой модуль чиним ("Корпус", "Броня" и т.д.)
    repair_needed_amount = 0  # Сколько ресурсов нужно
    drones = []
    # Список ремонтных дронов
    repair_drones = []
    # Словарь для отслеживания активных ремонтов: { (ship_id, module_name): True }
    active_repairs = {}
    ui_mode = "wreck"
    storage_deposit_rects = {}
    storage_withdraw_rects = {}
    storage_switch_rect = pygame.Rect(0, 0, 0, 0)
    storage_repair_switch_rect = pygame.Rect(0, 0, 0, 0)


    btn_w, btn_h = 240, 36
    cx_ui = CAMERA_WIDTH // 2
    cy_ui = CAMERA_HEIGHT // 2
    scan_button_rect = pygame.Rect(cx_ui - btn_w // 2, cy_ui - btn_h - 5, btn_w, btn_h)
    disassemble_button_rect = pygame.Rect(cx_ui - btn_w // 2, cy_ui + 5, btn_w, btn_h)

    def draw_hologram_button(surface, text, x, y, width, height, time_offset):
        """
        Рисует одну кнопку в стиле голограммы.
        """
        # Создаём прозрачную поверхность кнопки
        btn_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        # Полупрозрачный фон
        bg_color = (*HUD_NEON[:3], HUD_BG_ALPHA)
        btn_surf.fill(bg_color)

        # Неоновая рамка
        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(btn_surf, HUD_NEON, rect, HUD_BORDER_WIDTH)

        # Текст (моноширинный шрифт — стиль «техно»)
        font = pygame.font.SysFont("consolas", 16, bold=True)  # Чуть меньше шрифт
        text_surf = font.render(text, True, HUD_TEXT)
        text_rect = text_surf.get_rect(center=(width // 2, height // 2))
        btn_surf.blit(text_surf, text_rect)

        # Эффект помех (горизонтальные линии)
        noise_intensity = HUD_NOISE_INTENSITY
        for i in range(0, height, 6):
            shift = math.sin(time_offset * 2 + i * 0.5) * noise_intensity
            line_y = i + int(shift)
            if 0 <= line_y < height:
                line_color = (*HUD_GLOW, HUD_NOISE_LINE_ALPHA)
                pygame.draw.line(btn_surf, line_color, (0, line_y), (width, line_y))

        # Лёгкое свечение (bloom-эффект)
        glow_surf = btn_surf.copy()
        glow_color = (*HUD_GLOW, HUD_GLOW_OVERLAY_ALPHA)
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(glow_color)
        glow_surf.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)

        # Рисуем готовую кнопку на основной поверхности
        surface.blit(glow_surf, (x, y))

    def draw_hologram_scan_report(surface, ship_name, modules, x, y, time_offset, buttons_rects):
        """
        Рисует отчёт сканирования как набор кнопок модулей.
        buttons_rects: словарь { 'Название': pygame.Rect }, заполняется здесь.
        Возвращает Y-координату низа последней кнопки.
        """
        font_header = pygame.font.SysFont("consolas", 18, bold=True)
        font_body = pygame.font.SysFont("consolas", 14, bold=True)

        # 1. Заголовок
        header_surf = font_header.render(ship_name, True, HUD_NEON)
        surface.blit(header_surf, (x, y))

        # 2. Рисуем кнопки для каждого модуля
        start_y = y + 26
        btn_w = 180
        btn_h = 24
        gap_y = 6

        current_y = start_y

        # Очищаем словарь кнопок перед перерисовкой
        buttons_rects.clear()

        for mod_name, integrity in modules.items():
            # Формируем текст кнопки: "Броня — 32%"
            text = f"{mod_name} — {integrity}%"

            # Создаем Rect для этой кнопки (для проверки кликов)
            btn_rect = pygame.Rect(x, current_y, btn_w, btn_h)
            buttons_rects[mod_name] = btn_rect

            # Рисуем саму кнопку (используем нашу функцию отрисовки)
            # Передаем текст и координаты
            draw_hologram_button(surface, text, x, current_y, btn_w, btn_h, time_offset)

            current_y += btn_h + gap_y

        return current_y

    def draw_repair_cost_menu(surface, wreck, module_name, needed_amount, x, y, time_offset):
        """
        Рисует окно с расчетом стоимости ремонта.
        Показывает требуемое количество и наличие ресурса у игрока.
        """
        font_title = pygame.font.SysFont("consolas", 16, bold=True)
        font_body = pygame.font.SysFont("consolas", 14)

        title_text = f"РЕМОНТ: {module_name}"
        title_surf = font_title.render(title_text, True, HUD_NEON)

        res_icon = resource_surfaces.get(REPAIR_RESOURCE_TYPE)
        if not res_icon:
            res_icon = pygame.Surface((24, 24))
            res_icon.fill((150, 150, 150))

        available = player.inventory.get(REPAIR_RESOURCE_TYPE, 0)
        needed_int = int(needed_amount)

        if available >= needed_int:
            cost_color = HUD_TEXT
            cost_text = f"Требуется: {needed_int} ед."
        else:
            can_repair = int(available / REPAIR_COST_PER_PERCENT)
            cost_color = (255, 200, 80)
            cost_text = f"Требуется: {needed_int} ед. (есть: {available})"

        cost_surf = font_body.render(cost_text, True, cost_color)

        # Подсказка о частичном ремонте
        if available < needed_int and available > 0:
            partial_text = f"Будет восстановлено: +{can_repair}%"
            partial_surf = font_body.render(partial_text, True, (255, 200, 80))
        elif available == 0:
            partial_text = "Недостаточно металла!"
            partial_surf = font_body.render(partial_text, True, (255, 80, 80))
        else:
            partial_text = "Полное восстановление: +100%"
            partial_surf = font_body.render(partial_text, True, (100, 255, 100))

        win_w = 260
        win_h = 110

        win_surf = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        win_surf.fill((*HUD_NEON[:3], HUD_BG_ALPHA))
        pygame.draw.rect(win_surf, HUD_NEON, (0, 0, win_w, win_h), HUD_BORDER_WIDTH)

        for i in range(0, win_h, 6):
            shift = math.sin(time_offset * 2 + i * 0.5) * HUD_NOISE_INTENSITY
            line_y = i + int(shift)
            if 0 <= line_y < win_h:
                pygame.draw.line(win_surf, (*HUD_GLOW, HUD_NOISE_LINE_ALPHA),
                                 (0, line_y), (win_w, line_y))

        win_surf.blit(title_surf, (10, 8))
        win_surf.blit(res_icon, (10, 30))
        win_surf.blit(cost_surf, (res_icon.get_width() + 20, 33))
        win_surf.blit(partial_surf, (10, 56))

        btn_w, btn_h = 200, 26
        btn_x = (win_w - btn_w) // 2
        btn_y = win_h - btn_h - 8

        btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        btn_surf.fill((*HUD_NEON[:3], HUD_BG_ALPHA))
        pygame.draw.rect(btn_surf, HUD_NEON, (0, 0, btn_w, btn_h), HUD_BORDER_WIDTH)

        if available > 0:
            btn_text = font_body.render("РЕМОНТИРОВАТЬ", True, HUD_TEXT)
        else:
            btn_text = font_body.render("НЕТ МЕТАЛЛА", True, (255, 80, 80))

        btn_text_rect = btn_text.get_rect(center=(btn_w // 2, btn_h // 2))
        btn_surf.blit(btn_text, btn_text_rect)
        win_surf.blit(btn_surf, (btn_x, btn_y))

        surface.blit(win_surf, (x, y))

    def draw_repair_progress_bar(surface, wreck, drones, camera, time_offset):
        """Рисует полосу прогресса ремонта над обломком, если активен дрон-ремонтник."""
        # Ищем активный дрон-ремонтник для этого обломка
        active_drone = None
        for rd in drones:
            if rd.target_ship is wreck and rd.state == "REPAIRING":
                active_drone = rd
                break

        if active_drone is None:
            return

        # Расчёт прогресса
        progress = min(1.0, active_drone.elapsed_time / active_drone.total_duration)

        # Координаты обломка на экране
        wreck_sx = int(wreck.x - camera.x)
        wreck_sy = int(wreck.y - camera.y)

        # Размеры полосы
        bar_w = wreck.sprite.get_width()  # Ширина = ширина спрайта корабля
        bar_h = 6
        bar_x = wreck_sx - bar_w // 2
        bar_y = wreck_sy - wreck.sprite.get_height() // 2 - 20  # Над кораблём

        # Фон полосы (тёмный)
        bg_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bg_surf.fill((20, 20, 30, 180))
        surface.blit(bg_surf, (bar_x, bar_y))

        # Заполненная часть (неоновый циан)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            fill_surf = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            fill_surf.fill((*HUD_NEON[:3], 220))
            surface.blit(fill_surf, (bar_x, bar_y))

        # Рамка полосы
        pygame.draw.rect(surface, HUD_NEON, (bar_x, bar_y, bar_w, bar_h), 1)

        # Эффект мерцания (помехи)
        for i in range(0, bar_h, 3):
            shift = math.sin(time_offset * 3 + i * 0.7) * 2
            line_y = bar_y + i + int(shift)
            if bar_y <= line_y < bar_y + bar_h:
                pygame.draw.line(surface, (*HUD_GLOW[:3], 80),
                                 (bar_x, line_y), (bar_x + bar_w, line_y), 1)

        # Текст с процентами
        font = pygame.font.SysFont("consolas", 12, bold=True)
        percent_text = f"{active_drone.module_name}: {int(progress * 100)}%"
        text_surf = font.render(percent_text, True, HUD_NEON)
        text_rect = text_surf.get_rect(midbottom=(wreck_sx, bar_y - 2))
        surface.blit(text_surf, text_rect)

    def draw_storage_ui(surface, wreck, player, resource_surfaces, x, y, time_offset,
                        deposit_rects, withdraw_rects):
        font_header = pygame.font.SysFont("consolas", 18, bold=True)
        font_body = pygame.font.SysFont("consolas", 13, bold=True)

        header_surf = font_header.render("СКЛАД", True, HUD_NEON)
        surface.blit(header_surf, (x, y))

        deposit_rects.clear()
        withdraw_rects.clear()

        resource_order = ["metal", "precious", "crystal", "energy", "mineral", "uranium"]
        resource_names = {
            "metal": "Металл", "precious": "Драг.мет", "crystal": "Кристалл",
            "energy": "Энергия", "mineral": "Минерал", "uranium": "Уран"
        }

        start_y = y + 28
        row_h = 28
        gap_y = 4
        current_y = start_y

        for res_name in resource_order:
            player_count = player.inventory.get(res_name, 0)
            base_count = wreck.storage.get(res_name, 0)

            icon = resource_surfaces.get(res_name)
            if icon:
                small_icon = pygame.transform.smoothscale(icon, (16, 16))
                surface.blit(small_icon, (x, current_y + 3))

            name_surf = font_body.render(resource_names[res_name], True, HUD_TEXT)
            surface.blit(name_surf, (x + 22, current_y + 5))

            player_text = f"{player_count}/{player.max_resource}"
            surface.blit(font_body.render(player_text, True, HUD_TEXT), (x + 80, current_y + 5))

            dep_w, dep_h = 90, 22
            dep_x = x + 140
            dep_y = current_y + 2
            deposit_rects[res_name] = pygame.Rect(dep_x, dep_y, dep_w, dep_h)
            draw_hologram_button(surface, "ПОЛОЖИТЬ", dep_x, dep_y, dep_w, dep_h, time_offset)

            wd_w, wd_h = 90, 22
            wd_x = x + 240
            wd_y = current_y + 2
            withdraw_rects[res_name] = pygame.Rect(wd_x, wd_y, wd_w, wd_h)
            draw_hologram_button(surface, "ЗАБРАТЬ", wd_x, wd_y, wd_w, wd_h, time_offset)

            base_text = f"{base_count}/{wreck.storage_max}"
            surface.blit(font_body.render(base_text, True, HUD_TEXT), (x + 340, current_y + 5))

            current_y += row_h + gap_y

        rep_w, rep_h = 200, 28
        rep_x = x
        rep_y = current_y + 6
        repair_rect = pygame.Rect(rep_x, rep_y, rep_w, rep_h)
        draw_hologram_button(surface, "РЕМОНТ МОДУЛЕЙ", rep_x, rep_y, rep_w, rep_h, time_offset)
        return repair_rect


    while running:

        # 1. Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    show_scout_indicator = not show_scout_indicator
                    print(f"[DEBUG] Индикатор разведчика: {'ВКЛ' if show_scout_indicator else 'ВЫКЛ'}")
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Правая кнопка — запуск ракеты
                    fire_rocket = True
                if event.button == 1:  # Левая кнопка — UI
                    # --- ЛОГИКА КЛИКОВ ПО UI ---

                    # 0. Если открыт режим склада
                    if ui_mode == "storage" and ui_active and ui_target_wreck:
                        clicked_action = False

                        for res_name, rect in storage_deposit_rects.items():
                            if rect.collidepoint(event.pos):
                                amount = player.inventory.get(res_name, 0)
                                if amount > 0:
                                    actual = ui_target_wreck.deposit_resource(res_name, amount)
                                    if actual > 0:
                                        player.remove_resource(res_name, actual)
                                        print(f"[STORAGE] Положено {actual} {res_name}")
                                clicked_action = True
                                break

                        if not clicked_action:
                            for res_name, rect in storage_withdraw_rects.items():
                                if rect.collidepoint(event.pos):
                                    amount = ui_target_wreck.storage.get(res_name, 0)
                                    if amount > 0:
                                        actual = player.add_resource(res_name, amount)
                                        if actual > 0:
                                            ui_target_wreck.withdraw_resource(res_name, actual)
                                            print(f"[STORAGE] Забрано {actual} {res_name}")
                                    clicked_action = True
                                    break

                        if not clicked_action:
                            if storage_repair_switch_rect.collidepoint(event.pos):
                                ui_mode = "wreck"
                                repair_menu_active = False
                                repair_target_module = None
                                print("[ACTION] Переключение в режим ремонта")


                    # 1. Если открыто меню ремонта (подменю)
                    elif repair_menu_active and repair_target_module and ui_target_wreck:
                        wreck_sx = int(ui_target_wreck.x - camera.x)
                        wreck_sy = int(ui_target_wreck.y - camera.y)

                        # Координаты окна ремонта (должны совпадать с отрисовкой)
                        h_base_x = wreck_sx + 280
                        h_base_y = wreck_sy - 100

                        win_w, win_h = 260, 110
                        btn_w, btn_h = 200, 26
                        btn_x = (win_w - btn_w) // 2
                        btn_y = win_h - btn_h - 10

                        repair_btn_rect = pygame.Rect(h_base_x + btn_x, h_base_y + btn_y, btn_w, btn_h)

                        if repair_btn_rect.collidepoint(event.pos):
                            print(f"[ACTION] Нажата кнопка 'РЕМОНТИРОВАТЬ' для модуля: {repair_target_module}")

                            current_integrity = ui_target_wreck.modules.get(repair_target_module, 0)
                            needed_percent = 100 - current_integrity
                            needed_amount = needed_percent * REPAIR_COST_PER_PERCENT
                            available_metal = player.inventory.get(REPAIR_RESOURCE_TYPE, 0)

                            if available_metal <= 0:
                                print(f"[ERROR] Нет металла для ремонта '{repair_target_module}'.")
                                return  # Прерываем обработку клика

                            # Сколько реально можем починить
                            if available_metal >= needed_amount:
                                actual_repair_percent = needed_percent
                                actual_cost = int(needed_amount)
                            else:
                                actual_repair_percent = int(available_metal / REPAIR_COST_PER_PERCENT)
                                actual_cost = int(actual_repair_percent * REPAIR_COST_PER_PERCENT)

                            repair_key = (id(ui_target_wreck), repair_target_module)

                            # Проверяем, есть ли уже активные дроны-ремонтники
                            has_active_drone = any(d.state != "DONE" and d.state != "RETURNING" for d in repair_drones)

                            if has_active_drone:
                                print(f"[WARNING] Уже запущен дрон-ремонтник! Дождитесь его возвращения.")
                            elif repair_key in active_repairs:
                                print(f"[WARNING] Модуль '{repair_target_module}' уже чинится другим дроном!")
                            else:
                                # --- ВОТ ЗДЕСЬ мы реально запускаем ремонт ---
                                player.remove_resource(REPAIR_RESOURCE_TYPE, actual_cost)

                                new_drone = RepairDrone(
                                    player.x,
                                    player.y,
                                    ui_target_wreck,
                                    repair_target_module,
                                    drone_sprite,
                                    return_target=player,
                                    repair_amount=actual_repair_percent
                                )
                                repair_drones.append(new_drone)
                                active_repairs[repair_key] = True

                                if actual_repair_percent < needed_percent:
                                    print(
                                        f"[SUCCESS] Частичный ремонт '{repair_target_module}': +{actual_repair_percent}% за {actual_cost} металла")
                                else:
                                    print(
                                        f"[SUCCESS] Полный ремонт '{repair_target_module}': +{actual_repair_percent}% за {actual_cost} металла")

                                repair_menu_active = False
                                repair_target_module = None
                                repair_needed_amount = 0


                        else:
                            # Клик мимо кнопки — закрываем подменю
                            repair_menu_active = False
                            repair_target_module = None

                    # 2. Если открыто основное меню корабля (отсканировано)
                    elif ui_active and ui_target_wreck and ui_target_wreck.is_scanned:
                        wreck_sx = int(ui_target_wreck.x - camera.x)
                        wreck_sy = int(ui_target_wreck.y - camera.y)
                        h_base_x = wreck_sx + 60
                        h_base_y = wreck_sy - 80

                        btn_w = 180
                        btn_h = 24
                        gap_y = 6
                        current_y = h_base_y + 26

                        clicked_module = None

                        # Проходим по всем модулям и проверяем попадание клика
                        for mod_name in ui_target_wreck.modules.keys():
                            rect = pygame.Rect(h_base_x, current_y, btn_w, btn_h)
                            if rect.collidepoint(event.pos):
                                clicked_module = mod_name
                                break
                            current_y += btn_h + gap_y

                        if clicked_module:
                            # --- ЛОГИКА ОТКРЫТИЯ ПОДМЕНЮ СТОИМОСТИ ---
                            current_integrity = ui_target_wreck.modules[clicked_module]

                            if current_integrity >= 100:
                                print(f"[INFO] Модуль '{clicked_module}' уже полностью исправен.")
                            else:
                                needed_percent = 100 - current_integrity
                                needed_amount = needed_percent * REPAIR_COST_PER_PERCENT

                                repair_menu_active = True
                                repair_target_module = clicked_module
                                repair_needed_amount = needed_amount
                                print(
                                    f"[INFO] Требуется {needed_amount} металла для ремонта '{clicked_module}' до 100%")

                        elif disassemble_button_rect.collidepoint(event.pos):
                            wreck = ui_target_wreck
                            for res_name, res_amount in wreck.resources.items():
                                player.add_resource(res_name, res_amount)
                            wreck.is_disassembled = True
                            if ui_target_sector and wreck in ui_target_sector.objects:
                                ui_target_sector.objects.remove(wreck)
                            ui_active = False
                            print("[ACTION] Обломок разобран на ресурсы")

                        elif storage_switch_rect.collidepoint(event.pos) and ui_target_wreck.is_habitable:
                            ui_mode = "storage"
                            repair_menu_active = False
                            repair_target_module = None
                            print("[ACTION] Переключение в режим склада")


                    # 3. Если не отсканировано
                    elif ui_active and ui_target_wreck and not ui_target_wreck.is_scanned:
                        if scan_button_rect.collidepoint(event.pos):
                            drone = ScanDrone(player.x, player.y, ui_target_wreck,
                                              drone_sprite, scan_sprites, return_target=player)
                            drones.append(drone)
                            ui_active = False
                            print("[ACTION] Дрон-сканер запущен")
                        elif disassemble_button_rect.collidepoint(event.pos):
                            pass  # Логика разборки без сканирования

        keys = pygame.key.get_pressed()

        # --- ЛОГИКА КНОПКИ ДЕЙСТВИЯ (E) ---
        interaction_target = None

        if (not ui_active and not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed and
                keys[pygame.K_e]):

            room_x = int(player.x // ROOM_WIDTH)
            room_y = int(player.y // ROOM_HEIGHT)
            sector = generator.get_sector(room_x, room_y, asteroid_sprites,
                                          wreck_sprite=wreck_sprite, planet_sprite=planet_sprite,
                                          station_sprite=station_sprite)

            near_planet = None

            # 1. Приоритет: Планета (посадка)
            if sector and sector.objects:
                for obj in sector.objects:
                    if isinstance(obj, StaticPlanet):
                        dist_sq = (obj.x - player.x) ** 2 + (obj.y - player.y) ** 2
                        radius_sq = obj.highlight_radius ** 2
                        if dist_sq <= radius_sq:
                            near_planet = obj
                            break

            if near_planet:
                last_space_pos = (player.x, player.y)
                player.start_landing(near_planet)
                interaction_target = near_planet
            else:
                # 2. Станция (стыковка)
                near_station = None
                if sector and sector.objects:
                    for obj in sector.objects:
                        if isinstance(obj, Station):
                            dist_sq = (obj.x - player.x) ** 2 + (obj.y - player.y) ** 2
                            radius_sq = obj.highlight_radius ** 2
                            if dist_sq <= radius_sq:
                                near_station = obj
                                break

                if near_station:
                    player.start_docking(near_station)
                    interaction_target = near_station
                    print("[ACTION] Стыковка со станцией")
                else:
                    # 3. Обломок корабля (меню сканирования/разборки)
                    near_wreck = None
                    if sector and sector.objects:
                        for obj in sector.objects:
                            if isinstance(obj, StaticShip) and not obj.is_disassembled:
                                dist_sq = (obj.x - player.x) ** 2 + (obj.y - player.y) ** 2
                                radius_sq = obj.highlight_radius ** 2
                                if dist_sq <= radius_sq:
                                    near_wreck = obj
                                    break

                    if near_wreck:
                        ui_active = True
                        ui_target_wreck = near_wreck
                        ui_target_sector = sector
                        interaction_target = near_wreck
                        if near_wreck.is_habitable:
                            ui_mode = "storage"
                            print("[ACTION] Склад открыт")
                        else:
                            ui_mode = "wreck"
                            print("[ACTION] Меню обломка корабля открыто")
                    else:
                        # 4. Добыча астероида
                        closest_asteroid = None
                        closest_dist_sq = float('inf')

                        if sector and sector.asteroids:
                            for ast in sector.asteroids:
                                dx = ast.x - player.x
                                dy = ast.y - player.y
                                d_sq = dx * dx + dy * dy

                                if d_sq <= (150 ** 2):
                                    if (ast.type_key.startswith("ast_mod04") or ast.type_key.startswith(
                                            "ast_mod01")) and ast.size_px == 16:
                                        if d_sq < closest_dist_sq:
                                            closest_dist_sq = d_sq
                                            closest_asteroid = ast

                        if closest_asteroid:
                            started = player.try_start_collection(closest_asteroid)
                            if started:
                                print(f"[ACTION] Добыча начата с {closest_asteroid.type_key}")
                            interaction_target = closest_asteroid


        # --- КНОПКА ОТКАТА (Q) ---
        if keys[pygame.K_q] and ui_active:
            ui_active = False
            ui_target_wreck = None
            ui_target_sector = None
            repair_menu_active = False
            repair_target_module = None
            ui_mode = "wreck"
            print("[ACTION] Меню обломка закрыто")

        if keys[pygame.K_q] and (player.is_docking or player.is_docked):
            player.stop_docking()
            print("[ACTION] Отстыковка от станции")

        if keys[pygame.K_q] and player.on_planet_surface:
            player.exit_planet(*last_space_pos)
            print("[ACTION] Выход в космос")

        # Вращение и ускорение — ТОЛЬКО в космосе
        if not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active:

            if keys[pygame.K_a]:
                player.rotate(-1)
            if keys[pygame.K_d]:
                player.rotate(1)
            if keys[pygame.K_w]:
                player.accelerate()

        # СТРЕЛЬБА (Пробел)
        if keys[pygame.K_SPACE] and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active:
            player.shoot(bullet_sprite)

        # --- ЛОГИКА ИГРЫ (физика, коллизии, генерация) ---

        room_x = 0
        room_y = 0
        local_x = 0
        local_y = 0
        current_sector = None
        check_objects = []

        if not player.on_planet_surface:
            room_x = int(player.x // ROOM_WIDTH)
            room_y = int(player.y // ROOM_HEIGHT)
            local_x = player.x % ROOM_WIDTH
            local_y = player.y % ROOM_HEIGHT

            should_preload = False
            if (local_x < trigger_distance_x or local_x > ROOM_WIDTH - trigger_distance_x or
                    local_y < trigger_distance_y or local_y > ROOM_HEIGHT - trigger_distance_y):
                should_preload = True

            if should_preload:
                generator.preload_neighbors(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite,
                                            planet_sprite=planet_sprite, station_sprite=station_sprite)

            current_sector = generator.get_sector(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite,
                                                  planet_sprite=planet_sprite, station_sprite=station_sprite)

            if current_sector and current_sector.asteroids:
                check_objects = current_sector.asteroids

        # --- ЗАХВАТ ЦЕЛИ ДЛЯ РАКЕТЫ ---
        locked_target = None
        if current_sector and not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active:

            for obj in current_sector.objects:
                if isinstance(obj, (ScoutShip, DestroyerShip)) and not obj.is_destroyed:
                    dx = obj.x - player.x
                    dy = obj.y - player.y
                    dist = math.hypot(dx, dy)
                    if dist <= 500:
                        target_angle = math.degrees(math.atan2(dy, dx))
                        angle_diff = target_angle - player.angle
                        while angle_diff > 180:
                            angle_diff -= 360
                        while angle_diff < -180:
                            angle_diff += 360
                        if abs(angle_diff) <= 60:
                            locked_target = obj
                            break

        # --- ЗАПУСК РАКЕТЫ ---
        if fire_rocket:
            fire_rocket = False
            if not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active:
                rocket = Rocket(
                    x=player.x,
                    y=player.y,
                    angle=player.angle,
                    target=locked_target
                )
                rocket.set_sprites(rocket_sprites)
                rockets.append(rocket)

        # ВАЖНО: Вызываем update игрока, передавая список объектов.
        hit_asteroid = player.update(world_objects=check_objects)

        if hit_asteroid:
            # --- ЕДИНАЯ ФИЗИКА СТОЛКНОВЕНИЙ ДЛЯ ВСЕХ АСТЕРОИДОВ ---
            momentum_x = player.last_vx * player_mass
            momentum_y = player.last_vy * player_mass

            if abs(momentum_x) < 0.01 and abs(momentum_y) < 0.01:
                # Корабль почти стоял — слабый случайный толчок
                push_x = random.uniform(-0.5, 0.5) * 0.1
                push_y = random.uniform(-0.5, 0.5) * 0.1
            else:
                # Передача импульса от корабля к астероиду
                push_x = momentum_x / hit_asteroid.mass
                push_y = momentum_y / hit_asteroid.mass

            hit_asteroid.apply_knockback(push_x, push_y)

            # Отдача кораблю (зависит от массы астероида)
            recoil_factor = 0.2
            player.velocity.x -= push_x * (hit_asteroid.mass / player_mass) * recoil_factor
            player.velocity.y -= push_y * (hit_asteroid.mass / player_mass) * recoil_factor

        # --- ПОПАДАНИЕ ПУЛЬ ПО АСТЕРОИДАМ ---
        new_fragments = []
        if current_sector and current_sector.asteroids:
            for bullet in player.bullets[:]:
                if not bullet.is_active():
                    continue
                for ast in current_sector.asteroids:
                    if ast.marked_for_removal:
                        continue
                    if bullet.rect.colliderect(ast.rect):
                        ast.take_damage(bullet.damage)
                        if bullet in player.bullets:
                            player.bullets.remove(bullet)
                            explosions.append(Explosion(bullet.x, bullet.y, sparks_sprites))

                        if ast.hp <= 0:
                            ast.marked_for_removal = True
                            if player.collecting_asteroid is ast:
                                player.stop_collection()
                            fragments = ast.spawn_fragments(asteroid_sprites)
                            for frag in fragments:
                                if frag is not None:
                                    new_fragments.append(frag)
                        break
        # --- ПОПАДАНИЕ ПУЛЬ ПО АМЁБЕ ---
        if current_sector and current_sector.objects:
            for bullet in player.bullets[:]:
                if not bullet.is_active():
                    continue
                for obj in current_sector.objects:
                    if isinstance(obj, SpaceAmoeba) and not obj.is_destroyed:
                        if bullet.rect.colliderect(obj.rect):
                            obj.take_damage(bullet.damage)
                            if bullet in player.bullets:
                                player.bullets.remove(bullet)
                                explosions.append(Explosion(bullet.x, bullet.y, sparks_sprites))
                            break


        # --- ОБНОВЛЕНИЕ РАКЕТ ---
        for rocket in rockets[:]:
            rocket.update()
            if rocket.check_hit():
                rad = math.radians(rocket.angle)
                ex = rocket.x + math.cos(rad) * 20
                ey = rocket.y + math.sin(rad) * 20
                explosions.append(Explosion(ex, ey, explosion_sprites))
                rocket.target.take_damage(100)
                rockets.remove(rocket)
            elif not rocket.is_active():
                rockets.remove(rocket)

        # --- ОБНОВЛЕНИЕ ВЗРЫВОВ ---
        for exp in explosions[:]:
            exp.update()
            if exp.done:
                explosions.remove(exp)

        # --- ОБНОВЛЕНИЕ ДРОНОВ ---

        # 1. Обычные дроны (сканеры и т.д.)
        for drone in drones[:]:
            drone.update()
            if drone.done:
                drones.remove(drone)

        # 2. Ремонтные дроны (с очисткой словаря active_repairs)
        for rd in repair_drones[:]:
            rd.update()

            # ГЛАВНОЕ: Проверяем флаг завершения работы дрона
            if rd.done:
                # Удаляем дрон из списка
                repair_drones.remove(rd)

                # Формируем ключ, который использовали при создании дрона
                repair_key = (id(rd.target_ship), rd.module_name)

                # Удаляем запись из словаря активных ремонтов
                # .pop(key, None) безопасно удалит ключ, если он есть, и не вызовет ошибку, если его нет
                active_repairs.pop(repair_key, None)

                print(f"[DEBUG] Ремонт дроном завершен. Ключ удален: {repair_key}")

        # Добавляем фрагменты в сектор
        if new_fragments and current_sector:
            current_sector.asteroids.extend(new_fragments)

        # ОЧИСТКА УДАЛЕННЫХ АСТЕРОИДОВ
        if current_sector and current_sector.asteroids:
            current_sector.asteroids = [
                ast for ast in current_sector.asteroids if not ast.marked_for_removal
            ]
        # ОЧИСТКА УНИЧТОЖЕННОЙ АМЁБЫ
        if current_sector and current_sector.objects:
            current_sector.objects = [
                obj for obj in current_sector.objects
                if not (isinstance(obj, SpaceAmoeba) and obj.is_destroyed)
            ]


        # Движение камеры
        if player.on_planet_surface:
            target_x = max(0, min(player.x - CAMERA_WIDTH // 2, PLANET_ROOM_WIDTH - CAMERA_WIDTH))
            target_y = max(0, min(player.y - CAMERA_HEIGHT // 2, PLANET_ROOM_HEIGHT - CAMERA_HEIGHT))
            camera.topleft = (target_x, target_y)
        else:
            target_x = player.x - CAMERA_WIDTH // 2
            target_y = player.y - CAMERA_HEIGHT // 2
            camera.topleft = (target_x, target_y)

        # --- ОТРИСОВКА ---
        if player.on_planet_surface:
            screen.fill((135, 206, 235))
            player.draw(screen, camera.topleft, interaction_target=None)
        else:
            screen.fill((0, 0, 20))

            # Параллакс звёзд
            if backgrounds and "stars" in backgrounds:
                stars = backgrounds["stars"]
                w, h = stars.get_size()
                speed = 0.4
                offset_x = -int(camera.x * speed)
                offset_y = -int(camera.y * speed)

                for x in range(-1, 2):
                    for y in range(-1, 2):
                        screen.blit(stars, (offset_x + x * w, offset_y + y * h))

            all_objects = []
            if current_sector:
                if hasattr(current_sector, 'asteroids') and current_sector.asteroids:
                    all_objects.extend(current_sector.asteroids)
                if hasattr(current_sector, 'objects') and current_sector.objects:
                    all_objects.extend(current_sector.objects)

            for obj in all_objects:
                if isinstance(obj, list):
                    continue

                if hasattr(obj, 'update'):
                    if isinstance(obj, DestroyerShip):
                        obj.update(target=player)
                    elif isinstance(obj, SpaceAmoeba):
                        obj.update(target=player)
                    else:
                        obj.update()

                show_highlight = False
                if (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'highlight_radius')):
                    dist_sq = (obj.x - player.x) ** 2 + (obj.y - player.y) ** 2
                    radius_sq = obj.highlight_radius ** 2
                    if dist_sq <= radius_sq:
                        show_highlight = True

                if hasattr(obj, 'draw'):
                    if isinstance(obj, (StaticShip, StaticPlanet, Station)):
                        obj.draw(screen, camera, show_highlight=show_highlight)
                    else:
                        obj.draw(screen, camera)

            # --- СЕРАЯ ОКРУЖНОСТЬ ВОКРУГ MOD04 АСТЕРОИДОВ ---
            if current_sector and current_sector.asteroids:
                for ast in current_sector.asteroids:
                    if (ast.type_key.startswith("ast_mod04") or ast.type_key.startswith(
                            "ast_mod01")) and ast.size_px == 16:
                        dist_sq = (ast.x - player.x) ** 2 + (ast.y - player.y) ** 2
                        if dist_sq <= 150 ** 2:
                            sx = int(ast.x - camera.x)
                            sy = int(ast.y - camera.y)
                            pygame.draw.circle(screen, (128, 128, 128), (sx, sy), 32, 1)

            for bullet in player.bullets:
                bullet.draw(screen, camera)

            # --- ПРИЦЕЛЬНАЯ ПОДСКАЗКА ---
            if locked_target:
                sx = int(locked_target.x - camera.x)
                sy = int(locked_target.y - camera.y)
                pygame.draw.circle(screen, (255, 0, 0), (sx, sy), 40, 1)

            # --- РАКЕТЫ ---
            for rocket in rockets:
                rocket.draw(screen, camera)

            # Когда создаешь ракеты (или в цикле спавна):
            for r in rockets:
                if trail_sprite:
                    r.set_trail_sprite(trail_sprite)

            # --- ВЗРЫВЫ ---
            for exp in explosions:
                exp.draw(screen, camera)

            # --- ДРОНЫ ---
            for drone in drones:
                drone.draw(screen, camera)

            # --- ПУЛИ ИСТРЕБИТЕЛЯ ---
            for obj in all_objects:
                if isinstance(obj, DestroyerShip):
                    for bullet in obj.bullets[:]:
                        bullet.update()
                        if not bullet.is_active():
                            obj.bullets.remove(bullet)
                        elif bullet.rect.colliderect(player.rect):
                            player.take_damage(bullet.damage)
                            obj.bullets.remove(bullet)
                    for bullet in obj.bullets:
                        bullet.draw(screen, camera)

            # --- МЕНЮ ОБЛОМКА (голографические кнопки) ---
                    # Отрисовка дронов-ремонтников (ПОСЛЕ всех кораблей, но ДО UI)
            # Отрисовка дронов-ремонтников (ПОСЛЕ всех кораблей, но ДО UI)
            for rd in repair_drones:
                rd.draw(screen, camera)

            # Полоса прогресса ремонта (если активен дрон-ремонтник)
            h_time = pygame.time.get_ticks() / 1000.0
            for rd in repair_drones:
                if rd.target_ship and not rd.target_ship.is_disassembled:
                    draw_repair_progress_bar(screen, rd.target_ship, repair_drones, camera, h_time)
                    break

            if ui_active and ui_target_wreck:
                if ui_target_wreck.is_disassembled or (
                        ui_target_sector and ui_target_wreck not in ui_target_sector.objects
                ):
                    ui_active = False
                    ui_target_wreck = None
                else:
                    wreck_sx = int(ui_target_wreck.x - camera.x)
                    wreck_sy = int(ui_target_wreck.y - camera.y)
                    h_time = pygame.time.get_ticks() / 1000.0
                    module_buttons_rects = {}

                    if ui_mode == "storage":
                        # --- РЕЖИМ СКЛАДА ---
                        h_base_x = wreck_sx + 60
                        h_base_y = wreck_sy - 100
                        storage_repair_switch_rect = draw_storage_ui(
                            screen, ui_target_wreck, player, resource_surfaces,
                            h_base_x, h_base_y, h_time,
                            storage_deposit_rects, storage_withdraw_rects
                        )

                    elif not ui_target_wreck.is_scanned:
                        # --- ЭТАП 1: меню сканирования ---
                        h_btn_w, h_btn_h = 180, 30
                        h_base_x = wreck_sx + 60
                        h_base_y = wreck_sy - h_btn_h - 4

                        scan_button_rect = pygame.Rect(h_base_x, h_base_y, h_btn_w, h_btn_h)
                        disassemble_button_rect = pygame.Rect(h_base_x, h_base_y + h_btn_h + HUD_GAP, h_btn_w, h_btn_h)

                        draw_hologram_button(screen, "СКАНИРОВАНИЕ",
                                             h_base_x, h_base_y, h_btn_w, h_btn_h, h_time)
                        draw_hologram_button(screen, "РАЗОБРАТЬ",
                                             h_base_x, h_base_y + h_btn_h + HUD_GAP,
                                             h_btn_w, h_btn_h, h_time)

                    else:
                        # --- ЭТАП 2: отчёт сканирования ---
                        h_base_x = wreck_sx + 60
                        h_base_y = wreck_sy - 80

                        last_btn_y = draw_hologram_scan_report(
                            screen, ui_target_wreck.ship_name,
                            ui_target_wreck.modules,
                            h_base_x, h_base_y, h_time, module_buttons_rects
                        )

                        h_btn_w, h_btn_h = 200, 30
                        disassemble_button_rect = pygame.Rect(
                            h_base_x, last_btn_y + HUD_GAP, h_btn_w, h_btn_h
                        )
                        scan_button_rect = pygame.Rect(0, 0, 0, 0)

                        draw_hologram_button(screen, "РАЗОБРАТЬ НА РЕСУРСЫ",
                                             h_base_x, last_btn_y + HUD_GAP,
                                             h_btn_w, h_btn_h, h_time)

                        # Кнопка "СКЛАД" если Корпус отремонтирован
                        if ui_target_wreck.is_habitable:
                            sw_w, sw_h = 200, 30
                            sw_y = last_btn_y + HUD_GAP + h_btn_h + HUD_GAP
                            storage_switch_rect = pygame.Rect(h_base_x, sw_y, sw_w, sw_h)
                            draw_hologram_button(screen, "СКЛАД",
                                                 h_base_x, sw_y, sw_w, sw_h, h_time)
                        else:
                            storage_switch_rect = pygame.Rect(0, 0, 0, 0)

                    # --- ОТРИСОВКА МЕНЮ РЕМОНТА (если активно) ---
                    if repair_menu_active and repair_target_module:
                        repair_menu_x = wreck_sx + 280
                        repair_menu_y = wreck_sy - 100

                        draw_repair_cost_menu(
                            screen,
                            ui_target_wreck,
                            repair_target_module,
                            repair_needed_amount,
                            repair_menu_x,
                            repair_menu_y,
                            h_time
                        )

            # ОТРИСОВКА ИГРОКА
            player.draw(screen, camera.topleft, interaction_target=interaction_target)

            # --- DEBUG: ИНДИКАТОР НАПРАВЛЕНИЯ ---
            if show_scout_indicator:

                enemies = []
                for key, sect in generator.sectors.items():
                    if hasattr(sect, 'objects') and sect.objects:
                        for obj in sect.objects:
                            if isinstance(obj, (ScoutShip, DestroyerShip)):
                                label = "Scout" if isinstance(obj, ScoutShip) else "Destroyer"
                                color = (0, 255, 0) if isinstance(obj, ScoutShip) else (255, 100, 0)
                                enemies.append((obj.x, obj.y, label, color))

                psx = player.x - camera.x
                psy = player.y - camera.y

                for ex, ey, label, color in enemies:
                    dx = ex - player.x
                    dy = ey - player.y
                    dist = math.hypot(dx, dy)

                    if dist > 80:
                        ndx = dx / dist
                        ndy = dy / dist
                        arrow_len = 100
                        ax = psx + ndx * arrow_len
                        ay = psy + ndy * arrow_len

                        pygame.draw.line(screen, color, (psx, psy), (ax, ay), 2)

                        angle = math.atan2(ndy, ndx)
                        tri = 12
                        p2 = (ax - math.cos(angle - 0.4) * tri,
                              ay - math.sin(angle - 0.4) * tri)
                        p3 = (ax - math.cos(angle + 0.4) * tri,
                              ay - math.sin(angle + 0.4) * tri)
                        pygame.draw.polygon(screen, color, [(ax, ay), p2, p3])

                        dist_text = f"{label}: {int(dist)}px"
                        ts = font_debug.render(dist_text, True, color)
                        screen.blit(ts, (ax + 8, ay - 8))
                    else:
                        pygame.draw.circle(screen, color, (int(psx), int(psy)), 40, 2)
                        near_text = font_debug.render(f"{label.upper()} HERE", True, color)
                        screen.blit(near_text, (psx - 45, psy - 55))

        # --- ОТЛАДКА (текст поверх экрана) ---
        if not player.on_planet_surface:
            rx = int(player.x // ROOM_WIDTH)
            ry = int(player.y // ROOM_HEIGHT)
            room_text = f"Room: {rx}, {ry}"
        else:
            room_text = "Room: Planet"

        count = 0
        if current_sector and current_sector.asteroids:
            count = sum(1 for a in current_sector.asteroids if not isinstance(a, list))

        if player.on_planet_surface:
            mode_text = "PLANET"
        elif player.is_docking:
            mode_text = "DOCKING"
        elif player.is_docked:
            mode_text = "DOCKED"
        else:
            mode_text = "SPACE"

        info_text = (
            f"{room_text} | "
            f"Mode: {mode_text} | "
            f"HP: {player.hp}/{player.max_hp} | "
            f"Pos: {int(player.x)}, {int(player.y)} | "
            f"Angle: {int(player.angle)} | "
            f"Asteroids: {count} | Bullets: {len(player.bullets)}"
        )
        text_surf = font_debug.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        # Визуализация границ комнат (для отладки)
        if not player.on_planet_surface:
            for key, sector in generator.sectors.items():
                sx, sy = key
                rect = pygame.Rect(sx * ROOM_WIDTH, sy * ROOM_HEIGHT, ROOM_WIDTH, ROOM_HEIGHT)
                draw_rect = rect.copy()
                draw_rect.x -= camera.x
                draw_rect.y -= camera.y
                if draw_rect.colliderect(screen.get_rect()):
                    color = (0, 255, 0) if sector.is_generated else (255, 0, 0)
                    pygame.draw.rect(screen, color, draw_rect, 2)

        # --- HUD (ресурсы) ---
        hud_start_x = 10
        draw_hud(
            screen=screen,
            player=player,
            font=font_hud,
            resource_surfaces=resource_surfaces,
            start_x=hud_start_x,
            y_offset=30
        )

        # --- ПОЛОСКИ СОСТОЯНИЯ (справа внизу) ---
        bar_width = 200
        bar_height = 8
        bar_gap = 6
        bar_right_margin = 10
        bar_bottom_margin = 10
        bar_x = CAMERA_WIDTH - bar_width - bar_right_margin

        font_bar = pygame.font.SysFont('consolas', 11, bold=True)

        # Цвета: (фон, заливка, текст)
        bars = [
            ("HP", player.hp, player.max_hp, (40, 0, 0), (255, 0, 0), (255, 200, 200)),
            ("ENERGY", player.energy, player.max_energy, (0, 0, 40), (0, 150, 255), (180, 220, 255)),
            ("FUEL", player.fuel, player.max_fuel, (40, 20, 0), (180, 100, 30), (255, 200, 150)),
        ]

        for i, (label, value, max_val, bg_color, fill_color, text_color) in enumerate(bars):
            bar_y = CAMERA_HEIGHT - bar_height - bar_bottom_margin - i * (bar_height + bar_gap)

            pygame.draw.rect(screen, bg_color, (bar_x, bar_y, bar_width, bar_height))
            ratio = max(0, value / max_val) if max_val > 0 else 0
            fill_w = int(bar_width * ratio)
            if fill_w > 0:
                pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_w, bar_height))
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)

            label_surf = font_bar.render(f"{label} {int(value)}/{max_val}", True, text_color)
            label_rect = label_surf.get_rect(midleft=(bar_x + 4, bar_y + bar_height // 2))
            screen.blit(label_surf, label_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

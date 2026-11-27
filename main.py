# main.py
import pygame
import sys
import os
import math
import random

from config import ROOM_WIDTH, ROOM_HEIGHT, CAMERA_WIDTH, CAMERA_HEIGHT
from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
from game_objects.static_ship import StaticShip
from game_objects.asteroid import Asteroid
from sprites import get_backgrounds, get_ship_sprites, get_asteroid_sprites, get_warden_sprites, get_explosion_sprites, get_player_destroyed_sprite, get_drone_sprite, get_scan_sprites
from sprites import get_crystal_sprite
from game_objects.crystal import Crystal
from game_objects.player import PlayerShip
from world.generator import WorldGenerator
from game_objects.static_planet import StaticPlanet
from game_objects.station import Station
from config import (RESOURCE_ICONS, REPAIR_COST_PER_PERCENT, REPAIR_RESOURCE_TYPE, GAME_INTRO_TEXT,
                    RADAR_WAVE_SPEED, VIEW_REVEAL_MS, RADAR_COOLDOWN_MS)
from game_objects.rocket import Rocket
from game_objects.enemy import DestroyerShip, ScoutShip
from game_objects.warden import WardenShip
from sprites import get_rocket_sprites,get_orbital_warden_debris_sprites
from game_objects.explosion import Explosion
from sprites import get_sparks_sprites
from game_objects.drone import ScanDrone, RepairDrone
from game_objects.amoeba import SpaceAmoeba
from game_objects.debris import ShipDebris
from game_objects.cargo_hauler import CargoHauler
from sprites import get_destroyer_debris_sprites, get_scout_debris_sprites, get_hauler_debris_sprites
from ui_config import HUD_NEON, HUD_GLOW, HUD_TEXT, HUD_BG_ALPHA, HUD_BORDER_WIDTH, HUD_GAP, HUD_NOISE_INTENSITY, HUD_NOISE_LINE_ALPHA, HUD_GLOW_OVERLAY_ALPHA


from game_objects.bullet import Bullet

CAMERA_SPEED = 0.10  # Чем меньше число, тем плавнее (0.05 - очень медленно, 0.5 - почти мгновенно)
def draw_hud(screen, player, font, resource_surfaces, start_x, y_offset=20):
    x = start_x
    y = y_offset
    resource_order = ["metal", "precious", "steel", "crystal", "mineral", "uranium"]

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
    crystal_sprite = get_crystal_sprite()
    warden_idle, warden_anim = get_warden_sprites()

    wreck_path = "assets/ships/class_3/destroyer_128px_idle.png"
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
        movement_sprites=movement_sprites,
        class_id=4,
        start_damaged=True
    )
    player.set_destroyed_sprite(player_destroyed_sprite)


    generator = WorldGenerator()
    camera = pygame.Rect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
    fire_rocket = False
    rockets = []
    debris_list = []
    crystals = []
    destroyer_debris_sprites = get_destroyer_debris_sprites()
    scout_debris_sprites = get_scout_debris_sprites()
    hauler_debris_sprites = get_hauler_debris_sprites()
    # Загрузка осколков Орбитального Стража (19 штук)
    orbital_warden_debris_sprites = get_orbital_warden_debris_sprites()
    print(f"[INIT] Загружено {len(orbital_warden_debris_sprites)} спрайтов осколков Orbital Warden")

    warden_list = []
    warden_spawned = False



    locked_target = None
    running = True
    paused = False
    pause_quit_rect = pygame.Rect(0, 0, 0, 0)
    pause_save_rect = pygame.Rect(0, 0, 0, 0)

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
    # --- МЕНЮ РЕМОНТА КОРАБЛЯ ИГРОКА (контекстное, по клавише E) ---
    ship_repair_menu = False       # открыто ли меню ремонта собственного корабля
    # Была ли клавиша E нажата ранее и с тех пор НЕ отпускалась.
    # Нужен, чтобы не открывать меню ремонта, пока E ещё зажато после добычи:
    # меню открывается только свежим нажатием после того, как E отпустили.
    e_key_held = False             # True, если E зажата в рамках текущего касания
    # --- РАДАР / СКАНИРОВАНИЕ КОМНАТЫ ---
    radar_scan_active = False      # идёт ли волна сканирования
    radar_wave_progress = 0.0      # прогресс волны (0..1)
    # До какого момента нельзя сканировать повторно (перезагрузка радара)
    radar_cooldown_until = 0
    # id стационарных объектов (астероиды, планеты, станции, осколки),
    # которые мы увидели хоть раз и которые остаются на мини-карте навсегда.
    permanent_reveal = set()
    # Словарь времени последнего «озарения обзором» движущихся объектов
    # (корабли, амёбы, летающие осколки): {id(obj): ms}
    view_reveal_times = {}
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
    pilot_button_rect = pygame.Rect(0, 0, 0, 0)
    transfer_button_rect = pygame.Rect(0, 0, 0, 0)
    # Очередь отложенных отрядов истребителей (возмездие за транспортник).
    # Элементы: {"room": (x, y), "arrive_at": ms}
    hauler_retaliation_queue = []
    # Глобальный список всех транспортников (обновляются и рисуются всегда,
    # независимо от того, в какой комнате находится игрок).
    global_haulers = []
    # Хранение старых кораблей после пересадки (осколков) и кнопки обратной пересадки
    parked_ships = []  # список StaticShip-осколков, в которых игрок уже был и оставил старый корабль

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

        # Спрайт цели: у осколков — .sprite, у игрока — original_image/idle_sprite
        target_sprite = getattr(wreck, 'sprite', None)
        if target_sprite is None:
            target_sprite = getattr(wreck, 'original_image', None)
        if target_sprite is None:
            target_sprite = getattr(wreck, 'idle_sprite', None)

        # Размеры полосы
        bar_w = target_sprite.get_width()  # Ширина = ширина спрайта корабля
        bar_h = 6
        bar_x = wreck_sx - bar_w // 2
        bar_y = wreck_sy - target_sprite.get_height() // 2 - 20  # Над кораблём

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
        mod_name = active_drone.module_name
        # Человекочитаемое имя модуля для отображения над кораблём игрока
        human_name = {
            "fuel_leak": "Утечка топлива",
            "radar": "Радиолокатор",
        }.get(mod_name, mod_name)
        percent_text = f"{human_name}: {int(progress * 100)}%"
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

        resource_order = ["metal", "precious", "crystal", "steel", "mineral", "uranium"]
        resource_names = {
            "metal": "Металл", "precious": "Драг.мет", "crystal": "Кристалл",
            "steel": "Сталь", "mineral": "Минерал", "uranium": "Уран"
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

        # --- КНОПКА ПЕРЕСАДКИ (если корпус цел и двигатель рабочий) ---
        tr_w, tr_h = 200, 28
        tr_x = x
        tr_y = rep_y + rep_h + 6
        transfer_rect = pygame.Rect(tr_x, tr_y, tr_w, tr_h)
        if wreck.can_transfer:
            label = "ВЕРНУТЬСЯ В СВОЙ КОРАБЛЬ" if wreck.is_player_parked else "ПЕРЕСЕСТЬ В ЭТОТ"
            draw_hologram_button(surface, label, tr_x, tr_y, tr_w, tr_h, time_offset)
        return repair_rect, transfer_rect

    def _handle_transfer(wreck):
        """Пересадка игрока в/из осколка-склада. Если player уже управляет этим осколком
        (is_player_parked), возвращаем его в оставленный корабль."""
        nonlocal player
        # Спрайт отремонтированного Destroyer для управляемого корабля
        damage_sprites = StaticShip._get_repair_sprites()
        wreck_sprite = damage_sprites.get(100) or wreck_sprite

        if player.piloted_wreck is wreck:
            # --- ВЫХОД из осколка — возврат в оставленный корабль ---
            player.leave_wreck(wreck)
            player.x = wreck.parked_x
            player.y = wreck.parked_y
            player.angle = random.uniform(0, 360)
            wreck.is_player_parked = False
            wreck.parked_sprite = None
            # Закрываем меню
            ui_active = False
            ui_target_wreck = None
            ui_target_sector = None
            ui_mode = "wreck"
            print("[ACTION] Игрок вернулся в свой корабль")
            return

        # --- ПЕРЕСАДКА в осколок ---
        # Текущий обычный корабль игрока «паркуем» рядом с осколком
        wreck.parked_sprite = player.original_image
        wreck.parked_x = player.x
        wreck.parked_y = player.y
        wreck.is_player_parked = True

        player.board_wreck(wreck, wreck_sprite)

        ui_active = False
        ui_target_wreck = None
        ui_target_sector = None
        ui_mode = "wreck"
        print(f"[ACTION] Игрок пересед в осколок (Двигатель {wreck.get_engine_integrity()}%)")

    def _spawn_hauler_debris(wreck):
        """Спавнит осколки уничтоженного транспортника в текущую комнату."""
        nonlocal debris_list
        if not hauler_debris_sprites:
            return
        for debris_sprite in hauler_debris_sprites:
            debris = ShipDebris(wreck.x, wreck.y, debris_sprite)
            debris_list.append(debris)
        # Убираем транспортник из объектов сектора и глобального списка
        if current_sector is not None and wreck in current_sector.objects:
            current_sector.objects.remove(wreck)
        if wreck in generator.haulers:
            generator.haulers.remove(wreck)

    def _trigger_hauler_retaliation(room_x, room_y):
        """Ставит в очередь отряд из 3 истребителей в комнату, где подбили транспортник.
        Сам спавн происходит с задержкой (проверяется в игровом цикле)."""
        # Не спавним второй отряд в одну и ту же комнату, пока там уже есть
        # отряд из очереди
        if any(q["room"] == (room_x, room_y) for q in hauler_retaliation_queue):
            return
        # Задержка ~4 секунды
        arrive_at = pygame.time.get_ticks() + 4000
        hauler_retaliation_queue.append({"room": (room_x, room_y), "arrive_at": arrive_at})
        print(f"[HAULER] Отряд возмездия вызван в комнату ({room_x}, {room_y}) — прибудет через 4с")

    def _process_hauler_retaliation_queue():
        """Проверяет очередь отложенных отрядов и спавнит созревшие."""
        from sprites import get_destroyer_sprites, get_destroyer_destroyed_sprite
        now = pygame.time.get_ticks()
        for entry in [e for e in hauler_retaliation_queue if e["arrive_at"] <= now]:
            hauler_retaliation_queue.remove(entry)
            room_x, room_y = entry["room"]

            destroyer_idle, destroyer_anim = get_destroyer_sprites()
            destroyer_destroyed = get_destroyer_destroyed_sprite()

            target_sector = generator.get_sector(
                room_x, room_y, asteroid_sprites,
                wreck_sprite=wreck_sprite, planet_sprite=planet_sprite,
                station_sprite=station_sprite
            )
            spawn_x = room_x * ROOM_WIDTH + ROOM_WIDTH // 2
            spawn_y = room_y * ROOM_HEIGHT + ROOM_HEIGHT // 2

            for i in range(3):
                off_ang = (i * 2 * math.pi / 3) + random.uniform(0, 1)
                fighter = DestroyerShip(
                    x=spawn_x + math.cos(off_ang) * 200,
                    y=spawn_y + math.sin(off_ang) * 200,
                    idle_sprite=destroyer_idle,
                    movement_sprites=destroyer_anim,
                    sector_x=room_x, sector_y=room_y,
                    room_width=ROOM_WIDTH, room_height=ROOM_HEIGHT,
                )
                fighter.set_sector(target_sector)
                fighter.set_destroyed_sprite(destroyer_destroyed)
                # Отряд патрулирует; время на «облёт комнаты» перед уходом
                fighter.retaliation_timeout = pygame.time.get_ticks() + 20000
                target_sector.objects.append(fighter)

            if current_sector is not None and target_sector is current_sector:
                print(f"[HAULER] Отряд из 3 истребителей атакует в комнате ({room_x}, {room_y})!")
            else:
                print(f"[HAULER] Отряд из 3 истребителей прибыл в комнату ({room_x}, {room_y})")

    def draw_minimap(screen, player, current_sector, debris_list, camera, time_offset):
        """Рисует мини-карту текущей комнаты в правом верхнем углу."""
        if player.on_planet_surface or current_sector is None:
            return

        mm_size = 220
        mm_margin = 10
        mm_x = CAMERA_WIDTH - mm_size - mm_margin
        mm_y = mm_margin
        scale = mm_size / ROOM_WIDTH

        # Фон
        mm_surf = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
        mm_surf.fill((8, 12, 22, 200))

        # Сетка
        for i in range(1, 4):
            pos = i * mm_size // 4
            pygame.draw.line(mm_surf, (25, 35, 50, 120), (pos, 0), (pos, mm_size))
            pygame.draw.line(mm_surf, (25, 35, 50, 120), (0, pos), (mm_size, pos))

        # Координаты текущей комнаты
        rx = int(player.x // ROOM_WIDTH)
        ry = int(player.y // ROOM_HEIGHT)
        room_ox = rx * ROOM_WIDTH
        room_oy = ry * ROOM_HEIGHT

        def to_mm(wx, wy):
            return int((wx - room_ox) * scale), int((wy - room_oy) * scale)

        now = pygame.time.get_ticks()
        # Стационарные объекты (астероиды, планеты, станции, осколки StaticShip):
        # если хоть раз попали в обзор или были отсканированы — остаются навсегда.
        # Движущиеся (корабли, амёбы, летающие осколки): исчезают через VIEW_REVEAL_MS.
        def is_permanent_revealed(obj_key):
            return obj_key in permanent_reveal

        def is_moving_revealed(obj_key):
            return view_reveal_times.get(obj_key, 0) > now - VIEW_REVEAL_MS

        # Астероиды — стационарные: рисуем, если увидели хотя бы раз
        if current_sector.asteroids:
            for ast in current_sector.asteroids:
                if getattr(ast, 'marked_for_removal', False):
                    continue
                if not is_permanent_revealed(id(ast)):
                    continue
                mx, my = to_mm(ast.x, ast.y)
                if 0 <= mx < mm_size and 0 <= my < mm_size:
                    if ast.size_px >= 64:
                        pygame.draw.circle(mm_surf, (90, 90, 90), (mx, my), 2)
                    elif ast.size_px >= 32:
                        mm_surf.set_at((mx, my), (70, 70, 70))
                    else:
                        mm_surf.set_at((mx, my), (50, 50, 50))

        # Объекты сектора
        for obj in current_sector.objects:
            is_stationary = isinstance(obj, (StaticPlanet, Station, StaticShip))
            if is_stationary:
                revealed = is_permanent_revealed(id(obj))
            else:
                revealed = is_moving_revealed(id(obj))
            if not revealed:
                continue
            mx, my = to_mm(obj.x, obj.y)
            if not (0 <= mx < mm_size and 0 <= my < mm_size):
                continue

            if isinstance(obj, (ScoutShip, DestroyerShip, CargoHauler)):
                if isinstance(obj, CargoHauler):
                    color = (255, 190, 60)  # оранжевый — транспортник
                else:
                    color = (0, 255, 0) if isinstance(obj, ScoutShip) else (255, 100, 0)
                if getattr(obj, 'is_destroyed', False):
                    color = (70, 70, 70)
                pygame.draw.circle(mm_surf, color, (mx, my), 3)
            elif isinstance(obj, Station):
                pygame.draw.rect(mm_surf, (255, 200, 0), (mx - 3, my - 3, 6, 6))
            elif isinstance(obj, StaticPlanet):
                pygame.draw.circle(mm_surf, (0, 200, 100), (mx, my), 5)
            elif isinstance(obj, StaticShip):
                pygame.draw.circle(mm_surf, (200, 150, 50), (mx, my), 3)
            elif isinstance(obj, SpaceAmoeba):
                pygame.draw.circle(mm_surf, (150, 150, 160), (mx, my), 4)

        # Осколки (летающие) — движущиеся: исчезают через VIEW_REVEAL_MS
        for debris in debris_list:
            if getattr(debris, 'marked_for_removal', False):
                continue
            if not is_moving_revealed(id(debris)):
                continue
            mx, my = to_mm(debris.x, debris.y)
            if 0 <= mx < mm_size and 0 <= my < mm_size:
                pygame.draw.circle(mm_surf, (120, 100, 80), (mx, my), 2)

        # --- ВОЛНА СКАНИРОВАНИЯ РАДАРОМ ---
        if radar_scan_active:
            # Радиус волны: 0 → сторона комнаты
            wave_radius = radar_wave_progress * mm_size
            wx = int((player.x - room_ox) * scale)  # центр вокруг игрока
            wy = int((player.y - room_oy) * scale)
            # Растущий круг-волна
            pygame.draw.circle(mm_surf, (*HUD_GLOW, 120), (wx, wy), int(wave_radius), 1)
            # Искры по кромке волны
            for ang in range(0, 360, 15):
                sxa = wx + math.cos(math.radians(ang)) * wave_radius
                sya = wy + math.sin(math.radians(ang)) * wave_radius
                pygame.draw.circle(mm_surf, (*HUD_NEON[:3], 200), (int(sxa), int(sya)), 1, 0)

        # Прямоугольник обзора камеры
        cam_x = (camera.x - room_ox) * scale
        cam_y = (camera.y - room_oy) * scale
        cam_w = CAMERA_WIDTH * scale
        cam_h = CAMERA_HEIGHT * scale
        pygame.draw.rect(mm_surf, (255, 255, 255, 80),
                         (int(cam_x), int(cam_y), int(cam_w), int(cam_h)), 1)

        # Игрок — треугольник по направлению носа
        px, py = to_mm(player.x, player.y)
        rad = math.radians(player.angle)
        tip = (px + math.cos(rad) * 7, py + math.sin(rad) * 7)
        left = (px + math.cos(rad + 2.5) * 5, py + math.sin(rad + 2.5) * 5)
        right = (px + math.cos(rad - 2.5) * 5, py + math.sin(rad - 2.5) * 5)
        pygame.draw.polygon(mm_surf, HUD_NEON[:3], [tip, left, right])

        # Эффект помех (как в остальных UI)
        for i in range(0, mm_size, 6):
            shift = math.sin(time_offset * 2 + i * 0.5) * 1
            line_y = i + int(shift)
            if 0 <= line_y < mm_size:
                pygame.draw.line(mm_surf, (*HUD_GLOW, 15), (0, line_y), (mm_size, line_y))

        # Рамка
        pygame.draw.rect(mm_surf, (*HUD_NEON[:3], 150), (0, 0, mm_size, mm_size), 1)

        screen.blit(mm_surf, (mm_x, mm_y))

        # Подпись комнаты
        room_label = f"[{rx}, {ry}]"
        lbl = font_debug.render(room_label, True, HUD_NEON[:3])
        screen.blit(lbl, (mm_x + 4, mm_y + mm_size + 2))
    game_over_state = 0          # 0 = игра, 1 = ждём 3 секунды, 2 = экран «игра окончена»
    game_over_start_time = 0    # время начала отсчёта
    screen_dim_alpha = 0         # прозрачность затемнения
    show_intro = True            # показываем сюжетное интро при старте


    while running:
        # 1. Получаем позицию мыши (ИСПРАВЛЕНИЕ ОШИБКИ)
        mouse_pos = pygame.mouse.get_pos()

        # 2. Получаем время для эффектов UI
        time_offset = pygame.time.get_ticks() / 1000.0

        # 1. Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    show_scout_indicator = not show_scout_indicator
                    print(f"[DEBUG] Индикатор разведчика: {'ВКЛ' if show_scout_indicator else 'ВЫКЛ'}")
                # Свежее нажатие E: ставим флаг «только что нажата».
                # Он гасится после однократной обработки (или при KEYUP),
                # поэтому меню/действия не повторяются, пока E удерживается.
                if event.key == pygame.K_e:
                    e_key_held = True
                if event.key == pygame.K_ESCAPE:
                    if game_over_state == 2:
                        running = False
                    elif show_intro:
                        show_intro = False
                    else:
                        paused = not paused
                if event.key == pygame.K_RETURN and show_intro:
                    show_intro = False
                    print("[INTRO] Пропуск сюжетного интро")
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_e:
                    # Клавиша отпущена — следующее нажатие будет «свежим».
                    e_key_held = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Правая кнопка — запуск ракеты
                    fire_rocket = True
                if event.button == 1:  # Левая кнопка — UI
                    if paused:
                        if pause_quit_rect.collidepoint(event.pos):
                            running = False
                        continue
                    # --- ЛОГИКА КЛИКОВ ПО UI ---

                    # 0.1 Меню ремонта собственного корабля (по E)
                    if ship_repair_menu:
                        # Клики по кнопкам модулей
                        # Координаты СОВПАДАЮТ с отрисовкой меню (см. блок ОТРИСОВКА):
                        # menu_w=340, menu_h=240, центр экрана; кнопки от m_y+48, шаг btn_h+6.
                        m_status = player.module_status()
                        menu_w, menu_h = 340, 240
                        m_x = CAMERA_WIDTH // 2 - menu_w // 2
                        m_y = CAMERA_HEIGHT // 2 - menu_h // 2
                        btn_x = m_x + 20
                        btn_w = menu_w - 40
                        btn_h = 34
                        cur_y = m_y + 48
                        for mod_id in ("fuel_leak", "radar", "hull"):
                            info = m_status[mod_id]
                            btn_rect = pygame.Rect(btn_x, cur_y, btn_w, btn_h)
                            if btn_rect.collidepoint(event.pos):
                                if not info["repaired"]:
                                    # Защита от повторного запуска дрона на тот же модуль
                                    player_active = any(
                                        d.target_ship is player and d.module_name == mod_id
                                        and d.state != "DONE" and d.state != "RETURNING"
                                        for d in repair_drones
                                    )
                                    if player_active:
                                        print(f"[REPAIR] Модуль '{info['name']}' уже чинится дроном")
                                    else:
                                        # Списываем стоимость модуля
                                        if not player.repair_module(mod_id):
                                            # Не хватило ресурсов — не запускаем дрон
                                            print(f"[REPAIR] Недостаточно ресурсов для {info['name']}")
                                        else:
                                            # Ресурсы списаны — запускаем дрона-ремонтника,
                                            # который физически чинит модуль (как у осколка)
                                            hooks = player.make_repair_hooks(mod_id)
                                            if hooks is not None:
                                                # Модули игрока чинятся за 10 секунд
                                                new_drone = RepairDrone(
                                                    player.x, player.y, player, mod_id,
                                                    drone_sprite,
                                                    return_target=player,
                                                    read_integrity=hooks[0],
                                                    write_integrity=hooks[1],
                                                    duration_seconds=10,
                                                )
                                                repair_drones.append(new_drone)
                                                print(f"[REPAIR] Дрон-ремонтник запущен на модуль '{info['name']}'")
                            cur_y += btn_h + 6
                        continue

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
                            elif transfer_button_rect.collidepoint(event.pos) and ui_target_wreck.can_transfer:
                                _handle_transfer(ui_target_wreck)


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

                        # --- НОВАЯ ЛОГИКА: КНОПКА "СЕСТЬ ЗА ШТУРВАЛ" ---
                        # --- ОБРАБОТКА КНОПКИ "СЕСТЬ ЗА ШТУРВАЛ" ---
                        if ui_active and ui_target_wreck and pilot_button_rect.collidepoint(mouse_pos):
                            # Проверка условий (Корпус >= 100, Двигатель >= 30)
                            hull_ok = ui_target_wreck.modules.get("Корпус", 0) >= 100
                            engines_ok = ui_target_wreck.modules.get("Двигатель", 0) >= 30

                            if hull_ok and engines_ok:
                                player.board_wreck_legacy(ui_target_wreck)
                                ui_active = False
                                ui_target_wreck = None
                                print("Игрок успешно пересел!")
                            else:
                                print("Недостаточно модулей для управления!")
                            continue
                        # Здесь будет основная логика пересадки. Пока просто выводим в консоль.
                        # Например: player.enter_ship(ui_target_wreck)

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
        if not paused:
            # --- ЛОГИКА КНОПКИ ДЕЙСТВИЯ (E) ---
            interaction_target = None
            # ОПРЕДЕЛЯЕМ, КТО СЕЙЧАС УПРАВЛЯЕТСЯ
            if player.is_boarded and player.boarded_wreck:
                active_ship = player.boarded_wreck
            else:
                active_ship = player

            # Применяем ввод к активному кораблю
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                active_ship.rotate(-1)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                active_ship.rotate(1)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                active_ship.accelerate()

            # Стрельба (важно: метод shoot должен быть у обоих классов!)
            # Если у StaticShip нет метода shoot, скопируй логику из PlayerShip или оставь только для игрока
            if keys[pygame.K_SPACE]:
                if hasattr(active_ship, 'shoot'):
                    active_ship.shoot(bullet_sprite)
                elif active_ship == player:
                    player.shoot(bullet_sprite)

            # Выход из обломка (клавиша E)
            if player.is_boarded and player.boarded_wreck:
                if keys[pygame.K_e]:
                    player.leave_wreck_legacy()

        # Действие по E срабатывает ОДИН раз за каждое свежее нажатие (e_key_held).
        # При удержании клавиши (даже когда добыча уже закончилась) меню НЕ открывается —
        # нужно отпустить E и нажать заново. Добыча по зажатой E продолжается отдельно
        # в цикле (player.is_collecting), поэтому здесь fresh-press достаточно.
        if (e_key_held and not ui_active and not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed):
            # Гасим флаг сразу — действие произойдёт только один раз за нажатие.
            e_key_held = False

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

                        # Поиск ближайшего осколка (если астероид не найден)
                        if not closest_asteroid and debris_list:
                            closest_debris = None
                            closest_debris_dist_sq = float('inf')
                            for debris in debris_list:
                                if debris.marked_for_removal:
                                    continue
                                dx = debris.x - player.x
                                dy = debris.y - player.y
                                d_sq = dx * dx + dy * dy
                                if d_sq <= (150 ** 2) and d_sq < closest_debris_dist_sq:
                                    closest_debris_dist_sq = d_sq
                                    closest_debris = debris
                            if closest_debris:
                                closest_asteroid = closest_debris
                        # Поиск ближайшего кристалла
                        if not closest_asteroid and crystals:
                            closest_crystal = None
                            closest_crystal_dist_sq = float('inf')
                            for crystal in crystals:
                                if crystal.marked_for_removal:
                                    continue
                                dx = crystal.x - player.x
                                dy = crystal.y - player.y
                                d_sq = dx * dx + dy * dy
                                if d_sq <= (150 ** 2) and d_sq < closest_crystal_dist_sq:
                                    closest_crystal_dist_sq = d_sq
                                    closest_crystal = crystal
                            if closest_crystal:
                                closest_asteroid = closest_crystal


                        if closest_asteroid:
                            started = player.try_start_collection(closest_asteroid)
                            if started:
                                print(f"[ACTION] Добыча начата с {closest_asteroid.type_key}")
                            interaction_target = closest_asteroid
                        else:
                            # Рядом ничего нет — открываем контекстное меню ремонта
                            # собственного корабля (утечка топлива, радиолокатор и т.д.)
                            ship_repair_menu = True
                            print("[ACTION] Открыто меню ремонта надстройки корабля")

        # --- ПОДДЕРЖАНИЕ ЛАЗЕРА ДОБЫЧИ ---
        # Пока идёт сбор ресурсов — белый лазер от корабля к астероиду остаётся
        # даже после того, как клавиша E отпущена. Он исчезнет сам, когда добыча
        # закончится (ресурсы добыты / вышли из зоны) или по нажатию Q.
        if player.is_collecting and player.collecting_asteroid is not None:
            interaction_target = player.collecting_asteroid


        # --- КНОПКА ОТКАТА (Q) ---
        if keys[pygame.K_q] and ui_active:
            ui_active = False
            ui_target_wreck = None
            ui_target_sector = None
            repair_menu_active = False
            repair_target_module = None
            ui_mode = "wreck"
            print("[ACTION] Меню обломка закрыто")

        # Отмена добычи по Q (лазер также исчезает — interaction_target обнулится ниже)
        if keys[pygame.K_q] and player.is_collecting:
            player.stop_collection()
            interaction_target = None
            print("[ACTION] Добыча отменена")

        if keys[pygame.K_q] and ship_repair_menu:
            ship_repair_menu = False
            print("[ACTION] Меню ремонта корабля закрыто")

        if keys[pygame.K_q] and (player.is_docking or player.is_docked):
            player.stop_docking()
            print("[ACTION] Отстыковка от станции")

        if keys[pygame.K_q] and player.on_planet_surface:
            player.exit_planet(*last_space_pos)
            print("[ACTION] Выход в космос")

        # Вращение и ускорение — ТОЛЬКО в космосе
        if not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active and not ship_repair_menu:

            if keys[pygame.K_a]:
                player.rotate(-1)
            if keys[pygame.K_d]:
                player.rotate(1)
            if keys[pygame.K_w]:
                player.accelerate()

        # --- СКАНИРОВАНИЕ КОМНАТЫ РАДАРОМ (R) ---
        now_ticks = pygame.time.get_ticks()
        # Радар работает только в своей комнате; после сканирования — перезагрузка.
        if (keys[pygame.K_r] and not player.on_planet_surface and not player.is_landing and
                not player.is_docking and not player.is_docked and not player.is_destroyed and
                not ui_active and not ship_repair_menu and player.radar_online and not radar_scan_active
                and now_ticks >= radar_cooldown_until):
            # Запускаем сканирование текущей комнаты
            radar_wave_progress = 0.0
            radar_scan_active = True
            print("[RADAR] Сканирование комнаты запущено")
        elif keys[pygame.K_r] and player.radar_online and now_ticks < radar_cooldown_until:
            print(f"[RADAR] Радар перезаряжается... {max(0, (radar_cooldown_until - now_ticks) // 1000)}с")

        # --- АНИМАЦИЯ ВОЛНЫ РАДАРА ---
        if radar_scan_active and not paused:
            radar_wave_progress += RADAR_WAVE_SPEED
            if radar_wave_progress >= 1.0:
                radar_wave_progress = 1.0
                # Сканирование завершено: вскрываем все объекты комнаты.
                # Стационарные — навсегда, движущиеся — на время VIEW_REVEAL_MS.
                rad_sector = generator.get_sector(
                    int(player.x // ROOM_WIDTH), int(player.y // ROOM_HEIGHT),
                    asteroid_sprites, wreck_sprite=wreck_sprite,
                    planet_sprite=planet_sprite, station_sprite=station_sprite)
                rad_now = pygame.time.get_ticks()
                if rad_sector is not None:
                    all_objs = list(rad_sector.asteroids or []) + list(rad_sector.objects or []) + list(debris_list)
                    for o in all_objs:
                        if not hasattr(o, 'x') or not hasattr(o, 'y'):
                            continue
                        if isinstance(o, (Asteroid, StaticPlanet, Station, StaticShip)):
                            permanent_reveal.add(id(o))
                        else:
                            view_reveal_times[id(o)] = rad_now
                        # Сканирование радаром — признак внимания к транспортнику
                        if isinstance(o, CargoHauler):
                            o.mark_attention()
                # Включаем перезагрузку радара (15 сек)
                radar_cooldown_until = rad_now + RADAR_COOLDOWN_MS
                radar_scan_active = False
                print("[RADAR] Сканирование завершено, радар перезаряжается")

        # СТРЕЛЬБА (Пробел)
        if keys[pygame.K_SPACE] and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active and not ship_repair_menu:
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
            # --- ПЕРЕНОС ОСКОЛКОВ QUICK SHUTTLE ИЗ sector.objects В debris_list ---
            if current_sector and current_sector.objects:
                for obj in current_sector.objects[:]:
                    if isinstance(obj, ShipDebris):
                        debris_list.append(obj)
                        current_sector.objects.remove(obj)
                        print(f"[DEBUG] Осколок Quick Shuttle перенесён в debris_list")


            if current_sector and current_sector.asteroids:
                check_objects = current_sector.asteroids

        # --- ЗАХВАТ ЦЕЛИ ДЛЯ РАКЕТЫ ---
        locked_target = None
        if current_sector and not player.on_planet_surface and not player.is_landing and not player.is_docking and not player.is_docked and not player.is_destroyed and not ui_active:

            # Захват цели: враги текущей комнаты + глобальные транспортники (могут быть
            # в соседней комнате, но видимы игроку).
            lock_candidates = []
            if current_sector and current_sector.objects:
                lock_candidates.extend(current_sector.objects)
            lock_candidates.extend(generator.haulers)

            for obj in lock_candidates:
                if isinstance(obj, (ScoutShip, DestroyerShip, CargoHauler)) and not obj.is_destroyed:
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
        # --- ЛОГИКА GAME OVER ---
        if player.is_destroyed and game_over_state == 0:
            game_over_state = 1
            game_over_start_time = pygame.time.get_ticks()

        if game_over_state == 1:
            elapsed = (pygame.time.get_ticks() - game_over_start_time) / 1000.0
            screen_dim_alpha = min(160, int(160 * (elapsed / 3.0)))
            if elapsed >= 3.0:
                game_over_state = 2
                screen_dim_alpha = 160

        if game_over_state == 2:
            screen_dim_alpha = 160


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
        # --- ПОПАДАНИЕ ПУЛЬ ПО АМЁБЕ И ТРАНСПОРТНИКАМ ---
        # Пули проверяют амёб/врагов текущей комнаты + все транспортники (глобально).
        bullet_hit_targets = []
        if current_sector and current_sector.objects:
            bullet_hit_targets.extend(current_sector.objects)
        bullet_hit_targets.extend(generator.haulers)

        for bullet in player.bullets[:]:
            if not bullet.is_active():
                continue
            for obj in bullet_hit_targets:
                if isinstance(obj, (SpaceAmoeba, CargoHauler)) and not obj.is_destroyed:
                    if bullet.rect.colliderect(obj.rect):
                        hit_target = obj
                        was_destroyed = hit_target.is_destroyed
                        hit_target.take_damage(bullet.damage)
                        if bullet in player.bullets:
                            player.bullets.remove(bullet)
                            explosions.append(Explosion(bullet.x, bullet.y, sparks_sprites))
                        # Транспортник только что уничтожен — осколки + отряд истребителей
                        if (isinstance(hit_target, CargoHauler)
                                and not was_destroyed and hit_target.is_destroyed):
                            _spawn_hauler_debris(hit_target)
                            ax, ay = getattr(hit_target, 'attack_room', (0, 0))
                            _trigger_hauler_retaliation(ax, ay)
                        break

        # --- ОБНОВЛЕНИЕ РАКЕТ ---
        for rocket in rockets[:]:
            rocket.update()
            if rocket.check_hit():
                rad = math.radians(rocket.angle)
                ex = rocket.x + math.cos(rad) * 20
                ey = rocket.y + math.sin(rad) * 20
                explosions.append(Explosion(ex, ey, explosion_sprites))

                target = rocket.target
                was_destroyed = target.is_destroyed
                target.take_damage(100)

                # Если корабль только что уничтожен — спавним осколки
                if not was_destroyed and target.is_destroyed:
                    debris_sprites = []

                    if isinstance(target, WardenShip) and orbital_warden_debris_sprites:
                        # Для Стража используем его уникальные 19 осколков
                        debris_sprites = orbital_warden_debris_sprites
                        print("[ACTION] Орбитальный страж разрушен на осколки!")

                    elif isinstance(target, DestroyerShip) and destroyer_debris_sprites:
                        debris_sprites = destroyer_debris_sprites

                    elif isinstance(target, ScoutShip) and scout_debris_sprites:
                        debris_sprites = scout_debris_sprites

                    elif isinstance(target, CargoHauler):
                        # Транспортник уничтожен ракетой: осколки + отряд истребителей
                        if hauler_debris_sprites:
                            debris_sprites = hauler_debris_sprites
                        # Вызываем отряд возмездия в комнате, где произошло нападение
                        ax, ay = getattr(target, 'attack_room', (0, 0))
                        _trigger_hauler_retaliation(ax, ay)
                        print("[HAULER] Транспортник уничтожен ракетой — вызван отряд!")

                    if debris_sprites:
                        for debris_sprite in debris_sprites:
                            debris = ShipDebris(target.x, target.y, debris_sprite)
                            debris_list.append(debris)
                        if current_sector and target in current_sector.objects:
                            current_sector.objects.remove(target)
                        # Уничтоженный транспортник убираем и из глобального списка
                        if isinstance(target, CargoHauler) and target in generator.haulers:
                            generator.haulers.remove(target)

                rockets.remove(rocket)
            elif not rocket.is_active():
                rockets.remove(rocket)

        # --- ОБНОВЛЕНИЕ ВЗРЫВОВ ---
        for exp in explosions[:]:
            exp.update()
            if exp.done:
                explosions.remove(exp)

        # --- ОБНОВЛЕНИЕ ОСКОЛКОВ ---
        for debris in debris_list[:]:
            debris.update()
            if debris.marked_for_removal:
                debris_list.remove(debris)

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
        # ОЧИСТКА АМЁБЫ (только когда fully_destroyed)
        if current_sector and current_sector.objects:
            current_sector.objects = [
                obj for obj in current_sector.objects
                if not (isinstance(obj, SpaceAmoeba) and obj.fully_destroyed)
            ]
        # --- СПАВН ОРБИТАЛЬНОГО СТРАЖА В КОМНАТЕ (1, 0) ---
        if room_x == 1 and room_y == 0 and not warden_spawned and not player.on_planet_surface:
            warden_spawned = True

            room_center_x = 1 * ROOM_WIDTH + ROOM_WIDTH // 2
            room_center_y = 0 * ROOM_HEIGHT + ROOM_HEIGHT // 2

            dx = room_center_x - player.x
            dy = room_center_y - player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx /= dist
                dy /= dist

            spawn_x = room_center_x + dx * (ROOM_WIDTH // 2 + 300)
            spawn_y = room_center_y + dy * (ROOM_HEIGHT // 2 + 300)

            flight_angle = math.degrees(math.atan2(-dy, -dx))

            warden = WardenShip(
                x=spawn_x,
                y=spawn_y,
                idle_sprite=warden_idle,
                movement_sprites=warden_anim,
                direction_angle=flight_angle
            )
            warden_list.append(warden)
            warden.set_asteroid_sprites(asteroid_sprites)
            print(f"[DEBUG] Орбитальный страж создан в комнате (1, 0)")

        # --- ОБНОВЛЕНИЕ ОРБИТАЛЬНОГО СТРАЖА ---
        for warden in warden_list[:]:
            w_room_x = int(warden.x // ROOM_WIDTH)
            w_room_y = int(warden.y // ROOM_HEIGHT)
            w_sector = generator.get_sector(w_room_x, w_room_y, asteroid_sprites,
                                            wreck_sprite=wreck_sprite, planet_sprite=planet_sprite,
                                            station_sprite=station_sprite)
            warden.set_sector(w_sector)

            warden.update(camera_rect=camera)

            # Собираем осколки от тарана и добавляем в сектор стража
            if warden.pending_fragments:
                w_sector.asteroids.extend(warden.pending_fragments)
                warden.pending_fragments.clear()

            # Очистка разрушенных астероидов в секторе стража
            if w_sector and hasattr(w_sector, 'asteroids') and w_sector.asteroids:
                w_sector.asteroids = [
                    ast for ast in w_sector.asteroids if not ast.marked_for_removal
                ]

            # Уничтожение стража — взрыв + удаление
            if warden.is_destroyed:
                explosions.append(Explosion(warden.x, warden.y, explosion_sprites))

                # Спавним 19 осколков Орбитального Стража
                if orbital_warden_debris_sprites:
                    for debris_sprite in orbital_warden_debris_sprites:
                        debris = ShipDebris(warden.x, warden.y, debris_sprite)
                        debris_list.append(debris)
                    print(
                        f"[ACTION] Орбитальный страж разрушен при таране — {len(orbital_warden_debris_sprites)} осколков добавлено")

                warden_list.remove(warden)
                continue

            if warden.should_despawn:
                warden_list.remove(warden)
                print("[DEBUG] Орбитальный страж исчез (вне поля зрения 15 сек)")

        # --- ОБНОВЛЕНИЕ КРИСТАЛЛОВ ---
        for crystal in crystals[:]:
            crystal.update()

        # --- СПАВН КРИСТАЛЛОВ ИЗ АМЁБЫ ---
        if current_sector and current_sector.objects:
            for obj in current_sector.objects:
                if isinstance(obj, SpaceAmoeba) and obj.pending_crystal_count > 0:
                    for _ in range(obj.pending_crystal_count):
                        cx = obj.x + random.uniform(-40, 40)
                        cy = obj.y + random.uniform(-40, 40)
                        crystals.append(Crystal(cx, cy, crystal_sprite))
                    obj.pending_crystal_count = 0

        # --- ОЧИСТКА СОБРАННЫХ КРИСТАЛЛОВ ---
        crystals = [c for c in crystals if not c.marked_for_removal]

        # Движение камеры
        # Внутри цикла while running, вместо прямого присваивания:
        if player.on_planet_surface:
            target_x = player.x - CAMERA_WIDTH // 2
            target_y = player.y - CAMERA_HEIGHT // 2

            # Ограничиваем целевые координаты границами комнаты
            target_x = max(0, min(target_x, PLANET_ROOM_WIDTH - CAMERA_WIDTH))
            target_y = max(0, min(target_y, PLANET_ROOM_HEIGHT - CAMERA_HEIGHT))

            # Плавно интерполируем текущую позицию камеры к целевой
            camera.x += (target_x - camera.x) * CAMERA_SPEED
            camera.y += (target_y - camera.y) * CAMERA_SPEED
        else:
            target_x = player.x - CAMERA_WIDTH // 2
            target_y = player.y - CAMERA_HEIGHT // 2

            # В космосе камера мгновенно следует за игроком (корабль в центре),
            # чтобы управление не ощущалось «резким» из-за отставания камеры
            camera.x = target_x
            camera.y = target_y

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
                # Берём смещение по модулю размера тайла: иначе при большом
                # смещении камеры часть экрана остаётся не покрытой тайлом,
                # и видна заливочная полоса (0,0,20) — «синяя граница» между
                # комнатами в колонке x = -3. Модуль всегда закрывает экран
                # звёздами, второй тайл по циклу (-1..1) покрывает остальное.
                offset_x = -int(camera.x * speed) % w
                offset_y = -int(camera.y * speed) % h

                for x in range(-1, 2):
                    for y in range(-1, 2):
                        screen.blit(stars, (offset_x + x * w, offset_y + y * h))

            all_objects = []
            if current_sector:
                if hasattr(current_sector, 'asteroids') and current_sector.asteroids:
                    all_objects.extend(current_sector.asteroids)
                if hasattr(current_sector, 'objects') and current_sector.objects:
                    all_objects.extend(current_sector.objects)

            # Синхронизируем глобальный список транспортников с генератором
            global_haulers[:] = [h for h in generator.haulers if not h.is_destroyed]

            # Обрабатываем отложенные отряды возмездия (прибытие истребителей)
            if not paused:
                _process_hauler_retaliation_queue()

                # Обновляем все транспортники независимо от комнаты игрока
                for h in global_haulers[:]:
                    h.update(target=player)
                    # Транспортник исчезает, если игрок в течение минуты его
                    # не сканировал радаром и не преследовал/не обстреливал.
                    if pygame.time.get_ticks() - h.last_attention_time > h.vanishing_timeout:
                        if h in generator.haulers:
                            generator.haulers.remove(h)
                        owner_sector = getattr(h, 'sector', None)
                        if owner_sector is not None and h in owner_sector.objects:
                            owner_sector.objects.remove(h)

            for obj in all_objects:
                if isinstance(obj, list):
                    continue

                # Осколок, которым игрок сейчас управляет, рисуется как сам игрок — пропускаем его здесь
                if obj is player.piloted_wreck:
                    continue

                if hasattr(obj, 'update') and not paused:
                    if isinstance(obj, DestroyerShip):
                        obj.update(target=player)
                        # Отряд возмездия: если игрок не в комнате, истребители
                        # некоторое время патрулируют, затем «улетают обратно».
                        if getattr(obj, 'retaliation_timeout', None):
                            if (pygame.time.get_ticks() > obj.retaliation_timeout
                                    and player is not None
                                    and not (obj.room_left <= player.x <= obj.room_right
                                             and obj.room_top <= player.y <= obj.room_bottom)):
                                # Истребители улетают — удаляем из сектора
                                owner_sector = getattr(obj, 'sector', None)
                                if owner_sector is not None and obj in owner_sector.objects:
                                    owner_sector.objects.remove(obj)
                                    print(f"[HAULER] Отряд улетел из комнаты ({obj.room_left // ROOM_WIDTH}, {obj.room_top // ROOM_HEIGHT}) — игрока нет")
                    elif isinstance(obj, SpaceAmoeba):
                        obj.update(target=player)
                    else:
                        obj.update()
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

            # --- ОТРИСОВКА ПРИПАРКОВАННЫХ КОРАБЛЕЙ (старые корабли игрока) ---
            # Отдельный проход: рисуем даже если соответствующий осколок пропущен
            # (управляемый игроком осколок не рисуется в цикле выше).
            for obj in all_objects:
                if isinstance(obj, StaticShip) and obj.is_player_parked and obj.parked_sprite:
                    psx = int(obj.parked_x - camera.x)
                    psy = int(obj.parked_y - camera.y)
                    parked_img = obj.parked_sprite
                    parked_rect = parked_img.get_rect(center=(psx, psy))
                    screen.blit(parked_img, parked_rect)

            # --- ОТРИСОВКА ТРАНСПОРТНИКОВ (всегда, независимо от комнаты игрока) ---
            # Транспортники летят сквозь комнаты и не должны пропадать из виду,
            # покидая комнату. Рисуем их отдельно поверх объектов комнаты.
            for h in global_haulers:
                if h.is_destroyed:
                    continue
                h.draw(screen, camera)

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

            # --- СЕРАЯ ОКРУЖНОСТЬ ВОКРУГ ОСКОЛКОВ ---
            for debris in debris_list:
                if debris.marked_for_removal:
                    continue
                dist_sq = (debris.x - player.x) ** 2 + (debris.y - player.y) ** 2
                if dist_sq <= 150 ** 2:
                    sx = int(debris.x - camera.x)
                    sy = int(debris.y - camera.y)
                    pygame.draw.circle(screen, (128, 128, 128), (sx, sy), 40, 1)
            # --- СЕРАЯ ОКРУЖНОСТЬ ВОКРУГ КРИСТАЛЛОВ ---
            for crystal in crystals:
                if crystal.marked_for_removal:
                    continue
                dist_sq = (crystal.x - player.x) ** 2 + (crystal.y - player.y) ** 2
                if dist_sq <= 150 ** 2:
                    sx = int(crystal.x - camera.x)
                    sy = int(crystal.y - camera.y)
                    pygame.draw.circle(screen, (128, 128, 128), (sx, sy), 32, 1)

            for bullet in player.bullets:
                bullet.draw(screen, camera)

            # --- ПРИЦЕЛЬНАЯ ПОДСКАЗКА ---
            if locked_target:
                sx = int(locked_target.x - camera.x)
                sy = int(locked_target.y - camera.y)
                # Прозрачная поверхность 80×80
                reticle = pygame.Surface((80, 80), pygame.SRCALPHA)
                # Неоновый квадрат, толщина 1px, полупрозрачный
                pygame.draw.rect(reticle, (*HUD_NEON[:3], 120), (0, 0, 80, 80), 1)
                # Неоновая точка в центре
                pygame.draw.circle(reticle, (*HUD_NEON[:3], 160), (40, 40), 2)
                screen.blit(reticle, (sx - 40, sy - 40))

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

            # --- ОСКОЛКИ ---
            for debris in debris_list:
                debris.draw(screen, camera)

            # --- КРИСТАЛЛЫ ---
            for crystal in crystals:
                if not crystal.marked_for_removal:
                    crystal.draw(screen, camera)

            # --- ДРОНЫ ---
            for drone in drones:
                drone.draw(screen, camera)

            # --- ОРБИТАЛЬНЫЙ СТРАЖ ---
            for warden in warden_list:
                warden.draw(screen, camera)

            # --- ПУЛИ ИСТРЕБИТЕЛЯ ---
            if not paused:
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
                if rd.target_ship and not getattr(rd.target_ship, 'is_disassembled', False):
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
                        storage_repair_switch_rect, transfer_button_rect = draw_storage_ui(
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
                        # --- КНОПКА "РАЗОБРАТЬ НА РЕСУРСЫ" ---
                        # --- КНОПКА "РАЗОБРАТЬ НА РЕСУРСЫ" ---
                        h_btn_w, h_btn_h = 200, 30
                        disassemble_button_rect = pygame.Rect(
                            h_base_x, last_btn_y + HUD_GAP, h_btn_w, h_btn_h
                        )
                        scan_button_rect = pygame.Rect(0, 0, 0, 0)

                        draw_hologram_button(screen, "РАЗОБРАТЬ НА РЕСУРСЫ",
                                             h_base_x, last_btn_y + HUD_GAP,
                                             h_btn_w, h_btn_h, h_time)

                        # --- КНОПКА "СЕСТЬ ЗА ШТУРВАЛ" ---
                        # Проверяем точные ключи: "Корпус" и "Двигатель"
                        hull_ok = ui_target_wreck.modules.get("Корпус", 0) >= 100
                        engines_ok = ui_target_wreck.modules.get("Двигатель", 0) >= 30

                        pilot_button_rect = pygame.Rect(0, 0, 0, 0)  # Сброс по умолчанию
                        pilot_y = 0

                        if hull_ok and engines_ok:
                            pilot_y = last_btn_y + HUD_GAP + h_btn_h + HUD_GAP
                            pilot_button_rect = pygame.Rect(h_base_x, pilot_y, h_btn_w, h_btn_h)
                            draw_hologram_button(screen, "СЕСТЬ ЗА ШТУРВАЛ",
                                                 h_base_x, pilot_y, h_btn_w, h_btn_h, h_time)

                        # --- КНОПКА "СКЛАД" ---
                        storage_switch_rect = pygame.Rect(0, 0, 0, 0)  # Сброс по умолчанию

                        if ui_target_wreck.is_habitable:
                            sw_y = last_btn_y + HUD_GAP + h_btn_h + HUD_GAP

                            # Если кнопка пилота есть, сдвигаем склад ниже неё
                            if pilot_button_rect.width > 0:
                                sw_y += h_btn_h + HUD_GAP

                            storage_switch_rect = pygame.Rect(h_base_x, sw_y, h_btn_w, h_btn_h)
                            draw_hologram_button(screen, "СКЛАД",
                                                 h_base_x, sw_y, h_btn_w, h_btn_h, h_time)

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
            # --- ИСПРАВЛЕНИЕ ОТРИСОВКИ ИГРОКА ---
            # Рисуем игрока ТОЛЬКО если он НЕ на борту
            if not (player.is_boarded and player.boarded_wreck):
                player.draw(screen, camera.topleft, interaction_target=interaction_target)

            # Если игрок на борту, мы НЕ рисуем player.
            # Но мы УЖЕ нарисовали StaticShip (wreck) в цикле all_objects выше.
            # Благодаря board_wreck(), у wreck теперь спрайт игрока (_base_sprite = player.idle_sprite).
            # Визуально это выглядит как пересадка.

            # --- КОНТЕКСТНОЕ МЕНЮ РЕМОНТА КОРАБЛЯ (по клавише E) ---
            if ship_repair_menu:
                # Затемнение и рамка
                menu_w, menu_h = 340, 240
                m_x = CAMERA_WIDTH // 2 - menu_w // 2
                m_y = CAMERA_HEIGHT // 2 - menu_h // 2

                m_bg = pygame.Surface((menu_w, menu_h), pygame.SRCALPHA)
                m_bg.fill((10, 18, 30, 235))
                pygame.draw.rect(m_bg, (*HUD_NEON[:3], 180), (0, 0, menu_w, menu_h), 2)
                screen.blit(m_bg, (m_x, m_y))

                m_title = font_ui.render("МЕНЮ РЕМОНТА НАДСТРОЙКИ", True, HUD_NEON[:3])
                screen.blit(m_title, (m_x + 20, m_y + 12))

                m_status = player.module_status()
                btn_x = m_x + 20
                btn_w = menu_w - 40
                btn_h = 34
                cur_y = m_y + 48
                font_btn = pygame.font.SysFont("consolas", 14, bold=True)

                for mod_id in ("fuel_leak", "radar", "hull"):
                    info = m_status[mod_id]
                    # Проверяем, не занят ли модуль активным дроном-ремонтником
                    mod_drone_active = any(
                        d.target_ship is player and d.module_name == mod_id
                        and d.state != "DONE" and d.state != "RETURNING"
                        for d in repair_drones
                    )
                    # Кнопка
                    if info["repaired"]:
                        color = (120, 200, 130)  # зелёный — починено
                        state_txt = "OK"
                    elif mod_drone_active:
                        color = (200, 200, 120)  # жёлтый — в процессе ремонта
                        state_txt = "ДРОН В ПУТИ..."
                    else:
                        needs = " / ".join(f"{res}:{amt}" for res, amt in info["cost"].items())
                        has = all(player.inventory.get(res, 0) >= amt for res, amt in info["cost"].items())
                        color = (120, 255, 120) if has else (200, 120, 120)
                        state_txt = needs
                        # Для корпуса дополнительно показываем текущее HP
                        if mod_id == "hull":
                            hp_pct = info.get("hp_pct", 0)
                            state_txt = f"Hull {hp_pct}%  {needs}"
                    draw_hologram_button(screen, info["name"], btn_x, cur_y, btn_w, btn_h, h_time)
                    # Стоимость/состояние
                    st = font_btn.render(state_txt, True, color)
                    screen.blit(st, (btn_x + btn_w + 8, cur_y + 8))
                    cur_y += btn_h + 6

                hint = font_btn.render("Клик по модулю — ремонт. Q — закрыть", True, (180, 190, 210))
                screen.blit(hint, (btn_x, cur_y + 4))

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

        # # Визуализация границ комнат (для отладки)
        # if not player.on_planet_surface:
        #     for key, sector in generator.sectors.items():
        #         sx, sy = key
        #         rect = pygame.Rect(sx * ROOM_WIDTH, sy * ROOM_HEIGHT, ROOM_WIDTH, ROOM_HEIGHT)
        #         draw_rect = rect.copy()
        #         draw_rect.x -= camera.x
        #         draw_rect.y -= camera.y
        #         if draw_rect.colliderect(screen.get_rect()):
        #             color = (0, 255, 0) if sector.is_generated else (255, 0, 0)
        #             pygame.draw.rect(screen, color, draw_rect, 2)

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
        # --- МИНИ-КАРТА ---
        h_time = pygame.time.get_ticks() / 1000.0
        # Поле зрения: объекты в пределах обзора камеры запоминаем как «виденные».
        # Стационарные тела (астероиды, планеты, станции, осколки) — навсегда,
        # движущиеся (корабли, амёбы, летающие осколки) — только на время.
        cam_left = camera.x
        cam_top = camera.y
        cam_right = camera.x + CAMERA_WIDTH
        cam_bottom = camera.y + CAMERA_HEIGHT
        now_ms = pygame.time.get_ticks()
        if not player.on_planet_surface and current_sector is not None and not paused:
            reveal_objs = []
            if current_sector.asteroids:
                reveal_objs.extend(current_sector.asteroids)
            if current_sector.objects:
                reveal_objs.extend(current_sector.objects)
            reveal_objs.extend(debris_list)
            for o in reveal_objs:
                if not hasattr(o, 'x') or not hasattr(o, 'y'):
                    continue
                if cam_left - 50 <= o.x <= cam_right + 50 and cam_top - 50 <= o.y <= cam_bottom + 50:
                    if isinstance(o, (Asteroid, StaticPlanet, Station, StaticShip)):
                        permanent_reveal.add(id(o))
                    else:
                        view_reveal_times[id(o)] = now_ms

        draw_minimap(screen, player, current_sector, debris_list, camera, h_time)

        # --- ЭКРАН GAME OVER ---
        if game_over_state > 0:
            # Затемнение всего экрана
            if screen_dim_alpha > 0:
                dim_surf = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, screen_dim_alpha))
                screen.blit(dim_surf, (0, 0))

            # Текст и рамка — только когда экран полностью затемнён
            if game_over_state == 2:
                pulse = (math.sin(h_time * 2) + 1) / 2
                text_alpha = int(180 + pulse * 75)

                font_go = pygame.font.SysFont("consolas", 52, bold=True)
                sub_font = pygame.font.SysFont("consolas", 18, bold=True)

                # Рендерим тексты, чтобы измерить размер
                text_surf = font_go.render("ИГРА ОКОНЧЕНА!", True, HUD_NEON[:3])
                sub_surf = sub_font.render("[ нажмите ESC для выхода ]", True, HUD_TEXT[:3])

                text_w = text_surf.get_width()
                text_h = text_surf.get_height()
                sub_h = sub_surf.get_height()

                # Рамка вокруг текста + подсказки
                frame_padding = 30
                frame_w = max(text_w, sub_surf.get_width()) + frame_padding * 2
                frame_h = text_h + sub_h + frame_padding * 2 + 20
                frame_x = (CAMERA_WIDTH - frame_w) // 2
                frame_y = (CAMERA_HEIGHT - frame_h) // 2

                # Полупрозрачный фон рамки
                frame_surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                frame_surf.fill((*HUD_NEON[:3], 40))

                # Помехи — только внутри рамки
                for i in range(0, frame_h, 4):
                    shift = math.sin(h_time * 3 + i * 0.3) * 2
                    line_y = i + int(shift)
                    if 0 <= line_y < frame_h:
                        pygame.draw.line(frame_surf, (*HUD_GLOW, 18),
                                         (0, line_y), (frame_w, line_y))

                # Неоновая рамка
                pygame.draw.rect(frame_surf, (*HUD_NEON[:3], 180),
                                 (0, 0, frame_w, frame_h), HUD_BORDER_WIDTH)

                screen.blit(frame_surf, (frame_x, frame_y))

                # Многослойное свечение текста
                for layer in range(5, 0, -1):
                    glow_surf = font_go.render("ИГРА ОКОНЧЕНА!", True, HUD_GLOW[:3])
                    glow_surf.set_alpha(15 + layer * 8)
                    glow_rect = glow_surf.get_rect(
                        center=(CAMERA_WIDTH // 2, frame_y + frame_padding + text_h // 2))
                    screen.blit(glow_surf, glow_rect)

                # Чёткий текст
                text_surf.set_alpha(text_alpha)
                text_rect = text_surf.get_rect(
                    center=(CAMERA_WIDTH // 2, frame_y + frame_padding + text_h // 2))
                screen.blit(text_surf, text_rect)

                # Подсказка
                sub_pulse = (math.sin(h_time * 1.5) + 1) / 2
                sub_alpha = int(80 + sub_pulse * 60)
                sub_surf.set_alpha(sub_alpha)
                sub_rect = sub_surf.get_rect(
                    center=(CAMERA_WIDTH // 2, frame_y + frame_padding + text_h + 20 + sub_h // 2))
                screen.blit(sub_surf, sub_rect)

        # --- МЕНЮ ПАУЗЫ ---
        if paused:
            dim = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 140))
            screen.blit(dim, (0, 0))

            h_time = pygame.time.get_ticks() / 1000.0

            font_pause = pygame.font.SysFont("consolas", 36, bold=True)
            title_surf = font_pause.render("ПАУЗА", True, HUD_NEON[:3])
            title_rect = title_surf.get_rect(center=(CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2 - 80))
            screen.blit(title_surf, title_rect)

            btn_w, btn_h = 260, 40
            btn_x = CAMERA_WIDTH // 2 - btn_w // 2

            # Кнопка "ВЫЙТИ ИЗ ИГРЫ" — активная
            btn_y_quit = CAMERA_HEIGHT // 2 - 20
            pause_quit_rect = pygame.Rect(btn_x, btn_y_quit, btn_w, btn_h)
            draw_hologram_button(screen, "ВЫЙТИ ИЗ ИГРЫ", btn_x, btn_y_quit, btn_w, btn_h, h_time)

            # Кнопка "СОХРАНИТЬ" — неактивная (серая)
            btn_y_save = CAMERA_HEIGHT // 2 + 30
            pause_save_rect = pygame.Rect(btn_x, btn_y_save, btn_w, btn_h)

            save_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            save_surf.fill((*HUD_NEON[:3], 30))
            pygame.draw.rect(save_surf, (80, 80, 80), (0, 0, btn_w, btn_h), HUD_BORDER_WIDTH)
            font_btn = pygame.font.SysFont("consolas", 16, bold=True)
            save_text = font_btn.render("СОХРАНИТЬ", True, (100, 100, 100))
            save_text_rect = save_text.get_rect(center=(btn_w // 2, btn_h // 2))
            save_surf.blit(save_text, save_text_rect)
            screen.blit(save_surf, (btn_x, btn_y_save))

        # --- СЮЖЕТНОЕ ИНТРО (заставка при старте) ---
        if show_intro:
            intro_ov = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT), pygame.SRCALPHA)
            intro_ov.fill((0, 0, 10, 235))
            screen.blit(intro_ov, (0, 0))

            it_font = pygame.font.SysFont("consolas", 15, bold=True)
            overlay_h = 30 + (len(GAME_INTRO_TEXT) * 22)
            box_x = 120
            box_y = (CAMERA_HEIGHT - overlay_h) // 2
            box_w = CAMERA_WIDTH - 240

            intro_box = pygame.Surface((box_w, overlay_h), pygame.SRCALPHA)
            intro_box.fill((10, 18, 34, 220))
            pygame.draw.rect(intro_box, (*HUD_NEON[:3], 160), (0, 0, box_w, overlay_h), 2)
            screen.blit(intro_box, (box_x, box_y))

            for i, line in enumerate(GAME_INTRO_TEXT):
                color = (255, 230, 180) if i == len(GAME_INTRO_TEXT) - 1 else (220, 225, 235)
                if i == 0:
                    ls = it_font.render(line, True, (255, 220, 100))
                else:
                    ls = it_font.render(line, True, color)
                screen.blit(ls, (box_x + 30, box_y + 24 + i * 22))

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

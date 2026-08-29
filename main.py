# main.py
import pygame
import sys
import os
import math
from config import ROOM_WIDTH, ROOM_HEIGHT, CAMERA_WIDTH, CAMERA_HEIGHT
from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT
from game_objects.static_ship import StaticShip
from sprites import get_backgrounds, get_ship_sprites, get_asteroid_sprites
from game_objects.player import PlayerShip
from world.generator import WorldGenerator
from game_objects.static_planet import StaticPlanet
from config import RESOURCE_ICONS
from game_objects.bullet import Bullet


def draw_hud(screen, player, font, resource_surfaces, start_x, y_offset=20):
    """
    Рисует HUD строго слева направо.
    Размер иконок: 15x15.
    Отступ между иконками: 60px (запас для цифр).
    """
    x = start_x
    y = y_offset

    # Жесткий порядок ресурсов
    resource_order = ["metal", "precious", "crystal", "energy", "mineral", "uranium"]

    for name in resource_order:
        count = player.inventory.get(name, 0)

        if name not in resource_surfaces:
            continue

        icon = resource_surfaces[name]

        # 1. Гарантированно приводим иконку к 15x15
        if icon.get_width() != 15 or icon.get_height() != 15:
            icon = pygame.transform.smoothscale(icon, (15, 15))

        # 2. Рисуем иконку
        screen.blit(icon, (x, y))

        # 3. Рисуем текст (количество)
        text_x = x + icon.get_width() + 4
        text_y = y

        text_surf = font.render(str(count), True, (255, 255, 255))
        screen.blit(text_surf, (text_x, text_y))

        # 4. Сдвигаем X для следующей иконки
        x += 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((CAMERA_WIDTH, CAMERA_HEIGHT))
    pygame.display.set_caption('Stellar Horizons - Asteroid Belt')
    clock = pygame.time.Clock()

    # 1. Загрузка ассетов
    backgrounds = get_backgrounds()
    idle_sprite, movement_sprites = get_ship_sprites(4)
    asteroid_sprites = get_asteroid_sprites()

    # --- ЗАГРУЗКА СПРАЙТА КОРАБЛЯ-ОБЛОМКА ---
    wreck_path = "assets/ships/class_3/ship_destroyer_destroyer-01_128px_idle.png"
    wreck_sprite = None
    try:
        wreck_sprite = pygame.image.load(wreck_path).convert_alpha()
        print(f"[SUCCESS] Спрайт корабля загружен: {wreck_path}")
    except FileNotFoundError:
        print(f"[ERROR] Не удалось найти спрайт корабля по пути: {wreck_path}")
        print("Корабль не появится в комнате (1, 0). Проверьте путь к файлу.")

    # --- ЗАГРУЗКА СПРАЙТА ПЛАНЕТЫ ---
    planet_path = "assets/planets/habitable/planet_lariona_512px.png"
    planet_sprite = None
    try:
        planet_sprite = pygame.image.load(planet_path).convert_alpha()
        print(f"[SUCCESS] Спрайт планеты загружен: {planet_path}")
    except FileNotFoundError:
        print(f"[ERROR] Не удалось найти спрайт планеты: {planet_path}")
        print("Планета не появится в комнате. Проверьте путь к файлу.")

    # --- ЗАГРУЗКА СПРАЙТА ВЫСТРЕЛА ---
    bullet_path = "assets/projectiles/shot_16px_mod1.png"
    bullet_sprite = None
    try:
        bullet_sprite = pygame.image.load(bullet_path).convert_alpha()
        print(f"[SUCCESS] Спрайт выстрела загружен: {bullet_path}")
    except FileNotFoundError:
        print(f"[WARNING] Не удалось найти выстрел: {bullet_path}. Используется заглушка.")
        bullet_sprite = pygame.Surface((16, 16))
        bullet_sprite.fill((255, 0, 0))  # Красная точка вместо спрайта
    # ----------------------------------------

    # --- ЗАГРУЗКА ИКОНОК РЕСУРСОВ ---
    resource_surfaces = {}
    for name, path in RESOURCE_ICONS.items():
        try:
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                surf = pygame.transform.smoothscale(surf, (24, 24))
                resource_surfaces[name] = surf
                print(f"[SUCCESS] Иконка загружена: {name} -> {path}")
            else:
                raise FileNotFoundError
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить иконку {name}: {e}")
            placeholder = pygame.Surface((24, 24))
            placeholder.fill((150, 150, 150))
            resource_surfaces[name] = placeholder
    # ----------------------------------------

    font_hud = pygame.font.SysFont('Arial', 15, bold=False)

    # 2. Создание объектов
    player = PlayerShip(
        x=ROOM_WIDTH // 2,
        y=ROOM_HEIGHT // 2,
        idle_sprite=idle_sprite,
        movement_sprites=movement_sprites
    )

    # ВАЖНО: Если в классе PlayerShip нет self.inventory в __init__,
    if not hasattr(player, 'inventory'):
        player.inventory = {
            "metal": 0,
            "precious": 0,
            "crystal": 0,
            "energy": 0,
            "mineral": 0,
            "uranium": 0
        }

    generator = WorldGenerator()
    camera = pygame.Rect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
    running = True

    trigger_distance_x = ROOM_WIDTH - 50
    trigger_distance_y = ROOM_HEIGHT - 50

    last_space_pos = (player.x, player.y)

    while running:
        # --- Обработка событий ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Управление ---
        keys = pygame.key.get_pressed()

        # Вход на планету (E)
        if keys[pygame.K_e] and not player.is_landing and not player.on_planet_surface:
            room_x = int(player.x // ROOM_WIDTH)
            room_y = int(player.y // ROOM_HEIGHT)

            sector = generator.get_sector(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite,
                                          planet_sprite=planet_sprite)

            near_planet = None
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
                print("[ACTION] Начало посадки на планету")

        # Выход с планеты (Q)
        if keys[pygame.K_q] and player.on_planet_surface:
            player.exit_planet(*last_space_pos)
            print("[ACTION] Выход в космос")

        # Вращение и ускорение — ТОЛЬКО в космосе
        if not player.on_planet_surface and not player.is_landing:
            if keys[pygame.K_a]:
                player.rotate(-1)
            if keys[pygame.K_d]:
                player.rotate(1)
            if keys[pygame.K_w]:
                player.accelerate()

        # СТРЕЛЬБА (Пробел)
        # Вызываем метод shoot у игрока, передавая спрайт пули
        if keys[pygame.K_SPACE]:
            player.shoot(bullet_sprite)

        # --- Логика игры ---
        player.update()

        # Движение камеры
        if player.on_planet_surface:
            target_x = max(0, min(player.x - CAMERA_WIDTH // 2, PLANET_ROOM_WIDTH - CAMERA_WIDTH))
            target_y = max(0, min(player.y - CAMERA_HEIGHT // 2, PLANET_ROOM_HEIGHT - CAMERA_HEIGHT))
            camera.topleft = (target_x, target_y)
        else:
            target_x = player.x - CAMERA_WIDTH // 2
            target_y = player.y - CAMERA_HEIGHT // 2
            camera.topleft = (target_x, target_y)

        # Определение текущей комнаты (только для космоса)
        room_x = 0
        room_y = 0
        local_x = 0
        local_y = 0

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
                                            planet_sprite=planet_sprite)

        current_sector = None
        if not player.on_planet_surface:
            current_sector = generator.get_sector(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite,
                                                  planet_sprite=planet_sprite)

        # --- ЛОГИКА ДОБЫЧИ РЕСУРСОВ (Столкновение с астероидами) ---
        if current_sector and current_sector.asteroids:
            for asteroid in current_sector.asteroids[:]:
                if hasattr(asteroid, 'rect'):
                    player_rect = player.rect.copy()
                    player_rect.center = (player.x, player.y)

                    if player_rect.colliderect(asteroid.rect):
                        player.inventory["metal"] += 1
                        print(f"Добыт металл! Всего: {player.inventory['metal']}")
                        current_sector.asteroids.remove(asteroid)
                        break
        # ------------------------------------------------------------

        # --- Отрисовка ---
        if player.on_planet_surface:
            screen.fill((135, 206, 235))  # Sky Blue
            player.draw(screen, camera.topleft)
        else:
            screen.fill((0, 0, 20))  # Чёрный космос

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
                    obj.update()

                show_highlight = False
                if (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'highlight_radius')):
                    dist_sq = (obj.x - player.x) ** 2 + (obj.y - player.y) ** 2
                    radius_sq = obj.highlight_radius ** 2
                    if dist_sq <= radius_sq:
                        show_highlight = True

                if hasattr(obj, 'draw'):
                    if isinstance(obj, (StaticShip, StaticPlanet)):
                        obj.draw(screen, camera, show_highlight=show_highlight)
                    else:
                        obj.draw(screen, camera)

 
            # --- ОТРИСОВКА И ОБНОВЛЕНИЕ ПУЛЬ ---
            for bullet in player.bullets[:]:
                bullet.update()
                bullet.draw(screen, camera)  # <-- теперь пуля сама знает про поворот и камеру
                if not bullet.is_active():
                    player.bullets.remove(bullet)
            # ------------------------------------

            player.draw(screen, camera.topleft)

        # --- ОТЛАДКА: Вывод информации на экран ---
        font_debug = pygame.font.SysFont('Arial', 16)

        if not player.on_planet_surface:
            rx = int(player.x // ROOM_WIDTH)
            ry = int(player.y // ROOM_HEIGHT)
            room_text = f"Room: {rx}, {ry}"
        else:
            room_text = "Room: Planet"

        count = 0
        if current_sector and current_sector.asteroids:
            count = sum(1 for a in current_sector.asteroids if not isinstance(a, list))

        mode_text = "PLANET" if player.on_planet_surface else "SPACE"
        info_text = (
            f"{room_text} | "
            f"Mode: {mode_text} | "
            f"Pos: {int(player.x)}, {int(player.y)} | "
            f"Angle: {int(player.angle)} | "
            f"Asteroids: {count} | Bullets: {len(player.bullets)}"
        )
        text_surf = font_debug.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        # --- ВИЗУАЛИЗАЦИЯ ГРАНИЦ КОМНАТ ---
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

        # --- ОТРИСОВКА HUD (РЕСУРСЫ) ---
        hud_start_x = 10
        draw_hud(
            screen=screen,
            player=player,
            font=font_hud,
            resource_surfaces=resource_surfaces,
            start_x=hud_start_x,
            y_offset=30
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

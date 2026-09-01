# main.py
import pygame
import sys
import os
import math
import random

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

    bullet_path = "assets/projectiles/shot_16px_mod1.png"
    bullet_sprite = None
    try:
        bullet_sprite = pygame.image.load(bullet_path).convert_alpha()
        print(f"[SUCCESS] Спрайт выстрела загружен: {bullet_path}")
    except FileNotFoundError:
        print("[WARNING] Не удалось найти выстрел. Используется заглушка.")
        bullet_sprite = pygame.Surface((16, 16))
        bullet_sprite.fill((255, 0, 0))

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

    player = PlayerShip(
        x=ROOM_WIDTH // 2,
        y=ROOM_HEIGHT // 2,
        idle_sprite=idle_sprite,
        movement_sprites=movement_sprites
    )

    generator = WorldGenerator()
    camera = pygame.Rect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
    running = True

    trigger_distance_x = ROOM_WIDTH - 50
    trigger_distance_y = ROOM_HEIGHT - 50
    last_space_pos = (player.x, player.y)
    player_mass = 64.0  # Масса корабля для расчёта импульса

    # Константа дистанции подсветки (как ты просил)
    INTERACTION_MAX_DIST = 250
    INTERACTION_MAX_DIST_SQ = INTERACTION_MAX_DIST ** 2

    while running:
        # 1. Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # --- ЛОГИКА КНОПКИ ДЕЙСТВИЯ (E) ---
        interaction_target = None

        if (not player.on_planet_surface and not player.is_landing and keys[pygame.K_e]):

            room_x = int(player.x // ROOM_WIDTH)
            room_y = int(player.y // ROOM_HEIGHT)
            sector = generator.get_sector(room_x, room_y, asteroid_sprites,
                                          wreck_sprite=wreck_sprite, planet_sprite=planet_sprite)

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
                # 2. Добыча астероида
                closest_asteroid = None
                closest_dist_sq = float('inf')

                if sector and sector.asteroids:
                    for ast in sector.asteroids:
                        # Быстрая проверка дистанции (150px)
                        dx = ast.x - player.x
                        dy = ast.y - player.y
                        d_sq = dx * dx + dy * dy

                        # Условие: дистанция <= 150^2 И тип mod04 И размер 16px
                        if d_sq <= (150 ** 2):
                            if ast.type_key.startswith("ast_mod04") and ast.size_px == 16:
                                if d_sq < closest_dist_sq:
                                    closest_dist_sq = d_sq
                                    closest_asteroid = ast

                if closest_asteroid:
                    started = player.try_start_collection(closest_asteroid)
                    if started:
                        print(f"[ACTION] Добыча начата с {closest_asteroid.type_key}")
                    interaction_target = closest_asteroid

        # --- КНОПКА ОТКАТА (Q) ---
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
        if keys[pygame.K_SPACE]:
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
                                            planet_sprite=planet_sprite)

            current_sector = generator.get_sector(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite,
                                                  planet_sprite=planet_sprite)

            if current_sector and current_sector.asteroids:
                check_objects = current_sector.asteroids

        # ВАЖНО: Вызываем update игрока, передавая список объектов.
        hit_asteroid = player.update(world_objects=check_objects)

        if hit_asteroid:
            is_mod04 = hit_asteroid.type_key.startswith("ast_mod04")

            if is_mod04:
                momentum_x = player.last_vx * player_mass
                momentum_y = player.last_vy * player_mass
                bounce_factor = 0.1

                if abs(momentum_x) < 0.01 and abs(momentum_y) < 0.01:
                    hit_asteroid.apply_knockback(random.uniform(-0.5, 0.5) * bounce_factor,
                                                 random.uniform(-0.5, 0.5) * bounce_factor)
                else:
                    push_x = momentum_x / hit_asteroid.mass
                    push_y = momentum_y / hit_asteroid.mass
                    hit_asteroid.apply_knockback(push_x, push_y)

                recoil_factor = 0.2
                player.velocity.x -= push_x * (hit_asteroid.mass / player_mass) * recoil_factor
                player.velocity.y -= push_y * (hit_asteroid.mass / player_mass) * recoil_factor
            else:
                player.inventory["metal"] += 1
                if current_sector and hit_asteroid in current_sector.asteroids:
                    current_sector.asteroids.remove(hit_asteroid)

        # ОЧИСТКА УДАЛЕННЫХ АСТЕРОИДОВ (должно быть ДО отрисовки!)
        if current_sector and current_sector.asteroids:
            current_sector.asteroids = [
                ast for ast in current_sector.asteroids if not ast.marked_for_removal
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
            screen.fill((135, 206, 235))  # Sky Blue
            # На планете линию не рисуем (или рисуем только если нужно)
            player.draw(screen, camera.topleft, interaction_target=None)
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
                        # --- СЕРАЯ ОКРУЖНОСТЬ ВОКРУГ MOD04 АСТЕРОИДОВ В РАДИУСЕ 150px ---
            if current_sector and current_sector.asteroids:
                for ast in current_sector.asteroids:
                    if ast.type_key.startswith("ast_mod04") and ast.size_px == 16:
                        dist_sq = (ast.x - player.x) ** 2 + (ast.y - player.y) ** 2
                        if dist_sq <= 150 ** 2:
                            sx = int(ast.x - camera.x)
                            sy = int(ast.y - camera.y)
                            pygame.draw.circle(screen, (128, 128, 128), (sx, sy), 32, 1)
            for bullet in player.bullets:
                bullet.draw(screen, camera)

            # ОТРИСОВКА ИГРОКА С ЛИНИЕЙ
            # Передаем interaction_target, чтобы draw() мог нарисовать линию
            player.draw(screen, camera.topleft, interaction_target=interaction_target)

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

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


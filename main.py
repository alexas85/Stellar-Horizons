# main.py
import pygame
import sys
from config import ROOM_WIDTH, ROOM_HEIGHT, CAMERA_WIDTH, CAMERA_HEIGHT
from config import PLANET_ROOM_WIDTH, PLANET_ROOM_HEIGHT  # Новые константы
from game_objects.static_ship import StaticShip
from sprites import get_backgrounds, get_ship_sprites, get_asteroid_sprites
from game_objects.player import PlayerShip
from world.generator import WorldGenerator
from game_objects.static_planet import StaticPlanet


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
    # ----------------------------------------

    # 2. Создание объектов
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

    # Переменная для хранения позиции в космосе перед входом на планету
    last_space_pos = (player.x, player.y)

    while running:
        # --- Обработка событий ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Управление ---
        keys = pygame.key.get_pressed()

        # Вход на планету (E) — только если не в процессе посадки и не на планете
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
        if keys[pygame.K_q] and player.on_planet_surface and not player.is_landing:
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

        # --- Логика игры ---
        player.update()

        # Движение камеры
        if player.on_planet_surface:
            # Камера на планете: центрируем на игроке, но не выходим за границы комнаты
            target_x = max(0, min(player.x - CAMERA_WIDTH // 2, PLANET_ROOM_WIDTH - CAMERA_WIDTH))
            target_y = max(0, min(player.y - CAMERA_HEIGHT // 2, PLANET_ROOM_HEIGHT - CAMERA_HEIGHT))
            camera.topleft = (target_x, target_y)
        else:
            # Камера в космосе: обычная слежка за игроком
            target_x = player.x - CAMERA_WIDTH // 2
            target_y = player.y - CAMERA_HEIGHT // 2
            camera.topleft = (target_x, target_y)

        # Определение текущей комнаты (только для космоса)
        room_x = 0
        room_y = 0
        if not player.on_planet_surface:
            room_x = int(player.x // ROOM_WIDTH)
            room_y = int(player.y // ROOM_HEIGHT)

            local_x = player.x % ROOM_WIDTH
            local_y = player.y % ROOM_HEIGHT

            # Упреждающая загрузка соседей
            should_preload = False
            if (local_x < trigger_distance_x or local_x > ROOM_WIDTH - trigger_distance_x or
                    local_y < trigger_distance_y or local_y > ROOM_HEIGHT - trigger_distance_y):
                should_preload = True

            if should_preload:
                generator.preload_neighbors(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite, planet_sprite=planet_sprite)

        current_sector = None
        if not player.on_planet_surface:
            current_sector = generator.get_sector(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite, planet_sprite=planet_sprite)

        # --- Отрисовка ---
        if player.on_planet_surface:
            # === КОМНАТА ПЛАНЕТЫ (ГОЛУБОЙ ФОН) ===
            screen.fill((135, 206, 235))  # Sky Blue — «небо» планеты

            # Игрок рисуется как обычно (координаты уже в системе комнаты планеты)
            player.draw(screen, camera.topleft)

        else:
            # === КОСМОС ===
            screen.fill((0, 0, 20))  # чёрный космос

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

            # Отрисовка астероидов, обломков, планет
            all_objects = []
            if current_sector:
                if hasattr(current_sector, 'asteroids') and current_sector.asteroids:
                    all_objects.extend(current_sector.asteroids)
                if hasattr(current_sector, 'objects') and current_sector.objects:
                    all_objects.extend(current_sector.objects)

            for obj in all_objects:
                if isinstance(obj, list):
                    continue

                # Обновляем объект
                if hasattr(obj, 'update'):
                    obj.update()

                show_highlight = False
                # ПРОВЕРКА ДИСТАНЦИИ
                if (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'highlight_radius')):
                    dist_sq = (obj.x - player.x) ** 2 + (obj.y - player.y) ** 2
                    radius_sq = obj.highlight_radius ** 2
                    if dist_sq <= radius_sq:
                        show_highlight = True

                # ОТРИСОВКА
                if hasattr(obj, 'draw'):
                    if isinstance(obj, (StaticShip, StaticPlanet)):
                        obj.draw(screen, camera, show_highlight=show_highlight)
                    else:
                        obj.draw(screen, camera)

            # Игрок
            player.draw(screen, camera.topleft)

        # Отладочная информация
        font = pygame.font.SysFont('Arial', 16)
        count = 0
        if current_sector and current_sector.asteroids:
            count = sum(1 for a in current_sector.asteroids if not isinstance(a, list))

        mode_text = "PLANET" if player.on_planet_surface else "SPACE"
        info_text = (
            f"Mode: {mode_text} | "
            f"Pos: {int(player.x)}, {int(player.y)} | "
            f"Angle: {int(player.angle)} | "
            f"Asteroids: {count}"
        )
        text_surf = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        # --- ОТЛАДКА: Визуализация границ комнат (только в космосе) ---
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

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

# main.py
import pygame
import sys
from config import ROOM_WIDTH, ROOM_HEIGHT, CAMERA_WIDTH, CAMERA_HEIGHT
from sprites import get_backgrounds, get_ship_sprites, get_asteroid_sprites
from game_objects.player import PlayerShip
from world.generator import WorldGenerator


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
    try:
        wreck_sprite = pygame.image.load(wreck_path).convert_alpha()
        print(f"[SUCCESS] Спрайт корабля загружен: {wreck_path}")
    except FileNotFoundError:
        print(f"[ERROR] Не удалось найти спрайт корабля по пути: {wreck_path}")
        print("Корабль не появится в комнате (1, 0). Проверьте путь к файлу.")
        wreck_sprite = None
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

    while running:
        # --- Обработка событий ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Управление ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            player.rotate(-1)
        if keys[pygame.K_d]:
            player.rotate(1)
        if keys[pygame.K_w]:
            player.accelerate()

        # --- Логика игры ---
        player.update()

        # Движение камеры за игроком
        target_x = player.x - CAMERA_WIDTH // 2
        target_y = player.y - CAMERA_HEIGHT // 2
        camera.topleft = (target_x, target_y)

        # Определение текущей комнаты
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
            # Передаем wreck_sprite в генератор, чтобы он мог создать корабль при генерации соседей
            generator.preload_neighbors(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite)

        # Получаем текущий сектор
        # Также передаем wreck_sprite сюда, на случай если текущая комната еще не сгенерирована
        current_sector = generator.get_sector(room_x, room_y, asteroid_sprites, wreck_sprite=wreck_sprite)

        # --- Отрисовка ---
        screen.fill((0, 0, 20))

        # Фон (звёзды)
        if backgrounds and "stars" in backgrounds:
            stars = backgrounds["stars"]
            w, h = stars.get_size()
            speed = 0.4
            offset_x = -int(camera.x * speed)
            offset_y = -int(camera.y * speed)

            for x in range(-1, 2):
                for y in range(-1, 2):
                    screen.blit(stars, (offset_x + x * w, offset_y + y * h))

        # --- ОТРИСОВКА ВСЕХ ОБЪЕКТОВ (Астероиды + Другие объекты) ---
        all_objects = []

        if current_sector:
            # Добавляем астероиды
            if hasattr(current_sector, 'asteroids') and current_sector.asteroids:
                all_objects.extend(current_sector.asteroids)

            # Добавляем другие объекты (корабли, станции)
            if hasattr(current_sector, 'objects') and current_sector.objects:
                all_objects.extend(current_sector.objects)

        for obj in all_objects:
            if isinstance(obj, list):
                continue

            if hasattr(obj, 'update'):
                obj.update()

            if hasattr(obj, 'draw'):
                obj.draw(screen, camera)
        # -------------------------------------------------------------

        # Игрок
        player.draw(screen, camera.topleft)

        # Отладочная информация
        font = pygame.font.SysFont('Arial', 16)
        count = 0
        if current_sector and current_sector.asteroids:
            count = sum(1 for a in current_sector.asteroids if not isinstance(a, list))

        info_text = (
            f"Pos: {int(player.x)}, {int(player.y)} | "
            f"Angle: {int(player.angle)} | "
            f"Room: {room_x}, {room_y} | "
            f"Asteroids: {count}"
        )
        text_surf = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        # --- ОТЛАДКА: Визуализация границ комнат ---
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

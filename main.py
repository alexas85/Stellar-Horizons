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

    # Настройки упреждающей загрузки
    # Критически важно: триггер должен быть БОЛЬШЕ половины комнаты.
    # Мы ставим его почти на всю ширину комнаты, чтобы сосед генерировался заранее.
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

        # Позиция игрока внутри комнаты (от 0 до ROOM_WIDTH)
        local_x = player.x % ROOM_WIDTH
        local_y = player.y % ROOM_HEIGHT

        # Упреждающая загрузка соседей
        # Если игрок близко к краю комнаты (любой из 4 сторон) -> грузим соседей
        should_preload = False
        if (local_x < trigger_distance_x or local_x > ROOM_WIDTH - trigger_distance_x or
                local_y < trigger_distance_y or local_y > ROOM_HEIGHT - trigger_distance_y):
            should_preload = True

        if should_preload:
            generator.preload_neighbors(room_x, room_y, asteroid_sprites)

        # Получаем текущий сектор
        current_sector = generator.get_sector(room_x, room_y, asteroid_sprites)

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

        # Астероиды
        if current_sector and current_sector.asteroids:
            # Защита от битых данных (список списков)
            if isinstance(current_sector.asteroids, list):
                for asteroid in current_sector.asteroids:
                    if isinstance(asteroid, list):
                        continue
                    if hasattr(asteroid, 'update') and hasattr(asteroid, 'draw'):
                        asteroid.update()
                        asteroid.draw(screen, camera)
            else:
                print("ОШИБКА: current_sector.asteroids не является списком!")

        # Игрок
        player.draw(screen, camera.topleft)

        # Отладочная информация (позиция, комната, кол-во астероидов)
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
        # Отладка: рисуем границы комнат (опционально)
        for key, sector in generator.sectors.items():
            sx, sy = key
            rect = pygame.Rect(sx * ROOM_WIDTH, sy * ROOM_HEIGHT, ROOM_WIDTH, ROOM_HEIGHT)
            # Сдвигаем под камеру
            draw_rect = rect.copy()
            draw_rect.x -= camera.x
            draw_rect.y -= camera.y
            if draw_rect.colliderect(screen.get_rect()):
                color = (0, 255, 0) if sector.is_generated else (255, 0, 0)
                pygame.draw.rect(screen, color, draw_rect, 2)

        # -----------------------------------

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

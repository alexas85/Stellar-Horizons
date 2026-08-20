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

    # Получаем словарь спрайтов астероидов (ключ: имя файла/типа, значение: Surface)
    asteroid_sprites = get_asteroid_sprites()

    # 2. Создание объектов
    player = PlayerShip(
        x=ROOM_WIDTH // 2,
        y=ROOM_HEIGHT // 2,
        idle_sprite=idle_sprite,
        movement_sprites=movement_sprites
    )

    # Инициализируем генератор мира
    generator = WorldGenerator()

    # Камера (хранит позицию в мире)
    camera = pygame.Rect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
    running = True

    while running:
        # --- Обработка событий ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Управление ---
        keys = pygame.key.get_pressed()

        # Поворот (A - против часовой, D - по часовой)
        if keys[pygame.K_a]:
            player.rotate(-1)
        if keys[pygame.K_d]:
            player.rotate(1)

        # Ускорение (W)
        if keys[pygame.K_w]:
            player.accelerate()

        # --- Логика игры ---
        player.update()

        # Движение камеры за игроком
        target_x = player.x - CAMERA_WIDTH // 2
        target_y = player.y - CAMERA_HEIGHT // 2
        camera.topleft = (target_x, target_y)

        # Ограничение камеры границами мира (чтобы не уходила в бесконечность)
        world_rect = pygame.Rect(0, 0, ROOM_WIDTH, ROOM_HEIGHT)
        # camera.clamp_ip(world_rect)

        # ОПРЕДЕЛЕНИЕ ТЕКУЩЕГО СЕКТОРА (КОМНАТЫ)
        # Делим мировые координаты игрока на размер комнаты, чтобы понять, в какой ячейке мы находимся
        room_x = int(player.x // ROOM_WIDTH)
        room_y = int(player.y // ROOM_HEIGHT)

        current_sector = generator.get_sector(room_x, room_y, asteroid_sprites)

        # --- Отрисовка ---
        screen.fill((0, 0, 20))  # Цвет космоса (темно-синий)

        # 1. Отрисовка фона (со слоями параллакса)
        if backgrounds:
            if isinstance(backgrounds, dict):
                for layer_name, image in backgrounds.items():
                    speed = 0.5 if layer_name == 'far' else 1.0
                    offset_x = -int(camera.x * speed)
                    offset_y = -int(camera.y * speed)

                    w, h = image.get_size()
                    # Рисуем сетку тайлов, чтобы закрыть весь экран при скролле
                    for x in range(-1, 2):
                        for y in range(-1, 2):
                            screen.blit(image, (offset_x + x * w, offset_y + y * h))

            elif isinstance(backgrounds, list):
                for image in backgrounds:
                    w, h = image.get_size()
                    for x in range(-1, 2):
                        for y in range(-1, 2):
                            screen.blit(image, (-camera.x + x * w, -camera.y + y * h))
            else:
                w, h = backgrounds.get_size()
                for x in range(-1, 2):
                    for y in range(-1, 2):
                        screen.blit(backgrounds, (-camera.x + x * w, -camera.y + y * h))

        # 2. ОБНОВЛЕНИЕ И ОТРИСОВКА АСТЕРОИДОВ ТЕКУЩЕГО СЕКТОРА
        # Если в секторе есть астероиды (обычное поле или пояс), обновляем их физику и рисуем
        if current_sector.asteroids:
            for asteroid in current_sector.asteroids:
                asteroid.update()  # Двигаем по орбите и крутим сам астероид
                asteroid.draw(screen, camera)

        # 3. Отрисовка игрока
        player.draw(screen, camera.topleft)

        # 4. Отладочная информация
        font = pygame.font.SysFont('Arial', 16)
        info_text = (
            f"Pos: {int(player.x)}, {int(player.y)} | "
            f"Angle: {int(player.angle)} | "
            f"Room: {room_x}, {room_y}"
        )
        text_surf = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

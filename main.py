import pygame
import sys
from config import ROOM_WIDTH, ROOM_HEIGHT, CAMERA_WIDTH, CAMERA_HEIGHT, SHIP_ACCELERATION
from sprites import get_backgrounds, get_ship_sprites, get_asteroid_sprites
from game_objects.player import PlayerShip


# Раскомментируй следующую строку, только если генератор мира реально нужен и работает
# from world.generator import WorldGenerator

def main():
    pygame.init()
    screen = pygame.display.set_mode((CAMERA_WIDTH, CAMERA_HEIGHT))
    pygame.display.set_caption('Stellar Horizons')
    clock = pygame.time.Clock()

    # 1. Загрузка ассетов
    backgrounds = get_backgrounds()

    # Получаем спрайты корабля класса 4
    # Ожидается: (idle_sprite, [anim1, anim2, anim3])
    idle_sprite, movement_sprites = get_ship_sprites(4)

    # asteroid_sprites = get_asteroid_sprites() # Раскомментируй, если нужны астероиды

    # 2. Создание объектов
    player = PlayerShip(
        x=ROOM_WIDTH // 2,
        y=ROOM_HEIGHT // 2,
        idle_sprite=idle_sprite,
        movement_sprites=movement_sprites
    )

    # generator = WorldGenerator() # Раскомментируй, если нужен генератор

    camera = pygame.Rect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
    running = True

    while running:
        # --- Обработка событий ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Управление ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]:
            player.rotate(-1)
        if keys[pygame.K_e]:
            player.rotate(1)
        if keys[pygame.K_w]:
            player.accelerate()

        # --- Логика ---
        player.update()

        # Движение камеры за игроком
        target_x = player.x - CAMERA_WIDTH // 2
        target_y = player.y - CAMERA_HEIGHT // 2
        camera.topleft = (target_x, target_y)

        # Ограничение камеры границами мира
        camera.clamp_ip(pygame.Rect(0, 0, ROOM_WIDTH, ROOM_HEIGHT))

        # --- Отрисовка ---
        screen.fill((0, 0, 20))  # Цвет космоса

        # --- ИСПРАВЛЕННАЯ ОТРИСОВКА ФОНА ---
        # Теперь код умеет работать и со списком, и со словарем (слоями)
        if backgrounds:
            if isinstance(backgrounds, dict):
                # Если это словарь слоев (например, {'far': img, 'near': img})
                for layer_name, image in backgrounds.items():
                    # Простая отрисовка слоя с учетом параллакса (опционально можно усложнить)
                    # Для начала просто рисуем слой, сдвинутый на -camera.x, -camera.y
                    # Можно добавить множитель скорости для параллакса, например: speed = 0.5 для дальних слоев
                    offset_x = -int(camera.x * 0.5) if layer_name == 'far' else -camera.x
                    offset_y = -int(camera.y * 0.5) if layer_name == 'far' else -camera.y

                    # Рисуем картинку несколько раз, чтобы закрыть весь экран при скролле
                    w, h = image.get_size()
                    for x in range(-1, 2):
                        for y in range(-1, 2):
                            screen.blit(image, (offset_x + x * w, offset_y + y * h))

            elif isinstance(backgrounds, list):
                # Если это список слоев
                for image in backgrounds:
                    w, h = image.get_size()
                    for x in range(-1, 2):
                        for y in range(-1, 2):
                            screen.blit(image, (-camera.x + x * w, -camera.y + y * h))

            else:
                # Если это просто одна картинка (Surface)
                w, h = backgrounds.get_size()
                for x in range(-1, 2):
                    for y in range(-1, 2):
                        screen.blit(backgrounds, (-camera.x + x * w, -camera.y + y * h))
        # ----------------------------------

        # Отрисовка игрока
        player.draw(screen, camera.topleft)

        # Отладочная информация
        font = pygame.font.SysFont('Arial', 16)
        info_text = f"Pos: {int(player.x)}, {int(player.y)} | Angle: {int(player.angle)}"
        text_surf = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

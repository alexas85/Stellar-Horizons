# asteroid.py
import math
import pygame
import random

# --- НАСТРОЙКА ОТЛАДКИ ---
DEBUG_HITBOX = False  # Отображение коллизий

# --- НАСТРОЙКИ ФИЗИКИ ---
MAX_ASTEROID_SPEED = 3.0  # Максимальная скорость астероида (подбирай под баланс)
ASTEROID_DECAY = 0.98    # Затухание скорости (трение)


class Asteroid:
    @staticmethod
    def calculate_mass_from_size(size_px):
        """
        Единая формула расчёта массы по размеру.
        Используй её везде (в sector.py, main.py и т.д.), чтобы баланс был стабильным.

        16px  -> ~2.0
        32px  -> ~8.0
        64px  -> ~32.0
        124px -> ~119.0 (почти неподвижный)
        """
        return (size_px ** 2) / 128.0

    def __init__(self, sprite, x, y, angle, rotation_speed, orbit_center, orbit_radius, orbit_speed,
                 size_px=64, type_key="", mass=None):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.angle = angle
        self.rotation_speed = rotation_speed
        self.orbit_center = orbit_center
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.size_px = size_px
        self.type_key = type_key

        # Масса: если не передали — считаем по размеру
        if mass is None:
            mass = self.calculate_mass_from_size(size_px)
        self.mass = mass

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        try:
            self.width = sprite.get_width()
            self.height = sprite.get_height()
        except AttributeError:
            self.width = size_px
            self.height = size_px

        self.hitbox_offset_x = -2
        self.hitbox_offset_y = -1

        # --- НОВЫЕ ПОЛЯ ДЛЯ МЕХАНИКИ СБОРА ---
        self.is_collecting = False          # идёт ли сейчас сбор этого астероида
        self.collection_start_time = 0.0   # время начала сбора (в мс)
        self.collected_resources = None    # словарь с ресурсами, которые будут начислены (или None)
        self.marked_for_removal = False     # флаг: объект нужно удалить из сектора
        # --- HP АСТЕРОИДА ---
        self.hp = {16: 10, 32: 40, 64: 70}.get(size_px, 10)

    def apply_knockback(self, push_x, push_y):
        """Добавляет импульс к астероиду (для отскока)."""
        self.velocity_x += push_x
        self.velocity_y += push_y
    def take_damage(self, amount):
        """Получение урона от пули."""
        self.hp -= amount

    def spawn_fragments(self, asteroid_sprites):
        """
        Создаёт фрагменты при разрушении астероида.
        Возвращает список новых объектов Asteroid.
        """
        fragments = []

        if self.size_px == 64:
            count_32 = random.randint(1, 2)
            count_16 = random.randint(2, 6)
            for _ in range(count_32):
                frag = self._create_fragment(32, asteroid_sprites)
                if frag:
                    fragments.append(frag)
            for _ in range(count_16):
                frag = self._create_fragment(16, asteroid_sprites)
                if frag:
                    fragments.append(frag)

        elif self.size_px == 32:
            count_16 = random.randint(4, 8)
            for _ in range(count_16):
                frag = self._create_fragment(16, asteroid_sprites)
                if frag:
                    fragments.append(frag)

        # 16px не spawning фрагментов — это конечный размер для лазера

        return fragments

    def _create_fragment(self, size_px, asteroid_sprites):
        """Создаёт один фрагмент заданного размера."""
        mod_prefix = self.type_key.split("_s")[0]  # "ast_mod04"
        key = f"{mod_prefix}_s{size_px}"

        sprite_data = asteroid_sprites.get(key)
        if not sprite_data:
            print(f"[WARN] Нет спрайта для фрагмента: {key}")
            return None

        sprite, _ = sprite_data

        # Случайное направление и скорость 2-5
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        mass = self.calculate_mass_from_size(size_px)

        frag = Asteroid(
            sprite=sprite,
            x=self.x,
            y=self.y,
            angle=random.uniform(0, 2 * math.pi),
            rotation_speed=random.uniform(-0.02, 0.02),
            orbit_center=None,
            orbit_radius=0,
            orbit_speed=0,
            size_px=size_px,
            type_key=key,
            mass=mass
        )
        frag.velocity_x = vx
        frag.velocity_y = vy
        return frag

    def update(self):
        # Если у астероида есть орбита — двигаем по орбите
        if self.orbit_center is not None:
            cx, cy = self.orbit_center
            angle_delta = self.orbit_speed
            self.angle += angle_delta
            self.x = cx + math.cos(self.angle) * self.orbit_radius
            self.y = cy + math.sin(self.angle) * self.orbit_radius
        else:
            # Если нет орбиты (например, после удара) — двигаем по инерции
            self.x += self.velocity_x
            self.y += self.velocity_y

            # Затухание скорости (трение/сопротивление среды)
            self.velocity_x *= ASTEROID_DECAY
            self.velocity_y *= ASTEROID_DECAY

            # Ограничение максимальной скорости (чтобы астероид не улетал за экран)
            speed = math.hypot(self.velocity_x, self.velocity_y)
            if speed > MAX_ASTEROID_SPEED:
                ratio = MAX_ASTEROID_SPEED / speed
                self.velocity_x *= ratio
                self.velocity_y *= ratio

        self.angle += self.rotation_speed

        # --- ЛОГИКА СБОРА РЕСУРСОВ ---
        if self.is_collecting:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.collection_start_time

            # Сбор длится 3000 мс (3 секунды)
            if elapsed >= 3000:
                # Сбор завершён: помечаем на удаление, сбрасываем флаги
                self.marked_for_removal = True
                self.is_collecting = False
                self.collection_start_time = 0.0
            # Если сбор идёт — ничего не делаем, ждём таймера

    @property
    def rect(self):
        """Возвращает прямоугольник хитбокса со смещением."""
        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.center = (self.x, self.y)
        rect.move_ip(self.hitbox_offset_x, self.hitbox_offset_y)
        return rect

    def draw(self, screen, camera):
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y

        rotated_sprite = pygame.transform.rotate(self.sprite, math.degrees(self.angle))
        rect = rotated_sprite.get_rect(center=(draw_x, draw_y))
        screen.blit(rotated_sprite, rect)

        if DEBUG_HITBOX:
            hitbox = self.rect
            screen_hitbox = hitbox.copy()
            screen_hitbox.x -= camera.x
            screen_hitbox.y -= camera.y
            pygame.draw.rect(screen, (0, 255, 0), screen_hitbox, 2)
            center_x = screen_hitbox.centerx
            center_y = screen_hitbox.centery
            pygame.draw.circle(screen, (255, 0, 0), (int(center_x), int(center_y)), 4)

# game_object/asteroid.py
import math
import pygame
import random

# --- НАСТРОЙКА ОТЛАДКИ ---
DEBUG_HITBOX = False

# --- НАСТРОЙКИ ФИЗИКИ ---
MAX_ASTEROID_SPEED = 3.0
ASTEROID_DECAY = 0.98

# --- НАСТРОЙКИ ВОЗВРАТА НА ОРБИТУ ---
FREE_DURATION_MS = 10000       # сколько секунд астероид летает свободно (10 сек)
RETURN_LERP_SPEED = 0.005      # скорость возврата (чем меньше — тем плавнее)
RETURN_THRESHOLD = 5.0          # расстояние до точки орбиты для переключения в ORBIT


class Asteroid:
    @staticmethod
    def calculate_mass_from_size(size_px):
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

        self.is_collecting = False
        self.collection_start_time = 0.0
        self.collected_resources = None
        self.marked_for_removal = False
        self.hp = {16: 10, 32: 40, 64: 70}.get(size_px, 10)

        # --- СОСТОЯНИЕ ОРБИТЫ ---
        # ORBIT  — на орбите (орбитальное движение)
        # FREE   — выбит с орбиты (инерция + трение, таймер 10 сек)
        # RETURNING — возврат на орбиту (плавная интерполяция к точке орбиты)
        self.orbit_state = "ORBIT" if orbit_center is not None else "FREE"
        self._free_timer = 0.0          # накопитель времени в состоянии FREE (мс)
        self._orbit_angle = angle       # угол на орбите — продолжает двигаться во всех состояниях

    def apply_knockback(self, push_x, push_y):
        """Добавляет импульс и выбивает астероид с орбиты."""
        self.velocity_x += push_x
        self.velocity_y += push_y

        # Если астероид на орбите — сбрасываем на свободный полёт
        if self.orbit_state == "ORBIT" and self.orbit_center is not None:
            self.orbit_state = "FREE"
            self._free_timer = 0.0

    def take_damage(self, amount):
        self.hp -= amount

    def spawn_fragments(self, asteroid_sprites):
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

        return fragments

    def _create_fragment(self, size_px, asteroid_sprites):
        mod_prefix = self.type_key.split("_s")[0]
        key = f"{mod_prefix}_s{size_px}"

        sprite_data = asteroid_sprites.get(key)
        if not sprite_data:
            print(f"[WARN] Нет спрайта для фрагмента: {key}")
            return None

        sprite, _ = sprite_data

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

    def _advance_orbit_angle(self):
        """Продвигает орбитальный угол — вызывается в любом состоянии."""
        self._orbit_angle += self.orbit_speed

    def _get_orbit_point(self):
        """Возвращает точку на орбите, где астероид должен быть сейчас."""
        cx, cy = self.orbit_center
        ox = cx + math.cos(self._orbit_angle) * self.orbit_radius
        oy = cy + math.sin(self._orbit_angle) * self.orbit_radius
        return ox, oy

    def update(self):
        dt = 0.016  # ~60 FPS

        # Орбитальный угол всегда движется (даже когда астероид сбит)
        if self.orbit_center is not None and self.orbit_speed != 0:
            self._advance_orbit_angle()

        if self.orbit_state == "ORBIT" and self.orbit_center is not None:
            # --- НА ОРБИТЕ ---
            ox, oy = self._get_orbit_point()
            self.x = ox
            self.y = oy

        elif self.orbit_state == "FREE":
            # --- СВОБОДНЫЙ ПОЛЁТ (выбит с орбиты или кластерный) ---
            self.x += self.velocity_x
            self.y += self.velocity_y

            self.velocity_x *= ASTEROID_DECAY
            self.velocity_y *= ASTEROID_DECAY

            speed = math.hypot(self.velocity_x, self.velocity_y)
            if speed > MAX_ASTEROID_SPEED:
                ratio = MAX_ASTEROID_SPEED / speed
                self.velocity_x *= ratio
                self.velocity_y *= ratio

            # Таймер свободного полёта (только для поясных астероидов)
            if self.orbit_center is not None:
                self._free_timer += dt * 1000  # переводим в миллисекунды
                if self._free_timer >= FREE_DURATION_MS:
                    self.orbit_state = "RETURNING"

        elif self.orbit_state == "RETURNING" and self.orbit_center is not None:
            # --- ВОЗВРАТ НА ОРБИТУ (плавный) ---
            ox, oy = self._get_orbit_point()

            # Интерполяция позиции к точке орбиты
            self.x += (ox - self.x) * RETURN_LERP_SPEED
            self.y += (oy - self.y) * RETURN_LERP_SPEED

            # Гасим остаточную скорость
            self.velocity_x *= 0.9
            self.velocity_y *= 0.9

            # Проверяем, достаточно ли близко к орбите
            dist = math.hypot(self.x - ox, self.y - oy)
            if dist < RETURN_THRESHOLD:
                self.orbit_state = "ORBIT"
                self.velocity_x = 0.0
                self.velocity_y = 0.0

        # Вращение спрайта
        self.angle += self.rotation_speed

        # --- ЛОГИКА СБОРА РЕСУРСОВ ---
        if self.is_collecting:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.collection_start_time

            if elapsed >= 3000:
                self.marked_for_removal = True
                self.is_collecting = False
                self.collection_start_time = 0.0

    @property
    def rect(self):
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

# game_objects/particle_rocket.py
import pygame
import math
import random

class ParticleRocket:
    def __init__(self, x, y, angle, target=None, max_distance=2000):
        self.x = x
        self.y = y
        self.angle = angle
        self.target = target
        self.max_distance = max_distance
        self.distance_traveled = 0
        self.speed = 9.0
        self.turn_speed = 5.0

        self.particles = []
        self.emit_rate = 3          # частиц за кадр
        self.max_particles = 40    # лимит частиц
        self.particle_life_min = 20
        self.particle_life_max = 35

        self.sprites = None
        self.animation_index = 0
        self.animation_timer = 0
        self.rect = pygame.Rect(0, 0, 16, 16)
        self.rect.center = (int(self.x), int(self.y))

    def set_sprites(self, sprites):
        self.sprites = sprites
        if sprites and len(sprites) > 0:
            w = sprites[0].get_width()
            h = sprites[0].get_height()
            self.rect = pygame.Rect(0, 0, w, h)
            self.rect.center = (int(self.x), int(self.y))

    def update(self):
        # Самонаведение (аналогично обычной ракете)
        if self.target is not None and not self.target.is_destroyed:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            diff = target_angle - self.angle
            while diff > 180: diff -= 360
            while diff < -180: diff += 360
            if abs(diff) <= self.turn_speed:
                self.angle = target_angle
            elif diff > 0:
                self.angle += self.turn_speed
            else:
                self.angle -= self.turn_speed

        # Движение
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed

        # Rect
        if self.sprites and len(self.sprites) > 0:
            w = self.sprites[0].get_width()
            h = self.sprites[0].get_height()
            self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(self.x), int(self.y))

        # Анимация
        if self.sprites:
            self.animation_timer += 1
            if self.animation_timer >= 4:
                self.animation_index = (self.animation_index + 1) % len(self.sprites)
                self.animation_timer = 0

        # Эмиссия частиц
        if len(self.particles) < self.max_particles:
            angle_offset = random.uniform(-20, 20)
            p_angle = self.angle + math.radians(angle_offset)
            speed = random.uniform(1.5, 3.5)

            px = self.x + math.cos(p_angle) * 12
            py = self.y + math.sin(p_angle) * 12

            life = random.randint(self.particle_life_min, self.particle_life_max)
            size = random.randint(4, 7)
            # Цвет пламени: оранжевый -> жёлтый
            color = (255, random.randint(100, 180), random.randint(0, 60))

            self.particles.append({
                "x": px, "y": py,
                "vx": math.cos(p_angle) * speed,
                "vy": math.sin(p_angle) * speed,
                "life": life,
                "size": size,
                "color": color
            })

        # Обновление и удаление частиц
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def is_active(self):
        return self.distance_traveled < self.max_distance

    def check_hit(self):
        if self.target is not None and not self.target.is_destroyed:
            dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if dist < 35:
                return True
            if self.rect.colliderect(self.target.rect):
                return True
        return False

    def draw(self, surface, camera):
        cam_x, cam_y = camera.x, camera.y
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Рисуем частицы (дым/пламя)
        for p in self.particles:
            sx = int(p["x"] - cam_x)
            sy = int(p["y"] - cam_y)
            alpha = int(255 * (p["life"] / self.particle_life_max))
            surf = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            c = p["color"]
            surf.fill((c[0], c[1], c[2], alpha))
            surface.blit(surf, (sx, sy))

        # Рисуем ракету поверх дыма
        if self.sprites and len(self.sprites) > 0:
            sprite = self.sprites[self.animation_index]
            rotated = pygame.transform.rotate(sprite, -self.angle)
            rect = rotated.get_rect(center=(int(draw_x), int(draw_y)))
            surface.blit(rotated, rect)
        else:
            pygame.draw.circle(surface, (255, 150, 50), (int(draw_x), int(draw_y)), 5)

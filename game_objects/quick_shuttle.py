# game_objects/quick_shuttle.py
import math
from game_objects.static_ship import StaticShip
from game_objects.debris import ShipDebris


class QuickShuttle(StaticShip):
    """Статичный корабль-челнок.

    При приближении игрока ближе 1000px разлетается на осколки.
    Осколки остаются в мире и доступны для сбора ресурсов
    (через ShipDebris с type_key 'destroyer_debris').
    """

    TRIGGER_DISTANCE = 1000

    def __init__(self, sprite, x, y, debris_sprites, angle=0.0):
        super().__init__(sprite, x, y, angle)

        # Используем idle-спрайт целиком, а не 20%-ремонтный
        self._base_sprite = sprite
        self.sprite = sprite
        self.ship_name = "Quick Shuttle"

        # Список спрайтов осколков (10 штук)
        self._debris_sprites = debris_sprites

        # Одноразовый флаг срабатывания триггера
        self.is_triggered = False

    def update(self):
        """Quick Shuttle не использует ремонтные стадии —
        _update_sprite_by_hull() не вызываем, чтобы idle-спрайт не подменялся."""
        pass

    def check_proximity(self, player_x, player_y):
        """Возвращает True, если игрок в пределах TRIGGER_DISTANCE."""
        if self.is_triggered:
            return False
        dist = math.hypot(player_x - self.x, player_y - self.y)
        return dist < self.TRIGGER_DISTANCE

    def spawn_debris(self):
        """Создаёт осколки ShipDebris в позиции корабля.

        Возвращает список созданных объектов ShipDebris.
        Осколки наследуют type_key='destroyer_debris',
        поэтому сбор ресурсов работает через существующую
        логику в PlayerShip.try_start_collection().
        """
        self.is_triggered = True
        debris_list = []

        if self._debris_sprites:
            for debris_sprite in self._debris_sprites:
                debris = ShipDebris(self.x, self.y, debris_sprite)
                debris_list.append(debris)

        return debris_list

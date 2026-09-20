import random

EMPTY = 0
SHIP = 1
MISS = 2
HIT = 3


class Ship:
    def __init__(self, cells):
        self.cells = set(cells)
        self.hits = set()

    def register_hit(self, cell):
        self.hits.add(cell)

    def is_sunk(self):
        return self.cells <= self.hits


class Board:
    def __init__(self, size=10):
        self.size = size
        self.grid = [[EMPTY] * size for _ in range(size)]
        self.ships = []

    def can_place(self, cells):
        for (x, y) in cells:
            if not (0 <= x < self.size and 0 <= y < self.size):
                return False
            if self.grid[y][x] != EMPTY:
                return False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.size and 0 <= ny < self.size:
                        if self.grid[ny][nx] == SHIP and (nx, ny) not in cells:
                            return False
        return True

    def place_ship(self, cells):
        ship = Ship(cells)
        for (x, y) in cells:
            self.grid[y][x] = SHIP
        self.ships.append(ship)
        return ship

    def place_ships_randomly(self, sizes):
        for length in sizes:
            placed = False
            attempts = 0
            while not placed and attempts < 1000:
                attempts += 1
                horizontal = random.choice([True, False])
                if horizontal:
                    x = random.randint(0, self.size - length)
                    y = random.randint(0, self.size - 1)
                    cells = [(x + i, y) for i in range(length)]
                else:
                    x = random.randint(0, self.size - 1)
                    y = random.randint(0, self.size - length)
                    cells = [(x, y + i) for i in range(length)]
                if self.can_place(cells):
                    self.place_ship(cells)
                    placed = True
            if not placed:
                raise RuntimeError(
                    "Не удалось расставить корабли — уменьшите их количество в настройках"
                )

    def shoot(self, x, y):
        cell = self.grid[y][x]
        if cell in (HIT, MISS):
            return "repeat"
        if cell == SHIP:
            self.grid[y][x] = HIT
            for ship in self.ships:
                if (x, y) in ship.cells:
                    ship.register_hit((x, y))
                    return "sunk" if ship.is_sunk() else "hit"
        self.grid[y][x] = MISS
        return "miss"

    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def ship_cells_of_sunk_ships(self):
        cells = set()
        for ship in self.ships:
            if ship.is_sunk():
                cells |= ship.cells
        return cells


class ComputerPlayer:
    """Компьютерный игрок. В режиме medium или hard после попадания
    достреливает соседние клетки."""

    def __init__(self, board_size, difficulty="medium"):
        self.size = board_size
        self.difficulty = difficulty
        self.available = {(x, y) for x in range(board_size) for y in range(board_size)}
        self.hit_stack = []

    def choose_shot(self):
        if self.difficulty != "easy":
            while self.hit_stack:
                cell = self.hit_stack.pop()
                if cell in self.available:
                    return cell
        return random.choice(list(self.available))

    def register_result(self, cell, result):
        self.available.discard(cell)
        if self.difficulty == "easy":
            return
        if result == "sunk":
            self.hit_stack.clear()
        elif result == "hit":
            x, y = cell
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in self.available:
                    self.hit_stack.append((nx, ny))

"""
Задание 5: Игра "Жизнь" (Conway's Game of Life)

Программа читает начальную конфигурацию поля из текстового файла,
моделирует несколько шагов игры "Жизнь" и для каждого шага:
  1) дописывает новую конфигурацию поля в текстовый выходной файл.
  2) сохраняет "снимок" поля в виде отдельного PNG-файла.

Клетки, которые живут дольше, рисуются более темным 
оттенком, а только что родившиеся клетки — светлым,
почти белым оттенком. 

ФОРМАТ ВХОДНОГО ФАЙЛА:

Первая строка:  ШИРИНА ВЫСОТА
Далее ВЫСОТА строк, каждая длиной ШИРИНА символов, где:
    '#' — живая клетка
    '.' — мёртвая клетка

Пример:

    10 10
    ..........
    ...#......
    ....#.....
    ..###.....
    ..........
    ..........
    ..........
    ..........
    ..........
    ..........

"""

import argparse
import os
from PIL import Image, ImageDraw

# 1. РАБОТА С ВХОДНЫМ ФАЙЛОМ

def read_field(filename):
    """Читает начальное поле из текстового файла.

    Возвращает кортеж (ширина, высота, grid), где grid - это список
    списков булевых значений: True - клетка жива, False - мертва.
    """
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip("\n") != ""]

    if not lines:
        raise ValueError("Входной файл пуст")

    # первая строка - размеры поля
    width, height = map(int, lines[0].split())

    grid = []
    for y in range(height):
        row_text = lines[1 + y]
        # если строка короче, чем нужно - дополняем мёртвыми клетками
        row_text = row_text.ljust(width, ".")
        row = [ch == "#" for ch in row_text[:width]]
        grid.append(row)

    return width, height, grid



# 2. ПРОВЕРКА "ЧИСТОГО" ЦВЕТА


def parse_pure_color(hex_str):
    """Разбирает HEX-строку цвета и проверяет, что цвет "чистый":
    каждый из каналов R, G, B равен либо 0, либо 255.

    Возвращает кортеж (r, g, b).
    """
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) != 6:
        raise ValueError("Цвет должен быть в формате #RRGGBB, например #00FF00")

    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)

    if not all(channel in (0, 255) for channel in (r, g, b)):
        raise ValueError(
            "Цвет должен быть 'чистым': каждый канал R, G, B должен быть "
            "равен 0 или 255 (например #FF0000, #00FF00, #0000FF, #FFFF00)"
        )

    if (r, g, b) in [(0, 0, 0), (255, 255, 255)]:
        raise ValueError("Чёрный и белый цвета использовать нельзя")

    return (r, g, b)


def color_for_age(age, pure_color, max_age):
    """Возвращает цвет клетки в зависимости от её возраста.

    Молодая клетка (age маленький) — светлый, почти белый оттенок.
    Старая клетка (age >= max_age) — полностью насыщенный базовый цвет.
    """
    white = (255, 255, 255)
    t = min(age / max_age, 1.0)  # доля "насыщенности" цвета, от 0 до 1

    r = round(white[0] + (pure_color[0] - white[0]) * t)
    g = round(white[1] + (pure_color[1] - white[1]) * t)
    b = round(white[2] + (pure_color[2] - white[2]) * t)
    return (r, g, b)



# 3. ПРАВИЛА ИГРЫ "ЖИЗНЬ"


def count_alive_neighbors(grid, x, y, width, height):
    """Считает количество живых соседей клетки (x, y) среди 8 соседних клеток.
    Клетки за пределами поля считаются мёртвыми (поле не замкнуто в тор).
    """
    count = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx]:
                count += 1
    return count


def next_generation(grid, ages, width, height):
    """Вычисляет следующее поколение по классическим правилам игры "Жизнь":
      - живая клетка с 2 или 3 живыми соседями выживает;
      - мёртвая клетка ровно с 3 живыми соседями оживает;
      - во всех остальных случаях клетка мертва (умирает или остаётся мёртвой).

    Возвращает новую пару (grid, ages).
    """
    new_grid = [[False] * width for _ in range(height)]
    new_ages = [[0] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            alive = grid[y][x]
            neighbors = count_alive_neighbors(grid, x, y, width, height)

            if alive and neighbors in (2, 3):
                new_grid[y][x] = True
                new_ages[y][x] = ages[y][x] + 1       # клетка выжила - стала на год старше
            elif not alive and neighbors == 3:
                new_grid[y][x] = True
                new_ages[y][x] = 1                    # клетка только что родилась
            else:
                new_grid[y][x] = False
                new_ages[y][x] = 0                    # клетка мертва

    return new_grid, new_ages



# 4. ЗАПИСЬ РЕЗУЛЬТАТОВ


def append_text_generation(output_file, generation_number, grid, width, height):
    """Дописывает текстовое представление текущего поколения в выходной файл."""
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"Поколение {generation_number}:\n")
        for y in range(height):
            row = "".join("#" if grid[y][x] else "." for x in range(width))
            f.write(row + "\n")
        f.write("\n")


def save_image(grid, ages, width, height, pure_color, max_age, cell_size, filename):
    """Сохраняет PNG-снимок текущего состояния поля.
    Живые клетки закрашиваются оттенком базового цвета в зависимости от возраста,
    мёртвые клетки остаются белыми. Между клетками рисуется тонкая серая сетка.
    """
    img_width = width * cell_size
    img_height = height * cell_size
    image = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(image)

    for y in range(height):
        for x in range(width):
            if grid[y][x]:
                color = color_for_age(ages[y][x], pure_color, max_age)
                x0, y0 = x * cell_size, y * cell_size
                x1, y1 = x0 + cell_size - 1, y0 + cell_size - 1
                draw.rectangle([x0, y0, x1, y1], fill=color)

    # рисуем сетку поверх клеток
    for x in range(0, img_width + 1, cell_size):
        draw.line([(x, 0), (x, img_height)], fill="lightgray")
    for y in range(0, img_height + 1, cell_size):
        draw.line([(0, y), (img_width, y)], fill="lightgray")

    image.save(filename)



# 5. ГЛАВНАЯ ФУНКЦИЯ


def main():
    parser = argparse.ArgumentParser(
        description="Игра 'Жизнь' (Conway's Game of Life) в консольном режиме."
    )
    parser.add_argument("input", help="путь к входному файлу с начальной конфигурацией поля")
    parser.add_argument("steps", type=int, help="количество шагов моделирования")
    parser.add_argument("color", help="базовый чистый цвет живой клетки, например #00FF00")
    parser.add_argument("--output", default="life_output.txt",
                         help="имя текстового выходного файла (по умолчанию life_output.txt)")
    parser.add_argument("--images-dir", default="life_images",
                         help="папка для PNG-снимков (по умолчанию life_images)")
    parser.add_argument("--cell-size", type=int, default=20,
                         help="размер клетки в пикселях на картинке (по умолчанию 20)")
    parser.add_argument("--max-age", type=int, default=10,
                         help="возраст, после которого цвет клетки уже не темнеет (по умолчанию 10)")

    args = parser.parse_args()

    # 1. читаем начальное поле
    width, height, grid = read_field(args.input)
    ages = [[1 if cell else 0 for cell in row] for row in grid]

    # 2. проверяем базовый цвет
    pure_color = parse_pure_color(args.color)

    # 3. готовим выходные файлы/папки
    if os.path.exists(args.output):
        os.remove(args.output)  # начинаем выходной файл с чистого листа
    os.makedirs(args.images_dir, exist_ok=True)

    # 4. основной цикл 
    for generation in range(args.steps + 1):
        append_text_generation(args.output, generation, grid, width, height)

        image_filename = os.path.join(args.images_dir, f"generation_{generation:04d}.png")
        save_image(grid, ages, width, height, pure_color, args.max_age,
                   args.cell_size, image_filename)

        print(f"Поколение {generation}: сохранено в '{args.output}' и '{image_filename}'")

        if generation < args.steps:
            grid, ages = next_generation(grid, ages, width, height)

    print("\nГотово!")
    print(f"Текстовый результат: {args.output}")
    print(f"Картинки:            {args.images_dir}/")


if __name__ == "__main__":
    import sys
    sys.argv = ["game_of_life.py", "glider.txt", "15", "#00FF00"]
    main()

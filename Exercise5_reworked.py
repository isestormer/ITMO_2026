import argparse

import os

from PIL import Image, ImageDraw

def read_field(filename):
    
    if not os.path.isfile(filename):
        
        raise FileNotFoundError(f"Входной файл '{filename}' не найден")

    with open(filename, 'r', encoding='utf-8') as f:
        
        raw_lines = f.readlines()

    lines = [line.rstrip('\r\n') for line in raw_lines]

    while lines and lines[-1] == '':
        
        lines.pop()

    if not lines:
        
        raise ValueError('Входной файл пуст')

    header = lines[0].split()
    
    if len(header) != 2:
        
        raise ValueError(
            
            "Первая строка файла должна содержать два числа: "
            "ширину и высоту поля, например '10 5'"
        )
    
    try:
        
        width, height = (int(header[0]), int(header[1]))
        
    except ValueError:
        
        raise ValueError('Ширина и высота поля в первой строке должны быть целыми числами')

    if width <= 0 or height <= 0:
        
        raise ValueError('Ширина и высота поля должны быть положительными числами')

    data_lines = lines[1:]
    
    if len(data_lines) < height:
        
        raise ValueError(
            
            f"В первой строке указана высота поля {height}, "
            f"но после неё в файле только {len(data_lines)} строк(и) данных"
        )

    grid = []
    
    for y in range(height):
        
        row_text = data_lines[y]
        
        if len(row_text) != width:
            
            raise ValueError(
                
                f"Строка {y + 2} файла имеет длину {len(row_text)} символов, "
                f"а по первой строке файла ожидалась ширина {width}. "
                "Проверьте формат входного файла."
            )
        row = [ch == '#' for ch in row_text]
        
        grid.append(row)
        
    return (width, height, grid)

def parse_pure_color(hex_str):
    
    hex_str = hex_str.strip().lstrip('#')
    
    if len(hex_str) != 6:
        
        raise ValueError('Цвет должен быть в формате #RRGGBB, например #00FF00')
    
    r = int(hex_str[0:2], 16)
    
    g = int(hex_str[2:4], 16)
    
    b = int(hex_str[4:6], 16)
    
    if not all((channel in (0, 255) for channel in (r, g, b))):
        
        raise ValueError("Цвет должен быть 'чистым': каждый канал R, G, B должен быть равен 0 или 255 (например #FF0000, #00FF00, #0000FF, #FFFF00)")
    
    if (r, g, b) in [(0, 0, 0), (255, 255, 255)]:
        
        raise ValueError('Чёрный и белый цвета использовать нельзя')
    
    return (r, g, b)

def color_for_age(age, pure_color, max_age):
    
    white = (255, 255, 255)
    
    t = min(age / max_age, 1.0)
    
    r = round(white[0] + (pure_color[0] - white[0]) * t)
    
    g = round(white[1] + (pure_color[1] - white[1]) * t)
    
    b = round(white[2] + (pure_color[2] - white[2]) * t)
    
    return (r, g, b)

def count_alive_neighbors(grid, x, y, width, height):
    
    count = 0
    
    for dy in (-1, 0, 1):
        
        for dx in (-1, 0, 1):
            
            if dx == 0 and dy == 0:
                
                continue
            
            nx, ny = (x + dx, y + dy)
            
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx]:
                
                count += 1
                
    return count

def next_generation(grid, ages, width, height):
    
    new_grid = [[False] * width for _ in range(height)]
    
    new_ages = [[0] * width for _ in range(height)]
    
    for y in range(height):
        
        for x in range(width):
            
            alive = grid[y][x]
            
            neighbors = count_alive_neighbors(grid, x, y, width, height)
            
            if alive and neighbors in (2, 3):
                
                new_grid[y][x] = True
                
                new_ages[y][x] = ages[y][x] + 1
                
            elif not alive and neighbors == 3:
                
                new_grid[y][x] = True
                
                new_ages[y][x] = 1
                
            else:
                
                new_grid[y][x] = False
                
                new_ages[y][x] = 0
                
    return (new_grid, new_ages)

def append_text_generation(output_file, generation_number, grid, width, height):
    
    with open(output_file, 'a', encoding='utf-8') as f:
        
        f.write(f'Поколение {generation_number}:\n')
        
        for y in range(height):
            
            row = ''.join(('#' if grid[y][x] else '.' for x in range(width)))
            
            f.write(row + '\n')
            
        f.write('\n')

def save_image(grid, ages, width, height, pure_color, max_age, cell_size, filename):
    
    img_width = width * cell_size
    
    img_height = height * cell_size
    
    image = Image.new('RGB', (img_width, img_height), 'white')
    
    draw = ImageDraw.Draw(image)
    
    for y in range(height):
        
        for x in range(width):
            
            if grid[y][x]:
                
                color = color_for_age(ages[y][x], pure_color, max_age)
                
                x0, y0 = (x * cell_size, y * cell_size)
                
                x1, y1 = (x0 + cell_size - 1, y0 + cell_size - 1)
                
                draw.rectangle([x0, y0, x1, y1], fill=color)
                
    for x in range(0, img_width + 1, cell_size):
        
        draw.line([(x, 0), (x, img_height)], fill='lightgray')
        
    for y in range(0, img_height + 1, cell_size):
        
        draw.line([(0, y), (img_width, y)], fill='lightgray')
        
    image.save(filename)

def main():
    parser = argparse.ArgumentParser(description="Игра 'Жизнь' (Conway's Game of Life) в консольном режиме.")
    parser.add_argument('input', help='путь к входному файлу с начальной конфигурацией поля')
    parser.add_argument('steps', type=int, help='количество шагов моделирования')
    parser.add_argument('color', help='базовый чистый цвет живой клетки, например #00FF00')
    parser.add_argument('--output', default='life_output.txt', help='имя текстового выходного файла (по умолчанию life_output.txt)')
    parser.add_argument('--images-dir', default='life_images', help='папка для PNG-снимков (по умолчанию life_images)')
    parser.add_argument('--cell-size', type=int, default=20, help='размер клетки в пикселях на картинке (по умолчанию 20)')
    parser.add_argument('--max-age', type=int, default=10, help='возраст, после которого цвет клетки уже не темнеет (по умолчанию 10)')
    args = parser.parse_args()
    width, height, grid = read_field(args.input)
    ages = [[1 if cell else 0 for cell in row] for row in grid]
    pure_color = parse_pure_color(args.color)
    if os.path.exists(args.output):
        os.remove(args.output)
    os.makedirs(args.images_dir, exist_ok=True)
    for generation in range(args.steps + 1):
        append_text_generation(args.output, generation, grid, width, height)
        image_filename = os.path.join(args.images_dir, f'generation_{generation:04d}.png')
        save_image(grid, ages, width, height, pure_color, args.max_age, args.cell_size, image_filename)
        print(f"Поколение {generation}: сохранено в '{args.output}' и '{image_filename}'")
        if generation < args.steps:
            grid, ages = next_generation(grid, ages, width, height)
    print('\nГотово!')
    print(f'Текстовый результат: {args.output}')
    print(f'Картинки:            {args.images_dir}/')
if __name__ == '__main__':
    try:
        main()
    except (FileNotFoundError, ValueError) as e:
        print(f'Ошибка: {e}')

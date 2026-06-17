from PIL import Image

import os

import sys


def read_field(filename):
    
    with open(filename, "r", encoding="utf-8") as f:
        
        n, m = map(int, f.readline().split())

        field = []
        
        for _ in range(n):
            
            row = f.readline().strip()
            
            field.append([1 if c == "#" else 0 for c in row])

    return field


def count_neighbors(field, x, y):
    
    n = len(field)
    
    m = len(field[0])

    cnt = 0

    for dx in (-1, 0, 1):
        
        for dy in (-1, 0, 1):

            if dx == 0 and dy == 0:
                
                continue

            nx = x + dx
            
            ny = y + dy

            if 0 <= nx < n and 0 <= ny < m:
                
                if field[nx][ny] > 0:
                    
                    cnt += 1

    return cnt


def next_generation(field):
    
    n = len(field)
    
    m = len(field[0])

    new_field = [[0] * m for _ in range(n)]

    for i in range(n):
        
        for j in range(m):

            neighbors = count_neighbors(field, i, j)

            if field[i][j] > 0:
                
                if neighbors == 2 or neighbors == 3:
                    
                    new_field[i][j] = field[i][j] + 1
                    
            else:
                
                if neighbors == 3:
                    
                    new_field[i][j] = 1

    return new_field


def save_text(field, filename):
    
    with open(filename, "w", encoding="utf-8") as f:

        n = len(field)
        
        m = len(field[0])

        f.write(f"{n} {m}\n")

        for row in field:
            
            line = "".join("#" if cell > 0 else "." for cell in row)
            
            f.write(line + "\n")


def save_png(field, filename, base_color, cell_size=20):

    n = len(field)
    
    m = len(field[0])

    img = Image.new("RGB", (m * cell_size, n * cell_size), "white")
    
    pixels = img.load()

    max_age = max(max(row) for row in field)

    if max_age == 0:
        
        max_age = 1

    br, bg, bb = base_color

    for i in range(n):
        
        for j in range(m):

            age = field[i][j]

            if age > 0:

                k = min(age / max_age, 1.0)

                r = int(br * k)
                
                g = int(bg * k)
                
                b = int(bb * k)

                for y in range(i * cell_size,
                               
                               (i + 1) * cell_size):
                    
                    for x in range(j * cell_size,
                                   
                                   (j + 1) * cell_size):
                        
                        pixels[x, y] = (r, g, b)

    img.save(filename)


def main():

    input_file = "input.txt"

    steps = int(input("Количество шагов: "))

    r = int(input("R: "))
    
    g = int(input("G: "))
    
    b = int(input("B: "))

    base_color = (r, g, b)

    field = read_field(input_file)

    os.makedirs("result", exist_ok=True)

    for step in range(1, steps + 1):

        field = next_generation(field)

        save_text(
            
            field,
            
            f"result/step_{step}.txt"
        )

        save_png(
            
            field,
            
            f"result/step_{step}.png",
            
            base_color
        )

    print("Моделирование завершено")


if __name__ == "__main__":
    main()

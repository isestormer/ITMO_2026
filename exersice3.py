import math

#1

def get_input():
    """Ввод данных пользователем."""
    d1_yards = float(input("Введите кратчайшее расстояние между спасателем и кромкой воды, d1 (ярды) => "))
    d2_feet = float(input("Введите кратчайшее расстояние от утопающего до берега, d2 (футы) => "))
    h_yards = float(input("Введите боковое смещение между спасателем и утопающим, h (ярды) => "))
    v_sand_mph = float(input("Введите скорость движения спасателя по песку, v_sand (мили в час) => "))
    n = float(input("Введите коэффициент замедления спасателя при движении в воде, n => "))

    return d1_yards, d2_feet, h_yards, v_sand_mph, n

#2

def convert_units(d1_yards, d2_feet, h_yards, v_sand_mph):
    """Перевод единиц измерения."""
    d1 = d1_yards * 3          # ярды → футы
    d2 = d2_feet              # уже в футах
    h = h_yards * 3           # ярды → футы

    v_sand = v_sand_mph * 5280 / 3600  # мили/час → футы/сек

    return d1, d2, h, v_sand

#3

def calculate_time(d1, d2, h, v_sand, n, theta_deg):
    """Вычисление времени для заданного угла."""

    theta_rad = math.radians(theta_deg)

    x = d1 * math.tan(theta_rad)

    L1 = math.sqrt(x ** 2 + d1 ** 2)
    L2 = math.sqrt((h - x) ** 2 + d2 ** 2)

    t = (L1 + n * L2) / v_sand

    return t

#4

def find_optimal_angle(d1, d2, h, v_sand, n):
    """
    Подбор оптимального угла методом перебора.
    Шаг перебора = 0.1 градуса.
    """

    best_angle = 0
    best_time = float('inf')

    angle = 0.1

    while angle < 89.9:

        t = calculate_time(
            d1,
            d2,
            h,
            v_sand,
            n,
            angle
        )

        if t < best_time:
            best_time = t
            best_angle = angle

        angle += 0.1

    return best_angle, best_time

#5

def print_result(angle, time_sec):
    print()
    print(f"Оптимальный угол движения спасателя: {angle:.1f}°")
    print(f"Минимальное время достижения утопающего: {time_sec:.1f} секунд")

#6
    
def main():

    d1_yards, d2_feet, h_yards, v_sand_mph, n = get_input()

    d1, d2, h, v_sand = convert_units(
        d1_yards,
        d2_feet,
        h_yards,
        v_sand_mph
    )

    best_angle, best_time = find_optimal_angle(
        d1,
        d2,
        h,
        v_sand,
        n
    )

    print_result(best_angle, best_time)

# МОДУЛЬНЫЕ ТЕСТЫ

def test_convert_units():

    d1, d2, h, v = convert_units(
        8,
        10,
        50,
        5
    )

    assert d1 == 24
    assert d2 == 10
    assert h == 150
    assert abs(v - 7.3333333333) < 0.001


def test_calculate_time():

    d1, d2, h, v = convert_units(
        8,
        10,
        50,
        5
    )

    t = calculate_time(
        d1,
        d2,
        h,
        v,
        2,
        39.413
    )

    assert round(t, 1) == 39.9


def test_find_optimal_angle():

    d1, d2, h, v = convert_units(
        8,
        10,
        50,
        5
    )

    angle, time_sec = find_optimal_angle(
        d1,
        d2,
        h,
        v,
        2
    )

    assert angle > 0
    assert time_sec > 0


# Запуск тестов

test_convert_units()
test_calculate_time()
test_find_optimal_angle()

# Запуск программы

main()

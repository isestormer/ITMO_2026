import math

#1

def get_input():
    """Ввод данных пользователем."""
    d1_yards = float(input("Введите кратчайшее расстояние между спасателем и кромкой воды, d1 (ярды) => "))
    d2_feet = float(input("Введите кратчайшее расстояние от утопающего до берега, d2 (футы) => "))
    h_yards = float(input("Введите боковое смещение между спасателем и утопающим, h (ярды) => "))
    v_sand_mph = float(input("Введите скорость движения спасателя по песку, v_sand (мили в час) => "))
    n = float(input("Введите коэффициент замедления спасателя при движении в воде, n => "))
    theta1_deg = float(input("Введите направление движения спасателя по песку, theta1 (градусы) => "))

    return d1_yards, d2_feet, h_yards, v_sand_mph, n, theta1_deg

#2

def convert_units(d1_yards, d2_feet, h_yards, v_sand_mph):
    """Преобразование единиц измерения."""
    d1 = d1_yards * 3
    d2 = d2_feet
    h = h_yards * 3
    v_sand = v_sand_mph * 5280 / 3600

    return d1, d2, h, v_sand

#3

def calculate_time(d1, d2, h, v_sand, n, theta1_deg):
    """Вычисление времени достижения утопающего."""
    theta1_rad = math.radians(theta1_deg)

    x = d1 * math.tan(theta1_rad)
    L1 = math.sqrt(x ** 2 + d1 ** 2)
    L2 = math.sqrt((h - x) ** 2 + d2 ** 2)

    t = (1 / v_sand) * (L1 + n * L2)

    return t

#4

def print_result(theta1_deg, t):
    """Вывод результата."""
    theta1_rounded = round(theta1_deg)

    print(
        f"Если спасатель начнёт движение под углом theta1, "
        f"равным {theta1_rounded} градусам, "
        f"он достигнет утопающего через {t:.1f} секунды"
    )

#5
    
def main():
    d1_yards, d2_feet, h_yards, v_sand_mph, n, theta1_deg = get_input()

    d1, d2, h, v_sand = convert_units(
        d1_yards,
        d2_feet,
        h_yards,
        v_sand_mph
    )

    t = calculate_time(
        d1,
        d2,
        h,
        v_sand,
        n,
        theta1_deg
    )

    print_result(theta1_deg, t)

# МОДУЛЬНЫЕ ТЕСТЫ

def test_convert_units():
    d1, d2, h, v = convert_units(8, 10, 50, 5)

    assert d1 == 24
    assert d2 == 10
    assert h == 150
    assert abs(v - 7.3333333333) < 0.0001

def test_calculate_time():
    d1, d2, h, v = convert_units(8, 10, 50, 5)

    t = calculate_time(
        d1=d1,
        d2=d2,
        h=h,
        v_sand=v,
        n=2,
        theta1_deg=39.413
    )

    assert round(t, 1) == 39.9

# Запуск тестов
test_convert_units()
test_calculate_time()

# Запуск программы
main()

import csv
import math
import os
from datetime import datetime

MARKETS_CSV = "Export.csv"
REVIEWS_CSV = "reviews.csv"

REVIEW_FIELDS = ["FMID", "FirstName", "LastName", "Rating", "ReviewText", "Timestamp"]

PAYMENT_FIELDS = ["Credit", "WIC", "WICcash", "SFMNP", "SNAP"]
PRODUCT_FIELDS = [
    "Organic", "Bakedgoods", "Cheese", "Crafts", "Flowers", "Eggs", "Seafood",
    "Herbs", "Vegetables", "Honey", "Jams", "Maple", "Meat", "Nursery", "Nuts",
    "Plants", "Poultry", "Prepared", "Soap", "Trees", "Wine", "Coffee", "Beans",
    "Fruits", "Grains", "Juices", "Mushrooms", "PetFood", "Tofu", "WildHarvested",
]

EARTH_RADIUS_MILES = 3958.8

# 1. ЧТЕНИЕ И ЗАПИСЬ CSV-ФАЙЛОВ


def load_markets(path=MARKETS_CSV):
 
    markets = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            market = {key: (value.strip() if isinstance(value, str) else value)
                      for key, value in row.items()}
            market["x"] = _to_float_or_none(market.get("x"))
            market["y"] = _to_float_or_none(market.get("y"))
            markets.append(market)
    return markets


def _to_float_or_none(value):
 
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def save_markets(markets, path=MARKETS_CSV):
    
    if not markets:
        return
    fieldnames = list(markets[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in markets:
            writer.writerow({key: ("" if m.get(key) is None else m.get(key)) for key in fieldnames})


def load_reviews(path=REVIEWS_CSV):
  
    if not os.path.exists(path):
        return []
    reviews = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            review = dict(row)
            review["Rating"] = int(row["Rating"])
            reviews.append(review)
    return reviews


def save_reviews(reviews, path=REVIEWS_CSV):
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for r in reviews:
            writer.writerow({key: r.get(key, "") for key in REVIEW_FIELDS})

# 2. РАССТОЯНИЕ МЕЖДУ ТОЧКАМИ (формула гаверсинуса)

def haversine_miles(lat1, lon1, lat2, lon2):
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))

# 3. ПОИСК И ФИЛЬТРАЦИЯ

def get_market_by_fmid(markets, fmid):
   
    for m in markets:
        if m["FMID"] == fmid:
            return m
    return None


def search_by_city_state(markets, city=None, state=None):
   
    def matches(m):
        ok = True
        if city:
            ok = ok and city.lower() in (m.get("city") or "").lower()
        if state:
            ok = ok and state.lower() in (m.get("State") or "").lower()
        return ok

    return [m for m in markets if matches(m)]


def find_center_by_zip(markets, zip_code):
    
    for m in markets:
        if m.get("zip") == zip_code and m["x"] is not None and m["y"] is not None:
            return m["y"], m["x"]
    return None


def search_by_zip_radius(markets, zip_code, radius_miles):
    
    center = find_center_by_zip(markets, zip_code)
    if center is None:
        return None

    lat0, lon0 = center
    result = []
    for m in markets:
        if m["x"] is None or m["y"] is None:
            continue
        distance = haversine_miles(lat0, lon0, m["y"], m["x"])
        if distance <= radius_miles:
            result.append((m, distance))

    result.sort(key=lambda pair: pair[1])
    return result

# 4. РЕЦЕНЗИИ И РЕЙТИНГИ

def get_reviews_for_market(reviews, fmid):
    
    return [r for r in reviews if r["FMID"] == fmid]


def average_rating(reviews, fmid):
    
    market_reviews = get_reviews_for_market(reviews, fmid)
    if not market_reviews:
        return None
    return sum(r["Rating"] for r in market_reviews) / len(market_reviews)


def add_review(reviews, fmid, first_name, last_name, rating, text):
    
    new_review = {
        "FMID": fmid,
        "FirstName": first_name,
        "LastName": last_name,
        "Rating": rating,
        "ReviewText": text,
        "Timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    return reviews + [new_review]

# 5. СОРТИРОВКА И УДАЛЕНИЕ

def sort_markets(markets, reviews, key="name", reverse=False, ref_point=None):
    
    def sort_key(m):
        if key == "rating":
            r = average_rating(reviews, m["FMID"])
            return r if r is not None else -1
        elif key == "city":
            return (m.get("city") or "").lower()
        elif key == "state":
            return (m.get("State") or "").lower()
        elif key == "distance":
            if not ref_point or m["x"] is None or m["y"] is None:
                return float("inf")
            lat0, lon0 = ref_point
            return haversine_miles(lat0, lon0, m["y"], m["x"])
        else:
            return (m.get("MarketName") or "").lower()

    return sorted(markets, key=sort_key, reverse=reverse)


def delete_market(markets, reviews, fmid):

    new_markets = [m for m in markets if m["FMID"] != fmid]
    new_reviews = [r for r in reviews if r["FMID"] != fmid]
    return new_markets, new_reviews

# 6. ВЫВОД ДАННЫХ И ПАГИНАЦИЯ (разбивка по страницам)

def paginate(items, page_size=10):

    if page_size <= 0:
        page_size = 5
    return [items[i:i + page_size] for i in range(0, len(items), page_size)]


def format_rating(reviews, fmid):
    rating = average_rating(reviews, fmid)
    return f"{rating:.1f} из 5" if rating is not None else "нет рецензий"


def print_market_short(m, reviews):
    print(f"[{m['FMID']}] {m['MarketName']} — {m.get('city')}, {m.get('State')} "
          f"{m.get('zip')}  (рейтинг: {format_rating(reviews, m['FMID'])})")


def print_market_full(m, reviews):
    print("=" * 70)
    print(f"Название:   {m.get('MarketName')}")

    address_parts = [m.get('street'), m.get('city'), m.get('County'), m.get('State'), m.get('zip')]
    address = ", ".join(part for part in address_parts if part)
    print(f"Адрес:      {address or '-'}")

    if m.get("Website"):
        print(f"Сайт:       {m['Website']}")
    if m.get("Facebook"):
        print(f"Facebook:   {m['Facebook']}")

    if m.get("x") is not None and m.get("y") is not None:
        print(f"Координаты: широта {m['y']}, долгота {m['x']}")
    else:
        print("Координаты: неизвестны")

    schedule_lines = []
    for i in range(1, 5):
        season_date = m.get(f"Season{i}Date")
        season_time = m.get(f"Season{i}Time")
        if season_date or season_time:
            schedule_lines.append(f"  Сезон {i}: {season_date or '-'}  {season_time or ''}".rstrip())
    if schedule_lines:
        print("Расписание:")
        for line in schedule_lines:
            print(line)

    payment = [name for name in PAYMENT_FIELDS if m.get(name) == "Y"]
    if payment:
        print(f"Способы оплаты: {', '.join(payment)}")

    products = [name for name in PRODUCT_FIELDS if m.get(name) == "Y"]
    if products:
        print(f"Ассортимент:    {', '.join(products)}")

    market_reviews = get_reviews_for_market(reviews, m["FMID"])
    print(f"Средний рейтинг: {format_rating(reviews, m['FMID'])} "
          f"({len(market_reviews)} рец.)")
    for r in market_reviews:
        stars = "★" * r["Rating"] + "☆" * (5 - r["Rating"])
        text = r.get("ReviewText") or ""
        print(f"  - {r['FirstName']} {r['LastName']}  {stars}  {text}")
    print("=" * 70)


def show_markets_paginated(markets, reviews, page_size=10):

    if not markets:
        print("Рынки не найдены.")
        return

    pages = paginate(markets, page_size)
    idx = 0
    while True:
        print(f"\n--- Страница {idx + 1} из {len(pages)} (всего рынков: {len(markets)}) ---")
        for m in pages[idx]:
            print_market_short(m, reviews)
        cmd = input("[N] следующая, [P] предыдущая, [Enter] назад в меню: ").strip().lower()
        if cmd == "n":
            if idx < len(pages) - 1:
                idx += 1
            else:
                print("Это последняя страница.")
        elif cmd == "p":
            if idx > 0:
                idx -= 1
            else:
                print("Это первая страница.")
        elif cmd == "":
            break
        else:
            print("Неизвестная команда.")

# 7. ГЛАВНОЕ МЕНЮ (REPL)

def read_int_in_range(prompt, low, high):

    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and low <= int(raw) <= high:
            return int(raw)
        print(f"Пожалуйста, введите целое число от {low} до {high}.")


def action_list_all(markets, reviews):
    show_markets_paginated(markets, reviews)


def action_search_city_state(markets, reviews):
    city = input("Город (Enter, чтобы пропустить): ").strip() or None
    state = input("Штат, например Vermont (Enter, чтобы пропустить): ").strip() or None
    found = search_by_city_state(markets, city, state)
    show_markets_paginated(found, reviews)


def action_search_zip(markets, reviews):
    zip_code = input("Почтовый индекс: ").strip()
    radius_raw = input("Радиус поиска в милях (по умолчанию 30): ").strip()
    try:
        radius = float(radius_raw) if radius_raw else 30.0
    except ValueError:
        print("Некорректное значение радиуса, использую 30 миль.")
        radius = 30.0

    result = search_by_zip_radius(markets, zip_code, radius)
    if result is None:
        print("Такого почтового индекса нет в базе данных.")
        return
    if not result:
        print("В заданном радиусе рынков не найдено.")
        return

    for m, distance in result:
        print_market_short(m, reviews)
        print(f"    расстояние: {distance:.1f} миль")


def action_view_details(markets, reviews):
    fmid = input("Введите FMID рынка: ").strip()
    m = get_market_by_fmid(markets, fmid)
    if m is None:
        print("Рынок с таким FMID не найден.")
        return
    print_market_full(m, reviews)


def action_add_review(markets, reviews):
    fmid = input("Введите FMID рынка: ").strip()
    m = get_market_by_fmid(markets, fmid)
    if m is None:
        print("Рынок с таким FMID не найден.")
        return reviews

    first_name = input("Ваше имя: ").strip()
    last_name = input("Ваша фамилия: ").strip()
    rating = read_int_in_range("Оценка (1-5, обязательно): ", 1, 5)
    text = input("Текст рецензии (необязательно): ").strip()

    reviews = add_review(reviews, fmid, first_name, last_name, rating, text)
    save_reviews(reviews)
    print("Спасибо за рецензию! Она сохранена.")
    return reviews


def action_sort(markets, reviews):
    print("Критерии сортировки: name, rating, city, state, distance")
    key = input("Сортировать по: ").strip().lower() or "name"
    if key not in ("name", "rating", "city", "state", "distance"):
        print("Неизвестный критерий, использую 'name'.")
        key = "name"

    order = input("Порядок (asc/desc, по умолчанию asc): ").strip().lower()
    reverse = order == "desc"

    ref_point = None
    if key == "distance":
        zip_code = input("Почтовый индекс точки отсчёта: ").strip()
        ref_point = find_center_by_zip(markets, zip_code)
        if ref_point is None:
            print("Такой индекс не найден в данных, сортировка по расстоянию невозможна.")
            return

    sorted_markets = sort_markets(markets, reviews, key=key, reverse=reverse, ref_point=ref_point)
    show_markets_paginated(sorted_markets, reviews)


def action_delete(markets, reviews):
    fmid = input("Введите FMID рынка для удаления: ").strip()
    m = get_market_by_fmid(markets, fmid)
    if m is None:
        print("Рынок с таким FMID не найден.")
        return markets, reviews

    confirm = input(f"Удалить рынок '{m['MarketName']}' и все его рецензии? (да/нет): ").strip().lower()
    if confirm == "да":
        markets, reviews = delete_market(markets, reviews, fmid)
        save_markets(markets)
        save_reviews(reviews)
        print("Рынок удалён.")
    else:
        print("Удаление отменено.")
    return markets, reviews


MENU_TEXT = """
=== Фермерские рынки: главное меню ===
1. Показать список всех рынков
2. Найти рынок по городу и штату
3. Найти рынок по почтовому индексу (в радиусе)
4. Просмотреть подробную информацию о рынке
5. Оставить рецензию
6. Отсортировать список рынков
7. Удалить рынок
0. Выход
"""


def main_menu():
    print("Загрузка данных...")
    markets = load_markets()
    reviews = load_reviews()
    print(f"Загружено рынков: {len(markets)}, рецензий: {len(reviews)}")

    while True:
        print(MENU_TEXT)
        choice = input("Выберите пункт меню: ").strip()

        if choice == "1":
            action_list_all(markets, reviews)
        elif choice == "2":
            action_search_city_state(markets, reviews)
        elif choice == "3":
            action_search_zip(markets, reviews)
        elif choice == "4":
            action_view_details(markets, reviews)
        elif choice == "5":
            reviews = action_add_review(markets, reviews)
        elif choice == "6":
            action_sort(markets, reviews)
        elif choice == "7":
            markets, reviews = action_delete(markets, reviews)
        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неизвестный пункт меню, попробуйте ещё раз.")

# 8. ПРОСТЫЕ ТЕСТЫ (запускаются в блоке if __name__ == '__main__')

def _run_self_tests():

    sample_markets = [
        {"FMID": "1", "MarketName": "Test Market", "Website": "", "street": "",
         "city": "Springfield", "County": "", "State": "IL", "zip": "62701",
         "x": -89.6501, "y": 39.7817},
        {"FMID": "2", "MarketName": "Other Market", "Website": "", "street": "",
         "city": "Chicago", "County": "", "State": "IL", "zip": "60601",
         "x": -87.6298, "y": 41.8781},
    ]

    found = search_by_city_state(sample_markets, city="Chicago")
    assert len(found) == 1 and found[0]["FMID"] == "2"

    m = get_market_by_fmid(sample_markets, "1")
    assert m is not None and m["MarketName"] == "Test Market"
    assert get_market_by_fmid(sample_markets, "999") is None

    reviews = []
    new_reviews = add_review(reviews, "1", "Иван", "Иванов", 5, "Отлично!")
    assert reviews == []                      
    assert average_rating(new_reviews, "1") == 5
    assert average_rating(new_reviews, "2") is None

    distance = haversine_miles(39.7817, -89.6501, 41.8781, -87.6298)
    assert 150 < distance < 200

    sorted_by_name = sort_markets(sample_markets, new_reviews, key="name")
    assert sorted_by_name[0]["MarketName"] == "Other Market"

    remaining_markets, remaining_reviews = delete_market(sample_markets, new_reviews, "1")
    assert len(remaining_markets) == 1
    assert len(remaining_reviews) == 0

    pages = paginate(list(range(12)), page_size=5)
    assert len(pages) == 3 and pages[-1] == [10, 11]

    print("Все встроенные тесты пройдены успешно.\n")


if __name__ == "__main__":
    _run_self_tests()
    main_menu()

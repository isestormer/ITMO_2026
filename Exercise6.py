import math

import zip_util


def haversine(lat1, lon1, lat2, lon2):
    
    R = 3958.8  # радиус Земли в милях

    lat1 = math.radians(lat1)
    
    lon1 = math.radians(lon1)
    
    lat2 = math.radians(lat2)
    
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2) ** 2 +
         
         math.cos(lat1) * math.cos(lat2) *
         
         math.sin(dlon / 2) ** 2)

    c = 2 * math.asin(math.sqrt(a))

    return R * c


def deg_to_dms(value, is_lat=True):
    
    direction = 'N' if is_lat else 'E'

    if value < 0:
        
        direction = 'S' if is_lat else 'W'

    value = abs(value)

    degrees = int(value)
    
    minutes_float = (value - degrees) * 60
    
    minutes = int(minutes_float)
    
    seconds = (minutes_float - minutes) * 60

    return f"({degrees:03d}°{minutes:02d}'{seconds:05.2f}\"{direction})"


zip_codes = zip_util.read_zip_all()

zip_dict = {}

city_state_dict = {}

for record in zip_codes:
    
    zip_code, lat, lon, city, state, county = record

    zip_dict[zip_code] = {
        
        "lat": lat,
        
        "lon": lon,
        
        "city": city,
        
        "state": state,
        
        "county": county
    }

    key = (city.upper(), state.upper())

    if key not in city_state_dict:
        
        city_state_dict[key] = []

    city_state_dict[key].append(zip_code)


while True:
    
    command = input("Command ('loc', 'zip', 'dist', 'end') => ").strip().lower()

    if command == "end":
        
        print("Done")
        
        break

    elif command == "loc":

        zip_code = input("Enter a ZIP Code to lookup => ").strip()
        
        print(zip_code)

        if zip_code not in zip_dict:
            
            print("Error: ZIP Code not found")
            
            continue

        data = zip_dict[zip_code]

        lat = deg_to_dms(data["lat"], True)
        
        lon = deg_to_dms(data["lon"], False)

        print(
            
            f"ZIP Code {zip_code} is in "
            
            f"{data['city']}, {data['state']}, "
            
            f"{data['county']} county"
        )

        print(f"coordinates: {lat},{lon}")

    elif command == "zip":

        city = input("Enter a city name to lookup => ").strip()
        
        print(city)

        state = input("Enter the state name to lookup => ").strip()
        
        print(state)

        key = (city.upper(), state.upper())

        if key not in city_state_dict:
            
            print("Error: city/state not found")
            
            continue

        zips = sorted(city_state_dict[key])

        print(
            
            f"The following ZIP Code(s) found for "
            
            f"{city.title()}, {state.upper()}: "
            
            + ", ".join(zips)
        )

    elif command == "dist":

        zip1 = input("Enter the first ZIP Code => ").strip()
        
        print(zip1)

        zip2 = input("Enter the second ZIP Code => ").strip()
        
        print(zip2)

        if zip1 not in zip_dict or zip2 not in zip_dict:
            
            print("Error: ZIP Code not found")
            
            continue

        p1 = zip_dict[zip1]
        
        p2 = zip_dict[zip2]

        distance = haversine(
            
            p1["lat"], p1["lon"],
            
            p2["lat"], p2["lon"]
        )

        print(
            
            f"The distance between {zip1} and "
            
            f"{zip2} is {distance:.2f} miles"
        )

    else:
        
        print("Invalid command, ignoring")

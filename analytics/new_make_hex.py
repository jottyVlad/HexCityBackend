import math
import json
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
import sys
import time
from tqdm import tqdm

RADIUS_KM = 1.2
LAT_MIN, LAT_MAX = 53.4, 59.0
LON_MIN, LON_MAX = 33.5, 40.0
OUTPUT_JSON_FILE = 'moscow_hexagons2.json'

MKAD_POLYGON_COORDS_RAW = [
    [37.333727, 55.933541], [37.344452, 55.923801], [37.356644, 55.929873],
    [37.376506, 55.92163], [37.36116, 55.914088], [37.369455, 55.907788],
    [37.365739, 55.906276], [37.370094, 55.903594], [37.361961, 55.901366],
    [37.365497, 55.896786], [37.365557, 55.894994], [37.374117, 55.89518],
    [37.377415, 55.892687], [37.372992, 55.891327], [37.372905, 55.887602],
    [37.372508, 55.881907], [37.382085, 55.877884], [37.403668, 55.876062],
    [37.410827, 55.870757], [37.394467, 55.854197], [37.387028, 55.855902],
    [37.377747, 55.868282], [37.347619, 55.864480], [37.333023, 55.845503],
    [37.348873, 55.843874], [37.340475, 55.839055], [37.344782, 55.826164],
    [37.352113, 55.821034], [37.354054, 55.826327], [37.356898, 55.826556],
    [37.362183, 55.822071], [37.380655, 55.830585], [37.393968, 55.829714],
    [37.387990, 55.809853], [37.373696, 55.812689], [37.372044, 55.803158],
    [37.381356, 55.809481], [37.386693, 55.806732], [37.367632, 55.791047],
    [37.349858, 55.796860], [37.357800, 55.803289], [37.348965, 55.806694],
    [37.334083, 55.799432], [37.307738, 55.797445], [37.324837, 55.796489],
    [37.314130, 55.793697], [37.309938, 55.791994], [37.315129, 55.788335],
    [37.310487, 55.784394], [37.312197, 55.779666], [37.312861, 55.786360],
    [37.328211, 55.781109], [37.322718, 55.776866], [37.310775, 55.775429],
    [37.308728, 55.770241], [37.332267, 55.771919], [37.348521, 55.770036],
    [37.370575, 55.788185], [37.368915, 55.772951], [37.366612, 55.770135],
    [37.365868, 55.764366], [37.374798, 55.731911], [37.382436, 55.712960],
    [37.392623, 55.705848], [37.388982, 55.700820], [37.374846, 55.711452],
    [37.326020, 55.681862], [37.354484, 55.676509], [37.402461, 55.698615],
    [37.417653, 55.680817], [37.340007, 55.662856], [37.239333, 55.645805],
    [37.186052, 55.619124], [37.116490, 55.605525], [37.074896, 55.584765],
    [37.099997, 55.445767], [36.815578, 55.509474], [37.020793, 55.137332],
    [37.057235, 55.109822], [37.141774, 55.155766], [37.269423, 55.257563],
    [37.316800, 55.220658], [37.406081, 55.251084], [37.405328, 55.250563],
    [37.468576, 55.406710], [37.386484, 55.438441], [37.445240, 55.482092],
    [37.538306, 55.437531], [37.544755, 55.472566], [37.611030, 55.491414],
    [37.578603, 55.521781], [37.606772, 55.575117], [37.670430, 55.571554],
    [37.692785, 55.576587], [37.844412, 55.657521], [37.833863, 55.684417],
    [37.856814, 55.675787], [37.900333, 55.706582], [37.915378, 55.697125],
    [37.917356, 55.686472], [37.920532, 55.676229], [37.963945, 55.674003],
    [37.949848, 55.711258], [37.966683, 55.710508], [37.960022, 55.714460],
    [37.967221, 55.716361], [37.948105, 55.720306], [37.942547, 55.722374],
    [37.877111, 55.720191], [37.890264, 55.741970], [37.882526, 55.749229],
    [37.844338, 55.747033], [37.836710, 55.825015], [37.819872, 55.835909],
    [37.700935, 55.894961], [37.556665, 55.909807], [37.575554, 55.958570],
    [37.519040, 55.941856], [37.536975, 55.907551], [37.430569, 55.877840],
    [37.409643, 55.881071], [37.389777, 55.912666], [37.398475, 55.916808],
    [37.396885, 55.926150], [37.422451, 55.951451], [37.335067, 55.953807],
    [37.333727, 55.933541]
]
MKAD_POLYGON = Polygon(MKAD_POLYGON_COORDS_RAW)


def hex_corner(center_lat_lon, size_km, i):
    angle_deg = 60 * i + 30
    angle_rad = math.radians(angle_deg)

    dy = size_km * math.sin(angle_rad)
    dx = size_km * math.cos(angle_rad)

    dest_lat = geodesic(kilometers=dy).destination(center_lat_lon, 0)
    dest = geodesic(kilometers=dx).destination((dest_lat.latitude, dest_lat.longitude), 90)

    return [dest.longitude, dest.latitude]


def get_center_from_start_coords(lat, lon, row, dx):
    offset_x_km = dx / 2 if row % 2 == 1 else 0

    shifted = geodesic(kilometers=offset_x_km).destination((lat, lon), 90)

    return (shifted.latitude, shifted.longitude)


def create_hexagon(center_lat_lon, size_km):
    return [hex_corner(center_lat_lon, size_km, i) for i in range(6)]


def generate_hex_grid():
    hexagons_data = {}

    dx = RADIUS_KM * math.sqrt(3)
    dy = RADIUS_KM * 1.5

    lat = LAT_MIN
    hex_id = 1
    row = 0

    print(f"Начинается генерация гексагональной сетки")

    try:
        temp_point = geodesic(kilometers=dy).destination((LAT_MIN, LON_MIN), 0)
        lat_step = temp_point.latitude - LAT_MIN
        total_rows_estimate = math.ceil((LAT_MAX - LAT_MIN) / lat_step) if lat_step != 0 else 1000
    except Exception:
        total_rows_estimate = 1000

    with tqdm(total=total_rows_estimate, desc="Обработка рядов") as pbar:
        while lat <= LAT_MAX:

            offset_x_km = dx / 2 if row % 2 == 1 else 0
            start_point = geodesic(kilometers=offset_x_km).destination((lat, LON_MIN), 90)
            current_lat = start_point.latitude
            current_lon = start_point.longitude

            while current_lon <= LON_MAX:

                center_lat_lon = (current_lat, current_lon)
                center_point = Point(center_lat_lon[1], center_lat_lon[0])

                if MKAD_POLYGON.contains(center_point):
                    hexagon_peaks = create_hexagon(center_lat_lon, RADIUS_KM)

                    hexagons_data[str(hex_id)] = {
                        "center": [center_lat_lon[1], center_lat_lon[0]],
                        "peaks": hexagon_peaks,
                    }
                    hex_id += 1

                next_point = geodesic(kilometers=dx).destination((current_lat, current_lon), 90)
                current_lat = next_point.latitude
                current_lon = next_point.longitude

            next_row = geodesic(kilometers=dy).destination((lat, LON_MIN), 0)
            next_row_lat = next_row.latitude

            if next_row_lat > lat:
                pbar.update(1)

            lat = next_row_lat
            row += 1

    return hexagons_data


start_time = time.time()
hex_data = generate_hex_grid()
end_time = time.time()

try:
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(hex_data, f, indent=2)

    print(f"Генерация завершена. Сгенерировано {len(hex_data)} шестиугольников.")
    print(f"Данные сохранены в '{OUTPUT_JSON_FILE}'.")
    print(f"Время выполнения: {end_time - start_time:.2f} секунд.")
except Exception as e:
    print(f"Ошибка при сохранении JSON: {e}")
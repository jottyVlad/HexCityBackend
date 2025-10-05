import json
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point, Polygon
from tqdm import tqdm
from typing import Dict, Any, Optional
import time
import warnings

warnings.filterwarnings("ignore")

INPUT_HEX_JSON_FILE = 'moscow_hexagons_with_speeds_2.json'
INPUT_STOPS_CSV_FILE = 'f_public_mgt_fact_schedule_optimized.csv'
OUTPUT_JSON_FILE = 'moscow_hexagons_with_stops_and_routes_2.json'
CSV_ENCODING = 'utf-8'
CSV_SEPARATOR = ','
TARGET_CRS = "EPSG:4326"


def load_hex_data(file_path: str) -> Optional[Dict]:
    print(f"Шаг 1: Загрузка сетки гексов из '{file_path}'")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            hex_data = json.load(f)
        print(f"Успешно загружено {len(hex_data)} гексов.")
        return hex_data
    except Exception as e:
        print(f"Ошибка при чтении JSON: {e}")
        return None


def preprocess_stops_data(file_path: str) -> Optional[GeoDataFrame]:
    print(f"Шаг 2: Загрузка и подготовка данных об остановках из '{file_path}'")

    stops_df = None
    required_cols = ['route_id', 'stop_id', 'stop_latitude', 'stop_longitude']

    try:
        stops_df = pd.read_csv(
            file_path,
            usecols=required_cols,
            sep=CSV_SEPARATOR,
            encoding=CSV_ENCODING,
            index_col=False
        )
        print(f"Успешно прочитано. Всего записей: {len(stops_df):,}.")
    except KeyError as e:
        print(f"ОШИБКА: Не найдена обязательная колонка {e}. Проверьте заголовки в CSV (регистр!).")
        return None
    except Exception as e:
        print(f"Критическая ошибка при чтении CSV: {e}")
        return None

    try:
        stops_df['stop_latitude'] = pd.to_numeric(stops_df['stop_latitude'], errors='coerce')
        stops_df['stop_longitude'] = pd.to_numeric(stops_df['stop_longitude'], errors='coerce')
        stops_df['route_id'] = stops_df['route_id'].astype(str)
        stops_df['stop_id'] = stops_df['stop_id'].astype(str)

        stops_df.dropna(subset=required_cols, inplace=True)

        geometry = [Point(xy) for xy in zip(stops_df['stop_longitude'], stops_df['stop_latitude'])]
        stops_gdf = GeoDataFrame(stops_df, geometry=geometry, crs=TARGET_CRS)

        stops_gdf.drop_duplicates(subset=['stop_id', 'route_id'], inplace=True)

        print(f"Успешно подготовлено {len(stops_gdf):,} уникальных гео-записей (остановка+маршрут).")
        return stops_gdf

    except Exception as e:
        print(f"Ошибка обработки GeoDataFrame: {e}")
        return None


def process_spatial_join(hex_data: Dict, stops_gdf: GeoDataFrame) -> Dict:
    print("Шаг 3: Привязка остановок к гексам...")

    hex_list_for_gdf = []
    for hid, data in hex_data.items():
        try:
            hex_polygon = Polygon(data['peaks'])
            hex_list_for_gdf.append({'hex_id': hid, 'geometry': hex_polygon})
        except Exception:
            continue

    hex_gdf_polygons = GeoDataFrame(hex_list_for_gdf, crs=TARGET_CRS)

    joined_data = hex_gdf_polygons.sjoin(stops_gdf, how="left", predicate='contains')

    print("Агрегация: подсчет остановок и уникальных маршрутов...")

    grouped = joined_data.groupby('hex_id', dropna=False)

    total_hexes = len(hex_data)

    for hex_id in tqdm(hex_data.keys(), total=total_hexes, desc="Агрегация результатов"):

        if hex_id not in grouped.groups:
            hex_data[hex_id]['stop_count'] = 0
            hex_data[hex_id]['unique_routes_count'] = 0
            continue

        group = grouped.get_group(hex_id)

        valid_stops = group.dropna(subset=['stop_id'])

        if valid_stops.empty:
            stop_count = 0
            unique_routes_count = 0
        else:
            stop_count = valid_stops['stop_id'].nunique()
            unique_routes_count = valid_stops['route_id'].nunique()

        hex_data[hex_id]['stop_count'] = stop_count
        hex_data[hex_id]['unique_routes_count'] = unique_routes_count

    print(f"Шаг 3 завершен. Обновлено {len(hex_data)} гексов.")
    return hex_data


if __name__ == '__main__':
    start_time = time.time()

    hex_data = load_hex_data(INPUT_HEX_JSON_FILE)
    stops_gdf = preprocess_stops_data(INPUT_STOPS_CSV_FILE)

    if hex_data and stops_gdf is not None:
        final_data = process_spatial_join(hex_data, stops_gdf)

        try:
            with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)

            end_time = time.time()
            print(f"ФИНАЛЬНАЯ СБОРКА ЗАВЕРШЕНА.")
            print(f"Результат сохранен в '{OUTPUT_JSON_FILE}'.")
            print(f"Общее время выполнения: {end_time - start_time:.2f} секунд.")
        except Exception as e:
            print(f"ОШИБКА при сохранении финального JSON: {e}")
    else:
        print("Процесс остановлен из-за критических ошибок при загрузке данных.")
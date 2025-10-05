import json
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
from shapely.wkt import loads as wkt_loads
from tqdm import tqdm
from collections import defaultdict
import time
from typing import Dict, Any, Optional
import warnings

warnings.filterwarnings("ignore")

INPUT_HEX_JSON_FILE = 'moscow_hexagons_with_stops_and_routes_2.json'
INPUT_PEDESTRIAN_CSV_FILE = 'pedestrian_graph_2gis_optimized.csv'
OUTPUT_JSON_FILE = 'moscow_hexagons_final_analysis_2.json'
CSV_ENCODINGS_TO_TRY = ['utf-8', 'cp1251', 'latin1']
CSV_SEPARATOR = ';'
TARGET_CRS = "EPSG:4326"

DOWNSAMPLE_N_PEDESTRIAN = 6


def load_hex_data(file_path: str) -> Optional[Dict]:
    print(f"Шаг 1: Загрузка текущей сетки гексов из '{file_path}'")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            hex_data = json.load(f)
        print(f"Успешно загружено {len(hex_data)} гексов.")
        return hex_data
    except Exception as e:
        print(f"Ошибка при чтении JSON: {e}")
        return None


def preprocess_pedestrian_data(file_path: str) -> Optional[GeoDataFrame]:
    print(
        f"Шаг 2: Загрузка и подготовка пешеходных дорог из '{file_path}' (Downsample N={DOWNSAMPLE_N_PEDESTRIAN})")

    roads_df = None
    required_cols = ['edge_id', 'geometry', 'coverage_type_nm']

    for enc in CSV_ENCODINGS_TO_TRY:
        try:
            roads_df = pd.read_csv(
                file_path,
                usecols=required_cols,
                sep=CSV_SEPARATOR,
                dtype={'geometry': object},
                encoding=enc
            )
            print(f"Успешно прочитано с кодировкой: {enc}. Всего записей: {len(roads_df):,}.")
            break
        except Exception:
            continue

    if roads_df is None:
        print("ОШИБКА: Не удалось прочитать CSV файл пешеходных дорог.")
        return None

    if DOWNSAMPLE_N_PEDESTRIAN > 1:
        roads_df = roads_df.iloc[::DOWNSAMPLE_N_PEDESTRIAN].copy()
        print(f"Применена фильтрация: оставлено {len(roads_df):,} дорог (каждая {DOWNSAMPLE_N_PEDESTRIAN}-я).")

    def safe_line_string_conversion(geom_str):
        if not isinstance(geom_str, str) or not geom_str.startswith('LINESTRING'):
            return None
        try:
            clean_s = geom_str.strip().replace('lineString', 'LINESTRING').replace('Linestring', 'LINESTRING')
            return wkt_loads(clean_s)
        except Exception:
            return None

    roads_df['geometry'] = roads_df['geometry'].apply(safe_line_string_conversion)
    roads_df.dropna(subset=['geometry'], inplace=True)

    roads_df['edge_id'] = roads_df['edge_id'].astype(str)

    roads_gdf = GeoDataFrame(roads_df, geometry='geometry', crs=TARGET_CRS)
    processed_roads_count = len(roads_gdf)

    print(f"УСПЕХ: Успешно обработано {processed_roads_count:,} корректных пешеходных сегментов.")
    return roads_gdf


def process_pedestrian_to_hexagons(hex_data: Dict, roads_gdf: GeoDataFrame) -> Dict:

    if roads_gdf is None or hex_data is None:
        return hex_data

    hex_list_for_gdf = []
    for hid, data in hex_data.items():
        try:
            hex_polygon = Polygon(data['peaks'])
            hex_list_for_gdf.append({'hex_id': hid, 'geometry': hex_polygon})
        except Exception:
            continue

    hex_gdf = GeoDataFrame(hex_list_for_gdf, crs=TARGET_CRS)

    final_hex_pedestrian_data = defaultdict(lambda: {'roads': [], 'coverage_types': defaultdict(int)})

    print("Шаг 3: Расчет пересечений и привязка пешеходных дорог (Макс. пересечение)...")

    roads_in_hexes = hex_gdf.sjoin(roads_gdf, how="inner", predicate='intersects')
    unique_roads = roads_in_hexes.groupby('edge_id')

    total_to_process = len(unique_roads)

    print(f"Осталось обработать: {total_to_process:,} пешеходных дорог, пересекающих гексы.")

    grouped_iterator = tqdm(unique_roads, desc="Анализ пересечений дорог")

    for edge_id, group in grouped_iterator:

        max_intersection_length = -1
        best_hex_id = None
        coverage_type = str(group['coverage_type_nm'].iloc[0])

        road_geometry = roads_gdf[roads_gdf['edge_id'] == edge_id]['geometry'].iloc[0]

        for _, row in group.iterrows():
            hex_id = row['hex_id']
            hex_polygon = hex_gdf[hex_gdf['hex_id'] == hex_id]['geometry'].iloc[0]

            intersection = road_geometry.intersection(hex_polygon)
            current_length = intersection.length

            if current_length > max_intersection_length:
                max_intersection_length = current_length
                best_hex_id = hex_id

        if best_hex_id:
            final_hex_pedestrian_data[best_hex_id]['roads'].append(edge_id)
            final_hex_pedestrian_data[best_hex_id]['coverage_types'][coverage_type] += 1

    print(f"Шаг 3 завершен. Привязано {len(final_hex_pedestrian_data):,} гексов.")

    print("Шаг 4: Агрегация результатов и обновление JSON...")

    for hex_id in tqdm(hex_data.keys(), total=len(hex_data), desc="Обновление гексов"):

        pedestrian_data = final_hex_pedestrian_data[hex_id]

        roads_count = len(pedestrian_data['roads'])

        if roads_count > 0:
            hex_data[hex_id]['pedestrian_roads_count'] = roads_count

            coverage_counts = pedestrian_data['coverage_types']
            dominant_type = max(coverage_counts, key=coverage_counts.get)
            hex_data[hex_id]['dominant_coverage_type'] = dominant_type
        else:
            hex_data[hex_id]['pedestrian_roads_count'] = 0
            hex_data[hex_id]['dominant_coverage_type'] = "None"

    return hex_data


if __name__ == '__main__':
    start_time = time.time()

    hex_data = load_hex_data(INPUT_HEX_JSON_FILE)
    pedestrian_gdf = preprocess_pedestrian_data(INPUT_PEDESTRIAN_CSV_FILE)

    if hex_data and pedestrian_gdf is not None:
        final_data = process_pedestrian_to_hexagons(hex_data, pedestrian_gdf)

        try:
            with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)

            end_time = time.time()
            print(f"ФИНАЛЬНЫЙ АНАЛИЗ ЗАВЕРШЕН.")
            print(f"Результат сохранен в '{OUTPUT_JSON_FILE}'.")
            print(f"Общее время выполнения: {end_time - start_time:.2f} секунд.")
        except Exception as e:
            print(f"ОШИБКА при сохранении финального JSON: {e}")
    else:
        print("Процесс остановлен из-за критических ошибок при загрузке данных.")
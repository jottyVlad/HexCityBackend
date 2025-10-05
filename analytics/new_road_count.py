import json
import pandas as pd
from shapely.geometry import Polygon
from shapely.wkt import loads as wkt_loads
from geopandas import GeoDataFrame
from tqdm import tqdm
from collections import defaultdict
import warnings
import time
import os
from typing import Dict, Optional


warnings.filterwarnings("ignore")

INPUT_HEX_JSON_FILE = 'moscow_hexagons2.json'
ROADS_CSV_FILE = 'auto_graph_2gis_optimized.csv'
OUTPUT_JSON_FILE = 'moscow_hexagons_with_roads_DOWNSAMPLE_2.json'
AUTOSAVE_FILE = 'moscow_hex_autosave_singlethread.json'
AUTOSAVE_INTERVAL = 50000

CSV_ENCODINGS_TO_TRY = ['utf-8', 'cp1251', 'latin1']
DOWNSAMPLE_N = 6


def load_hex_data(file_path: str) -> Optional[Dict]:
    print(f"Шаг 1: Загрузка существующей сетки гексов из '{file_path}'")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            hex_data = json.load(f)
        print(f"Успешно загружено {len(hex_data)} гексов.")
        return hex_data
    except FileNotFoundError:
        print(f"ОШИБКА: Файл гексов '{file_path}' не найден.")
        return None
    except Exception as e:
        print(f"Ошибка при чтении JSON: {e}")
        return None


def save_autosave_data(data: Dict, file_path: str):
    temp_data = {}
    for hid, val in data.items():
        temp_data[hid] = {"roads": val['roads'], "type_road": dict(val['types'])}

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(temp_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ОШИБКА АВТОСОХРАНЕНИЯ: {e}")


def process_roads_to_hexagons(hex_data: Dict, roads_file: str) -> Dict:
    if hex_data is None:
        return {}

    roads_df = None

    print(f"Шаг 2: Загрузка и подготовка данных о дорогах из '{roads_file}' (Downsample N={DOWNSAMPLE_N})")

    for enc in CSV_ENCODINGS_TO_TRY:
        try:
            roads_df = pd.read_csv(
                roads_file,
                usecols=['edge_id', 'geometry', 'road_type_cd'],
                sep=';',
                dtype={'geometry': object},
                encoding=enc
            )
            print(f"Успешно прочитано с кодировкой: {enc}. Всего строк: {len(roads_df):,}.")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Критическая ошибка при чтении CSV: {e}")
            return hex_data

    if roads_df is None:
        print("ОШИБКА: Не удалось прочитать CSV файл ни с одной из предложенных кодировок.")
        return hex_data

    if DOWNSAMPLE_N > 1:
        roads_df = roads_df.iloc[::DOWNSAMPLE_N].copy()
        print(f"Применена фильтрация: оставлено {len(roads_df):,} дорог (каждая {DOWNSAMPLE_N}-я).")

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

    roads_gdf = GeoDataFrame(roads_df, geometry='geometry', crs="EPSG:4326")
    processed_roads_count = len(roads_gdf)

    print(f"Успешно обработано {processed_roads_count:,} корректных дорожных сегментов.")

    if processed_roads_count == 0:
        print("АНАЛИЗ ПРЕКРАЩЕН.")
        return hex_data

    print("Подготовка гексагональной сетки для геопространственного анализа...")

    hex_list = []
    for hex_id, data in hex_data.items():
        data['roads'] = []
        data['type_road'] = defaultdict(int)

        hex_polygon = Polygon(data['peaks'])
        hex_list.append({'hex_id': hex_id, 'geometry': hex_polygon})

    hex_gdf = GeoDataFrame(hex_list, geometry='geometry', crs="EPSG:4326")

    final_hex_road_data = defaultdict(lambda: {'roads': [], 'types': defaultdict(int)})
    processed_edges = set()
    initial_processed_count = 0

    if os.path.exists(AUTOSAVE_FILE):
        try:
            with open(AUTOSAVE_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            print(f"Найден файл автосохранения: подгружено {len(saved):,} гексов.")
            for hid, val in saved.items():
                final_hex_road_data[hid]['roads'].extend(val.get('roads', []))
                for t, c in val.get('type_road', {}).items():
                    final_hex_road_data[hid]['types'][t] += c
                for e in val.get('roads', []):
                    processed_edges.add(e)
            initial_processed_count = len(processed_edges)
            print(f"Восстановлено {initial_processed_count:,} уже обработанных дорог. Будем пропускать их.")
        except Exception as e:
            print(f"Ошибка при чтении автосохранения: {e}. Начинаю с чистого листа.")

    print("Шаг 3: Расчет пересечений и привязка дорог...")

    roads_to_process_gdf = roads_gdf[~roads_gdf['edge_id'].isin(processed_edges)]

    roads_in_hexes = hex_gdf.sjoin(roads_to_process_gdf, how="inner", predicate='intersects')

    unique_roads = roads_in_hexes.groupby('edge_id')

    total_to_process = len(unique_roads)
    processed_counter = 0

    print(f"Осталось обработать: {total_to_process:,} дорог.")

    grouped_iterator = tqdm(unique_roads, desc="Анализ пересечений дорог")

    for edge_id, group in grouped_iterator:

        max_intersection_length = -1
        best_hex_id = None
        road_type_cd = str(group['road_type_cd'].iloc[0])

        road_geometry = roads_to_process_gdf[roads_to_process_gdf['edge_id'] == edge_id]['geometry'].iloc[0]

        for _, row in group.iterrows():
            hex_id = row['hex_id']
            hex_polygon = hex_gdf[hex_gdf['hex_id'] == hex_id]['geometry'].iloc[0]

            intersection = road_geometry.intersection(hex_polygon)
            current_length = intersection.length

            if current_length > max_intersection_length:
                max_intersection_length = current_length
                best_hex_id = hex_id

        if best_hex_id:
            final_hex_road_data[best_hex_id]['roads'].append(edge_id)
            final_hex_road_data[best_hex_id]['types'][road_type_cd] += 1

        processed_counter += 1
        if processed_counter % AUTOSAVE_INTERVAL == 0:
            save_autosave_data(final_hex_road_data, AUTOSAVE_FILE)
            grouped_iterator.set_postfix_str(f"SAVED {processed_counter:,}/{total_to_process:,}")

    save_autosave_data(final_hex_road_data, AUTOSAVE_FILE)

    final_processed_count = initial_processed_count + processed_counter
    print(f"Шаг 3 завершен. Обработано {final_processed_count:,} уникальных дорог.")
    print("Шаг 4: Форматирование итоговой JSON-структуры...")
    for hex_id, road_data in final_hex_road_data.items():
        if hex_id in hex_data:
            hex_data[hex_id]['roads'] = list(set(road_data['roads']))
            hex_data[hex_id]['type_road'] = dict(road_data['types'])

    return hex_data


if __name__ == '__main__':
    start_time = time.time()

    hex_data = load_hex_data(INPUT_HEX_JSON_FILE)

    if hex_data:
        final_data = process_roads_to_hexagons(hex_data, ROADS_CSV_FILE)

        try:
            with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)

            if os.path.exists(AUTOSAVE_FILE):
                os.remove(AUTOSAVE_FILE)

            end_time = time.time()
            print(f"Результат сохранен в '{OUTPUT_JSON_FILE}'.")
            print(f"Общее время выполнения: {end_time - start_time:.2f} секунд.")
        except Exception as e:
            print(f"ОШИБКА при сохранении финального JSON: {e}")
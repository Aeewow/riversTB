import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import geopandas as gpd
from shapely.geometry import Point, LineString
import json
import glob
import os
from geopy.distance import geodesic

def load_and_prepare_data():
    json_files = glob.glob("buildsKirovsk_json/*.json")
    data_list = []
    
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
                if 'result' in json_data and 'items' in json_data['result']:
                    for item in json_data['result']['items']:
                        if 'address' in item and 'components' in item['address'] and 'geometry' in item:
                            street = None
                            house_number = None
                            for component in item['address']['components']:
                                if 'street' in component:
                                    street = component['street']
                                if 'number' in component:
                                    house_number = component['number']
                            
                            if street and house_number and 'centroid' in item['geometry']:
                                centroid = item['geometry']['centroid']
                                coords = centroid.replace('POINT(', '').replace(')', '').split()
                                if len(coords) == 2:
                                    lon, lat = map(float, coords)
                                    # Проверка на корректность координат
                                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                                        data_list.append({
                                            'Улица': street,
                                            'Номер дома': house_number,
                                            'Широта': lat,
                                            'Долгота': lon,
                                            'cluster': 0
                                        })
                                    else:
                                        print(f"Invalid coordinates for {street} {house_number}")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error processing file {file}: {str(e)}")
                continue
    
    if not data_list:
        raise ValueError("No building data found in JSON files")
    
    df = pd.DataFrame(data_list)
    required_columns = ['Широта', 'Долгота']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns: {', '.join(missing_columns)}")
    
    df = df.dropna(subset=['Широта', 'Долгота'])
    
    if len(df) == 0:
        raise ValueError("No valid building data after filtering")

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['Долгота'], df['Широта']),
        crs="EPSG:4326"
    )

    return df, gdf

def save_coordinates(selected_streets=None):
    df, _ = load_and_prepare_data()
    
    if selected_streets:
        df = df[df['Улица'].isin(selected_streets)].copy()
        if len(df) == 0:
            print("No buildings found for selected streets")
            return None
    
    df['cluster'] = 0
    df.to_csv('clustered_buildings.csv', index=False, encoding='utf-8')
    print("Coordinates successfully written to clustered_buildings.csv")
    
    return df

def load_street_network():
    streets = gpd.read_file("Иркутск_Модель_Граф/Сеть_link.shp", encoding='cp1251')
    nodes = gpd.read_file("Иркутск_Модель_Граф/Сеть_node.shp", encoding='cp1251')
    return streets, nodes

def find_nearest_street(point, streets):
    point_geom = Point(point['Долгота'], point['Широта'])
    distances = streets.geometry.distance(point_geom)
    return distances.idxmin()

def perform_clustering(selected_streets=None, eps_meters=200, street_multiplier=1.5, min_samples=5):
    """
    Кластеризация с учетом улиц через кастомную матрицу расстояний:
      - если здания на разных улицах, умножаем расстояние на street_multiplier
      - eps_meters — радиус для DBSCAN в метрах
      - min_samples — минимальное число точек для образования кластера
    """
    # 1. Загружаем исходные данные
    df, _ = load_and_prepare_data()

    # 2. Фильтруем, если указаны конкретные улицы
    if selected_streets:
        df = df[df['Улица'].isin(selected_streets)].copy()
        if df.empty:
            print("No buildings found for the selected streets.")
            return None

    df.reset_index(drop=True, inplace=True)

    # 3. Формируем матрицу расстояний (metric='precomputed')
    n_samples = len(df)
    distance_matrix = np.zeros((n_samples, n_samples))

    for i in range(n_samples):
        for j in range(i+1, n_samples):
            latlon_i = (df.loc[i, 'Широта'], df.loc[i, 'Долгота'])
            latlon_j = (df.loc[j, 'Широта'], df.loc[j, 'Долгота'])

            # Базовое географическое расстояние в метрах
            dist = geodesic(latlon_i, latlon_j).meters

            # Если улицы разные — умножаем на коэффициент
            if df.loc[i, 'Улица'] != df.loc[j, 'Улица']:
                dist *= street_multiplier

            distance_matrix[i, j] = dist
            distance_matrix[j, i] = dist

    # 4. Запуск DBSCAN с кастомной матрицей расстояний
    dbscan = DBSCAN(
        eps=eps_meters,
        min_samples=min_samples,
        metric='precomputed'
    )
    labels = dbscan.fit_predict(distance_matrix)
    df['cluster'] = labels

    # 5. Визуализация
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(
        df['Долгота'],
        df['Широта'],
        c=df['cluster'],
        cmap='viridis',
        marker='o',
        edgecolors='k'
    )
    plt.xlabel('Долгота')
    plt.ylabel('Широта')
    plt.title('Кластеризация зданий с учетом улиц (кастомная метрика)')
    plt.colorbar(scatter, label='Кластер')
    plt.show()

    # 6. Сохранение результата в папку clustered_buildings
    output_dir = 'clustered_buildings'
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'clustered_buildings.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Результаты кластеризации сохранены в: {output_file}")

    return df

if __name__ == '__main__':
    # Пример вызова без указания улиц (кластеризуем все)
    # Можно также передать список улиц: perform_clustering(['улица Ленина', 'улица Пушкина'], eps_meters=300, street_multiplier=2)
    perform_clustering()

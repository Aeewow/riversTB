import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import geopandas as gpd
from shapely.geometry import Point, LineString

def get_side_of_line(point: Point, line: LineString) -> str:
    """
    Возвращает 'left' или 'right' в зависимости от того,
    слева или справа находится точка относительно направления линии.
    """
    # 1) Находим расстояние вдоль линии (проекция точки на линию)
    dist_along_line = line.project(point)
    # 2) Вычисляем координаты "ближайшей" точки на линии
    point_on_line = line.interpolate(dist_along_line)

    # Чтобы понять «вектор направления» линии, возьмём небольшое смещение вдоль неё
    delta = 0.0001
    dist_next = dist_along_line + delta
    if dist_next > line.length:  # если вышли за пределы
        dist_next = dist_along_line - delta

    point_on_line_next = line.interpolate(dist_next)

    # Вектор вдоль линии
    v_line = np.array([
        point_on_line_next.x - point_on_line.x,
        point_on_line_next.y - point_on_line.y
    ])
    # Вектор от линии к нашей точке
    v_point = np.array([
        point.x - point_on_line.x,
        point.y - point_on_line.y
    ])

    # Псевдоскалярное произведение
    cross_prod = np.cross(v_line, v_point)

    return "left" if cross_prod > 0 else "right"

def cluster_dbscan(geo_df, eps=0.2, min_samples=5):
    if len(geo_df) == 0:
        geo_df["cluster"] = -1
        return geo_df

    coords = np.array([(pt.x, pt.y) for pt in geo_df.geometry])
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords)
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(coords_scaled)
    geo_df["cluster"] = labels
    return geo_df

def load_and_prepare_data():
    # Загрузка Excel с данными
    df = pd.read_excel("data2.xlsx")
    df = df.dropna(subset=['Широта', 'Долгота'])

    # Загрузка реки из GeoJSON
    river_gdf = gpd.read_file("riverMAin.json")
    river_line = river_gdf.geometry.iloc[0]

    # Создание GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['Широта'], df['Долгота']),
        crs="EPSG:4326"
    )

    # Определение стороны реки
    gdf["side"] = gdf.geometry.apply(lambda p: get_side_of_line(p, river_line))

    return df, gdf, river_line

def perform_clustering(selected_streets=None):
    # Загрузка и подготовка данных
    df, gdf, river_line = load_and_prepare_data()

    # Фильтрация по выбранным улицам
    if selected_streets:
        gdf = gdf[gdf['Улица'].isin(selected_streets)].copy()
        if len(gdf) == 0:
            print("No buildings found for selected streets.")
            return

    # Разделение на левый и правый берег
    left_points = gdf[gdf["side"] == "left"].copy()
    right_points = gdf[gdf["side"] == "right"].copy()

    # Кластеризация
    left_clustered = cluster_dbscan(left_points, eps=0.2, min_samples=5)
    right_clustered = cluster_dbscan(right_points, eps=0.2, min_samples=5)

    # Объединение результатов
    all_clustered = pd.concat([left_clustered, right_clustered]).sort_index()

    # Сохранение результатов
    result_df = all_clustered[['Широта', 'Долгота', 'Кластер']]
    result_df.to_csv('clustered_buildings.csv', sep=';', index=False)

    print("Clustering completed and saved to clustered_buildings.csv.")
    return result_df

if __name__ == '__main__':
    # Этот код будет выполняться только при прямом запуске файла
    df = perform_clustering()
    
    # Визуализация
    plt.figure(figsize=(10, 6))
    plt.scatter(
        df['Широта'],
        df['Долгота'],
        c=df['cluster'],
        cmap='viridis',
        marker='o',
        edgecolors='k'
    )
    plt.xlabel('Широта')
    plt.ylabel('Долгота')
    plt.title('Кластеризация с учётом разделения реки (DBSCAN)')
    plt.colorbar(label='Кластер')
    plt.show()

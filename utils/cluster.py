# -*- coding:utf-8 -*-
# @FileName  :cluster.py
# @Time      :2023/5/5 15:36
# @Author    :Jian
from geopy.distance import distance as sphere_distance
import pandas as pd


def clustering_algorithm(example_data, threshold_distance, min_point):
    # 判断是否统计停留时间
    time_col = 'gnss_time' in example_data.columns
    # 计算点间距离
    distances = []
    for i in range(len(example_data) - 1):
        coord1 = (example_data.iloc[i]['latitude'], example_data.iloc[i]['longitude'])
        coord2 = (example_data.iloc[i + 1]['latitude'], example_data.iloc[i + 1]['longitude'])
        distances.append(sphere_distance(coord1, coord2).km)

    # 把距离添加到DataFrame中
    example_data['distance'] = [0] + distances

    # 定义一个空的DataFrame，用于存储聚类后的数据
    clustered = pd.DataFrame(columns=['latitude', 'longitude', 'distance', 'cluster_id'])

    # 初始化聚类id和距离
    cluster_id = 1
    time_span = []
    # 遍历数据中的每个点
    for i in range(len(example_data)):
        current_point = example_data.iloc[i]

        # 如果是第一个点，则直接将其加入聚类中
        if i == 0:
            clustered.loc[0] = [current_point['latitude'], current_point['longitude'], current_point['distance'],
                                cluster_id]
            if time_col:
                start_time = current_point['gnss_time']
            continue

        # 计算当前点和上一个点之间的距离
        distance = current_point['distance']

        # 获取当前点和同一类别中的其他点之间的距离的最大值 太耗时了，暂时不考虑这样做
        # distance =calculate_max_distance(current_point['latitude'], current_point['longitude'], clustered.loc[clustered['cluster_id'] == cluster_id])

        # 如果当前点和上一个点之间的距离小于阈值，则将其加入当前聚类中
        if distance < threshold_distance:
            clustered.loc[len(clustered)] = [current_point['latitude'], current_point['longitude'],
                                             current_point['distance'], cluster_id]
        else:
            # 如果当前点和上一个点之间的距离大于阈值，则将其作为新的聚类的第一个点
            cluster_id += 1
            clustered.loc[len(clustered)] = [current_point['latitude'], current_point['longitude'],
                                             current_point['distance'], cluster_id]
            if time_col:
                time_span.append(f'{start_time}-{current_point["gnss_time"]}')
                start_time = current_point['gnss_time']

        if (i == len(example_data) - 1) and (distance < threshold_distance) and time_col:
            time_span.append(f'{start_time}-{current_point["gnss_time"]}')

    # 使用value_counts()方法计算每个cluster_id出现的次数
    counts = clustered['cluster_id'].value_counts()

    # 选择出现次数大于三的cluster_id
    cluster_ids = counts.loc[counts > min_point].index

    # 筛选出cluster_id在cluster_ids中的数据
    cluster_over_3 = clustered.loc[clustered['cluster_id'].isin(cluster_ids)]

    # 使用groupby()方法按照cluster_id对DataFrame进行分组，并计算每个分组的平均值
    cluster_means = cluster_over_3.groupby('cluster_id')[['longitude', 'latitude']].mean()

    cluster_means['gps_num'] = counts[cluster_ids].sort_index()

    if time_col:
        cluster_means['time_span'] = [time_span[int(i) - 1] for i in list(map(int, cluster_means.index.tolist()))]

    return cluster_means.reset_index()

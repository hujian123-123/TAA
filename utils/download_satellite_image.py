# -*- coding:utf-8 -*-
# @FileName  :download_satellite_image.py
# @Time      :2023/5/5 21:27
# @Author    :Jian

import requests
import math

# 用 ArcGIS REST API 导出地图图像
url = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export"
headers = {
    "Referer": "https://www.arcgis.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
}


# 下载聚类点卫星图像
def download_one_img(center_lon, center_lat, idx, save_path, scale):
    width = 150*(scale/0.08)
    height = 150*(scale/0.08)
    try_num = 0
    # print(scale)
    while try_num < 2:
        params = {
            "bbox": f"{center_lon - 0.01 * scale},{center_lat - 0.01 * scale},{center_lon + 0.01 * scale},{center_lat + 0.01 * scale}",
            "size": f"{width},{height}",
            "format": "png",
            "bboxSR": "4326",
            "imageSR": "3857",
            "f": "image",
            "dpi": "300",
            "transparent": "true",
            "layers": "show:0",
            "scale": scale,
        }
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            break
        else:
            scale += 0.02
            try_num += 1

    # 将响应的二进制数据保存到本地文件
    with open(f"{save_path}/image_{idx}.png", "wb") as f:
        f.write(response.content)


def download_satellite_img(cluster_data, save_path):
    # 批量下载卫星图像
    for idx, row in cluster_data.iterrows():
        download_one_img(row['longitude'], row['latitude'], idx, save_path)


x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def gcj02towgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False

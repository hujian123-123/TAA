import os
import base64
import shutil

import pyproj as pyproj
import streamlit as st
import pandas as pd
import folium
from IPython.display import HTML
from streamlit_folium import folium_static
import uuid

from utils import clustering_algorithm, download_satellite_img, identify_gps_point, download_one_img,gcj02towgs84

#######################################################

# The code below is to control the layout width of the app.
if "widen" not in st.session_state:
    layout = "centered"
else:
    layout = "wide" if st.session_state.widen else "centered"

#######################################################

# The code below is for the title and logo.
st.set_page_config(layout=layout, page_title="Truck trajectory data analysis", page_icon="🚛")

#######################################################

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

# Get user ID
user_id = st.session_state['user_id']
# 隔离不同用户的数据和卫星图像
# Create directory for user
user_dir = os.path.join('./images', user_id)
os.makedirs(user_dir, exist_ok=True)
# st.write(user_dir)
scale_dict = {'Small':0.05,'Medium':0.08,'Big':0.2}

#######################################################
# 创建 Streamlit 应用程序并添加文件上传器
st.title("🚛 Truck activity identification")

with st.expander('🔋 About this app '):
    st.write('🌍 Identifying truck activity from GPS data based on satellite imagery ')

with st.expander('🎈 Our advantages '):
    st.markdown("""
    <div style="display: flex; justify-content: space-between;">
        <div style="text-align: center;"><b> 🤖 Only use GPS data</b></div>
        <div style="text-align: center;"><b> ⚡ Real time</b></div>
        <div style="text-align: center;"><b> 🛠️ Extensible</b></div>
    </div>
    """, unsafe_allow_html=True)
#######################################################
# 输入参数
col1, col2,col3,col4 = st.columns([1, 1, 1,1])

with col1:
    threshold_distance = st.selectbox(
        'Threshold distance (m)',
        (10, 100, 250),
        index=1)

with col2:
    min_point = st.selectbox(
        'Min stop GPS point num',
        (3, 10, 20),
        index=0)
with col3:
    gps_coordinate = st.selectbox(
        'GPS geographic coordinate',
        ('GCJ-02', 'WGS-84'),
        index=1)
with col4:
    satellite_image_scale = st.selectbox(
        'satellite_image_size',
        ('Small', 'Medium','Big'),
        index=1)
#######################################################

#######################################################
# 显示复选框和按钮
# col1, col2 = st.columns(2)
# # 刷新获取卫星图像
# toggle = col1.checkbox('Download satellite image', True)
# # 添加一个按钮来清空目录
# if col2.button('Clear satellite directory'):
#     shutil.rmtree('./images')
#     os.makedirs('./images')
#     st.success('Directory cleared.')

#######################################################


#######################################################
# 上传文件
file = st.file_uploader("📄 Upload truck trajectory data file(with longitude and latitude)  ", type="csv")

# 如果上传了文件，则读取文件并更新地图
if file is not None:
    # 读取 CSV 文件并提取经纬度信息
    data = pd.read_csv(file)
    # 上传数据列名检验
    columns_check = ('longitude' in data.columns) and ('latitude' in data.columns)
    if not columns_check:
        st.warning('Please upload data including GPS longitude and latitude', icon="⚠️")

    # 上传数据坐标系转换
    if gps_coordinate == 'GCJ-02':
        data['location_wgs'] = [gcj02towgs84(i, j) for i, j in
                                       list(zip(data['longitude'].values, data['latitude'].values))]
        data['longitude'] = data.location_wgs.apply(lambda x: x[0])
        data['latitude'] = data.location_wgs.apply(lambda x: x[1])

    # 展示前五行数据
    st.table(data.head())
    # 聚类结果
    clustering_reslut = clustering_algorithm(data, threshold_distance=threshold_distance / 1000, min_point=min_point)

    # 进度条
    progress_text = "Operation in progress. Please wait."
    progress_bar = st.progress(0)
    # 下载对应的卫星图像
    # if toggle:
    for idx, row in clustering_reslut.iterrows():
        progress_bar.progress(int(1 / len(clustering_reslut) * 100)*(idx+1),text=progress_text)
        if idx == len(clustering_reslut)-1:
            progress_bar.progress(100)
        download_one_img(row['longitude'], row['latitude'], idx, user_dir,scale=scale_dict[satellite_image_scale])

    # 识别点的类型
    identify_result = identify_gps_point(clustering_reslut, user_dir)

    # 聚类结果
    st.subheader(f'Dwell point num: {len(clustering_reslut)}')

    st.table(clustering_reslut.head())

    # 识别结果
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f'LU point num:{len(identify_result.loc[identify_result["label"] == 1])}')

    with col2:
        st.subheader(f'Resting point num:{len(identify_result.loc[identify_result["label"] == 0])}')

    # 全部点
    latitudes = data["latitude"].tolist()
    longitudes = data["longitude"].tolist()

    # 创建地图并添加轨迹
    m = folium.Map(location=[sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)], zoom_start=12)

    for lat, lon in zip(latitudes, longitudes):
        folium.CircleMarker(location=[lat, lon], radius=0.2, color='lightgreen', fill=True, fill_opacity=0.5).add_to(m)

    marker_color = ['orange', 'red', 'green']
    # 添加识别结果
    for idx, row in identify_result.iterrows():
        # 创建标记
        marker = folium.Marker(location=[row['latitude'], row['longitude']],
                               icon=folium.Icon(color=marker_color[row['label']], icon='info-sign'))

        with open(row["img_path"], "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()

        # 创建Popup
        popup_html = f'GPS point num: {row["gps_num"]}<br> <img src="data:image/png;base64,{encoded_string}" width="120">'
        popup = folium.Popup(popup_html, max_width=120)
        # 将Popup添加到标记上
        popup.add_to(marker)
        # 将标记添加到地图上
        marker.add_to(m)

    # 更换为其他卫星图层
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                     name='ESRI World Imagery', attr='ESRI World Imagery').add_to(m)

    # m.save(r'./files/index.html')
    # 将更新后的地图嵌入到应用程序中
    folium_static(m)

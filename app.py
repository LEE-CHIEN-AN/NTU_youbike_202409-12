import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd

# 載入資料
stats_df = pd.read_csv("hourly_station_availability.csv")
sites_df = pd.read_excel("要撈的站點.xlsx", header=None)
sites_df.columns = ["index", "sno", "sna", "sarea", "latitude", "longitude", "ar", "sareaen", "aren", "act"]
sites_df = sites_df.drop(columns=["index"])

# 合併統計與站點地理資訊
merged_df = pd.merge(stats_df, sites_df, on="sno")

# Streamlit 網頁設定
st.set_page_config(page_title="YouBike 站點統計地圖", layout="wide")
st.title("🚲 YouBike 2024 09/01到12/25 各站點小時統計地圖")

# 使用者選擇小時與站點（可複選）
hour = st.selectbox("請選擇要查看的時段 (24hr)", list(range(24)), index=8)
station_options = sites_df[['sno', 'sna']].drop_duplicates().sort_values('sna')
station_names = station_options['sna'].tolist()
selected_stations = st.multiselect("選擇要顯示的站點（可複選）", station_names, default=station_names[:5])

# 篩選資料
filtered_df = merged_df[(merged_df['hour'] == hour) & (merged_df['sna'].isin(selected_stations))]

# 建立 Folium 地圖
def create_map(data):
    m = folium.Map(location=[25.014, 121.535], zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in data.iterrows():
        popup_text = f"""
        <b>{row['sna']}</b><br>
        行政區: {row['sarea']}<br>
        地址: {row['ar']}<br>
        <hr>
        <b>{hour}:00 - {hour+1}:00</b><br>
        可借車輛數: {row['avg_available_rent_bike']:.2f}<br>
        可還車輛數: {row['avg_available_return_bike']:.2f}<br>
        可借機率: {row['avg_available_rent_ratio']:.2%}<br>
        可還機率: {row['avg_available_return_ratio']:.2%}
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
        ).add_to(marker_cluster)

    return m

# 顯示地圖
st_data = st_folium(create_map(filtered_df), width=1000, height=700)

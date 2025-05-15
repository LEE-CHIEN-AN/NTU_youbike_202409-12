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
st.title("🚲 YouBike 各站點小時統計地圖")

# 使用者選擇地圖顯示用的小時（可複選）
hour = st.selectbox("請選擇要查看的時段 (24hr)", list(range(24)), index=8)
station_options = sites_df[['sno', 'sna']].drop_duplicates().sort_values('sna')


# 篩選資料
filtered_df = merged_df[(merged_df['hour'] == hour))]

# 建立 Folium 地圖（僅顯示地點標記，不含統計）
def create_map(data):
    m = folium.Map(location=[25.014, 121.535], zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in data.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row['sna'],
            icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
        ).add_to(marker_cluster)

    return m

# 顯示地圖
st_data = st_folium(create_map(filtered_df), width=1000, height=700)

# 額外統計區塊（用下拉選單選小時與多站點）
st.subheader("📋 站點統計資料表")
stat_hour = st.selectbox("選擇統計資料時段 (24hr)", list(range(24)), index=8, key="table_hour")
stat_stations = st.multiselect("選擇要顯示在表格的站點（可複選）", station_names, default=station_names[:5], key="table_stations")

# 篩選表格資料
stat_df = merged_df[(merged_df['hour'] == stat_hour) & (merged_df['sna'].isin(stat_stations))]

# 顯示統計資料表格
st.dataframe(
    stat_df[[
        "sna", "sarea", "avg_available_rent_bike", "avg_available_return_bike",
        "avg_available_rent_ratio", "avg_available_return_ratio"
    ]].rename(columns={
        "sna": "站點名稱",
        "sarea": "行政區",
        "avg_available_rent_bike": "可借車輛數",
        "avg_available_return_bike": "可還車輛數",
        "avg_available_rent_ratio": "可借機率",
        "avg_available_return_ratio": "可還機率"
    }),
    use_container_width=True
)

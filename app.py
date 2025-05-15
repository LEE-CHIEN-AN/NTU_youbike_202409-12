import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 使用思源黑體或其他支援中文字體
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft JhengHei', 'Arial Unicode MS', 'Heiti TC', 'Noto Sans CJK TC']
plt.rcParams['axes.unicode_minus'] = False  # 正常顯示負號


# 載入資料
stats_df = pd.read_csv("hourly_station_availability.csv")
sites_df = pd.read_excel("要撈的站點.xlsx", header=None)
sites_df.columns = ["index", "sno", "sna", "sarea", "latitude", "longitude", "ar", "sareaen", "aren", "act"]
sites_df = sites_df.drop(columns=["index"])

# 合併統計與站點地理資訊
merged_df = pd.merge(stats_df, sites_df, on="sno")

# Streamlit 網頁設定
st.set_page_config(page_title="YouBike 站點統計地圖", layout="wide")
st.title("🚲 YouBike 2024 9/1 - 12/25 台大各站點小時統計地圖")

# 選單：選擇小時
hour = st.selectbox("請選擇要查看的時段 (24hr)", list(range(24)), index=8)

# 建立 Folium 地圖
def create_map(hour):
    m = folium.Map(location=[25.014, 121.535], zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)

    hour_data = merged_df[merged_df['hour'] == hour]

    for _, row in hour_data.iterrows():
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
st_data = st_folium(create_map(hour), width=1000, height=700)

# 折線圖區塊：選擇站點顯示 24 小時統計趨勢
st.subheader("📈 選擇站點顯示 24 小時統計折線圖")
station_names = sites_df[['sno', 'sna']].drop_duplicates().sort_values('sna')['sna'].tolist()
selected_sna = st.selectbox("請選擇一個站點", station_names)

station_hourly = merged_df[merged_df['sna'] == selected_sna].sort_values("hour")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(station_hourly['hour'], station_hourly['avg_available_rent_bike'], label="Rentable Bikes")
ax.plot(station_hourly['hour'], station_hourly['avg_available_return_bike'], label="Returnable Bikes")
ax.set_xticks(range(24))
ax.set_xlabel("Hour")
ax.set_ylabel("Bike Count")
ax.set_title(f"{selected_sna} Hourly Availability")
ax.legend()
ax.grid(True)
st.pyplot(fig)

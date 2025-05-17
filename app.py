import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime

# Set up matplotlib to avoid Chinese font errors
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Load data
stats_df = pd.read_csv("hourly_station_availability.csv")
sites_df = pd.read_excel("要撈的站點.xlsx", header=None)
sites_df.columns = ["index", "sno", "sna", "sarea", "latitude", "longitude", "ar", "sareaen", "aren", "act"]
sites_df = sites_df.drop(columns=["index"])

# Merge data
merged_df = pd.merge(stats_df, sites_df, on="sno")

# Streamlit page setup
st.set_page_config(page_title="YouBike Station Dashboard",layout="centered")
st.title("🚲 NTU History YouBike Station Dashboard 台大 YouBike 歷史紀錄 車站儀表板  24/09/01-24/12/25")

# Page selector
page = st.sidebar.radio("Choose a view:", ["Map View 地圖", "Hourly Line Chart 每小時折線圖", "Current vs Stats 目前的 vs 統計資料"])

if page == "Map View 地圖":
    st.header("🗺️ Station Map with Hourly Stats")
    # 選單：選擇小時
    hour = st.selectbox(
        "請選擇要查看的時段",
        [f"{h}:00 - {h+1}:00" for h in range(24)],
        index=8
    )
    hour = int(hour.split(":")[0])

    def create_map(hour):
        m = folium.Map(location=[25.014, 121.535], zoom_start=15)
        marker_cluster = MarkerCluster().add_to(m)
        hour_data = merged_df[merged_df['hour'] == hour]

        for _, row in hour_data.iterrows():
            popup_text = f"""
            <b>{row['sna']}</b><br>
            District 行政區: {row['sarea']}<br>
            Address 地址: {row['ar']}<br>
            <b>{hour}:00 - {hour+1}:00</b><br>
            Avg. Rentable Bikes 可借車數: {row['avg_available_rent_bike']:.2f}<br>
            Avg. Returnable Bikes 可還車數: {row['avg_available_return_bike']:.2f}<br>
            Rent Availability 可借機率: {row['avg_available_rent_ratio']:.2%}<br>
            Return Availability 可還機率: {row['avg_available_return_ratio']:.2%}
            """
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
            ).add_to(marker_cluster)
        return m
   
    st_data = st_folium(create_map(hour), height=450, use_container_width=True)

elif page == "Hourly Line Chart 每小時折線圖":
    st.header("📈 Hourly Trend for a Selected Station 選定車站的每小時趨勢")
    station_names = sites_df[['sno', 'sna']].drop_duplicates().sort_values('sna')['sna'].tolist()
    selected_sna = st.selectbox("Select a station", station_names)
    station_hourly = merged_df[merged_df['sna'] == selected_sna].sort_values("hour")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(station_hourly['hour'], station_hourly['avg_available_rent_bike'], label="Rentable Bikes")
    ax.plot(station_hourly['hour'], station_hourly['avg_available_return_bike'], label="Returnable Bikes")
    ax.set_xticks(range(24))
    ax.set_xlabel("Hour")
    ax.set_ylabel("Bike Count")
    ax.set_title(f"Hourly Availability")
    ax.legend()
    #ax.grid(True)
    st.pyplot(fig)

elif page == "Current vs Stats 目前的 vs 統計資料":
    st.header("📊 Real-Time vs Historical Hourly Statistics 即時 vs 歷史每小時統計資料")

    import pytz
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.datetime.now(tz)
    current_hour = now.hour

    api_url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    try:
        r = requests.get(api_url)
        realtime_df = pd.DataFrame(r.json())
        realtime_df["sno"] = pd.to_numeric(realtime_df["sno"], errors="coerce")
        realtime_df["latitude"] = pd.to_numeric(realtime_df["latitude"], errors="coerce")
        realtime_df["longitude"] = pd.to_numeric(realtime_df["longitude"], errors="coerce")

        # 地圖：顯示所有站點統計與即時資料
        st.markdown("點選地圖上任一站點，可查看即時與歷史每小時統計資料")
        stat_map = folium.Map(location=[25.014, 121.535], zoom_start=15)

        for _, site in sites_df.iterrows():
            try:
                lat = float(site['latitude'])
                lon = float(site['longitude'])
                site_id = site['sno']
                site_name = site['sna']
                site_area = site['sarea']
                site_address = site['ar']

                realtime_row = realtime_df[realtime_df['sno'] == site_id]
                stat_row = merged_df[(merged_df['sno'] == site_id) & (merged_df['hour'] == current_hour)]

                if realtime_row.empty or stat_row.empty:
                    continue

                realtime_row = realtime_row.iloc[0]
                stat_row = stat_row.iloc[0]

                popup_text = f"""
                <b>{site_name}</b><br>
                District 行政區: {site_area}<br>
                Address 地址: {site_address}<br>
                <hr>
                <b>{current_hour}:00 - {current_hour+1}:00</b><br>
                <b>Real-Time Data 即時資料:</b><br>
                可借車輛數: {realtime_row['available_rent_bikes']}<br>
                可還車輛數: {realtime_row['available_return_bikes']}<br>
                可借機率: {realtime_row['available_rent_bikes']/realtime_row['total']:.2%}<br>
                可還機率: {realtime_row['available_return_bikes']/realtime_row['total']:.2%}<br>
                <hr>
                <b>Historical Avg 歷史平均:</b><br>
                可借車輛數: {stat_row['avg_available_rent_bike']:.2f}<br>
                可還車輛數: {stat_row['avg_available_return_bike']:.2f}<br>
                可借機率: {stat_row['avg_available_rent_ratio']:.2%}<br>
                可還機率: {stat_row['avg_available_return_ratio']:.2%}
                """
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color='orange', icon='info-sign')
                ).add_to(stat_map)
            except Exception as marker_err:
                continue

        st_folium(stat_map, height=500, use_container_width=True)

    except Exception as e:
        st.error("Failed to fetch real-time data. Please try again later.")
        st.error(str(e))


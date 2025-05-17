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

        # 地圖 + 下拉式選單選擇站點
        st.markdown("請從地圖點選或下拉選單 **擇一方式** 選擇一個站點以比較即時與歷史資料")
        select_map = folium.Map(location=[25.014, 121.535], zoom_start=15)
        for _, row in sites_df.iterrows():
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                folium.Marker(
                    location=[lat, lon],
                    popup=row['sna'],
                    icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
                ).add_to(select_map)
            except:
                continue

        select_data = st_folium(select_map, height=450, use_container_width=True)

        # 下拉選單提供另一種選擇方式
        station_names = sites_df[['sno', 'sna']].drop_duplicates().sort_values('sna')
        dropdown_sna = st.selectbox("或從此處選擇站點：", station_names['sna'].tolist(), key="selectbox")

        selected_sna = None
        if select_data and select_data.get("last_object_clicked_popup"):
            selected_sna = select_data["last_object_clicked_popup"]
        else:
            selected_sna = dropdown_sna

        station_info = sites_df[sites_df['sna'] == selected_sna].iloc[0]
        station_id = station_info['sno']

        realtime_row = realtime_df[realtime_df['sno'] == station_id].iloc[0]
        stat_row = merged_df[(merged_df['sno'] == station_id) & (merged_df['hour'] == current_hour)].iloc[0]

        st.markdown(f"### ⏱️ {selected_sna} @ {current_hour}:00")
        st.write("**Real-time Data 即時資料:**")
        st.write(f"Current Rentable Bikes 目前可借車輛數: {realtime_row['available_rent_bikes']}")
        st.write(f"Current Returnable Slots 目前可還車輛數: {realtime_row['available_return_bikes']}")
        st.write(f"Rentable bike count rate  可借到車的機率 : {realtime_row['available_rent_bikes']/realtime_row['total']:.2%}")
        st.write(f"Returnable bike count rate 可還到車的機率: {realtime_row['available_return_bikes']/realtime_row['total']:.2%}")

        st.write("**Historical Average at This Hour:**")
        st.write(f"Avg. Rentable Bikes 歷史此小時平均可借車輛數: {stat_row['avg_available_rent_bike']:.2f}")
        st.write(f"Avg. Returnable Bikes 歷史此小時平均可還車輛數: {stat_row['avg_available_return_bike']:.2f}")
        st.write(f"Rentable bike count rate 可借到車的機率: {stat_row['avg_available_rent_ratio']:.2%}")
        st.write(f"Returnable bike count rate 可還到車的機率: {stat_row['avg_available_return_ratio']:.2%}")

    # 顯示地圖標記該站點
        st.subheader("📍 Map View of This Station 此站點的地圖檢視")
        realtime_map = folium.Map(location=[station_info['latitude'], station_info['longitude']], zoom_start=16)
        popup_text = f"""
        <b>{selected_sna}</b><br>
        District: {station_info['sarea']}<br>
        Address: {station_info['ar']}<br>
        <hr>
        <b>{current_hour}:00 - {current_hour+1}:00</b><br>
        Current Rentable Bikes: {realtime_row['available_rent_bikes']}<br>
        Current Returnable Slots: {realtime_row['available_return_bikes']}<br>
        Avg. Rentable Bikes: {stat_row['avg_available_rent_bike']:.2f}<br>
        Avg. Returnable Bikes: {stat_row['avg_available_return_bike']:.2f}
        """
        folium.Marker(
            location=[station_info['latitude'], station_info['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(realtime_map)

        st_folium(realtime_map,height=450, use_container_width=True)

    except Exception as e:
        st.error("Failed to fetch real-time data. Please try again later.")
        st.error(str(e))

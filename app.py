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
st.set_page_config(page_title="YouBike Station Dashboard", layout="wide")
st.title("🚲 YouBike Station Dashboard")

# Page selector
page = st.sidebar.radio("Choose a view:", ["Map View", "Hourly Line Chart", "Current API vs Stats"])

if page == "Map View":
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
            District: {row['sarea']}<br>
            Address: {row['ar']}<br>
            <hr>
            <b>{hour}:00 - {hour+1}:00</b><br>
            Avg. Rentable Bikes: {row['avg_available_rent_bike']:.2f}<br>
            Avg. Returnable Bikes: {row['avg_available_return_bike']:.2f}<br>
            Rent Availability: {row['avg_available_rent_ratio']:.2%}<br>
            Return Availability: {row['avg_available_return_ratio']:.2%}
            """
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
            ).add_to(marker_cluster)
        return m

    st_data = st_folium(create_map(hour), width=1000, height=700)

elif page == "Hourly Line Chart":
    st.header("📈 Hourly Trend for a Selected Station")
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

elif page == "Current API vs Stats":
    st.header("📊 Real-Time vs Historical Hourly Statistics")

    import pytz

    # 使用台灣時區取得目前小時
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.datetime.now(tz)
    current_hour = now.hour

  

    api_url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    try:
        r = requests.get(api_url)
        realtime_df = pd.DataFrame(r.json())
        realtime_df["sno"] = pd.to_numeric(realtime_df["sno"], errors="coerce")

        # 使用者選擇站點
        station_names = sites_df[['sno', 'sna']].drop_duplicates().sort_values('sna')
        selected_sna = st.selectbox("Select a station to compare", station_names['sna'].tolist(), key="compare")

        station_info = sites_df[sites_df['sna'] == selected_sna].iloc[0]
        station_id = station_info['sno']

        realtime_row = realtime_df[realtime_df['sno'] == station_id].iloc[0]
        stat_row = merged_df[(merged_df['sno'] == station_id) & (merged_df['hour'] == current_hour)].iloc[0]

        st.markdown(f"### ⏱️ {selected_sna} @ {current_hour}:00")
        st.write("**Real-time Data:**")
        st.write(f"Current Rentable Bikes: {realtime_row['available_rent_bikes']}")
        st.write(f"Current Returnable Slots: {realtime_row['available_return_bikes']}")

        st.write("**Historical Average at This Hour:**")
        st.write(f"Avg. Rentable Bikes: {stat_row['avg_available_rent_bike']:.2f}")
        st.write(f"Avg. Returnable Bikes: {stat_row['avg_available_return_bike']:.2f}")
        st.write(f"Rent Availability: {stat_row['avg_available_rent_ratio']:.2%}")
        st.write(f"Return Availability: {stat_row['avg_available_return_ratio']:.2%}")

    # 顯示地圖標記該站點
        st.subheader("📍 Map View of This Station")
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

        st_folium(realtime_map, width=700, height=450)

    except Exception as e:
        st.error("Failed to fetch real-time data. Please try again later.")
        st.error(str(e))

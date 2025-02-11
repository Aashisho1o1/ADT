import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timedelta
from geopy.distance import geodesic

# Configure page
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    page_icon="🌍",
    layout="wide"
)

# Add title with clear styling
st.title("🌍 Alumni Natural Disaster Monitor")
st.markdown("---")

def load_alumni_data():
    """Load and process alumni data from simplified CSV"""
    try:
        st.write("📂 Loading alumni data...")
        file_path = 'assets/simplified_alumni.csv'

        # Read CSV file
        df = pd.read_csv(file_path)

        total_records = len(df)
        st.success(f"✅ Successfully loaded {total_records} alumni records")

        # Show sample of data
        with st.expander("🔍 View Sample Data"):
            st.dataframe(
                df[['Name', 'Location', 'Latitude', 'Longitude']].head(),
                hide_index=True
            )

        return df

    except Exception as e:
        st.error(f"❌ Error loading alumni data: {str(e)}")
        return pd.DataFrame()

def fetch_disasters():
    """Fetch natural disaster data from EONET"""
    st.write("🌐 Fetching disaster data...")

    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    params = {
        "status": "open",
        "days": 7,
        "category": "wildfires,severeStorms,volcanoes,earthquakes"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('events', [])
            st.success(f"✅ Found {len(data)} disaster events")
            return data
        else:
            st.error(f"❌ API request failed with status code: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"❌ Error fetching disaster data: {str(e)}")
        return []

# Main application
try:
    # Load alumni data
    alumni_df = load_alumni_data()
    if alumni_df.empty:
        st.error("❌ No alumni data available")
        st.stop()

    # Fetch disaster data
    disasters = fetch_disasters()

    # Create map
    st.subheader("🗺️ Disaster Monitoring Map")
    st.info("🔵 Blue markers: Alumni locations | 🔴 Red markers: Natural disasters")

    # Initialize map centered on Pacific region to show both Japan and US
    m = folium.Map(
        location=[30.0, 180.0],
        zoom_start=3,
        tiles="OpenStreetMap"
    )

    # Add alumni markers
    for _, row in alumni_df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"Alumni: {row['Name']}<br>Location: {row['Location']}",
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.7
        ).add_to(m)

    # Display map and stats
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display map with explicit dimensions
        map_data = st_folium(
            m,
            width=800,
            height=600,
            returned_objects=["last_active_drawing"]
        )

    with col2:
        st.subheader("📊 Location Statistics")
        st.info(f"""
        Total Alumni: {len(alumni_df)}
        Countries Represented: {alumni_df['Country'].nunique()}
        States/Regions: {alumni_df['State'].nunique()}
        """)

        # Add disaster markers and track proximity
        alerts = []
        for disaster in disasters:
            try:
                coords = disaster['geometry'][0]['coordinates']
                lat, lon = coords[1], coords[0]

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=15,
                    popup=f"Disaster: {disaster['title']}",
                    color='red',
                    fill=True,
                    fill_opacity=0.7
                ).add_to(m)

                # Check proximity to alumni
                for _, alumni in alumni_df.iterrows():
                    distance = int(geodesic(
                        (alumni['Latitude'], alumni['Longitude']),
                        (lat, lon)
                    ).kilometers)

                    if distance <= 500:  # Alert for disasters within 500km
                        alerts.append({
                            'alumni': alumni['Name'],
                            'disaster': disaster['title'],
                            'distance': distance
                        })

            except Exception as e:
                st.warning(f"⚠️ Error processing disaster: {str(e)}")
                continue

        # Show proximity alerts
        st.subheader("⚠️ Proximity Alerts")
        if alerts:
            for alert in sorted(alerts, key=lambda x: x['distance']):
                st.warning(
                    f"🚨 {alert['alumni']} is {alert['distance']}km "
                    f"from {alert['disaster']}"
                )
        else:
            st.info("✅ No alerts within 500km")

except Exception as e:
    st.error(f"❌ Application error: {str(e)}")
    st.write("Please check the error message above and try again.")
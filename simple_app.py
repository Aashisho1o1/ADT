import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timedelta
import chardet

# Configure page
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    layout="wide"
)

# Add title with clear styling
st.title("🌍 Alumni Natural Disaster Monitor")
st.markdown("---")

def load_alumni_data():
    """Load and process alumni data with debug information"""
    try:
        st.write("📂 Attempting to load alumni data...")
        file_path = 'attached_assets/Sohokai_List_20240726(Graduated).csv'

        # Read and detect file encoding
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            st.info(f"📝 Detected file encoding: {result['encoding']}")

        # Read CSV file
        df = pd.read_csv(file_path, encoding=result['encoding'])
        st.success(f"✅ Successfully read CSV with {len(df)} rows")

        # Process alumni data
        alumni_data = []
        for _, row in df.iterrows():
            name = f"{str(row.get('First Name', '')).strip()} {str(row.get('Prim_Last', '')).strip()}".strip()
            location = f"{str(row.get('City', '')).strip()}, {str(row.get('State', '')).strip()}, {str(row.get('Country', '')).strip()}"

            alumni_data.append({
                'Name': name,
                'Location': location,
                'Latitude': 35.6762,  # Default to Tokyo for testing
                'Longitude': 139.6503
            })

        return pd.DataFrame(alumni_data)
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

    # Display sample of loaded data
    st.subheader("📊 Sample Alumni Data")
    st.dataframe(alumni_df.head(), use_container_width=True)

    # Fetch disaster data
    disasters = fetch_disasters()

    # Create map
    st.subheader("🗺️ Disaster Monitoring Map")
    st.info("🔵 Blue markers: Alumni | 🔴 Red markers: Natural disasters")

    # Initialize map centered on Tokyo
    m = folium.Map(
        location=[35.6762, 139.6503],
        zoom_start=4,
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
            fill_opacity=0.7
        ).add_to(m)

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

                if distance <= 500:
                    alerts.append({
                        'alumni': alumni['Name'],
                        'disaster': disaster['title'],
                        'distance': distance
                    })
        except Exception as e:
            st.warning(f"⚠️ Error processing disaster: {str(e)}")
            continue

    # Display map and alerts in columns
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
        st.subheader("⚠️ Proximity Alerts")
        if alerts:
            for alert in alerts:
                st.warning(
                    f"🚨 {alert['alumni']} is {alert['distance']}km "
                    f"from {alert['disaster']}"
                )
        else:
            st.info("✅ No alerts within 500km")

        st.divider()
        st.subheader("📋 Alumni List")
        st.dataframe(
            alumni_df[['Name', 'Location']],
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"❌ Application error: {str(e)}")
    st.write("Please check the error message above and try again.")
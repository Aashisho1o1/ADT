import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
from datetime import datetime, timedelta
from geopy.distance import geodesic

# Configure page with proper layout
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better map display
st.markdown("""
    <style>
    .stApp > header {
        background-color: transparent;
    }
    .main > div {
        padding-top: 2rem;
    }
    div[data-testid="stVerticalBlock"] > div:has(iframe) {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Add title with clear styling
st.title("🌍 Alumni Natural Disaster Monitor")
st.markdown("---")

def load_alumni_data():
    """Load and process alumni data from simplified CSV"""
    try:
        with st.spinner("📂 Loading alumni data..."):
            file_path = 'assets/simplified_alumni.csv'
            df = pd.read_csv(file_path)

            if df.empty:
                st.error("❌ No alumni data found")
                return None

            st.success(f"✅ Successfully loaded {len(df)} alumni records")
            return df

    except Exception as e:
        st.error(f"❌ Error loading alumni data: {str(e)}")
        return None

def fetch_disasters():
    """Fetch natural disaster data from EONET"""
    with st.spinner("🌐 Fetching disaster data..."):
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
                st.success(f"✅ Found {len(data)} active disaster events")
                return data
            else:
                st.error(f"❌ API request failed with status code: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"❌ Error fetching disaster data: {str(e)}")
            return []

# Main application
try:
    # Create two columns for the layout
    col1, col2 = st.columns([7, 3])

    with col1:
        st.subheader("🗺️ Disaster Monitoring Map")
        st.info("🔵 Blue markers: Alumni locations | 🔴 Red markers: Natural disasters")

        # Load data
        alumni_df = load_alumni_data()
        if alumni_df is None:
            st.stop()

        # Create map centered on average coordinates
        center_lat = alumni_df['Latitude'].mean()
        center_lon = alumni_df['Longitude'].mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=3,
            tiles="OpenStreetMap"
        )

        # Add alumni markers
        for _, row in alumni_df.iterrows():
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                popup=f"Alumni: {row['Name']}<br>Location: {row['Location']}",
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.7
            ).add_to(m)

        # Fetch and add disaster markers
        disasters = fetch_disasters()
        alerts = []

        for disaster in disasters:
            try:
                coords = disaster['geometry'][0]['coordinates']
                lat, lon = coords[1], coords[0]

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=12,
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

        # Display the map using folium_static
        folium_static(m, width=800, height=600)

    # Right sidebar with statistics and alerts
    with col2:
        st.subheader("📊 Location Statistics")
        st.info(f"""
        Total Alumni: {len(alumni_df)}
        Countries: {alumni_df['Country'].nunique()}
        States/Regions: {alumni_df['State'].nunique()}
        """)

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
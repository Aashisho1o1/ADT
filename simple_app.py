import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
from datetime import datetime, timedelta
from geopy.distance import geodesic
import numpy as np

# Configure page
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better visual feedback
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
        z-index: 1;  /* Ensure map stays above other elements */
    }
    div[data-testid="stSidebar"] {
        z-index: 2;  /* Keep sidebar above map */
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_alumni_data():
    """Load and cache alumni data"""
    try:
        file_path = 'assets/simplified_alumni.csv'
        df = pd.read_csv(file_path)

        if df.empty:
            st.error("❌ No alumni data found")
            return None

        return df
    except Exception as e:
        st.error(f"❌ Error loading alumni data: {str(e)}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_disasters():
    """Fetch and cache disaster data"""
    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    params = {
        "status": "open",
        "days": 7,
        "category": "wildfires,severeStorms,volcanoes,earthquakes"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get('events', [])
        return []
    except Exception as e:
        st.error(f"❌ Error fetching disaster data: {str(e)}")
        return []

def calculate_proximity_alerts(alumni_df, disasters, threshold_km):
    """Optimized proximity calculation"""
    alerts = []

    try:
        # Convert to numpy arrays for faster calculation
        alumni_coords = alumni_df[['Latitude', 'Longitude']].values

        for disaster in disasters:
            try:
                coords = disaster['geometry'][0]['coordinates']
                disaster_coords = np.array([coords[1], coords[0]])

                # Vectorized distance calculation
                distances = np.array([
                    geodesic(coord, disaster_coords).kilometers 
                    for coord in alumni_coords
                ])

                # Find alumni within threshold
                nearby_indices = np.where(distances <= threshold_km)[0]

                for idx in nearby_indices:
                    alerts.append({
                        'alumni': alumni_df.iloc[idx]['Name'],
                        'location': alumni_df.iloc[idx]['Location'],
                        'disaster': disaster['title'],
                        'distance': int(distances[idx])
                    })

            except (KeyError, IndexError):
                continue

        return sorted(alerts, key=lambda x: x['distance'])
    except Exception as e:
        st.error(f"❌ Error calculating proximities: {str(e)}")
        return []

# Main application
try:
    st.title("🌍 Alumni Natural Disaster Monitor")

    # Add proximity threshold slider in sidebar
    with st.sidebar:
        st.title("🎯 Monitoring Settings")
        proximity_threshold = st.slider(
            "Proximity Alert Threshold (km)",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Set the distance threshold for disaster proximity alerts"
        )

    st.markdown("---")

    # Create layout with more space for the map
    col1, col2 = st.columns([8, 4])

    with col1:
        st.subheader("🗺️ Disaster Monitoring Map")

        # Load data with progress indicators
        with st.spinner("📂 Loading alumni data..."):
            alumni_df = load_alumni_data()

        if alumni_df is None:
            st.stop()

        with st.spinner("🌐 Fetching disaster data..."):
            disasters = fetch_disasters()

        # Create map centered on data
        center_lat = alumni_df['Latitude'].mean()
        center_lon = alumni_df['Longitude'].mean()

        with st.spinner("🗺️ Generating map..."):
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=2,
                tiles="OpenStreetMap"
            )

            # Add alumni markers in batches
            batch_size = 100
            total_alumni = len(alumni_df)

            progress_bar = st.progress(0)

            for i in range(0, total_alumni, batch_size):
                batch = alumni_df.iloc[i:i+batch_size]
                for _, row in batch.iterrows():
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=4,  # Smaller radius for better performance
                        popup=f"Alumni: {row['Name']}<br>Location: {row['Location']}",
                        color='blue',
                        fill=True,
                        fill_opacity=0.7
                    ).add_to(m)

                progress = min((i + batch_size) / total_alumni, 1.0)
                progress_bar.progress(progress)

            # Add disaster markers
            for disaster in disasters:
                try:
                    coords = disaster['geometry'][0]['coordinates']
                    folium.CircleMarker(
                        location=[coords[1], coords[0]],
                        radius=8,
                        popup=f"Disaster: {disaster['title']}",
                        color='red',
                        fill=True,
                        fill_opacity=0.7
                    ).add_to(m)
                except (KeyError, IndexError):
                    continue

            progress_bar.empty()

            # Display map
            folium_static(m, width=800, height=600)

    with col2:
        # Collapsible statistics section
        with st.expander("📊 Location Statistics", expanded=True):
            st.info(f"""
            Total Alumni: {len(alumni_df):,}
            Countries: {alumni_df['Country'].nunique():,}
            States/Regions: {alumni_df['State'].nunique():,}
            """)

        # Collapsible proximity alerts section
        with st.expander("⚠️ Proximity Alerts", expanded=True):
            st.caption(f"🎯 Showing alerts within {proximity_threshold:,}km")

            with st.spinner("🔍 Analyzing proximities..."):
                alerts = calculate_proximity_alerts(alumni_df, disasters, proximity_threshold)

            if alerts:
                for alert in alerts:
                    st.warning(
                        f"🚨 {alert['alumni']} in {alert['location']} is "
                        f"{alert['distance']:,}km from {alert['disaster']}"
                    )
            else:
                st.info(f"✅ No alerts within {proximity_threshold:,}km")

except Exception as e:
    st.error(f"❌ Application error: {str(e)}")
    st.exception(e)
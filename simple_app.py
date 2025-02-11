import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timedelta
import chardet
from geopy.distance import geodesic
import time

# Configure page
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    layout="wide"
)

# Add title with clear styling
st.title("🌍 Alumni Natural Disaster Monitor")
st.markdown("---")

def clean_address_field(field):
    """Clean and validate address field."""
    if pd.isna(field) or field == '':
        return ""
    # Convert float or int to string if necessary
    if isinstance(field, (float, int)):
        field = str(int(field)) if float(field).is_integer() else str(field)
    return str(field).strip()

def load_alumni_data():
    """Load and process alumni data from geocoded CSV"""
    try:
        st.write("📂 Loading alumni data...")
        file_path = 'attached_assets/combo.csv'

        # Read and detect file encoding
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            st.info(f"📝 Detected file encoding: {result['encoding']}")

        # Read CSV file
        df = pd.read_csv(file_path, encoding=result['encoding'])
        st.success(f"✅ Successfully read {len(df)} records")

        # Process alumni data
        alumni_data = []
        progress_bar = st.progress(0)
        total_records = len(df)

        for idx, row in df.iterrows():
            progress = (idx + 1) / total_records
            progress_bar.progress(progress, f"Processing alumni {idx + 1}/{total_records}")

            # Get name components
            name = f"{clean_address_field(row['original_First Name'])} {clean_address_field(row['original_Prim_Last'])}".strip()

            # Get formatted location (use pre-formatted address if available, otherwise compose from components)
            location = (clean_address_field(row.get('formatted', '')) or 
                       ', '.join(clean_address_field(v) for v in [
                           row['original_City'],
                           row['original_State'],
                           row['original_Country']
                       ] if v))

            # Get coordinates
            lat = float(row['lat']) if pd.notna(row['lat']) else 35.6762
            lon = float(row['lon']) if pd.notna(row['lon']) else 139.6503

            # Check if using default coordinates
            is_default = pd.isna(row['lat']) or pd.isna(row['lon'])

            alumni_data.append({
                'Name': name,
                'Location': location,
                'Latitude': lat,
                'Longitude': lon,
                'Is_Default_Location': is_default
            })

        progress_bar.empty()
        return pd.DataFrame(alumni_data)

    except Exception as e:
        st.error(f"❌ Error loading alumni data: {str(e)}")
        st.exception(e)  # Show detailed error
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
    st.dataframe(
        alumni_df[['Name', 'Location', 'Is_Default_Location']],
        use_container_width=True
    )

    # Fetch disaster data
    disasters = fetch_disasters()

    # Create map
    st.subheader("🗺️ Disaster Monitoring Map")
    st.info("🔵 Blue markers: Alumni locations | ⚫ Gray markers: Default locations | 🔴 Red markers: Natural disasters")

    # Initialize map centered on Pacific region to show both Japan and US
    m = folium.Map(
        location=[30.0, 180.0],
        zoom_start=3,
        tiles="OpenStreetMap"
    )

    # Add alumni markers
    default_locations = 0
    for _, row in alumni_df.iterrows():
        # Different styling for default vs mapped locations
        if row['Is_Default_Location']:
            color = 'gray'
            fill_opacity = 0.4
            default_locations += 1
            popup_prefix = "Alumni (Approximate Location)"
        else:
            color = 'blue'
            fill_opacity = 0.7
            popup_prefix = "Alumni"

        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"{popup_prefix}: {row['Name']}<br>Location: {row['Location']}",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity
        ).add_to(m)

    # Show location statistics
    st.info(f"""
    📍 Location Statistics:
    - Total Alumni: {len(alumni_df)}
    - Geocoded Locations: {len(alumni_df) - default_locations}
    - Default Locations: {default_locations}
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
                # Skip proximity check for default locations
                if alumni['Is_Default_Location']:
                    continue

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
            for alert in sorted(alerts, key=lambda x: x['distance']):
                st.warning(
                    f"🚨 {alert['alumni']} is {alert['distance']}km "
                    f"from {alert['disaster']}"
                )
        else:
            st.info("✅ No alerts within 500km")

        st.divider()
        st.subheader("📋 Alumni List")
        st.dataframe(
            alumni_df[['Name', 'Location', 'Is_Default_Location']],
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"❌ Application error: {str(e)}")
    st.write("Please check the error message above and try again.")
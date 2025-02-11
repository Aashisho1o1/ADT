import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timedelta
import chardet
from geopy.distance import geodesic
import time
from utils.japan_locations import get_prefecture_coordinates

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

def get_coordinates_for_japanese_address(address_components):
    """Get coordinates using Japanese prefecture mapping"""
    # For Japanese addresses, use prefecture mapping
    address_str = ' '.join(clean_address_field(v) for v in address_components.values() if v)
    lat, lon = get_prefecture_coordinates(address_str)

    # Check if we got default Tokyo coordinates
    is_default = (lat == 35.6762 and lon == 139.6503)
    return lat, lon, is_default

def load_alumni_data():
    """Load and process alumni data using both geocoded and raw data"""
    try:
        st.write("📂 Loading alumni data...")

        # Load geocoded data first
        geocoded_file = 'attached_assets/Sohokai_List_20240726_geocodio_33dbd69d66d31a7292d132f4da9384855fb65a4e.csv'
        with open(geocoded_file, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            st.info(f"📝 Detected geocoded file encoding: {result['encoding']}")

        # Read geocoded CSV
        geocoded_df = pd.read_csv(geocoded_file, encoding=result['encoding'])
        st.success(f"✅ Loaded {len(geocoded_df)} geocoded records")

        # Load original data
        original_file = 'attached_assets/Sohokai_List_20240726(Graduated).csv'
        with open(original_file, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)

        # Read original CSV
        original_df = pd.read_csv(original_file, encoding=result['encoding'])

        # Process alumni data
        alumni_data = []
        progress_bar = st.progress(0)
        total_records = len(original_df)

        for idx, row in original_df.iterrows():
            progress = (idx + 1) / total_records
            progress_bar.progress(progress, f"Processing alumni {idx + 1}/{total_records}")

            # Get name components
            name = f"{clean_address_field(row.get('First Name', ''))} {clean_address_field(row.get('Prim_Last', ''))}".strip()

            # Check if we have geocoded data for this record
            geocoded_match = geocoded_df[
                (geocoded_df['First Name'] == row['First Name']) & 
                (geocoded_df['Prim_Last'] == row['Prim_Last'])
            ]

            # Get location components
            location = ', '.join(
                clean_address_field(v) for v in [
                    row.get('City', ''),
                    row.get('State', ''),
                    row.get('Country', '')
                ] if v
            )

            if not geocoded_match.empty and 'Latitude' in geocoded_match.columns:
                # Use pre-geocoded coordinates
                lat = float(geocoded_match.iloc[0]['Latitude'])
                lon = float(geocoded_match.iloc[0]['Longitude'])
                is_default = False
            else:
                # Check if it's a Japanese address
                country = clean_address_field(row.get('Country', ''))
                if 'japan' in country.lower() or 'jpn' in country.lower():
                    # Use Japanese prefecture mapping
                    address_components = {
                        'Address 1': row.get('Address 1', ''),
                        'Address 2': row.get('Address 2', ''),
                        'City': row.get('City', ''),
                        'State': row.get('State', ''),
                        'Postal': row.get('Postal', ''),
                        'Country': row.get('Country', '')
                    }
                    lat, lon, is_default = get_coordinates_for_japanese_address(address_components)
                else:
                    # For non-Japanese addresses without geocoding, use Tokyo coordinates
                    lat, lon = 35.6762, 139.6503
                    is_default = True

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
    - Geocoded/Mapped Locations: {len(alumni_df) - default_locations}
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
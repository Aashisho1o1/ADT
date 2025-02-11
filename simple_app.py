import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import geodesic
import chardet
import json

# Page config
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    layout="wide"
)

# Function to load alumni data
def load_alumni_data():
    try:
        file_path = 'attached_assets/Sohokai_List_20240726(Graduated).csv'

        # Detect file encoding
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            st.write(f"File encoding: {result['encoding']}")

        # Read CSV with detected encoding
        df = pd.read_csv(file_path, encoding=result['encoding'])
        st.write("Columns in the file:", df.columns.tolist())

        # Clean and prepare data
        alumni_data = []
        for _, row in df.iterrows():
            # Get name components
            first_name = str(row.get('First Name', '')).strip()
            last_name = str(row.get('Prim_Last', '')).strip()
            name = f"{first_name} {last_name}".strip()

            # Get location components
            city = str(row.get('City', '')).strip()
            state = str(row.get('State', '')).strip()
            country = str(row.get('Country', '')).strip()

            # For initial testing, use Tokyo coordinates for all
            # This ensures we see something on the map
            lat = 35.6762
            lon = 139.6503

            location = f"{city}, {state}, {country}"

            alumni_data.append({
                'Name': name,
                'Location': location,
                'Latitude': lat,
                'Longitude': lon
            })

        return pd.DataFrame(alumni_data)
    except Exception as e:
        st.error(f"Error loading alumni data: {str(e)}")
        return pd.DataFrame()

# Function to fetch disaster data
def fetch_disasters():
    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    params = {
        "status": "open",
        "days": 7,
        "category": "wildfires,severeStorms,volcanoes,earthquakes"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('events', [])
        st.error("Failed to fetch disaster data")
        return []
    except Exception as e:
        st.error(f"Error fetching disaster data: {str(e)}")
        return []

# Main app
def main():
    st.title("🌍 Alumni Natural Disaster Monitor")

    # Load data with debug information
    with st.spinner("Loading alumni data..."):
        alumni_df = load_alumni_data()
        if not alumni_df.empty:
            st.success(f"Loaded {len(alumni_df)} alumni records")
            st.write("Sample of loaded data:")
            st.dataframe(alumni_df.head())
        else:
            st.error("Failed to load alumni data")
            return

    # Fetch disasters
    with st.spinner("Fetching disaster data..."):
        disasters = fetch_disasters()
        if disasters:
            st.success(f"Found {len(disasters)} active natural disasters")
        else:
            st.warning("No disaster data available")

    # Create map centered on Tokyo
    m = folium.Map(location=[35.6762, 139.6503], zoom_start=4)

    # Add alumni markers
    for _, row in alumni_df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"Alumni: {row['Name']}<br>Location: {row['Location']}",
            color='blue',
            fill=True
        ).add_to(m)

    # Add disaster markers and check proximity
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
                fill=True
            ).add_to(m)

            # Check proximity to alumni
            for _, alumni in alumni_df.iterrows():
                distance = geodesic(
                    (alumni['Latitude'], alumni['Longitude']),
                    (lat, lon)
                ).kilometers

                if distance <= 500:  # Alert if within 500km
                    alerts.append({
                        'alumni': alumni['Name'],
                        'disaster': disaster['title'],
                        'distance': round(distance)
                    })

        except (KeyError, IndexError) as e:
            st.error(f"Error processing disaster data: {str(e)}")
            continue

    # Display map and alerts in columns
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Disaster Monitoring Map")
        st_folium(m, width=800, height=600)

    with col2:
        st.subheader("⚠️ Proximity Alerts")
        if alerts:
            for alert in alerts:
                st.warning(
                    f"🚨 {alert['alumni']} is {alert['distance']}km "
                    f"from {alert['disaster']}"
                )
        else:
            st.info("✅ No alerts at this time")

        # Show alumni list
        st.subheader("📋 Alumni List")
        st.dataframe(
            alumni_df[['Name', 'Location']],
            hide_index=True
        )

if __name__ == "__main__":
    main()
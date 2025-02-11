import folium
from geopy.distance import geodesic
import numpy as np
import streamlit as st

def create_map(alumni_df, disasters):
    """Create an interactive map with alumni and disaster locations."""
    # Calculate center of the map
    center_lat = alumni_df['Latitude'].mean()
    center_lon = alumni_df['Longitude'].mean()

    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=2)

    # Add alumni markers
    for _, row in alumni_df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"Alumni: {row['Name']}<br>Location: {row['Location']}",
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(m)

    # Add disaster markers with improved visibility
    for disaster in disasters:
        try:
            coordinates = disaster['geometry'][0]['coordinates']
            # Log disaster details for debugging
            st.info(f"Processing disaster: {disaster['title']} at coordinates {coordinates}")

            folium.CircleMarker(
                location=[coordinates[1], coordinates[0]],
                radius=15,  # Increased size for better visibility
                popup=f"Disaster: {disaster['title']}<br>Type: {disaster['categories'][0]['title']}",
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.7,
                weight=2  # Increased border weight
            ).add_to(m)
        except (KeyError, IndexError, TypeError) as e:
            st.error(f"Error plotting disaster marker: {str(e)}")
            continue

    return m

def calculate_proximity_alerts(alumni_df, disasters, threshold_km):
    """Calculate proximity alerts between alumni and disasters with improved accuracy."""
    alerts = []
    st.info(f"Calculating alerts for {len(alumni_df)} alumni and {len(disasters)} disasters...")

    # Log the first few disasters for debugging
    for i, disaster in enumerate(disasters[:3]):
        st.info(f"Sample disaster {i+1}: {disaster.get('title', 'Unknown')} - Type: {disaster.get('categories', [{}])[0].get('title', 'Unknown')}")

    for _, alumni in alumni_df.iterrows():
        alumni_coords = (alumni['Latitude'], alumni['Longitude'])

        # Skip invalid alumni coordinates
        if not all(isinstance(x, (int, float)) for x in alumni_coords) or alumni_coords == (0, 0):
            continue

        for disaster in disasters:
            try:
                disaster_coords = (
                    disaster['geometry'][0]['coordinates'][1],  # Latitude
                    disaster['geometry'][0]['coordinates'][0]   # Longitude
                )

                # Skip invalid disaster coordinates
                if not all(isinstance(x, (int, float)) for x in disaster_coords):
                    continue

                distance = geodesic(alumni_coords, disaster_coords).km

                if distance <= threshold_km:
                    alert = {
                        'alumni_name': alumni['Name'],
                        'location': alumni['Location'],
                        'disaster_type': disaster['categories'][0]['title'],
                        'disaster_description': disaster['title'],
                        'distance': round(distance, 1)
                    }
                    alerts.append(alert)
                    st.warning(
                        f"⚠️ ALERT: {alert['alumni_name']} is {alert['distance']}km from "
                        f"{alert['disaster_description']} ({alert['disaster_type']})"
                    )

            except (KeyError, IndexError, TypeError) as e:
                st.error(f"Error processing disaster data: {str(e)}")
                continue

    # Sort alerts by distance
    alerts = sorted(alerts, key=lambda x: x['distance'])

    if alerts:
        st.warning(f"🚨 Found {len(alerts)} alerts within {threshold_km}km threshold")
    else:
        st.info("No alerts found within the specified threshold")

    return alerts
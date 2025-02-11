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

    # Add alumni markers with different styles based on coordinate validity
    for _, row in alumni_df.iterrows():
        # Different styling for valid vs default coordinates
        if row.get('Has_Valid_Coords', True):
            # Valid coordinates - blue marker
            color = 'blue'
            fill_opacity = 0.7
            popup_prefix = "Alumni"
        else:
            # Default coordinates - grey marker with warning
            color = 'gray'
            fill_opacity = 0.4
            popup_prefix = "Alumni (Approximate Location)"

        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"{popup_prefix}: {row['Name']}<br>Location: {row['Location']}",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity
        ).add_to(m)

    # Add disaster markers
    for disaster in disasters:
        try:
            coordinates = disaster['geometry'][0]['coordinates']

            folium.CircleMarker(
                location=[coordinates[1], coordinates[0]],
                radius=15,
                popup=f"Disaster: {disaster['title']}<br>Type: {disaster['categories'][0]['title']}",
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.7,
                weight=2
            ).add_to(m)
        except (KeyError, IndexError) as e:
            continue

    return m

def calculate_proximity_alerts(alumni_df, disasters, threshold_km):
    """Calculate proximity alerts between alumni and disasters."""
    alerts = []

    for _, alumni in alumni_df.iterrows():
        alumni_coords = (alumni['Latitude'], alumni['Longitude'])

        # Skip processing for alumni with default coordinates
        if not alumni.get('Has_Valid_Coords', True):
            continue

        for disaster in disasters:
            try:
                disaster_coords = (
                    disaster['geometry'][0]['coordinates'][1],
                    disaster['geometry'][0]['coordinates'][0]
                )

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

            except (KeyError, IndexError):
                continue

    # Sort alerts by distance
    alerts = sorted(alerts, key=lambda x: x['distance'])

    if alerts:
        st.warning(f"🚨 Found {len(alerts)} proximity alerts")

    return alerts
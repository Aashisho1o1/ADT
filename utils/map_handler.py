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

        # Ensure coordinates are floats
        try:
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=f"{popup_prefix}: {row['Name']}<br>Location: {row['Location']}",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=fill_opacity
            ).add_to(m)
        except (ValueError, TypeError):
            # Skip invalid coordinates
            st.warning(f"Skipped invalid coordinates for {row['Name']}")

    # Add disaster markers
    for disaster in disasters:
        try:
            coordinates = disaster['geometry'][0]['coordinates']
            
            # Ensure coordinates are floats
            lat = float(coordinates[1])
            lon = float(coordinates[0])

            folium.CircleMarker(
                location=[lat, lon],
                radius=15,
                popup=f"Disaster: {disaster['title']}<br>Type: {disaster['categories'][0]['title']}",
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.7,
                weight=2
            ).add_to(m)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            # Skip invalid disaster data
            continue

    return m

def calculate_proximity_alerts(alumni_df, disasters, threshold_km):
    """Calculate proximity alerts between alumni and disasters."""
    alerts = []

    # Ensure threshold is a float
    try:
        threshold_km = float(threshold_km)
    except (ValueError, TypeError):
        st.error("Invalid threshold value")
        return []

    for _, alumni in alumni_df.iterrows():
        try:
            # Ensure coordinates are floats
            alumni_lat = float(alumni['Latitude'])
            alumni_lon = float(alumni['Longitude'])
            alumni_coords = (alumni_lat, alumni_lon)
            
            # Skip processing for alumni with default coordinates
            if not alumni.get('Has_Valid_Coords', True):
                continue

            for disaster in disasters:
                try:
                    disaster_lat = float(disaster['geometry'][0]['coordinates'][1])
                    disaster_lon = float(disaster['geometry'][0]['coordinates'][0])
                    disaster_coords = (disaster_lat, disaster_lon)

                    distance = geodesic(alumni_coords, disaster_coords).km

                    if distance <= threshold_km:
                        # Convert all values to appropriate types to avoid type errors
                        alert = {
                            'alumni_name': str(alumni['Name']),
                            'location': str(alumni['Location']),
                            'disaster_type': str(disaster['categories'][0]['title']),
                            'disaster_description': str(disaster['title']),
                            'distance': float(round(distance, 1))
                        }
                        alerts.append(alert)

                except (KeyError, IndexError, ValueError, TypeError):
                    continue
        except (ValueError, TypeError):
            # Skip alumni with invalid coordinates
            continue

    # Sort alerts by distance
    alerts = sorted(alerts, key=lambda x: x['distance'])

    if alerts:
        st.warning(f"🚨 Found {len(alerts)} proximity alerts")

    return alerts
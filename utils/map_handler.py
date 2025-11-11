import folium
from geopy.distance import geodesic
import numpy as np
import pandas as pd
import streamlit as st

def create_map(alumni_df, disasters):
    """Create an interactive map with alumni and disaster locations."""
    # Calculate center of the map using numeric columns directly
    center_lat = alumni_df['Latitude'].mean()
    center_lon = alumni_df['Longitude'].mean()

    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=2)

    # Pre-process alumni data for faster rendering
    # Separate valid and invalid coordinate alumni
    valid_mask = alumni_df.get('Has_Valid_Coords', pd.Series([True] * len(alumni_df)))
    valid_alumni = alumni_df[valid_mask]
    invalid_alumni = alumni_df[~valid_mask]
    
    # Add valid alumni markers (blue)
    for _, row in valid_alumni.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"Alumni: {row['Name']}<br>Location: {row['Location']}",
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.7
        ).add_to(m)
    
    # Add invalid/approximate alumni markers (grey)
    for _, row in invalid_alumni.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"Alumni (Approximate Location): {row['Name']}<br>Location: {row['Location']}",
            color='gray',
            fill=True,
            fill_color='gray',
            fill_opacity=0.4
        ).add_to(m)

    # Add disaster markers - pre-extract valid disasters
    for disaster in disasters:
        try:
            coordinates = disaster['geometry'][0]['coordinates']
            folium.CircleMarker(
                location=[float(coordinates[1]), float(coordinates[0])],
                radius=15,
                popup=f"Disaster: {disaster['title']}<br>Type: {disaster['categories'][0]['title']}",
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.7,
                weight=2
            ).add_to(m)
        except (KeyError, IndexError, ValueError, TypeError):
            # Skip invalid disaster data
            continue

    return m

def calculate_proximity_alerts(alumni_df, disasters, threshold_km):
    """Calculate proximity alerts between alumni and disasters using optimized algorithm."""
    alerts = []

    # Ensure threshold is a float
    try:
        threshold_km = float(threshold_km)
    except (ValueError, TypeError):
        st.error("Invalid threshold value")
        return []

    # Pre-filter valid alumni coordinates to avoid checking repeatedly
    valid_alumni = alumni_df[alumni_df.get('Has_Valid_Coords', True)].copy()
    
    if valid_alumni.empty or not disasters:
        return []
    
    # Pre-extract disaster coordinates to avoid repeated dict lookups
    disaster_info = []
    for disaster in disasters:
        try:
            disaster_lat = float(disaster['geometry'][0]['coordinates'][1])
            disaster_lon = float(disaster['geometry'][0]['coordinates'][0])
            disaster_info.append({
                'coords': (disaster_lat, disaster_lon),
                'type': str(disaster['categories'][0]['title']),
                'description': str(disaster['title'])
            })
        except (KeyError, IndexError, ValueError, TypeError):
            continue
    
    if not disaster_info:
        return []

    # Calculate distances more efficiently
    for _, alumni in valid_alumni.iterrows():
        alumni_coords = (float(alumni['Latitude']), float(alumni['Longitude']))
        alumni_name = str(alumni['Name'])
        alumni_location = str(alumni['Location'])
        
        for disaster in disaster_info:
            distance = geodesic(alumni_coords, disaster['coords']).km
            
            if distance <= threshold_km:
                alerts.append({
                    'alumni_name': alumni_name,
                    'location': alumni_location,
                    'disaster_type': disaster['type'],
                    'disaster_description': disaster['description'],
                    'distance': round(distance, 1)
                })

    # Sort alerts by distance once at the end
    if alerts:
        alerts.sort(key=lambda x: x['distance'])
        st.warning(f"🚨 Found {len(alerts)} proximity alerts")

    return alerts
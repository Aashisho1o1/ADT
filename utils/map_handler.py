import folium
from geopy.distance import geodesic
import numpy as np

def create_map(alumni_df, disasters):
    """Create an interactive map with alumni and disaster locations."""
    # Calculate center of the map
    center_lat = alumni_df['Latitude'].mean()
    center_lon = alumni_df['Longitude'].mean()
    
    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=3)
    
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
    
    # Add disaster markers
    for disaster in disasters:
        coordinates = disaster['geometry'][0]['coordinates']
        folium.CircleMarker(
            location=[coordinates[1], coordinates[0]],
            radius=10,
            popup=f"Disaster: {disaster['title']}<br>Type: {disaster['categories'][0]['title']}",
            color='red',
            fill=True,
            fill_color='red'
        ).add_to(m)
    
    return m

def calculate_proximity_alerts(alumni_df, disasters, threshold_km):
    """Calculate proximity alerts between alumni and disasters."""
    alerts = []
    
    for _, alumni in alumni_df.iterrows():
        alumni_coords = (alumni['Latitude'], alumni['Longitude'])
        
        for disaster in disasters:
            disaster_coords = (
                disaster['geometry'][0]['coordinates'][1],
                disaster['geometry'][0]['coordinates'][0]
            )
            
            distance = geodesic(alumni_coords, disaster_coords).km
            
            if distance <= threshold_km:
                alerts.append({
                    'alumni_name': alumni['Name'],
                    'location': alumni['Location'],
                    'disaster_type': disaster['categories'][0]['title'],
                    'disaster_description': disaster['title'],
                    'distance': distance
                })
    
    return sorted(alerts, key=lambda x: x['distance'])

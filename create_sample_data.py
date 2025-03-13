import pandas as pd
import numpy as np

# Create sample alumni data
def create_sample_data():
    np.random.seed(42)
    
    # Generate 100 random alumni
    names = [f"Alumni {i}" for i in range(1, 101)]
    
    # Generate locations around the world
    locations = []
    latitudes = []
    longitudes = []
    
    # Major cities around the world
    cities = [
        ("New York, USA", 40.7128, -74.0060),
        ("London, UK", 51.5074, -0.1278),
        ("Tokyo, Japan", 35.6762, 139.6503),
        ("Sydney, Australia", -33.8688, 151.2093),
        ("Rio de Janeiro, Brazil", -22.9068, -43.1729),
        ("Cape Town, South Africa", -33.9249, 18.4241),
        ("Moscow, Russia", 55.7558, 37.6173),
        ("Beijing, China", 39.9042, 116.4074),
        ("Mumbai, India", 19.0760, 72.8777),
        ("Paris, France", 48.8566, 2.3522)
    ]
    
    for i in range(100):
        city, lat, lng = cities[i % len(cities)]
        # Add some random noise to spread points
        lat_noise = np.random.uniform(-0.5, 0.5)
        lng_noise = np.random.uniform(-0.5, 0.5)
        
        locations.append(city)
        latitudes.append(lat + lat_noise)
        longitudes.append(lng + lng_noise)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Name': names,
        'Location': locations,
        'Latitude': latitudes,
        'Longitude': longitudes,
        'Has_Valid_Coords': True  # All coordinates are valid
    })
    
    # Save to a simple CSV file
    df.to_csv('assets/sample_alumni.csv', index=False)
    print("Sample data created successfully!")

if __name__ == "__main__":
    create_sample_data() 
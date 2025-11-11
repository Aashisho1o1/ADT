import pandas as pd
from sqlalchemy import create_engine
from .database import Base, engine
import chardet

def import_from_csv(csv_path):
    """Import alumni data from CSV with optimized processing."""
    # Detect file encoding and read file once
    with open(csv_path, 'rb') as file:
        raw_data = file.read()
    
    result = chardet.detect(raw_data)
    encoding = result['encoding']

    # Read CSV file from memory, skip the first row if it contains 'combo'
    from io import BytesIO
    df = pd.read_csv(BytesIO(raw_data), encoding=encoding, skiprows=1)
    
    # Build location string using vectorized operations instead of apply
    city = df.get('original_City', pd.Series([''] * len(df))).fillna('')
    state = df.get('original_State', pd.Series([''] * len(df))).fillna('')
    country = df.get('original_Country', pd.Series([''] * len(df))).fillna('')
    location_series = (city + ', ' + state + ', ' + country).str.strip(' ,')
    
    # Map columns to match our database schema
    alumni_data = pd.DataFrame({
        'name': df['original_First Name'].fillna('') + ' ' + df['original_Prim_Last'].fillna(''),
        'location': location_series,
        'latitude': df['lat'],
        'longitude': df['lon'],
        'last_updated': pd.Timestamp.now()
    })
    
    # Remove rows with missing required data
    alumni_data = alumni_data.dropna(subset=['name', 'latitude', 'longitude'])
    
    # Fill any remaining NaN values
    alumni_data = alumni_data.fillna('')
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Import data in batches for better performance with large datasets
    batch_size = 1000
    for i in range(0, len(alumni_data), batch_size):
        batch = alumni_data.iloc[i:i+batch_size]
        batch.to_sql('alumni', engine, if_exists='append', index=False)
    
    print(f"Successfully imported {len(alumni_data)} records")

if __name__ == "__main__":
    import_from_csv('assets/combo.csv')  # Updated path to your actual CSV file 
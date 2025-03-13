import pandas as pd
from sqlalchemy import create_engine
from .database import Base, engine
import chardet

def import_from_csv(csv_path):
    # Detect file encoding
    with open(csv_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    # Read CSV file, skip the first row if it contains 'combo'
    df = pd.read_csv(csv_path, encoding=encoding, skiprows=1)
    
    # Map columns to match our database schema
    alumni_data = pd.DataFrame({
        'name': df['original_First Name'].fillna('') + ' ' + df['original_Prim_Last'].fillna(''),
        'location': df.apply(
            lambda row: f"{row['original_City'] or ''}, {row['original_State'] or ''}, {row['original_Country'] or ''}".strip(' ,'),
            axis=1
        ),
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
    
    # Import data
    alumni_data.to_sql('alumni', engine, if_exists='append', index=False)
    print(f"Successfully imported {len(alumni_data)} records")

if __name__ == "__main__":
    import_from_csv('assets/combo 3.csv')  # Updated path to your actual CSV file 
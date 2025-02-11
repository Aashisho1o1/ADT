import pandas as pd
import chardet
from sqlalchemy import create_engine
import os
from utils.data_loader import format_address, get_coordinates
from utils.database import init_db, Alumni
from datetime import datetime

def load_csv_to_database(file_path):
    """Load Sohokai alumni data from CSV to PostgreSQL database."""
    print("Initializing database...")
    init_db()
    
    # Create database engine
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL not found in environment variables")
    engine = create_engine(DATABASE_URL)
    
    print("Reading CSV file...")
    # Detect file encoding
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        print(f"Detected encoding: {result['encoding']}")
        
    # Read CSV with detected encoding
    df = pd.read_csv(file_path, encoding=result['encoding'])
    print(f"Found {len(df)} records")
    
    # Process each record
    processed_data = []
    for idx, row in df.iterrows():
        try:
            # Combine name fields
            name = f"{row['First Name']} {row['Prim_Last']}"
            
            # Collect address components
            address_parts = [
                row.get('Address 1', ''),
                row.get('Address 2', ''),
                row.get('City', ''),
                row.get('State', ''),
                row.get('Postal', ''),
                row.get('Country', '')
            ]
            
            # Format address and get coordinates
            formatted_address = format_address(address_parts)
            coords = get_coordinates(address_parts, formatted_address)
            
            processed_data.append({
                'name': name,
                'location': formatted_address,
                'latitude': coords[0],
                'longitude': coords[1],
                'last_updated': datetime.now()
            })
            
            print(f"Processed {idx + 1}/{len(df)}: {name}")
            
        except Exception as e:
            print(f"Error processing record {idx}: {str(e)}")
            continue
    
    print("Saving to database...")
    # Convert to DataFrame and save to database
    processed_df = pd.DataFrame(processed_data)
    processed_df.to_sql('alumni', engine, if_exists='replace', index=False)
    print("Data successfully loaded to database!")

if __name__ == "__main__":
    file_path = 'attached_assets/Sohokai_List_20240726(Graduated).csv'
    load_csv_to_database(file_path)

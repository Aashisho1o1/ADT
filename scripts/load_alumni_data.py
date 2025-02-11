import pandas as pd
import chardet
from sqlalchemy import create_engine
import os
from datetime import datetime
import sys
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.japan_locations import get_prefecture_coordinates
from utils.database import init_db, Alumni, SessionLocal

def format_address(address_parts):
    """Format address for geocoding."""
    return ', '.join(part.strip() for part in address_parts if pd.notna(part) and str(part).strip())

def get_coordinates(address_parts, formatted_address):
    """Get coordinates using geocoding with fallback to prefecture mapping."""
    try:
        # Check if it's a Japanese address
        country = address_parts[-1].strip() if address_parts else ''
        is_japanese_address = 'japan' in country.lower() or 'jpn' in country.lower()

        if is_japanese_address:
            # Try prefecture mapping first for Japanese addresses
            coords = get_prefecture_coordinates(formatted_address)
            if coords != (0, 0):
                return coords

        # If not Japanese or prefecture mapping failed, try geocoding
        geolocator = Nominatim(user_agent="alumni_monitor")
        location = geolocator.geocode(formatted_address, timeout=10)

        if location:
            print(f"Found coordinates for {formatted_address}: {location.latitude}, {location.longitude}")
            return location.latitude, location.longitude

        # Fallback to prefecture mapping for Japanese addresses
        if is_japanese_address:
            return get_prefecture_coordinates(formatted_address)

        print(f"Could not find coordinates for: {formatted_address}")
        return (0, 0)

    except Exception as e:
        print(f"Error getting coordinates for {formatted_address}: {str(e)}")
        return (0, 0)

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
    total_records = len(df)

    print("Processing records...")
    for idx, row in df.iterrows():
        try:
            # Progress update
            if idx % 10 == 0:
                print(f"Processing record {idx + 1}/{total_records}")

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

            # Add delay to avoid hitting geocoding rate limits
            time.sleep(1)

        except Exception as e:
            print(f"Error processing record {idx}: {str(e)}")
            continue

    print(f"\nSaving {len(processed_data)} records to database...")
    # Create session and save to database
    session = SessionLocal()
    try:
        # Clear existing records
        session.query(Alumni).delete()

        # Add new records
        for record in processed_data:
            alumni = Alumni(**record)
            session.add(alumni)

        session.commit()
        print("Data successfully loaded to database!")

    except Exception as e:
        session.rollback()
        print(f"Error saving to database: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    file_path = 'attached_assets/Sohokai_List_20240726(Graduated).csv'
    load_csv_to_database(file_path)
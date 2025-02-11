import pandas as pd
import chardet
from sqlalchemy import create_engine
import os
from datetime import datetime
import sys
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import backoff

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.japan_locations import get_prefecture_coordinates
from utils.database import init_db, Alumni, SessionLocal

def clean_address_field(field):
    """Clean and validate address field."""
    if pd.isna(field):
        return ""
    # Convert float or int to string if necessary
    if isinstance(field, (float, int)):
        field = str(field)
    return str(field).strip()

def format_address(address_parts):
    """Format address for geocoding with improved cleaning."""
    # Clean and validate each part
    cleaned_parts = [clean_address_field(part) for part in address_parts]
    # Filter out empty strings
    valid_parts = [part for part in cleaned_parts if part]
    return ', '.join(valid_parts)

@backoff.on_exception(
    backoff.expo,
    (GeocoderTimedOut, GeocoderServiceError),
    max_tries=3
)
def geocode_address(geolocator, address):
    """Geocode address with retry logic."""
    return geolocator.geocode(address, timeout=30)

def get_coordinates(address_parts, formatted_address):
    """Get coordinates using geocoding with improved error handling and retry logic."""
    try:
        # Skip empty addresses
        if not formatted_address:
            print(f"Empty address, skipping geocoding")
            return (0, 0)

        # Check if it's a Japanese address
        country = clean_address_field(address_parts[-1])
        is_japanese_address = 'japan' in country.lower() or 'jpn' in country.lower()

        if is_japanese_address:
            # Try prefecture mapping first for Japanese addresses
            coords = get_prefecture_coordinates(formatted_address)
            if coords != (0, 0):
                print(f"Found Japanese prefecture coordinates for: {formatted_address}")
                return coords

        # If not Japanese or prefecture mapping failed, try geocoding
        geolocator = Nominatim(user_agent="alumni_monitor")

        try:
            location = geocode_address(geolocator, formatted_address)
            if location:
                print(f"Successfully geocoded: {formatted_address}")
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding service error for {formatted_address}: {str(e)}")
        except Exception as e:
            print(f"Unexpected geocoding error for {formatted_address}: {str(e)}")

        # Fallback to prefecture mapping for Japanese addresses
        if is_japanese_address:
            return get_prefecture_coordinates(formatted_address)

        print(f"Could not find coordinates for: {formatted_address}")
        return (0, 0)

    except Exception as e:
        print(f"Error processing address {formatted_address}: {str(e)}")
        return (0, 0)

def load_csv_to_database(file_path):
    """Load Sohokai alumni data from CSV to PostgreSQL database."""
    print("Initializing database...")
    init_db()

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
    successful_geocodes = 0

    print("\nProcessing records...")
    for idx, row in df.iterrows():
        try:
            # Progress update
            if idx % 10 == 0:
                print(f"\nProcessing record {idx + 1}/{total_records}")
                print(f"Successful geocodes so far: {successful_geocodes}")

            # Combine name fields
            name = f"{clean_address_field(row['First Name'])} {clean_address_field(row['Prim_Last'])}"

            # Collect and clean address components
            address_parts = [
                clean_address_field(row.get('Address 1', '')),
                clean_address_field(row.get('Address 2', '')),
                clean_address_field(row.get('City', '')),
                clean_address_field(row.get('State', '')),
                clean_address_field(row.get('Postal', '')),
                clean_address_field(row.get('Country', ''))
            ]

            # Format address and get coordinates
            formatted_address = format_address(address_parts)
            coords = get_coordinates(address_parts, formatted_address)

            if coords != (0, 0):
                successful_geocodes += 1

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

    print(f"\nProcessing complete!")
    print(f"Total records processed: {len(processed_data)}")
    print(f"Successfully geocoded: {successful_geocodes}")

    print("\nSaving records to database...")
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
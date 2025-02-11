import pandas as pd
import chardet
from sqlalchemy import create_engine
import os
from datetime import datetime
import sys
from pathlib import Path
from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import backoff
import requests
from ratelimit import limits, sleep_and_retry

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.japan_locations import get_prefecture_coordinates
from utils.database import init_db, Alumni, SessionLocal

# Configure rate limiting
CALLS_PER_MINUTE = 60
RATE_LIMIT_PERIOD = 60

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=RATE_LIMIT_PERIOD)
def geocode_with_rate_limit(geolocator, address):
    """Rate-limited geocoding function."""
    return geolocator.geocode(address, timeout=30)

def clean_address_field(field):
    """Clean and validate address field."""
    if pd.isna(field) or field == '':
        return ""
    # Convert float or int to string if necessary
    if isinstance(field, (float, int)):
        field = str(int(field)) if float(field).is_integer() else str(field)
    return str(field).strip()

def try_geocode_combinations(address_components):
    """Try different combinations of address components for geocoding."""
    geolocator = Nominatim(user_agent="alumni_monitor")

    # Extract components
    address1 = clean_address_field(address_components.get('Address 1', ''))
    address2 = clean_address_field(address_components.get('Address 2', ''))
    city = clean_address_field(address_components.get('City', ''))
    state = clean_address_field(address_components.get('State', ''))
    postal = clean_address_field(address_components.get('Postal', ''))
    country = clean_address_field(address_components.get('Country', ''))

    # Define geocoding attempts in order of specificity
    attempts = [
        # Full address
        f"{address1}, {address2}, {city}, {state} {postal}, {country}",
        # Address without unit number
        f"{address1.split('Unit')[0].split('Apt')[0]}, {city}, {state} {postal}, {country}",
        # City, State, ZIP, Country
        f"{city}, {state} {postal}, {country}",
        # City, State, Country
        f"{city}, {state}, {country}",
        # State, Country (fallback)
        f"{state}, {country}"
    ]

    for attempt in attempts:
        # Clean up the attempt string
        attempt = ', '.join(part.strip() for part in attempt.split(',') if part.strip())
        if not attempt:
            continue

        try:
            print(f"Trying geocoding with: {attempt}")
            location = geocode_with_rate_limit(geolocator, attempt)
            if location:
                print(f"Successfully geocoded using: {attempt}")
                return location.latitude, location.longitude
        except Exception as e:
            print(f"Failed geocoding attempt '{attempt}': {str(e)}")
            continue

    return None

def get_coordinates(address_components):
    """Get coordinates using various methods and fallbacks."""
    # Check if it's a Japanese address
    country = clean_address_field(address_components.get('Country', ''))
    is_japanese_address = 'japan' in country.lower() or 'jpn' in country.lower()

    if is_japanese_address:
        # Try prefecture mapping first for Japanese addresses
        address_str = ' '.join(clean_address_field(v) for v in address_components.values() if v)
        coords = get_prefecture_coordinates(address_str)
        if coords != (0, 0):
            print(f"Found Japanese prefecture coordinates for: {address_str}")
            return coords

    # Try different combinations of address components
    coords = try_geocode_combinations(address_components)
    if coords:
        return coords

    # Final fallback to Japanese prefecture mapping
    if is_japanese_address:
        return get_prefecture_coordinates(' '.join(
            v for v in [
                address_components.get('City', ''),
                address_components.get('State', ''),
                'Japan'
            ] if v
        ))

    print(f"Could not find coordinates for address components: {address_components}")
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
            first_name = clean_address_field(row.get('First Name', ''))
            last_name = clean_address_field(row.get('Prim_Last', ''))
            name = f"{first_name} {last_name}".strip()

            if not name:
                print(f"Skipping record {idx + 1}: Missing name")
                continue

            # Collect address components as a dictionary
            address_components = {
                'Address 1': row.get('Address 1', ''),
                'Address 2': row.get('Address 2', ''),
                'City': row.get('City', ''),
                'State': row.get('State', ''),
                'Postal': row.get('Postal', ''),
                'Country': row.get('Country', '')
            }

            # Get coordinates using various methods
            coords = get_coordinates(address_components)

            if coords != (0, 0):
                successful_geocodes += 1

            # Format full address for storage
            formatted_address = ', '.join(
                clean_address_field(v) for v in address_components.values() if v
            )

            processed_data.append({
                'name': name,
                'location': formatted_address,
                'latitude': coords[0],
                'longitude': coords[1],
                'last_updated': datetime.now()
            })

            # Add small delay to avoid overwhelming geocoding services
            time.sleep(0.5)

        except Exception as e:
            print(f"Error processing record {idx + 1}: {str(e)}")
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
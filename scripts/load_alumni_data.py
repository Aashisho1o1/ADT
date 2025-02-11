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

# Configure rate limiting to avoid hitting API limits
CALLS_PER_MINUTE = 60
RATE_LIMIT_PERIOD = 60

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=RATE_LIMIT_PERIOD)
def geocode_with_rate_limit(geolocator, address):
    """Rate-limited geocoding function."""
    return geolocator.geocode(address, timeout=30)

def normalize_country(country):
    """Normalize country names for better matching."""
    country_map = {
        'usa': 'United States',
        'jpn': 'Japan',
        'can': 'Canada',
        'aus': 'Australia',
        'gbr': 'United Kingdom',
        'fra': 'France',
        'deu': 'Germany',
        'aut': 'Austria',
        'esp': 'Spain',
        'ind': 'India',
        'kor': 'South Korea'
    }
    country = country.lower().strip()
    return country_map.get(country, country.title())

def clean_address_field(field):
    """Clean and validate address field."""
    if pd.isna(field) or field == '':
        return ""
    # Convert float or int to string if necessary
    if isinstance(field, (float, int)):
        field = str(int(field)) if float(field).is_integer() else str(field)
    return str(field).strip()

def format_address(address_parts):
    """Format address for geocoding with enhanced normalization."""
    # Clean and validate each part
    cleaned_parts = [clean_address_field(part) for part in address_parts if part]

    # Filter out empty strings and invalid values
    valid_parts = [part for part in cleaned_parts if part and part.lower() != 'nan']

    if not valid_parts:
        return ""

    # Normalize country name if present
    if valid_parts[-1]:
        valid_parts[-1] = normalize_country(valid_parts[-1])

    # Special formatting for different countries
    country = valid_parts[-1].lower() if valid_parts else ''

    if 'japan' in country:
        # Japanese address format
        return ' '.join(valid_parts)
    elif 'united states' in country:
        # US address format
        return ', '.join(valid_parts)
    else:
        # Default international format
        return ', '.join(valid_parts)

@backoff.on_exception(
    backoff.expo,
    (GeocoderTimedOut, GeocoderServiceError, requests.exceptions.RequestException),
    max_tries=3
)
def geocode_address(address):
    """Geocode address using multiple services with enhanced retry logic."""
    if not address:
        return None

    # Try Nominatim first
    try:
        geolocator = Nominatim(user_agent="alumni_monitor")
        location = geocode_with_rate_limit(geolocator, address)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Primary geocoding failed for {address}: {str(e)}")

    # Try with simplified address (removing apartment numbers, etc.)
    try:
        simplified_address = ', '.join([p.split('Apt')[0].split('Unit')[0].strip() 
                                      for p in address.split(',')]).strip()
        if simplified_address != address:
            location = geocode_with_rate_limit(geolocator, simplified_address)
            if location:
                return location.latitude, location.longitude
    except Exception as e:
        print(f"Simplified address geocoding failed for {address}: {str(e)}")

    return None

def get_coordinates(address_parts, formatted_address):
    """Get coordinates using geocoding with comprehensive fallback strategy."""
    if not formatted_address:
        print(f"Empty address, skipping geocoding")
        return (0, 0)

    # Check if it's a Japanese address
    country = clean_address_field(address_parts[-1])
    is_japanese_address = 'japan' in country.lower() or 'jpn' in country.lower()

    # Try prefecture mapping first for Japanese addresses
    if is_japanese_address:
        coords = get_prefecture_coordinates(formatted_address)
        if coords != (0, 0):
            print(f"Found Japanese prefecture coordinates for: {formatted_address}")
            return coords

    # Try geocoding with full address
    coords = geocode_address(formatted_address)
    if coords:
        print(f"Successfully geocoded: {formatted_address}")
        return coords

    # Try with city and country only for international addresses
    if not is_japanese_address and len(address_parts) >= 2:
        city = clean_address_field(address_parts[-3]) if len(address_parts) >= 3 else ''
        country = clean_address_field(address_parts[-1])
        if city and country:
            simplified = f"{city}, {country}"
            coords = geocode_address(simplified)
            if coords:
                print(f"Successfully geocoded with simplified address: {simplified}")
                return coords

    # Final fallback to prefecture mapping for Japanese addresses
    if is_japanese_address:
        return get_prefecture_coordinates(formatted_address)

    print(f"Could not find coordinates for: {formatted_address}")
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
            if not formatted_address:
                print(f"Skipping record {idx + 1}: No valid address")
                continue

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
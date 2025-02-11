import pandas as pd
import chardet
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from .japan_locations import get_prefecture_coordinates

def detect_encoding(file_path):
    """Detect the encoding of a file."""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            st.info(f"Detected file encoding: {result['encoding']}")
            return result['encoding']
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def format_address(address_parts):
    """Format address for geocoding."""
    # Filter out empty or None values
    address = ', '.join(part.strip() for part in address_parts if pd.notna(part) and str(part).strip())

    # Clean up common issues
    address = address.replace('JPN', 'Japan')

    return address

def geocode_address_with_retry(address, max_retries=3):
    """Geocode address with retry logic."""
    geolocator = Nominatim(user_agent="sohokai_alumni_monitor")

    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location.latitude, location.longitude
            time.sleep(1)
        except (GeocoderTimedOut, GeocoderServiceError):
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
    return None

def get_coordinates(address_parts, formatted_address):
    """Get coordinates using multiple methods."""
    try:
        # Check if it's a Japanese address
        country = address_parts[-1].strip() if address_parts else ''
        is_japanese_address = 'japan' in country.lower() or 'jpn' in country.lower()

        # First try regular geocoding
        coords = geocode_address_with_retry(formatted_address)
        if coords:
            return coords

        # For Japanese addresses, fall back to prefecture mapping
        if is_japanese_address:
            prefecture_coords = get_prefecture_coordinates(formatted_address)
            if prefecture_coords:
                return prefecture_coords

        # Last resort: try geocoding with just city and country
        if ',' in formatted_address:
            city_country = ', '.join(formatted_address.split(',')[-2:])
            coords = geocode_address_with_retry(city_country)
            if coords:
                return coords

    except Exception as e:
        st.error(f"Error getting coordinates: {str(e)}")

    # Default fallback coordinates (0, 0 for international addresses)
    return (0, 0) if not is_japanese_address else (35.6762, 139.6503)

def load_alumni_data(file_path='attached_assets/Sohokai_List_20240726(Graduated).csv'):
    """Load and process Sohokai alumni data from CSV."""
    try:
        # Initialize database
        db.init_db()
        session = next(db.get_db())

        try:
            # Detect file encoding
            encoding = detect_encoding(file_path)
            if not encoding:
                st.error("Could not detect file encoding")
                return None

            # Read CSV with detected encoding
            df = pd.read_csv(file_path, encoding=encoding)
            st.success(f"Successfully read CSV file with {len(df)} records")

            # Process alumni data
            processed_data = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            total_records = len(df)
            for index, row in df.iterrows():
                # Update progress
                progress = int((index + 1) * 100 / total_records)
                progress_bar.progress(progress)

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

                    # Format address
                    formatted_address = format_address(address_parts)
                    status_text.text(f"Processing {name}: {formatted_address}")

                    # Get coordinates using appropriate method
                    coords = get_coordinates(address_parts, formatted_address)

                    processed_data.append({
                        'Name': name,
                        'Location': formatted_address,
                        'Latitude': coords[0],
                        'Longitude': coords[1]
                    })
                    st.success(f"✓ Processed address for {name}")

                except Exception as e:
                    st.error(f"Error processing record for row {index}: {str(e)}")
                    continue

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            if not processed_data:
                st.error("No valid alumni data could be processed")
                return None

            # Convert to DataFrame
            processed_df = pd.DataFrame(processed_data)

            # Store in database
            session.query(Alumni).delete()
            for _, row in processed_df.iterrows():
                alumni = Alumni(
                    name=row['Name'],
                    location=row['Location'],
                    latitude=float(row['Latitude']),
                    longitude=float(row['Longitude']),
                    last_updated=datetime.now()
                )
                session.add(alumni)

            session.commit()
            st.success(f"Successfully processed {len(processed_df)} alumni records")
            return processed_df

        except Exception as e:
            session.rollback()
            st.error(f"Error processing alumni data: {str(e)}")
            return None

    except Exception as e:
        st.error(f"Error loading alumni data: {str(e)}")
        return None
    finally:
        session.close()
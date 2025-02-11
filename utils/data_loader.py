import pandas as pd
import chardet
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

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

def geocode_address_with_retry(address, max_retries=3):
    """Geocode address with retry logic."""
    geolocator = Nominatim(user_agent="sohokai_alumni_monitor")

    for attempt in range(max_retries):
        try:
            # Add country to improve geocoding accuracy if not present
            if 'japan' not in address.lower() and 'jpn' not in address.lower():
                address += ', Japan'

            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            time.sleep(1)  # Respect rate limits
        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))  # Exponential backoff
                continue
            st.warning(f"Geocoding timed out for address: {address}")
    return None

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
                    # Combine name fields (First Name and Prim_Last)
                    name = f"{row['First Name']} {row['Prim_Last']}"

                    # Combine address fields
                    address_parts = []
                    for field in ['Address 1', 'Address 2', 'City', 'State', 'Postal', 'Country']:
                        if pd.notna(row[field]) and str(row[field]).strip():
                            address_parts.append(str(row[field]).strip())

                    full_address = ', '.join(address_parts)
                    status_text.text(f"Processing {name}: {full_address}")

                    # Get coordinates
                    coords = geocode_address_with_retry(full_address)
                    if coords:
                        processed_data.append({
                            'Name': name,
                            'Location': full_address,
                            'Latitude': coords[0],
                            'Longitude': coords[1]
                        })
                        st.success(f"✓ Successfully geocoded address for {name}")
                    else:
                        st.warning(f"⚠ Could not geocode address for {name}")

                except Exception as e:
                    st.error(f"Error processing record for row {index}: {str(e)}")
                    continue

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            if not processed_data:
                st.error("No valid alumni data could be geocoded")
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
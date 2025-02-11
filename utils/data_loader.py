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
            st.info(f"Detected encoding: {result['encoding']}")
            return result['encoding']
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def geocode_address(address):
    """Convert address to coordinates using Nominatim."""
    geolocator = Nominatim(user_agent="alumni_disaster_monitor")
    try:
        # Add country to improve geocoding accuracy
        if 'japan' not in address.lower():
            address += ', Japan'
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None
    except GeocoderTimedOut:
        time.sleep(1)  # Wait before retry
        return None

def load_alumni_data(file_path='attached_assets/Sohokai_List_20240726(Graduated).csv'):
    """Load and process alumni data from CSV, store in database."""
    try:
        # Initialize database
        db.init_db()
        session = next(db.get_db())

        try:
            # First try to read from database
            existing_alumni = session.query(Alumni).all()
            if existing_alumni:
                st.success("Loaded alumni data from database")
                return pd.DataFrame([{
                    'Name': alumni.name,
                    'Location': alumni.location,
                    'Latitude': alumni.latitude,
                    'Longitude': alumni.longitude
                } for alumni in existing_alumni])

            # If no data in database, load from CSV
            try:
                # Try main CSV first with detected encoding
                encoding = detect_encoding(file_path)
                if encoding:
                    df = pd.read_csv(file_path, encoding=encoding)
                    st.success(f"Successfully read CSV file: {file_path}")
                    st.write("Available columns:", df.columns.tolist())
                else:
                    raise Exception("Could not detect file encoding")

                # Process alumni data
                processed_data = []
                with st.spinner('Processing alumni addresses...'):
                    for _, row in df.iterrows():
                        # Combine name fields
                        name = f"{row['First Name']} {row['Prim_Last']}"

                        # Combine address fields
                        address_parts = [
                            str(part) for part in [
                                row['Address 1'],
                                row['Address 2'],
                                row['City'],
                                row['State'],
                                row['Postal'],
                                row['Country']
                            ] if pd.notna(part)
                        ]
                        full_address = ', '.join(address_parts)

                        # Get coordinates
                        coords = geocode_address(full_address)
                        if coords:
                            processed_data.append({
                                'Name': name,
                                'Location': full_address,
                                'Latitude': coords[0],
                                'Longitude': coords[1]
                            })

                if not processed_data:
                    st.error("No valid alumni data could be geocoded")
                    return None

                # Convert to DataFrame
                processed_df = pd.DataFrame(processed_data)

                # Clear existing data
                session.query(Alumni).delete()

                # Store in database
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
                st.success(f"Successfully loaded {len(processed_df)} alumni records")
                return processed_df

            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
                return None

        except Exception as e:
            session.rollback()
            st.error(f"Error processing alumni data: {str(e)}")
            return None

    except Exception as e:
        st.error(f"Error loading alumni data: {str(e)}")
        return None
    finally:
        session.close()
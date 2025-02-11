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

def format_japanese_address(address_parts):
    """Format Japanese address for better geocoding results."""
    # Filter out empty or None values
    address = ', '.join(part.strip() for part in address_parts if pd.notna(part) and str(part).strip())

    # Clean up common issues in Japanese addresses
    address = address.replace('JPN', 'Japan')
    address = address.replace('-', ' ')

    return address

def get_coordinates(formatted_address):
    """Get coordinates using fallback mechanisms."""
    try:
        # First try prefecture-level coordinates
        prefecture_coords = get_prefecture_coordinates(formatted_address)
        if prefecture_coords:
            return prefecture_coords

        # If no prefecture match, return Tokyo coordinates as final fallback
        return (35.6762, 139.6503)  # Tokyo coordinates

    except Exception as e:
        st.error(f"Error getting coordinates: {str(e)}")
        return (35.6762, 139.6503)  # Tokyo coordinates as fallback

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
                    formatted_address = format_japanese_address(address_parts)
                    status_text.text(f"Processing {name}: {formatted_address}")

                    # Get coordinates using fallback mechanism
                    coords = get_coordinates(formatted_address)

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
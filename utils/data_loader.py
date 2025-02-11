import pandas as pd
import chardet
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni
import streamlit as st

def detect_encoding(file_path):
    """Detect the encoding of a file."""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def load_alumni_data(file_path='assets/sample_alumni.csv'):
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
                # Try main CSV first
                df = pd.read_csv(file_path)
            except Exception as main_file_error:
                st.warning(f"Could not read main CSV file: {str(main_file_error)}")
                st.info("Loading sample alumni data instead")
                # Fall back to sample data
                df = pd.read_csv('assets/sample_alumni.csv')

            # Check and rename columns if needed
            required_columns = ['Name', 'Location', 'Latitude', 'Longitude']

            # Map actual columns to required columns if they exist with different names
            column_mapping = {
                'name': 'Name',
                'location': 'Location',
                'latitude': 'Latitude',
                'longitude': 'Longitude'
            }

            df.rename(columns=column_mapping, inplace=True, errors='ignore')

            if not all(col in df.columns for col in required_columns):
                st.warning("Required columns not found in CSV, using sample data")
                df = pd.DataFrame({
                    'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
                    'Location': ['Tokyo, Japan', 'New York, USA', 'London, UK'],
                    'Latitude': [35.6762, 40.7128, 51.5074],
                    'Longitude': [139.6503, -74.0060, -0.1278]
                })

            # Filter out rows with missing location data
            df = df.dropna(subset=['Latitude', 'Longitude'])

            if len(df) == 0:
                st.error("No valid alumni data found with location information")
                return None

            # Store data in database
            for _, row in df.iterrows():
                alumni = Alumni(
                    name=row['Name'],
                    location=row['Location'],
                    latitude=float(row['Latitude']),
                    longitude=float(row['Longitude']),
                    last_updated=datetime.now()
                )
                session.add(alumni)

            session.commit()
            st.success(f"Successfully loaded {len(df)} alumni records")
            return df

        except Exception as e:
            session.rollback()
            st.error(f"Error processing alumni data: {str(e)}")
            return None

    except Exception as e:
        st.error(f"Error loading alumni data: {str(e)}")
        return None
    finally:
        session.close()
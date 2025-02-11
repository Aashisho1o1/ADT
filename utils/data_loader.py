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
            st.info(f"Detected encoding: {result['encoding']}")
            return result['encoding']
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
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

                # Map specific columns from your CSV file
                column_mapping = {
                    'Name/氏名': 'Name',
                    'Current Location/現住所': 'Location',
                    'Latitude': 'Latitude',
                    'Longitude': 'Longitude',
                    'Current Address/現住所': 'Location'
                }

                # Rename columns if they exist
                df.rename(columns=column_mapping, inplace=True, errors='ignore')

                # Clear existing data
                session.query(Alumni).delete()

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
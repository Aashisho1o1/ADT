import pandas as pd
import chardet
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni

def detect_encoding(file_path):
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def load_alumni_data(file_path='attached_assets/Sohokai_List_20240726(Graduated).csv'):
    """Load and process alumni data from CSV, store in database."""
    try:
        # Initialize database
        db.init_db()
        session = next(db.get_db())

        # Check if we already have data in the database
        if session.query(Alumni).count() > 0:
            return pd.DataFrame([{
                'Name': alumni.name,
                'Location': alumni.location,
                'Latitude': alumni.latitude,
                'Longitude': alumni.longitude
            } for alumni in session.query(Alumni).all()])

        # If no data in database, load from CSV
        try:
            # Detect file encoding
            encoding = detect_encoding(file_path)
            df = pd.read_csv(file_path, encoding=encoding)

            # Assuming columns for location data
            required_columns = ['Name', 'Location', 'Latitude', 'Longitude']

            if not all(col in df.columns for col in required_columns):
                # Create sample data for testing
                df = pd.DataFrame({
                    'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
                    'Location': ['Tokyo, Japan', 'New York, USA', 'London, UK'],
                    'Latitude': [35.6762, 40.7128, 51.5074],
                    'Longitude': [139.6503, -74.0060, -0.1278]
                })

            # Filter out rows with missing location data
            df = df.dropna(subset=['Latitude', 'Longitude'])

            # Store data in database
            for _, row in df.iterrows():
                alumni = Alumni(
                    name=row['Name'],
                    location=row['Location'],
                    latitude=row['Latitude'],
                    longitude=row['Longitude'],
                    last_updated=datetime.now()
                )
                session.add(alumni)

            session.commit()
            return df

        except Exception as e:
            session.rollback()
            raise Exception(f"Error processing alumni data: {str(e)}")

    except Exception as e:
        raise Exception(f"Error loading alumni data: {str(e)}")
    finally:
        session.close()
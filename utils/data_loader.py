import os
import logging
import pandas as pd
import streamlit as st
from datetime import datetime
from .database import Alumni, get_db_session

# Configure logging
logger = logging.getLogger(__name__)

@st.cache_data(ttl=3600)
def load_alumni_data(_=None):
    """Load alumni data with database and CSV fallbacks."""
    # Try database first
    df, metadata = load_from_database()
    if df is not None:
        return df, metadata
        
    # Fallback to CSV
    logger.info("Database loading failed, using CSV fallback")
    return load_from_csv()

def load_from_database():
    """Load alumni data from database with error handling."""
    try:
        with get_db_session() as session:
            if session is None:
                return None, None
                
            # Fetch all records with batch size hint for large datasets
            query = session.query(Alumni).order_by(Alumni.id).yield_per(1000)
            records = list(query)
            
            if not records:
                logger.warning("No records found in database")
                return None, None
                
            # Process records more efficiently using list comprehension
            # Pre-allocate lists for better performance
            names = []
            locations = []
            lats = []
            lons = []
            valid_coords = []
            invalid_coords = 0
            
            for record in records:
                # Direct float conversion - coordinates from DB should already be floats
                lat = record.latitude
                lon = record.longitude
                is_valid = (lat != 0 or lon != 0)
                
                if not is_valid:
                    invalid_coords += 1
                
                names.append(record.name)
                locations.append(record.location)
                lats.append(lat)
                lons.append(lon)
                valid_coords.append(is_valid)
            
            # Create DataFrame directly from lists (more efficient than list of dicts)
            df = pd.DataFrame({
                'Name': names,
                'Location': locations,
                'Latitude': lats,
                'Longitude': lons,
                'Has_Valid_Coords': valid_coords
            })
            
            metadata = {
                "total_records": len(records),
                "invalid_coords": invalid_coords,
                "source": "database"
            }
            
            logger.info(f"Loaded {len(records)} records from database")
            return df, metadata
            
    except Exception as e:
        logger.error(f"Database loading error: {e}")
        return None, None

def load_from_csv():
    """Load data from CSV files with error handling."""
    try:
        # Check for CSV files in priority order
        csv_paths = [
            'assets/combo.csv',
            'attached_assets/combo3.csv'
        ]
        
        for path in csv_paths:
            if not os.path.exists(path):
                continue
                
            # Found a CSV file
            logger.info(f"Loading data from {path}")
            
            # Handle different CSV formats
            is_combo = 'combo' in path
            df = pd.read_csv(path, skiprows=1 if is_combo else 0)
            
            # Process different CSV formats
            if 'lat' in df.columns and 'lon' in df.columns:
                # Process combo3.csv format
                try:
                    # Convert coordinates to numeric once
                    lat_series = pd.to_numeric(df['lat'], errors='coerce').fillna(0.0)
                    lon_series = pd.to_numeric(df['lon'], errors='coerce').fillna(0.0)
                    
                    # Vectorized location building
                    city = df.get('original_City', pd.Series([''] * len(df))).fillna('')
                    state = df.get('original_State', pd.Series([''] * len(df))).fillna('')
                    country = df.get('original_Country', pd.Series([''] * len(df))).fillna('')
                    location_series = (city + ' ' + state + ' ' + country).str.strip()
                    
                    alumni_data = pd.DataFrame({
                        'Name': df['original_First Name'].fillna('') + ' ' + df['original_Prim_Last'].fillna(''),
                        'Location': location_series,
                        'Latitude': lat_series,
                        'Longitude': lon_series,
                        'Has_Valid_Coords': (lat_series != 0) | (lon_series != 0)
                    })
                except Exception as e:
                    logger.error(f"Error processing CSV data: {e}")
                    # Create an empty dataframe with the right structure
                    alumni_data = pd.DataFrame(columns=['Name', 'Location', 'Latitude', 'Longitude', 'Has_Valid_Coords'])
            else:
                # Handle standard format
                alumni_data = df.copy()
                
                # Convert latitude and longitude to numeric once
                if 'Latitude' in alumni_data.columns:
                    alumni_data['Latitude'] = pd.to_numeric(alumni_data['Latitude'], errors='coerce').fillna(0.0)
                else:
                    alumni_data['Latitude'] = 0.0
                    
                if 'Longitude' in alumni_data.columns:
                    alumni_data['Longitude'] = pd.to_numeric(alumni_data['Longitude'], errors='coerce').fillna(0.0)
                else:
                    alumni_data['Longitude'] = 0.0
                    
                if 'Has_Valid_Coords' not in alumni_data:
                    alumni_data['Has_Valid_Coords'] = (alumni_data['Latitude'] != 0) | (alumni_data['Longitude'] != 0)
                    
            # Clean up data - only fillna for non-numeric columns
            for col in alumni_data.columns:
                if col not in ['Latitude', 'Longitude', 'Has_Valid_Coords']:
                    alumni_data[col] = alumni_data[col].fillna('')
            
            # Count invalid coordinates
            invalid_coords = len(alumni_data) - alumni_data['Has_Valid_Coords'].sum()
            
            logger.info(f"Loaded {len(alumni_data)} records from CSV with {invalid_coords} invalid coordinates")
            return alumni_data, {
                "total_records": len(alumni_data),
                "invalid_coords": invalid_coords,
                "source": "csv"
            }
            
        # No CSV files found - return a default minimal DataFrame
        logger.error("No CSV files found")
        empty_df = pd.DataFrame({
            'Name': ['Sample User'],
            'Location': ['Default Location'],
            'Latitude': [0.0],  # Explicit float
            'Longitude': [0.0],  # Explicit float
            'Has_Valid_Coords': [False]
        })
        return empty_df, {
            "total_records": 0, 
            "invalid_coords": 0, 
            "source": "default"
        }
        
    except Exception as e:
        logger.error(f"CSV loading error: {e}")
        # Return an empty DataFrame with the required columns
        empty_df = pd.DataFrame({
            'Name': ['Sample User'],
            'Location': ['Error Location'],
            'Latitude': [0.0],  # Explicit float
            'Longitude': [0.0],  # Explicit float
            'Has_Valid_Coords': [False]
        })
        return empty_df, {
            "total_records": 0, 
            "invalid_coords": 0, 
            "source": "error"
        }
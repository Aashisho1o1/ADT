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
                
            # Fetch all records (with batching for large datasets)
            query = session.query(Alumni).order_by(Alumni.id)
            records = query.all()
            
            if not records:
                logger.warning("No records found in database")
                return None, None
                
            # Process records
            data = []
            invalid_coords = 0
            
            for record in records:
                # Ensure coordinates are floats
                try:
                    lat = float(record.latitude)
                    lon = float(record.longitude)
                    valid_coords = lat != 0 or lon != 0
                except (ValueError, TypeError):
                    lat = 0.0
                    lon = 0.0
                    valid_coords = False
                    
                if not valid_coords:
                    invalid_coords += 1
                    
                data.append({
                    'Name': record.name,
                    'Location': record.location,
                    'Latitude': lat,  # Store as float
                    'Longitude': lon,  # Store as float
                    'Has_Valid_Coords': valid_coords
                })
                
            df = pd.DataFrame(data)
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
                    # Convert coordinates to numeric first
                    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                    
                    alumni_data = pd.DataFrame({
                        'Name': df['original_First Name'].fillna('') + ' ' + df['original_Prim_Last'].fillna(''),
                        'Location': df.apply(
                            lambda row: f"{row.get('original_City', '')} {row.get('original_State', '')} {row.get('original_Country', '')}".strip(),
                            axis=1
                        ),
                        'Latitude': df['lat'].astype(float),
                        'Longitude': df['lon'].astype(float),
                        'Has_Valid_Coords': (~df['lat'].isna() & ~df['lon'].isna() & 
                                           (df['lat'] != 0) & (df['lon'] != 0))
                    })
                except Exception as e:
                    logger.error(f"Error processing CSV data: {e}")
                    # Create an empty dataframe with the right structure
                    alumni_data = pd.DataFrame(columns=['Name', 'Location', 'Latitude', 'Longitude', 'Has_Valid_Coords'])
            else:
                # Handle standard format
                alumni_data = df.copy()
                
                # Convert latitude and longitude to numeric
                if 'Latitude' in alumni_data.columns:
                    alumni_data['Latitude'] = pd.to_numeric(alumni_data['Latitude'], errors='coerce').fillna(0.0)
                if 'Longitude' in alumni_data.columns:
                    alumni_data['Longitude'] = pd.to_numeric(alumni_data['Longitude'], errors='coerce').fillna(0.0)
                    
                if 'Has_Valid_Coords' not in alumni_data:
                    alumni_data['Has_Valid_Coords'] = (alumni_data['Latitude'] != 0) & (alumni_data['Longitude'] != 0)
                    
            # Clean up data
            alumni_data = alumni_data.fillna('')
            
            # Make sure coordinates are numeric
            alumni_data['Latitude'] = pd.to_numeric(alumni_data['Latitude'], errors='coerce').fillna(0.0)
            alumni_data['Longitude'] = pd.to_numeric(alumni_data['Longitude'], errors='coerce').fillna(0.0)
            
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
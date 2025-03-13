import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Alumni, get_db, engine
import streamlit as st
import time
import os.path

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_alumni_data(_=None):
    """Load alumni data with fallback options"""
    try:
        # Try database first
        if engine is not None:
            session = next(get_db())
            if session is not None:
                try:
                    # Use pagination for better memory management
                    page_size = 500
                    offset = 0
                    all_records = []

                    while True:
                        # Fetch records in batches
                        batch = session.query(Alumni)\
                            .order_by(Alumni.id)\
                            .limit(page_size)\
                            .offset(offset)\
                            .all()

                        if not batch:
                            break

                        all_records.extend(batch)
                        offset += page_size

                    total_records = len(all_records)

                    if not all_records:
                        return None, None

                    # Process records in batches for better memory efficiency
                    data = []
                    invalid_coords = 0

                    for record in all_records:
                        # Track records with missing coordinates
                        if record.latitude == 0 and record.longitude == 0:
                            invalid_coords += 1
                            # Use Tokyo coordinates as default for visualization
                            record.latitude = 35.6762
                            record.longitude = 139.6503

                        data.append({
                            'Name': record.name,
                            'Location': record.location,
                            'Latitude': record.latitude,
                            'Longitude': record.longitude,
                            'Has_Valid_Coords': not (record.latitude == 35.6762 and record.longitude == 139.6503)
                        })

                    df = pd.DataFrame(data)

                    metadata = {
                        'total_records': total_records,
                        'invalid_coords': invalid_coords
                    }

                    return df, metadata

                except Exception as e:
                    st.warning(f"Database query failed: {str(e)}. Trying CSV fallback.")
                    return load_from_csv()
                finally:
                    if session:
                        session.close()
        else:
            # No database connection, use CSV
            return load_from_csv()
    except Exception as e:
        st.warning(f"Error in data loader: {str(e)}. Trying CSV fallback.")
        return load_from_csv()

def load_from_csv():
    """Fallback to load data from CSV when database is unavailable"""
    try:
        # Check for various CSV locations
        potential_paths = [
            'assets/combo 3.csv',
            'assets/simplified_alumni.csv',
            'attached_assets/combo 3.csv'
        ]
        
        csv_path = None
        for path in potential_paths:
            if os.path.exists(path):
                csv_path = path
                break
                
        if csv_path is None:
            # If no CSV found, return empty data with metadata
            st.error("No data sources available - neither database nor CSV files found")
            return None, {"total_records": 0, "invalid_coords": 0}
            
        # Load and process CSV
        df = pd.read_csv(csv_path, skiprows=1 if 'combo' in csv_path else 0)
        
        # Map columns appropriately based on which CSV we have
        if 'lat' in df.columns and 'lon' in df.columns:
            alumni_data = pd.DataFrame({
                'Name': df['original_First Name'].fillna('') + ' ' + df['original_Prim_Last'].fillna(''),
                'Location': df.apply(
                    lambda row: f"{row.get('original_City', '')} {row.get('original_State', '')} {row.get('original_Country', '')}".strip(),
                    axis=1
                ),
                'Latitude': df['lat'],
                'Longitude': df['lon'],
                'Has_Valid_Coords': (df['lat'] != 0) & (df['lon'] != 0)
            })
        else:
            # Handle other CSV formats or simple CSV with direct columns
            alumni_data = df
            if 'Has_Valid_Coords' not in alumni_data:
                alumni_data['Has_Valid_Coords'] = True
        
        # Clean up data
        alumni_data = alumni_data.fillna('')
        alumni_data = alumni_data.dropna(subset=['Name', 'Latitude', 'Longitude'])
        
        invalid_coords = (~alumni_data['Has_Valid_Coords']).sum()
        
        metadata = {
            'total_records': len(alumni_data),
            'invalid_coords': invalid_coords,
            'source': 'csv'
        }
        
        return alumni_data, metadata
        
    except Exception as e:
        st.error(f"CSV fallback failed: {str(e)}")
        return None, None
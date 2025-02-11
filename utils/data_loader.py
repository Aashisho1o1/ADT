import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni
import streamlit as st
import time

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_alumni_data(_=None):
    """Load alumni data from PostgreSQL database with improved performance for large datasets."""
    try:
        session = next(db.get_db())
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
                st.error("No alumni records found in database")
                return None

            # Process records in batches for better memory efficiency
            data = []
            invalid_coords = 0

            for record in all_records:
                # Track records with missing coordinates
                if record.latitude == 0 and record.longitude == 0:
                    invalid_coords += 1
                    st.warning(f"⚠️ Missing coordinates for: {record.name} at {record.location}")
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

            # Display data quality metrics
            st.info(f"""
            📊 Alumni Data Summary:
            - Total Records: {total_records}
            - Records with Valid Coordinates: {total_records - invalid_coords}
            - Records with Default Coordinates: {invalid_coords}
            """)

            if not df.empty:
                # Show sample of the data (limit to avoid memory issues)
                with st.expander("🔍 View Sample Data"):
                    st.dataframe(
                        df[['Name', 'Location', 'Has_Valid_Coords']].head(100),
                        hide_index=True
                    )

            return df

        except Exception as e:
            st.error(f"Error fetching alumni data: {str(e)}")
            return None
        finally:
            session.close()

    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None
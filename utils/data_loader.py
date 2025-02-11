import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_alumni_data(_=None):
    """Load alumni data from PostgreSQL database with improved handling of missing coordinates."""
    try:
        session = next(db.get_db())
        try:
            # Fetch all alumni records
            alumni_records = session.query(Alumni).all()
            total_records = len(alumni_records)

            if not alumni_records:
                st.error("No alumni records found in database")
                return None

            # Convert to DataFrame with validation
            data = []
            invalid_coords = 0

            for record in alumni_records:
                # Track records with missing coordinates
                if record.latitude == 0 and record.longitude == 0:
                    invalid_coords += 1
                    # For records with invalid coordinates, mark them visually
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
                # Show sample of the data
                with st.expander("🔍 View Sample Data"):
                    st.dataframe(
                        df[['Name', 'Location', 'Has_Valid_Coords']].head(),
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
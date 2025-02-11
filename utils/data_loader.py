import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from . import database as db
from .database import Alumni
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_alumni_data(_=None):
    """Load alumni data from PostgreSQL database with caching."""
    try:
        session = next(db.get_db())
        try:
            # Fetch all alumni records
            alumni_records = session.query(Alumni).all()

            if not alumni_records:
                st.error("No alumni records found in database")
                return None

            # Convert to DataFrame
            data = [{
                'Name': record.name,
                'Location': record.location,
                'Latitude': record.latitude,
                'Longitude': record.longitude
            } for record in alumni_records]

            return pd.DataFrame(data)

        except Exception as e:
            st.error(f"Error fetching alumni data: {str(e)}")
            return None
        finally:
            session.close()

    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None
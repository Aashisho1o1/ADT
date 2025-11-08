import requests
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from . import database as db
from .database import DisasterEvent
import streamlit as st
from sqlalchemy import create_engine
import logging

# Set up logging at the top of your file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Access secrets
if "DATABASE_URL" in st.secrets:
    db_url = st.secrets["DATABASE_URL"]
else:
    db_url = None  # Fallback for local development

# Optimize caching for better performance
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def fetch_eonet_data():
    """Fetch natural disaster data from NASA's EONET API with optimized caching."""
    try:
        # Correctly access secrets
        api_key = None
        
        # Try to get from secrets in different ways
        if "nasa" in st.secrets:
            # If you have a nested structure like [nasa] api_key = "value"
            api_key = st.secrets["nasa"]["api_key"] 
        elif "NASA_API_KEY" in st.secrets:
            # If you have a flat structure like NASA_API_KEY = "value"
            api_key = st.secrets["NASA_API_KEY"]
            
        base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"
        
        # Optimize query parameters
        params = {
            "status": "open",
            "days": 3,
            "limit": 25,
            "api_key": api_key
        }
        
        # Send request
        response = requests.get(base_url, params=params)
        
        # Check status and parse JSON properly
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()  # Parse JSON
        
        # Access events (ensure it's a list)
        events = data.get("events", []) if isinstance(data, dict) else []
        
        return events
        
    except Exception as e:
        st.error(f"Error in fetch_eonet_data: {str(e)}")
        # Add debugging information
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return []

def filter_disasters_by_type(disaster_data, selected_types):
    """Filter disasters based on selected types with optimized matching."""
    # Replace st.write with logger.debug
    logger.debug(f"Disaster data type: {type(disaster_data)}")
    
    if isinstance(disaster_data, list) and len(disaster_data) > 0:
        logger.debug(f"First item type: {type(disaster_data[0])}")

    if not disaster_data or not selected_types:
        return []

    # Pre-computed type mapping for O(1) lookup
    type_mapping = {
        "wildfires": "Wildfires",
        "fire": "Wildfires",
        "severestorms": "Severe Storms",
        "severe": "Severe Storms",
        "storms": "Severe Storms",
        "volcanoes": "Volcanoes",
        "volcano": "Volcanoes",
        "earthquakes": "Earthquakes",
        "earthquake": "Earthquakes"
    }

    # Convert selected types to a set for O(1) lookup
    selected_set = set(selected_types)

    # Filter using more efficient logic
    filtered = []
    for d in disaster_data:
        try:
            # Extract category id and normalize
            category_id = d['categories'][0]['id'].lower()
            # Get first part before hyphen
            category_key = category_id.split('-')[0]
            
            # Map to standard type and check if selected
            if category_key in type_mapping and type_mapping[category_key] in selected_set:
                filtered.append(d)
        except (KeyError, IndexError):
            continue
    
    return filtered

# Modified database connection code
def get_db_connection():
    try:
        if "DATABASE_URL" in st.secrets:
            return create_engine(st.secrets["DATABASE_URL"])
        else:
            st.warning("No database configuration found")
            return None
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None
import requests
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from . import database as db
from .database import DisasterEvent
import streamlit as st

# Optimize caching for better performance
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def fetch_eonet_data():
    """Fetch natural disaster data from NASA's EONET API with optimized caching."""
    api_key = "hjp6PQBMN7kiHJf28k6EuTLIowh0AOcxPtxLkk1c"
    base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"

    # Optimize query parameters for faster response
    params = {
        "status": "open",
        "days": 3,  # Reduced to last 3 days for faster response
        "limit": 25,  # Further limited results for better performance
        "categories": "wildfires,severeStorms,volcanoes,earthquakes",  # Pre-filter categories
        "api_key": api_key
    }

    try:
        # Progress indicator for API request
        progress_bar = st.progress(0)
        progress_bar.progress(25, 'Connecting to EONET API...')

        response = requests.get(base_url, params=params, timeout=5)  # Reduced timeout
        progress_bar.progress(50, 'Processing response...')

        if response.status_code != 200:
            st.error("⚠️ Unable to fetch disaster data")
            return []

        data = response.json()
        if not data.get('events'):
            return []

        # Process events with minimal data structure
        processed_events = []
        for event in data['events']:
            try:
                if not (geometry := event.get('geometry', [{}])[0]):
                    continue

                coords = geometry.get('coordinates')
                if not coords:
                    continue

                # Minimal event structure
                processed_events.append({
                    'id': event['id'],
                    'title': event['title'],
                    'categories': [{'title': event['categories'][0]['title'], 
                                  'id': event['categories'][0]['id']}],
                    'geometry': [{'coordinates': coords}]
                })

            except (KeyError, IndexError):
                continue

        progress_bar.progress(100, 'Complete!')
        progress_bar.empty()

        return processed_events

    except Exception:
        st.error("🚫 Connection error")
        return []

def filter_disasters_by_type(disasters, selected_types):
    """Filter disasters based on selected types with optimized matching."""
    if not disasters or not selected_types:
        return []

    # Pre-computed type sets for faster lookup
    type_sets = {
        "Wildfires": {"wildfires", "fire"},
        "Severe Storms": {"severestorms", "severe-storms", "storms"},
        "Volcanoes": {"volcanoes", "volcano"},
        "Earthquakes": {"earthquakes", "earthquake"}
    }

    # Create single set of terms for faster matching
    selected_terms = set().union(*(type_sets[t] for t in selected_types if t in type_sets))

    # Use generator expression for memory efficiency
    return [d for d in disasters 
            if d['categories'][0]['id'].lower().split('-')[0] in selected_terms]
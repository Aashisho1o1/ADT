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
        "days": 7,  # Reduced to last week for faster response
        "limit": 50,  # Limit results for better performance
        "api_key": api_key
    }

    try:
        with st.spinner('🌍 Fetching disaster data...'):
            # Progress indicator for API request
            progress_bar = st.progress(0)
            progress_bar.progress(25, 'Connecting to EONET API...')

            response = requests.get(base_url, params=params, timeout=5)  # Reduced timeout
            progress_bar.progress(50, 'Processing response...')

            if response.status_code != 200:
                st.error("⚠️ Unable to fetch disaster data")
                return []

            data = response.json()
            if not isinstance(data, dict) or 'events' not in data:
                return []

            events = data['events']
            if not events:
                return []

            progress_bar.progress(75, 'Processing events...')

            # Process events with minimal data structure
            processed_events = []
            for event in events:
                try:
                    if not event.get('geometry'):
                        continue

                    # Only process relevant disasters
                    category_id = event.get('categories', [{}])[0].get('id', '').lower()
                    if not any(term in category_id for term in ['wildfires', 'severstorms', 'volcanoes', 'earthquakes']):
                        continue

                    geometry = event['geometry'][0]
                    if not geometry.get('coordinates'):
                        continue

                    # Minimal event structure for better performance
                    processed_event = {
                        'id': event['id'],
                        'title': event['title'],
                        'categories': [{'title': cat['title'], 'id': cat['id']}
                                     for cat in event['categories'][:1]],
                        'geometry': [{
                            'coordinates': geometry['coordinates']
                        }]
                    }
                    processed_events.append(processed_event)

                except (KeyError, IndexError):
                    continue

            progress_bar.progress(100, 'Complete!')
            time.sleep(0.5)  # Brief pause to show completion
            progress_bar.empty()

            if processed_events:
                st.success(f"✅ Found {len(processed_events)} active disasters")
            return processed_events

    except requests.exceptions.RequestException:
        st.error("🚫 Connection error - please try again")
        return []
    except Exception:
        st.error("🚫 Unexpected error fetching disaster data")
        return []

def filter_disasters_by_type(disasters, selected_types):
    """Filter disasters based on selected types with optimized matching."""
    if not disasters or not selected_types:
        return []

    # Use sets for faster lookups
    type_mapping = {
        "Wildfires": {"wildfires", "fire"},
        "Severe Storms": {"severestorms", "severe-storms", "storms"},
        "Volcanoes": {"volcanoes", "volcano"},
        "Earthquakes": {"earthquakes", "earthquake"}
    }

    selected_terms = set()
    for type_name in selected_types:
        selected_terms.update(type_mapping.get(type_name, set()))

    return [
        disaster for disaster in disasters
        if any(term in disaster['categories'][0]['id'].lower()
               for term in selected_terms)
    ]
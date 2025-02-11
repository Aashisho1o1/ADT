import requests
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from . import database as db
from .database import DisasterEvent
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_eonet_data():
    """Fetch natural disaster data from NASA's EONET API with improved error handling."""
    api_key = "hjp6PQBMN7kiHJf28k6EuTLIowh0AOcxPtxLkk1c"
    base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"

    # Query parameters with default values that work well
    params = {
        "status": "open",
        "days": 60,
        "api_key": api_key
    }

    try:
        st.info("Fetching disaster data from EONET...")
        response = requests.get(base_url, params=params, timeout=10)
        st.debug(f"API Response Status: {response.status_code}")
        st.debug(f"API URL: {response.url}")

        response.raise_for_status()
        data = response.json()

        if 'events' not in data:
            st.warning("No events found in API response")
            return []

        events = data['events']
        st.success(f"Retrieved {len(events)} events from EONET API")

        processed_events = []
        for event in events:
            try:
                # Extract and validate required fields
                if not event.get('geometry') or not event.get('categories'):
                    continue

                # Get the most recent geometry
                geometry = event['geometry'][0]
                if 'coordinates' not in geometry:
                    continue

                # Create standardized event structure
                processed_event = {
                    'id': event['id'],
                    'title': event['title'],
                    'categories': event['categories'],
                    'geometry': [{
                        'coordinates': geometry['coordinates'],
                        'date': geometry.get('date', datetime.now().isoformat())
                    }]
                }
                processed_events.append(processed_event)

            except (KeyError, IndexError) as e:
                st.debug(f"Skipping malformed event: {str(e)}")
                continue

        st.success(f"Successfully processed {len(processed_events)} disaster events")
        return processed_events

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching EONET data: {str(e)}")
        return []

def filter_disasters_by_type(disasters, selected_types):
    """Filter disasters based on selected types with improved type mapping."""
    if not selected_types:
        return disasters

    # Expanded type mapping for better matching
    type_mapping = {
        "Wildfires": ["wildfires", "fire"],
        "Severe Storms": ["severeStorms", "severe-storms", "storms"],
        "Volcanoes": ["volcanoes", "volcano"],
        "Earthquakes": ["earthquakes", "earthquake"]
    }

    filtered = []
    for disaster in disasters:
        try:
            categories = disaster.get('categories', [])
            if not categories:
                continue

            category = categories[0].get('id', '').lower()
            title = categories[0].get('title', '').lower()

            for selected_type in selected_types:
                mapped_terms = type_mapping.get(selected_type, [])
                if any(term.lower() in category or term.lower() in title for term in mapped_terms):
                    filtered.append(disaster)
                    break

        except (KeyError, IndexError) as e:
            st.debug(f"Error filtering disaster: {str(e)}")
            continue

    st.info(f"Filtered to {len(filtered)} relevant disasters")
    return filtered
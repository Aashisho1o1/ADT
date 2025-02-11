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

        if response.status_code != 200:
            st.error(f"API Error: Status {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, dict) or 'events' not in data:
            st.error("Invalid API response format")
            return []

        events = data['events']
        if not events:
            st.warning("No active disasters found in the current period")
            return []

        st.success(f"Retrieved {len(events)} events from EONET API")

        processed_events = []
        for event in events:
            try:
                # Extract and validate required fields
                if not all(key in event for key in ['id', 'title', 'categories', 'geometry']):
                    continue

                geometry = event['geometry'][0]
                if not geometry or 'coordinates' not in geometry:
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
                st.warning(f"Skipping malformed event data: {event.get('title', 'Unknown event')}")
                continue

        if not processed_events:
            st.warning("No valid disaster events found after processing")
            return []

        st.success(f"Successfully processed {len(processed_events)} disaster events")
        return processed_events

    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to EONET API: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Unexpected error processing disaster data: {str(e)}")
        return []

def filter_disasters_by_type(disasters, selected_types):
    """Filter disasters based on selected types with improved type mapping."""
    if not disasters:
        return []

    if not selected_types:
        st.warning("No disaster types selected")
        return []

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
            st.warning(f"Error processing disaster category for: {disaster.get('title', 'Unknown')}")
            continue

    if not filtered:
        st.warning(f"No disasters found matching selected types: {', '.join(selected_types)}")
    else:
        st.success(f"Found {len(filtered)} disasters matching selected types")

    return filtered
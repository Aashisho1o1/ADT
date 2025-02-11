import requests
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from . import database as db
from .database import DisasterEvent
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_eonet_data():
    """Fetch natural disaster data from NASA's EONET API with improved caching and performance."""
    api_key = "hjp6PQBMN7kiHJf28k6EuTLIowh0AOcxPtxLkk1c"
    base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"

    params = {
        "api_key": api_key,
        "status": "open",
        "days": 30,
        "limit": 100  # Limit to most recent events
    }

    session = next(db.get_db())

    try:
        # First try to get recent events from database
        cached_events = session.query(DisasterEvent).all()
        if cached_events:
            events = []
            for event in cached_events:
                events.append({
                    'id': event.eonet_id,
                    'title': event.title,
                    'categories': [{'title': event.disaster_type}],
                    'geometry': [{
                        'coordinates': [event.longitude, event.latitude],
                        'date': event.start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }]
                })
            return events

        # If no cached data, fetch from API
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if 'events' not in data:
            return []

        # Batch process events
        events = data['events']
        disaster_objects = []

        for event in events:
            try:
                coords = event['geometry'][0]['coordinates']
                disaster = DisasterEvent(
                    eonet_id=event['id'],
                    title=event['title'],
                    disaster_type=event['categories'][0]['title'],
                    latitude=coords[1],
                    longitude=coords[0],
                    start_date=datetime.strptime(event['geometry'][0]['date'], "%Y-%m-%dT%H:%M:%SZ")
                )
                disaster_objects.append(disaster)
            except (KeyError, IndexError):
                continue

        # Batch update database
        if disaster_objects:
            session.query(DisasterEvent).delete()
            session.bulk_save_objects(disaster_objects)
            session.commit()

        return events

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching disaster data: {str(e)}")
        # Return cached data if available, empty list otherwise
        return [event.__dict__ for event in cached_events] if cached_events else []

    finally:
        session.close()

def filter_disasters_by_type(disasters, selected_types):
    """Filter disasters based on selected types with improved matching."""
    if not selected_types:
        return disasters

    type_mapping = {
        "Wildfires": ["wildfires", "fire"],
        "Severe Storms": ["severeStorms", "storm"],
        "Volcanoes": ["volcanoes", "volcano"],
        "Earthquakes": ["earthquakes", "earthquake"]
    }

    filtered = []
    for disaster in disasters:
        try:
            disaster_category = disaster['categories'][0]['id'].lower()
            for disaster_type in selected_types:
                # Check if any of the mapped terms match the category
                if any(term.lower() in disaster_category 
                      for term in type_mapping.get(disaster_type, [])):
                    filtered.append(disaster)
                    break
        except (KeyError, IndexError):
            continue

    return filtered
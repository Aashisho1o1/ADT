import requests
from datetime import datetime, timedelta
import time

def fetch_eonet_data():
    """Fetch natural disaster data from NASA's EONET API with improved error handling."""
    api_key = "hjp6PQBMN7kiHJf28k6EuTLIowh0AOcxPtxLkk1c"
    base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"

    # Get events from the last 30 days
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "api_key": api_key,
        "status": "open",
        "days": 30
    }

    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code == 429:  # Rate limit exceeded
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("Rate limit exceeded. Please try again later.")

            response.raise_for_status()
            data = response.json()

            if 'events' not in data:
                return []  # Return empty list if no events found

            return data['events']

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception("Request timed out. Please try again later.")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching EONET data: {str(e)}")

    return []  # Return empty list if all retries failed

def filter_disasters_by_type(disasters, selected_types):
    """Filter disasters based on selected types with improved matching."""
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
            continue  # Skip malformed disaster entries

    return filtered
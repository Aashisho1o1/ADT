"""Core logic: load disaster events and alumni, find alumni near events.

No Streamlit here, so everything can be tested on its own.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
DATA_DIR = Path(__file__).parent / "data"
EARTH_RADIUS_KM = 6371.0
EVENT_COLUMNS = ["title", "category", "date", "lat", "lon"]
ALUMNI_COLUMNS = ["name", "city", "country", "lat", "lon"]


def fetch_events(days=30, timeout=10):
    """Open EONET events from the last `days` days.

    Returns (events, is_live). Falls back to the saved snapshot if the API fails.
    """
    try:
        resp = requests.get(EONET_URL, params={"status": "open", "days": days}, timeout=timeout)
        resp.raise_for_status()
        return parse_events(resp.json()["events"]), True
    except (requests.RequestException, ValueError, KeyError):
        snapshot = json.loads((DATA_DIR / "events.json").read_text())
        return parse_events(snapshot["events"]), False


def parse_events(raw_events):
    """One row per event, at its most recent position. Malformed events are skipped."""
    rows = []
    for event in raw_events:
        try:
            latest = max(event["geometry"], key=lambda g: g["date"])
            lon, lat = _lon_lat(latest)
            rows.append({
                "title": event["title"],
                "category": event["categories"][0]["title"],
                "date": latest["date"][:10],
                "lat": lat,
                "lon": lon,
            })
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def _lon_lat(geometry):
    if geometry["type"] == "Point":
        lon, lat = geometry["coordinates"]
    else:  # Polygon: use the average of the outer ring
        lon, lat = np.mean(geometry["coordinates"][0], axis=0)
    return float(lon), float(lat)


def load_alumni(path=DATA_DIR / "alumni.csv"):
    """Alumni with valid coordinates. Expects columns: name, city, country, lat, lon."""
    df = pd.read_csv(path, usecols=ALUMNI_COLUMNS)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    valid = df["lat"].between(-90, 90) & df["lon"].between(-180, 180)
    return df[valid].reset_index(drop=True)


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Works on scalars and numpy arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def find_nearby(alumni, events, radius_km):
    """Every (alumnus, event) pair within radius_km, closest first."""
    # Distance matrix: one row per alumnus, one column per event.
    dist = haversine_km(
        alumni["lat"].to_numpy()[:, None], alumni["lon"].to_numpy()[:, None],
        events["lat"].to_numpy()[None, :], events["lon"].to_numpy()[None, :],
    )
    i, j = np.nonzero(dist <= radius_km)
    nearby = pd.DataFrame({
        "name": alumni["name"].to_numpy()[i],
        "city": alumni["city"].to_numpy()[i],
        "event": events["title"].to_numpy()[j],
        "category": events["category"].to_numpy()[j],
        "distance_km": dist[i, j].round(1),
    })
    return nearby.sort_values("distance_km", ignore_index=True)

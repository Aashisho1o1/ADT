"""Offline tests for core.py. Run with: python -m pytest"""
import pandas as pd
import pytest
import requests

import core


def event(title="Fire", category="Wildfires", geometry=None):
    geometry = geometry or [{"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [10.0, 20.0]}]
    return {"title": title, "categories": [{"title": category}], "geometry": geometry}


def alumni(*rows):
    return pd.DataFrame(rows, columns=["name", "city", "country", "lat", "lon"])


def offline(*args, **kwargs):
    raise requests.ConnectionError("offline")


# --- distance -------------------------------------------------------------

def test_haversine_london_paris():
    assert core.haversine_km(51.5074, -0.1278, 48.8566, 2.3522) == pytest.approx(343.5, abs=1)


def test_haversine_same_point_is_zero():
    assert core.haversine_km(10, 20, 10, 20) == 0


# --- parsing events -------------------------------------------------------

def test_parse_uses_latest_position():
    geometry = [
        {"date": "2026-01-03T00:00:00Z", "type": "Point", "coordinates": [3.0, 30.0]},
        {"date": "2026-01-01T00:00:00Z", "type": "Point", "coordinates": [1.0, 10.0]},
    ]
    row = core.parse_events([event(geometry=geometry)]).iloc[0]
    assert (row.lon, row.lat, row.date) == (3.0, 30.0, "2026-01-03")


def test_parse_polygon_uses_center():
    square = [{"date": "2026-01-01", "type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2]]]}]
    row = core.parse_events([event(geometry=square)]).iloc[0]
    assert (row.lon, row.lat) == (1.0, 1.0)


def test_parse_skips_malformed_events():
    bad = [
        {"title": "no category", "categories": [], "geometry": event()["geometry"]},
        {"title": "no geometry", "categories": [{"title": "X"}], "geometry": []},
        {"title": "no fields"},
    ]
    events = core.parse_events(bad + [event("ok")])
    assert events["title"].tolist() == ["ok"]


def test_parse_empty_has_columns():
    assert list(core.parse_events([]).columns) == core.EVENT_COLUMNS


# --- fetching -------------------------------------------------------------

def test_fetch_falls_back_to_snapshot(monkeypatch):
    monkeypatch.setattr(core.requests, "get", offline)
    events, is_live = core.fetch_events()
    assert not is_live
    assert len(events) > 0


# --- alumni ---------------------------------------------------------------

def test_load_alumni_drops_invalid_coordinates(tmp_path):
    csv = tmp_path / "alumni.csv"
    csv.write_text("name,city,country,lat,lon\nOk,A,B,10,20\nText,A,B,abc,20\nOutOfRange,A,B,95,20\nEmpty,A,B,,\n")
    assert core.load_alumni(csv)["name"].tolist() == ["Ok"]


def test_bundled_alumni_file_loads():
    assert len(core.load_alumni()) == 200


# --- matching -------------------------------------------------------------

def test_find_nearby_respects_radius_and_sorts():
    people = alumni(("Near", "A", "B", 20.0, 10.0), ("Mid", "A", "B", 21.0, 10.0), ("Far", "A", "B", 40.0, 10.0))
    events = core.parse_events([event()])  # at lat 20, lon 10
    nearby = core.find_nearby(people, events, radius_km=200)
    assert nearby["name"].tolist() == ["Near", "Mid"]
    assert nearby["distance_km"].tolist() == [0.0, pytest.approx(111.2, abs=0.5)]


def test_find_nearby_one_row_per_pair():
    people = alumni(("A", "x", "y", 20.0, 10.0))
    events = core.parse_events([event("E1"), event("E2")])
    assert len(core.find_nearby(people, events, radius_km=10)) == 2


def test_find_nearby_handles_empty_inputs():
    people = alumni(("A", "x", "y", 20.0, 10.0))
    events = core.parse_events([event()])
    assert core.find_nearby(people.iloc[:0], events, 100).empty
    assert core.find_nearby(people, events.iloc[:0], 100).empty


# --- app smoke test -------------------------------------------------------

def test_app_runs_offline(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(core.requests, "get", offline)
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    assert at.metric[1].value == "200"

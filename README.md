# 🌍 Alumni Disaster Tracker

**When a natural disaster happens, which of our people are near it?**

A small Streamlit app that pulls live natural-disaster events from NASA's EONET feed, plots them on a world map next to alumni locations, and lists every alumnus within a chosen radius of an active event, closest first.

> **All alumni data in this repository is synthetic.** The 200 names, cities and coordinates in `data/alumni.csv` are randomly generated. They describe no real person. This was a deliberate choice to protect personal information and privacy: a public demo should never expose real names, addresses or locations. See [Privacy and data](#privacy-and-data).

---

## The problem

University alumni offices, NGOs and distributed companies all have the same question after a wildfire, hurricane or volcanic eruption: *who do we need to check on?* Answering it usually means cross-referencing a news map with a spreadsheet by hand.

This app answers it in one screen:

1. Open the app. It loads every open disaster event from the last 30 days.
2. See events (red) and alumni (blue, clustered) on one map. Each event has a shaded circle showing the alert radius.
3. Read the list on the right: who is near which event, and how far away.
4. Adjust the radius or event types in the sidebar. Everything updates instantly.

## Features

- **Live data** from [NASA EONET v3](https://eonet.gsfc.nasa.gov/docs/v3) (no API key needed), cached for 15 minutes.
- **Works offline.** If EONET is unreachable, the app falls back to a saved snapshot (`data/events.json`) and says so on screen.
- **Correct positions for moving events.** EONET stores storms as a time series of points; the app uses each event's most recent position.
- **Event types come from the data**, so new categories (sea and lake ice, floods, and so on) appear automatically.
- **Fast matching.** Distances are computed as one vectorised NumPy operation: 2,000 alumni × 49 events takes about 10 ms.
- **Zero setup.** No database, no secrets, no API keys.

## Quick start

Requires Python 3.12 or newer.

```bash
git clone https://github.com/Aashisho1o1/ADT.git
cd ADT
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

Run the tests:

```bash
pip install pytest
python -m pytest
```

## How it works

```
NASA EONET API ──► fetch_events() ──► parse_events() ──┐
  (fallback: data/events.json)        latest position  │
                                                       ▼
data/alumni.csv ──► load_alumni() ──────────────► find_nearby(radius) ──► app.py
                    drops bad coordinates          haversine matrix         map + table
```

| File | Lines | What it does |
|---|---|---|
| `app.py` | ~70 | The UI only: sidebar filters, three metrics, Folium map, results table. |
| `core.py` | ~90 | All logic, with no Streamlit imports, so it can be tested on its own. |
| `tests/test_core.py` | ~115 | 13 offline tests, including a smoke test of the whole app. |
| `data/alumni.csv` | 200 rows | Synthetic alumni: `name, city, country, lat, lon`. |
| `data/events.json` | 49 events | Saved EONET response, used as offline fallback and test fixture. |

### Key functions in `core.py`

- `fetch_events(days=30)` calls EONET with a 10-second timeout and returns `(events, is_live)`. On any network or parse error it loads the snapshot instead of failing.
- `parse_events(raw)` turns raw EONET JSON into a table with one row per event. It takes the latest point of each event's track, uses the centre of polygon geometries, and skips malformed events instead of crashing.
- `load_alumni(path)` reads the CSV and drops rows with missing or out-of-range coordinates.
- `haversine_km(...)` computes the great-circle distance. It works on single numbers and on whole arrays.
- `find_nearby(alumni, events, radius_km)` builds an alumni × events distance matrix in one step and returns every pair within the radius, sorted by distance.

## Privacy and data

This project handles exactly the kind of data that must be protected: people's names and where they live.

- **The demo uses synthetic data only.** `data/alumni.csv` was generated with a fixed random seed from lists of common first and last names and 40 world cities, with each point randomly shifted by up to about 30 km. It contains no real names, addresses, emails or phone numbers.
- **The data model is minimal by design.** The app only needs a name, a city and coordinates. It does not store or display emails, phone numbers or street addresses.
- **Using real data:** keep the same five columns, keep the file out of version control (add it to `.gitignore`), and run the app privately or behind authentication. Never deploy real personal data to a public URL.
- **No secrets are needed.** EONET is a public API, so there are no keys or passwords to leak.

## Design decisions

| Decision | Why | Trade-off |
|---|---|---|
| **Streamlit** instead of React plus an API | One language and one process; the fastest route to a working, shareable tool. | Less control over the UI; every interaction reruns the script, so caching matters. |
| **CSV instead of a database** | The demo runs with zero setup, and nothing secret is needed to start it. | Not suited to many users editing data at once. A database would be the next step for real use. |
| **NASA EONET** as the data source | Free, global, no API key, covers wildfires, storms, volcanoes and ice. | Event coverage and update speed depend on NASA's feed. |
| **Saved snapshot fallback** | The demo never shows an empty screen, and tests don't need the network. | The snapshot ages, so the app shows a clear notice when it is in use. |
| **Haversine on a sphere** | Simple, vectorised and fast. | Up to about 0.5% off compared with ellipsoid distance, which doesn't matter for a radius in kilometres. |

## Project history

This repository started as a larger prototype: a Postgres database, several data loaders, a geocoding pipeline, and leftover files from experiments with other platforms. It was then audited and cut down on purpose. The full record of what was found and how each issue was resolved is in [`AUDIT.md`](AUDIT.md).

| | Before | After |
|---|---|---|
| Tracked files | 48 | ~13 |
| Python lines | ~1,430 | ~280 (including tests) |
| Setup needed | Postgres, secrets, NASA key | `pip install`, then run |
| Tests | 0 | 13 (offline, a few seconds) |
| Proximity check (2,000 alumni) | 15.5 s | 10 ms |
| Known dependency vulnerabilities | 9 | 0 |

## What I'd build next

1. **Notifications:** email or Slack digest when someone new falls inside the radius.
2. **Event history:** show how close each event came over its lifetime, not just now.
3. **Private data mode:** load a real alumni file behind sign-in, with nothing stored server-side.
4. **More sources:** USGS earthquakes and GDACS alerts, to cover what EONET doesn't.

## Tech stack

Python · Streamlit · pandas · NumPy · Folium · NASA EONET API · pytest

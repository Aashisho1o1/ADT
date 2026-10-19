# Codebase Audit — Alumni Disaster Tracker

Working notes. Record now, fix later (after all phases).
Status legend: OPEN / FIXED. Evidence: VERIFIED (ran it) / INFERRED (read it).

Guiding principle: lean, simple, minimal. Delete before adding.

---

## Phase 1 — Inventory & Understanding (done 2026-10-19)

### What the app does today

1. Opens in a "safe mode" page with debug buttons (DB test, diagnosis).
2. "Load Full Application" button switches to the real app.
3. Real app: loads alumni (Postgres if configured, else `assets/combo.csv`),
   fetches open EONET events from the last 3 days (max 25), draws a Folium map,
   lists alumni within N km of a disaster.

### Runtime call graph (the only code that actually runs)

```
app.py
├─ utils/helpers.py        init_session_state, get_db_url, create_db_engine,
│                          mask_url, show_debug_info, run_database_diagnosis
├─ utils/data_loader.py    load_alumni_data → load_from_database / load_from_csv
│   └─ utils/database.py   Alumni, get_db_session (+ engine/session globals)
├─ utils/disaster_monitor.py  fetch_eonet_data, filter_disasters_by_type
└─ utils/map_handler.py    create_map, calculate_proximity_alerts
```

Everything else in the repo is not reachable from the app.

### Data flow

```
CSV (alumni) ──[4 different loaders, 3 broken]──> Postgres ──> data_loader ──┐
assets/combo.csv ─────────────(fallback)──────────────────────> data_loader ──┤
NASA EONET API ──> disaster_monitor (1h cache) ───────────────────────────────┤
                                                                              v
                                                    map_handler ──> app.py (map + alerts)
```

### What I ran

| Check | Result |
|---|---|
| `pip install -r requirements.txt` (Python 3.13) | FAIL — numpy 1.24.3 / pandas 2.0.3 won't build |
| Unpinned deps + `streamlit run app.py` | OK — boots, health check ok |
| Click "Load Full Application", no secrets.toml | FAIL — "No secrets found" crash |
| Same, with any secret present | OK — 15 fake alumni, map renders, 0 alerts |
| Live EONET (`status=open, days=3`) | 4 events, all storms → demo shows no alerts |
| `import scripts.load_alumni_data` | FAIL — missing `backoff`, imports non-existent `init_db` |

---

## Issues

Severity: CRITICAL / HIGH / MEDIUM / LOW

### A. Security & privacy

| # | Sev | Where | Issue | Status |
|---|---|---|---|---|
| A1 | CRITICAL | `CREDENTIALS_ROTATION_REQUIRED.md:13-24` | Plaintext Neon DB host/user/password and NASA API key committed at HEAD in a **public** repo. VERIFIED | FIXED at HEAD (step 1); still in history → A2 |
| A2 | CRITICAL | git history | Same DB password, `.env` and `.streamlit/secrets.toml` exist in older commits. Removing files from HEAD does not remove them from history. VERIFIED | OPEN |
| A3 | CRITICAL | git history | Older commits still contain alumni CSV files with personal data. Paths kept out of this file on purpose. VERIFIED | OPEN |
| A4 | HIGH | `app.py:57,133-136`, `utils/disaster_monitor.py:60-63` | Raw exceptions and full tracebacks shown to end users (can leak DB host, paths). INFERRED | FIXED (step 4) |
| A5 | HIGH | `env_debug.py` | Second Streamlit app that dumps all env vars; redaction is keyword-based, anything not matching leaks. INFERRED | FIXED (step 1) |
| A6 | MEDIUM | `app.py` safe mode, `utils/helpers.py:47-99` | Debug panel / DB diagnosis / sample data table exposed to every visitor of the public demo. VERIFIED | FIXED (step 4) |
| A7 | MEDIUM | `.github/workflows/sync-to-huggingface.yml` | HF token embedded in git remote URL, `git push --force`, echoes token length. Username hardcoded. INFERRED | OPEN |
| A8 | MEDIUM | `scripts/load_alumni_data.py:22,42` | Nominatim used with generic user agent at 60 req/min — violates Nominatim's 1 req/sec policy. INFERRED | FIXED (step 2) |
| A9 | LOW | `utils/disaster_monitor.py:48` | `requests.get` with no timeout — app can hang. INFERRED | FIXED (step 4) |
| A10 | LOW | `.github/workflows/main.yml` | Outdated `actions/checkout@v2`; workflow does nothing. INFERRED | OPEN |

Fix order for A1–A3 (needs owner action): rotate/delete credentials → (optional, later) purge history with `git filter-repo` → force-push.

### B. Broken code

| # | Sev | Where | Issue | Status |
|---|---|---|---|---|
| B1 | HIGH | `utils/disaster_monitor.py:16` | Reads `st.secrets` at import time → full app crashes on any fresh clone without `secrets.toml`. VERIFIED | FIXED (step 4) |
| B2 | HIGH | `requirements.txt`, `runtime.txt` | Pinned deps don't install on current Python; `runtime.txt` is empty so Python version is undefined. VERIFIED | OPEN |
| B3 | HIGH | `scripts/load_alumni_data.py:11,13,19` | Imports `backoff`, `ratelimit` (not in requirements) and `init_db` (does not exist). Script cannot run. VERIFIED | FIXED (step 2) |
| B4 | HIGH | `utils/import_csv_data.py:3`, `utils/init_db.py:1`, `utils/load_sample_data.py:2` | Import module-level `engine`, which is always `None` (lazy init) → `create_all(bind=None)` fails. INFERRED | FIXED (step 2) |
| B5 | MEDIUM | `utils/map_handler.py:50,96` | Only `geometry[0]` used. EONET geometry is chronological → distance uses the *oldest* position. VERIFIED: Tropical Cyclone Wati moved from (-163.3, -10.8) to (-156.8, -20.7), ~1,250 km, between first and last point. Polygons would be silently skipped. | FIXED (step 4) |
| B6 | MEDIUM | `utils/data_loader.py:84` | CSV fallback path `attached_assets/combo3.csv` no longer exists. VERIFIED | FIXED (step 4) |
| B7 | MEDIUM | `utils/data_loader.py` (3 branches) | Loader handles 3 different CSV schemas; `0,0` used as "invalid coord" sentinel; on error returns a fake "Sample User" at 0,0. INFERRED | FIXED (step 4) |
| B8 | LOW | `.replit` | Runs `simple_app.py`, which does not exist. VERIFIED | FIXED (step 2) |
| B9 | LOW | `utils/map_handler.py:45,80,123` | Business logic calls `st.warning`/`st.error` — couples math to UI, untestable. INFERRED | FIXED (step 4) |
| B10 | LOW | `utils/database.py:6` | Deprecated `sqlalchemy.ext.declarative.declarative_base`. INFERRED | FIXED (step 4) |
| B11 | LOW | `utils/disaster_monitor.py:1-10`, `utils/database.py:11` | Unused imports (`timedelta`, `time`, `Session`, `db`, `create_engine`); `logging.basicConfig` called in 3 modules. INFERRED | FIXED (step 4) |

### C. Duplicate / redundant code

| # | Where | Duplication | Status |
|---|---|---|---|
| C1 | `helpers.get_db_url` (reads `POSTGRES_URL`), `secrets_handler.get_db_url`, `database.get_connection_string` (reads `DATABASE_URL`), `disaster_monitor` (reads `st.secrets["DATABASE_URL"]`) | **4 ways to get the DB URL, using 3 different keys.** Pick one. | FIXED (step 4) |
| C2 | `helpers.create_db_engine`, `database.get_engine`, `disaster_monitor.get_db_connection` | 3 ways to create a DB engine. | FIXED (step 4) |
| C3 | `database.get_db_session` vs `database.get_db` | 2 session helpers; `get_db` unused. | FIXED (step 4) |
| C4 | `database.init_database` vs `utils/init_db.py` | Same function twice. | FIXED (step 2) |
| C5 | `import_csv_data.py`, `load_sample_data.py`, `scripts/load_alumni_data.py`, `scripts/simplify_csv.py`, `create_sample_data.py`, `test_csv_reader.py` | **6 data load/seed/convert scripts**, each expecting a different CSV schema. Need exactly one `seed` script. | FIXED (step 2) |
| C6 | `app.py` vs `env_debug.py` | 2 Streamlit apps. | FIXED (step 1) |
| C7 | NASA key lookup in `disaster_monitor.py` (2 secret shapes) and `secrets_handler.get_nasa_api_key` | Duplicated — and EONET doesn't need a key at all. | FIXED (step 4) |
| C8 | `.github/workflows/main.yml`, `sync-to-huggingface.yml`, `.replit`, Streamlit Cloud (README) | 3–4 deploy targets. Pick one. | OPEN |
| C9 | `SECURITY.md` + `CREDENTIALS_ROTATION_REQUIRED.md` + README security section | Security docs in 3 places. | OPEN |
| C10 | `assets/combo.csv`, `example_format.csv`, README "Data Format" | 3 different alumni schemas documented. | OPEN |

### D. Dead files / folders (not reachable from the app)

| # | Path | Why dead | Status |
|---|---|---|---|
| D1 | `src/` (8 JS files, 47 LOC) | Express/React/Mongoose fragments in a Python app. None run, none complete. | FIXED (step 2) |
| D2 | `ADT/` | Empty directory. | FIXED (step 2) |
| D3 | `utils/__pycache__/*.pyc` | Build artifacts committed despite `.gitignore`. | FIXED (step 2) |
| D4 | `attached_assets/*.txt` | Pasted React code. | FIXED (step 2) |
| D5 | `.replit`, `replit.nix`, `generated-icon.png` (337 KB) | Replit leftovers. | FIXED (step 2) |
| D6 | `.cursor/rules/learner.mdc` | Empty template. | FIXED (step 2) |
| D7 | `utils/japan_locations.py`, `utils/secrets_handler.py` | Not imported by the app. | FIXED (step 2) |
| D8 | `database.DisasterEvent`, `database.get_db`, `disaster_monitor.get_db_connection`, `disaster_monitor.db_url` | Defined, never used. | FIXED (step 4) |
| D9 | `env_debug.py`, `test_csv_reader.py`, `create_sample_data.py` | Root-level one-off scripts. | FIXED (step 2) |

### E. Docs & repo hygiene

| # | Issue | Status |
|---|---|---|
| E1 | README says NASA API key required — EONET needs none. | OPEN |
| E2 | README says Postgres is core — app actually runs off the CSV fallback. | OPEN |
| E3 | README references a LICENSE file that doesn't exist. | OPEN |
| E4 | README setup step `python utils/init_db.py` crashes (see B4). | OPEN |
| E5 | No tests. `test_csv_reader.py` is not a test. | OPEN |
| E6 | No working CI (lint/test). | OPEN |
| E7 | `~/CLAUDE.md` describes a different project ("Ripple") — misleads AI sessions in this repo. | OPEN |

### F. Product / demo

| # | Issue | Status |
|---|---|---|
| F1 | First screen is a debug "safe mode", not the product. A recruiter sees buttons, not a map. | FIXED (step 4) |
| F2 | With live data (3 days, open events) there are usually **0 alerts** — the core feature is invisible. | FIXED (step 4) |
| F3 | Demo depends on secrets/DB that a fresh clone doesn't have (B1). Should run with zero setup. | FIXED (step 4) |
| F4 | Alumni data is 15 fake US rows with a junk `combo` header row and ~40 empty columns. | FIXED (step 5) |

---

## Size snapshot

| | Now | Target (rough) |
|---|---|---|
| Tracked files | 48 | ~15 |
| Python LOC | ~1,430 | ~400 |
| Entry points | 9 | 2 (`app.py`, one seed script) |
| Fresh clone → working demo | crashes | `pip install -r requirements.txt && streamlit run app.py` |

---

## Phase 2 — Deep review (done 2026-10-19)

### What I ran

| Check | Result |
|---|---|
| `ruff check --select F,E9,B,S,UP` | 26 issues: 22 unused imports, 1 unused var, 1 request without timeout, 1 bare try/except/pass, 1 empty f-string |
| `vulture --min-confidence 60` | 17 dead items (see D8, I1) |
| `pip-audit -r requirements.txt` | **9 known vulns in 4 pinned packages**: streamlit 1.43.0, python-dotenv 1.0.0, geopy 2.4.1, requests 2.32.4 |
| Import `utils/disaster_monitor.py` in plain Python | FAIL — same as B1; module is untestable without secrets.toml |
| `filter_disasters_by_type` on live EONET (30 days) | Keeps 38 of 49 events; drops all 11 `seaLakeIce` silently. Empty `categories` → `IndexError` |
| `calculate_proximity_alerts`, 2,000 alumni × 49 events | **15.5 s**, not cached, reruns on every widget/map interaction |
| `create_map`, 2,000 alumni | 3.2 s, **2.1 MB** of HTML per rerun |
| Alumni name `<img src=x onerror=alert(1)>` in popup | Rendered **unescaped** into map HTML |
| Live EONET volume | `days=3`: 4 events. `days=30`: 49. No `days`: 7,221 (`limit=25` then picks an arbitrary 25) |

### New issues

#### A. Security (continued)

| # | Sev | Where | Issue | Status |
|---|---|---|---|---|
| A11 | MEDIUM | `utils/map_handler.py:37,59` | HTML injection: alumni name/location (CSV/DB) and disaster title (external API) go raw into Folium popup HTML. Runs inside the map iframe. Fix: `html.escape()`. VERIFIED | FIXED (step 4) |
| A12 | MEDIUM | `requirements.txt` | 9 known vulnerabilities in pinned versions (streamlit, python-dotenv, geopy, requests). VERIFIED | OPEN |
| A13 | MEDIUM | `app.py:124-128` | Alert list publicly shows each alumnus's name + location on a public URL. Real data must never be deployed publicly without auth; demo must use synthetic data only. INFERRED | FIXED (step 4) |
| A14 | LOW | `utils/helpers.py:16-17` | Bare `except: pass` hides config errors. VERIFIED (ruff S110) | FIXED (step 4) |

#### G. Correctness

| # | Sev | Where | Issue | Status |
|---|---|---|---|---|
| G1 | HIGH | `utils/disaster_monitor.py:78-83` + `app.py:82` | Filter only offers 4 types; `seaLakeIce` (and floods, dust, etc.) silently dropped. Type list is hardcoded in two places (UI + type map). VERIFIED | FIXED (step 4) |
| G2 | MEDIUM | `utils/disaster_monitor.py:90` | `d['categories'][0]` crashes on an event with no categories — one bad event kills the whole list. VERIFIED | FIXED (step 4) |
| G3 | MEDIUM | `utils/disaster_monitor.py:22,59-63` | On API error returns `[]` — and `st.cache_data` caches that `[]` for 1 hour. One blip = an hour of "no disasters". INFERRED | FIXED (step 4) |
| G4 | MEDIUM | `utils/data_loader.py:11` | `load_alumni_data` cached 1h, including a failed DB → CSV fallback. Strange unused `_=None` param. INFERRED | FIXED (step 4) |
| G5 | MEDIUM | `utils/disaster_monitor.py:40-44` | `days=3, limit=25` — window too narrow for a useful demo (F2); without `days` the 25 events are arbitrary. VERIFIED | FIXED (step 4) |
| G6 | LOW | `utils/map_handler.py:9-10` | Map center = mean of all alumni including `0,0` invalid ones. INFERRED | FIXED (step 4) |
| G7 | LOW | `utils/map_handler.py:20-27` | Invalid (0,0) alumni still drawn on the map at "Null Island" off Africa. INFERRED | FIXED (step 4) |
| G8 | LOW | `utils/database.py:95` | Session commits after read-only queries. Harmless, but noise. INFERRED | FIXED (step 4) |

#### H. Performance

| # | Sev | Where | Issue | Status |
|---|---|---|---|---|
| H1 | HIGH | `utils/map_handler.py:83-120` | O(alumni × events) Python loop with `geopy.geodesic` + `iterrows`: **15.5 s** for realistic size. Vectorised numpy haversine would be milliseconds and drops the geopy dependency from the app. VERIFIED | FIXED (step 4) |
| H2 | HIGH | `app.py:111` | `st_folium(...)` without `returned_objects=[]` → every pan/zoom triggers a full rerun → H1 + map rebuild again. INFERRED | FIXED (step 4) |
| H3 | MEDIUM | `utils/map_handler.py:16-43` | One `CircleMarker` per alumnus via `iterrows` → 2.1 MB HTML, 3.2 s. Use `MarkerCluster` or only draw alumni near events. VERIFIED | FIXED (step 4) |
| H4 | LOW | `app.py:73-76` | Heavy imports inside the try-block on each rerun; `import traceback` inside except. Harmless but messy. INFERRED | FIXED (step 4) |

#### I. Code quality

| # | Sev | Where | Issue | Status |
|---|---|---|---|---|
| I1 | MEDIUM | 22 places (ruff F401) | Unused imports, incl. `numpy` in `map_handler.py:3`. VERIFIED | FIXED (step 4) |
| I2 | MEDIUM | `requirements.txt` | `python-dotenv` never imported. `chardet`, `numpy` only used by dead scripts. `backoff`, `ratelimit` used but missing. VERIFIED | OPEN |
| I3 | MEDIUM | `map_handler.py`, `disaster_monitor.py`, `helpers.py` | UI calls (`st.error`/`st.warning`) mixed into logic functions. Logic can't be tested or reused. INFERRED | FIXED (step 4) |
| I4 | LOW | `app.py` | Two "modes" with session-state flags (`app_loaded`, `show_debugging`) — complexity that only exists to hide B1. INFERRED | FIXED (step 4) |
| I5 | LOW | whole codebase | Column names in 3 casings (`Latitude`/`lat`/`latitude`), dicts with ad-hoc keys passed between modules. One schema needed. INFERRED | FIXED (step 4) |
| I6 | LOW | multiple | Comments that restate the code ("# Create base map", "# Ensure coordinates are floats" ×6) and stale ones ("Replace st.write with logger.debug"). INFERRED | FIXED (step 4) |
| I7 | LOW | `data_loader.py`, `map_handler.py` | Defensive `float()` casts + try/except repeated in every function instead of cleaning data once at load. INFERRED | FIXED (step 4) |

#### J. Testing & CI

| # | Sev | Issue | Status |
|---|---|---|---|
| J1 | HIGH | Zero tests. Logic that most needs them: distance/threshold, EONET parsing (latest point, missing fields), CSV loading. | OPEN |
| J2 | MEDIUM | No offline fixture for EONET → demo and tests depend on live API. | OPEN |
| J3 | MEDIUM | CI does nothing (A10). Needs: ruff + pytest + pip-audit. | OPEN |

#### K. Git history (what a recruiter will see)

| # | Sev | Issue | Status |
|---|---|---|---|
| K1 | MEDIUM | 53 commits; messages like `a`, `b`, `c`, `good`, `ready` ×2, 6× `Update sync-to-huggingface.yml`, 8× auto-generated `Agent query: ...`. | OPEN |
| K2 | INFO | History purge for A1–A3 rewrites history anyway → good moment to squash to one clean "initial commit" and build forward with clear commits. Owner decision. | OPEN |

---

### Threat model (short)

| | |
|---|---|
| **Assets** | Alumni PII (name, address, phone, email, coords); DB credentials; NASA key; HF token |
| **Actors** | Anyone on the internet (public repo + public demo URL); compromised dependency |
| **Entry points** | Git history; public Streamlit/HF app; CSV/DB content → HTML; EONET API → HTML; CI secrets |

| Top risk | Today | Mitigation |
|---|---|---|
| 1. Leaked DB creds → read/delete all data | **Exposed now** (A1, A2) | Rotate, purge history |
| 2. Real PII readable by anyone | **Exposed in history** (A3), and app shows names publicly (A13) | Purge; synthetic data only in demo |
| 3. Internals leaked via error pages/debug | Live (A4, A5, A6) | Generic error messages, delete debug UI |
| 4. HTML injection via data | Live (A11) | `html.escape` |
| 5. Vulnerable dependencies | 9 known (A12) | Upgrade; pip-audit in CI |

---

### Product / engineering-management lens

**User:** an alumni-relations or emergency coordinator at a university.
**Job to be done:** "When a disaster happens, tell me which of our people are near it, so I can check on them."
**The 60-second demo:** open link → map with disasters + alumni → sidebar list "N alumni within X km of [event]" → change radius, list updates instantly.

**MoSCoW**

| Must (demo) | Should | Could | Won't (now) |
|---|---|---|---|
| Map of live events + alumni | Offline EONET fixture / "demo mode" | Postgres as optional source | Auth, accounts |
| Proximity list sorted by distance | Filter by event category (from data, not hardcoded) | Download alerts as CSV | Email/SMS notifications |
| Radius slider | Use latest event position (B5) | | Geocoding pipeline in-app |
| Works with zero setup (bundled synthetic CSV) | Tests + CI | | React/Node rewrite |

**Metrics a real product would track:** time from EONET event to alert; % alumni with valid coordinates; alert precision (alerts the coordinator actually acted on).

**Decisions to write down (ADRs, a few lines each):**
1. Streamlit over React + API — one person, one language, fastest path to a working demo.
2. CSV by default, Postgres optional — demo must run with zero setup; DB only matters for real private data.
3. EONET as data source — free, no key, global; trade-off: limited categories and update latency.

**What a senior interviewer would poke at — and the answer to have ready:**
1. "Why are there secrets / personal data in your git history?" → Show it's purged, rotated, and that the demo uses synthetic data by design.
2. "How do you test this?" → Pure functions for distance + parsing, tested offline with a saved EONET fixture.
3. "What happens with 10k alumni?" → Vectorised haversine (ms, not 15 s), cached, map clustering.

---

### Scorecard (today)

| Area | Score /10 | Why |
|---|---|---|
| Security | 1 | Live creds + PII public; tracebacks to users; 9 vulns |
| Simplicity | 2 | 48 files, ~7 used; 4 config paths, 6 loaders, 2 apps, 2 modes |
| Correctness | 4 | Core math is right; uses stale storm position, drops categories, caches failures |
| Testability | 1 | No tests; key module can't even be imported without secrets |
| Performance | 3 | 15 s per interaction at realistic size |
| Docs | 3 | README partly false |
| Demo-readiness | 2 | Debug screen first, crashes on fresh clone, usually 0 alerts |

---

### Proposed minimal target (for Phase 3 to confirm)

```
app.py              UI only (~80 lines)
core.py             fetch_events, latest_point, load_alumni, find_nearby (~120 lines, pure + cached fetch)
data/alumni.csv     synthetic, one schema: name,city,country,lat,lon
data/events.json    saved EONET snapshot for offline/demo mode
tests/test_core.py  distance, parsing, loading
requirements.txt    streamlit, pandas, folium, streamlit-folium, requests
README.md, LICENSE, .gitignore, .github/workflows/ci.yml
```

Postgres (`database.py`, `sqlalchemy`, `psycopg2`) kept only if the owner wants it — decide in Phase 3.

## Phase 3 — Plan (2026-10-19)

### Decisions

| # | Decision | Why |
|---|---|---|
| D-1 | **Drop Postgres.** Alumni come from one bundled synthetic CSV. | Zero-setup demo; removes `database.py`, `helpers.py`, sqlalchemy, psycopg2, all secrets handling. Closes C1–C4, B1, B4, A4–A6 by deletion. |
| D-2 | **Keep git history as-is for now.** History purge (A2, A3) stays OPEN and optional. | Owner choice. Rotating/deleting the credentials makes the leaked secrets useless; purge can be done later with `git filter-repo`. |
| D-3 | **No API key.** EONET is public. | Removes C7 and the NASA key from secrets entirely. |
| D-4 | **One deploy target: Streamlit Community Cloud.** Delete HF sync + Replit. | Free, deploys from GitHub, no token in CI. Closes A7, C8, D5. (Owner can override: keep HF instead.) |
| D-5 | **Offline fallback:** saved EONET snapshot used when the API fails, and as test fixture. | Demo never shows "no data"; tests don't hit the network. Closes G3, J2. |

### Owner actions (only you can do these)

- [ ] Delete the Neon database/project (Postgres is dropped, so delete beats rotate).
- [ ] Regenerate or delete the NASA API key at api.nasa.gov (no longer used).
- [ ] Remove the `HF_TOKEN` GitHub secret if moving off Hugging Face.

### Steps (one commit each; app must run after every step)

| Step | What | Files | Closes | Verify |
|---|---|---|---|---|
| 1 | **Remove secrets & debug apps** from HEAD | delete `CREDENTIALS_ROTATION_REQUIRED.md`, `env_debug.py` | A1 (HEAD), A5, C6 | `git grep` for the old password/key returns nothing |
| 2 | **Delete dead files** | delete `src/`, `ADT/`, `utils/__pycache__/`, `attached_assets/`, `.replit`, `replit.nix`, `generated-icon.png`, `.cursor/`, `test_csv_reader.py`, `create_sample_data.py`, `scripts/`, `utils/{secrets_handler,japan_locations,import_csv_data,init_db,load_sample_data}.py`, `example_format.csv` | D1–D9, B3, B4, B8, C5, A8 | app still boots |
| 3 | **Write `core.py`** — DONE (replaces `utils/`): `fetch_events()` with timeout + fallback to `data/events.json`; `latest_point()`; `load_alumni()` with one schema; `find_nearby()` with numpy haversine; `html.escape` for popup text; categories read from data | new `core.py`, `data/events.json`; delete `utils/` | B5, B6, B7, B9, G1–G7, H1, A11, A14, I1, I3, I5, I7, C1–C4 | unit tests (step 6) |
| 4 | **Rewrite `app.py`** — DONE: one screen — sidebar (categories, radius) + map + nearby list. No modes, no debug, generic error message. `st_folium(..., returned_objects=[])`. Cluster alumni markers. | `app.py` | A4, A6, A13 (synthetic only), F1, F3, H2, H3, H4, I4 | `streamlit run app.py` on fresh clone; AppTest smoke test |
| 5 | **Synthetic data** — DONE: ~200 fake alumni (`name,city,country,lat,lon`) spread over cities that often have events (California, Australia, Japan, Philippines, Caribbean…), so the demo shows alerts | `data/alumni.csv` (replaces `assets/combo.csv`) | F2, F4, C10, G5 | demo shows ≥1 alert with default radius |
| 6 | **Tests**: haversine known distances; threshold edge; `latest_point` picks last geometry; event with missing categories skipped; CSV loads with one schema | `tests/test_core.py` | J1, J2, G2 | `pytest` green, no network |
| 7 | **Dependencies**: `streamlit`, `pandas`, `numpy`, `folium`, `streamlit-folium`, `requests` — current versions, no known vulns; pin Python 3.12 | `requirements.txt`, `runtime.txt` | B2, A12, I2 | fresh venv install + `pip-audit` clean |
| 8 | **CI**: one workflow — ruff, pytest, pip-audit; pinned actions; `contents: read`. Delete old workflows. | `.github/workflows/ci.yml` | A10, J3, A7, C8 | green check on push |
| 9 | **Docs**: README (pitch, demo link, screenshot, 3-line quickstart, how it works, decisions D-1..D-5, what's next); MIT LICENSE; short SECURITY.md (synthetic data only, no secrets needed) | `README.md`, `LICENSE`, `SECURITY.md` | E1–E6, C9, F (story) | read it as a recruiter |
| 10 | **Later / optional**: history purge with `git filter-repo`; move `~/CLAUDE.md` (Ripple) out of the way | — | A2, A3, K1, K2, E7 | `git log --all -p` grep clean |

### Final layout

```
app.py              UI (~80 lines)
core.py             logic (~100 lines)
data/alumni.csv     synthetic
data/events.json    EONET snapshot (fallback + test fixture)
tests/test_core.py
requirements.txt  runtime.txt  .gitignore  .streamlit/config.toml
README.md  LICENSE  SECURITY.md  AUDIT.md
.github/workflows/ci.yml
```

From 48 files / ~1,430 Python LOC / 9 entry points → ~14 files / ~250 LOC / 1 entry point.

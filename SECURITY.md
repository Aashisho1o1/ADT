# Security and privacy

## Data

All alumni data in this repository (`data/alumni.csv`) is **synthetic**: randomly generated names and coordinates that describe no real person. Real personal data must never be committed here or deployed to a public URL.

If you run the app with a real alumni list:

- keep the file outside the repository, or add it to `.gitignore`
- keep only the columns the app needs: `name, city, country, lat, lon` (no emails, phone numbers or street addresses)
- run it privately or behind authentication

## Secrets

The app needs no secrets. NASA EONET is a public API with no key, and there is no database. If you add a secret later, put it in `.streamlit/secrets.toml` (already in `.gitignore`) or in your host's secrets settings, never in code.

## What the app does to stay safe

- Text from the data and from the EONET API is HTML-escaped before it is shown on the map.
- Error details are hidden from visitors (`showErrorDetails = false`).
- External requests have a timeout, and failures fall back to a local snapshot.
- CI checks dependencies for known vulnerabilities on every push (`pip-audit`).

## Reporting a problem

Please open a private [security advisory](https://github.com/Aashisho1o1/ADT/security/advisories/new) on GitHub, or contact the maintainer directly. Please don't open a public issue for security problems.

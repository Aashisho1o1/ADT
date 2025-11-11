---
title: Alumni Disaster Tracker
emoji: 🌍
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.43.0
app_file: app.py
pinned: false
---

# Alumni Disaster Tracker

A Streamlit application that monitors natural disasters around the world and alerts when they occur near alumni locations.

## Features

- Real-time disaster monitoring using NASA EONET API
- Alumni location visualization on interactive maps
- Proximity alerts for disasters near alumni
- Filtering by disaster types (wildfires, storms, volcanoes, etc.)
- PostgreSQL database integration for alumni data management
- Caching for optimal performance

## Technology Stack

- **Frontend**: Streamlit for the user interface
- **Maps**: Folium for interactive map visualization
- **Database**: PostgreSQL with SQLAlchemy ORM
- **APIs**: NASA EONET API for disaster data
- **Geolocation**: Geopy with Nominatim geocoding

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- NASA API key (free from https://api.nasa.gov)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ADT
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   NASA_API_KEY=your_nasa_api_key_here
   ```

4. **Initialize the database**
   ```bash
   python utils/init_db.py
   ```

5. **Load sample data (optional)**
   ```bash
   python scripts/load_alumni_data.py
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Deployment

#### Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Add secrets in the Streamlit Cloud dashboard:
   ```toml
   [postgres]
   url = "your_database_url"

   [nasa]
   api_key = "your_nasa_api_key"
   ```

#### Hugging Face Spaces

The repository includes a GitHub Actions workflow (`.github/workflows/sync-to-huggingface.yml`) that automatically syncs to Hugging Face Spaces.

## Security

**IMPORTANT**: This repository uses sample data for demonstration purposes. If you plan to use real alumni data:

1. Never commit real personal data to version control
2. Ensure you have proper consent and data protection measures
3. Review `SECURITY.md` for detailed security guidelines
4. Use environment variables for all credentials
5. Implement appropriate access controls

See [SECURITY.md](SECURITY.md) for more information.

## Data Format

Alumni data should be in CSV format with the following columns:
- ID, Name, Address, City, State, Country, Postal Code
- Latitude and Longitude (for mapping)
- Email and Phone (for contact information)

See `example_format.csv` for the expected structure.

## Usage

1. **View Alumni Locations**: The main map shows all alumni locations with markers
2. **Monitor Disasters**: Active disasters are displayed with their type and location
3. **Check Proximity**: The app automatically calculates which alumni are near active disasters
4. **Filter by Type**: Use the sidebar to filter disasters by type
5. **Refresh Data**: Disaster data is cached for 1 hour and refreshes automatically

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.

## Acknowledgments

- NASA EONET API for providing real-time disaster data
- Streamlit for the excellent web framework
- OpenStreetMap and Nominatim for geocoding services

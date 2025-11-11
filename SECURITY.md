# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by opening an issue or contacting the maintainers directly. We take security seriously and will respond promptly.

## Security Considerations

### Credentials Management

This application requires the following credentials to function:

1. **PostgreSQL Database URL** - Connection string for the alumni database
2. **NASA EONET API Key** - For accessing natural disaster data

**IMPORTANT**: Never commit credentials to the repository. Use environment variables or Streamlit secrets management.

### Setup Instructions

1. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

2. For Streamlit Cloud deployment, use Streamlit Secrets:
   - Go to your app settings in Streamlit Cloud
   - Add secrets in TOML format:
     ```toml
     [postgres]
     url = "your_database_url_here"

     [nasa]
     api_key = "your_nasa_api_key_here"
     ```

3. Never commit `.env` or `.streamlit/secrets.toml` files

### Getting API Keys

- **NASA API Key**: Free API key available at https://api.nasa.gov
- **PostgreSQL Database**: Set up a database with your preferred provider (e.g., Neon, Supabase, AWS RDS)

### Data Privacy

This application processes location data for alumni tracking during natural disasters. If you're deploying this for production use:

1. Ensure you have proper consent from individuals whose data you're tracking
2. Implement appropriate access controls
3. Use HTTPS for all connections
4. Regularly audit access logs
5. Comply with applicable data protection regulations (GDPR, CCPA, etc.)

### Known Security Considerations

- The sample data in `assets/combo.csv` is fictional and safe for public use
- Real alumni data should never be committed to version control
- Always use parameterized queries (SQLAlchemy ORM handles this)
- Input validation is performed on user-submitted data

## Security Best Practices for Contributors

1. Never hardcode credentials in source code
2. Use environment variables for all sensitive configuration
3. Review changes carefully before committing
4. Use `.gitignore` to prevent accidental commits of sensitive files
5. Enable two-factor authentication on your GitHub account

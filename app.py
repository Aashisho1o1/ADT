"""Alumni Disaster Monitor Streamlit application."""
import streamlit as st
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    page_icon="🌍",
    layout="wide"
)


st.title("🌍 Alumni Natural Disaster Monitor")
st.info("App is starting in safe mode for Hugging Face deployment")

# Create sidebar
st.sidebar.markdown("### System Status")
db_status = st.sidebar.empty()
db_status.warning("⚠️ Database connection deferred for stability")

# Main content area
st.write("Welcome to the Alumni Disaster Monitor application!")
st.write("This app helps track natural disasters near alumni locations.")

# Debug secrets loading
st.subheader("Secrets Debugging")

# Check file existence
import os
streamlit_dir = ".streamlit"
secrets_file = os.path.join(streamlit_dir, "secrets.toml")

file_exists = os.path.exists(secrets_file)
st.write(f"1. Secrets file exists at {secrets_file}: {file_exists}")

# Check if st.secrets is working
st.write("2. st.secrets content:")
try:
    # Print all secret keys
    if hasattr(st, "secrets"):
        all_keys = dir(st.secrets)
        secret_keys = [k for k in all_keys if not k.startswith('_')]
        st.write(f"Available keys in st.secrets: {secret_keys}")
        
        # Check for postgres specifically
        if "postgres" in secret_keys:
            st.write("'postgres' key exists in secrets")
            if hasattr(st.secrets.postgres, "url"):
                masked_url = "...@" + st.secrets.postgres.url.split("@")[-1]
                st.write(f"Database URL found: {masked_url}")
            else:
                st.write("No 'url' in postgres section")
    else:
        st.write("st.secrets does not exist")
except Exception as e:
    st.write(f"Error accessing secrets: {str(e)}")

# Environment vars
st.write("3. Environment variables:")
env_vars = {k: "[MASKED]" if "KEY" in k or "URL" in k or "TOKEN" in k else v 
           for k, v in os.environ.items() 
           if "POSTGRES" in k or "NASA" in k}
st.write(env_vars)

# Add button to attempt safe connection
if st.button("Test Database Connection"):
    try:
        # Try environment variables first (for Hugging Face)
        postgres_url = os.environ.get("POSTGRES_URL")
        
        # If not found in environment, try Streamlit secrets (for local development)
        if not postgres_url and hasattr(st, "secrets") and "postgres" in st.secrets:
            postgres_url = st.secrets.postgres.url
            
        if postgres_url:
            # Only show masked version for security
            masked_url = "...@" + postgres_url.split("@")[-1] if "@" in postgres_url else "[database url found but masked]"
            st.success(f"✅ Found database configuration ending with: {masked_url}")
            
            # Attempt connection
            st.info("Attempting connection...")
            from sqlalchemy import create_engine, text
            
            engine = create_engine(
                postgres_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5}  # 5 second timeout
            )
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                value = result.scalar()
                st.success(f"✅ Database connection test successful!")
        else:
            st.error("No database URL found in environment variables or secrets")
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

# Add button to enable full application mode
if st.button("Load Full Application"):
    try:
        st.warning("Loading full application... This may take a moment.")
        
        # Import required modules
        import pandas as pd
        import time
        from utils.data_loader import load_alumni_data
        from utils.disaster_monitor import fetch_eonet_data, filter_disasters_by_type
        from utils.map_handler import create_map, calculate_proximity_alerts
        import folium
        from streamlit_folium import st_folium

        # Create the application UI
        st.subheader("Disaster Monitoring Dashboard")
        
        # Sidebar filters
        disaster_types = ["Wildfires", "Severe Storms", "Volcanoes", "Earthquakes"]
        selected_types = st.sidebar.multiselect(
            "Select Disaster Types",
            disaster_types,
            default=disaster_types
        )
        proximity_threshold = st.sidebar.slider(
            "Proximity Alert Threshold (km)",
            min_value=50, max_value=1000, value=200, step=50
        )
        
        # Load alumni data
        with st.spinner('Loading alumni data...'):
            alumni_df, metadata = load_alumni_data()
            if metadata:
                st.success(f"Loaded {metadata.get('total_records', 0)} alumni records from {metadata.get('source', 'unknown')}")
        
        # Fetch disaster data
        with st.spinner('Fetching disaster data...'):
            disaster_data = fetch_eonet_data()
            filtered_disasters = filter_disasters_by_type(disaster_data, selected_types) if disaster_data else []
            if filtered_disasters:
                st.success(f"Found {len(filtered_disasters)} disasters matching selected types")
        
        # Display map if data is available
        if 'alumni_df' in locals() and 'filtered_disasters' in locals():
            try:
                map_obj = create_map(alumni_df, filtered_disasters)
                st.info("Blue: Alumni locations | Red: Natural disasters")
                st_folium(map_obj, width=800)
            except Exception as e:
                st.error(f"Error creating map: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading full application: {str(e)}")
"""Alumni Disaster Monitor Streamlit application."""
import streamlit as st
import pandas as pd
import logging
import time
from utils.data_loader import load_alumni_data
from utils.disaster_monitor import fetch_eonet_data, filter_disasters_by_type
from utils.map_handler import create_map, calculate_proximity_alerts
import folium
from streamlit_folium import st_folium
import os
from sqlalchemy import text

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
st.info("App is starting in safe mode without database connection.")

# Create sidebar
st.sidebar.markdown("### System Status")
db_status = st.sidebar.empty()
db_status.warning("⚠️ Database connection deferred for security")

# Main content area
st.write("Welcome to the Alumni Disaster Monitor application!")
st.write("This app helps track natural disasters near alumni locations.")

# Show environment information
st.subheader("Environment Information")
st.json({
    "Space Name": os.environ.get("SPACE_ID", "Unknown"),
    "Running On": "Hugging Face Spaces",
    "Has Environment Secret": "POSTGRES_URL" in os.environ
})

# Add button to attempt safe connection
if st.button("Test Database Connection"):
    try:
        postgres_url = os.environ.get("POSTGRES_URL")
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
                st.success(f"✅ Database connection test successful! Result: {value}")
        else:
            st.error("No database URL found in environment variables")
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

def main():
    """Main application function."""
    st.title("🌍 Alumni Natural Disaster Monitor")
    
    # Show database connection status
    show_db_status()
    
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
        try:
            alumni_df, metadata = load_alumni_data()
            
            if alumni_df is None or alumni_df.empty:
                st.error("Could not load alumni data. Please check data sources.")
                return
                
            show_data_summary(alumni_df, metadata)
        except Exception as e:
            logger.error(f"Error loading alumni data: {e}")
            st.error(f"Error loading data: {e}")
            return
    
    # Fetch disaster data
    with st.spinner('Fetching disaster data...'):
        try:
            disaster_data = fetch_eonet_data()
            if not disaster_data:
                st.warning("No current disaster data available")
                filtered_disasters = []
            else:
                filtered_disasters = filter_disasters_by_type(disaster_data, selected_types)
                st.success(f"Found {len(filtered_disasters)} disasters matching selected types")
        except Exception as e:
            logger.error(f"Disaster data error: {e}")
            st.error(f"Error fetching disaster data: {str(e)}")
            filtered_disasters = []
    
    # Display map and alerts
    display_map_and_alerts(alumni_df, filtered_disasters, proximity_threshold)

def show_db_status():
    """Display database connection status in sidebar."""
    st.sidebar.markdown("### System Status")
    
    # Start with a placeholder
    status_placeholder = st.sidebar.empty()
    status_placeholder.info("Checking database connection...")
    
    try:
        from utils.database import get_engine
        
        # Set a timeout for database connection
        start_time = time.time()
        engine = get_engine()
        
        if engine is not None:
            try:
                # Set a timeout for query execution
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM alumni"))
                    count = result.scalar()
                    status_placeholder.success("✅ Connected to Database")
                    st.sidebar.info(f"📊 {count} alumni records")
            except Exception as e:
                status_placeholder.warning("⚠️ Database query error")
                st.sidebar.info("Using CSV fallback")
                logger.error(f"Database query error: {e}")
        else:
            status_placeholder.warning("⚠️ Using CSV fallback - No engine")
    except Exception as e:
        status_placeholder.error(f"❌ Database error")
        st.sidebar.info("Using CSV fallback")
        logger.error(f"Database connection error: {e}")

def show_data_summary(alumni_df, metadata):
    """Display data quality summary."""
    if not metadata:
        return
        
    total_records = metadata.get('total_records', 0)
    invalid_coords = metadata.get('invalid_coords', 0)
    source = metadata.get('source', 'unknown')
    
    st.success(f"Loaded {total_records} alumni records from {source}")
    
    if invalid_coords > 0:
        st.info(f"""
        📊 Alumni Data: {total_records} total records
        - Valid coordinates: {total_records - invalid_coords}
        - Missing coordinates: {invalid_coords}
        """)

def display_map_and_alerts(alumni_df, disasters, threshold_km):
    """Display map and proximity alerts."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Disaster Monitoring Map")
        try:
            map_obj = create_map(alumni_df, disasters)
            st.info("Blue: Alumni locations | Red: Natural disasters")
            st_folium(map_obj, width=800)
        except Exception as e:
            logger.error(f"Error creating map: {e}")
            st.error(f"Error creating map: {e}")
    
    with col2:
        display_alerts(alumni_df, disasters, threshold_km)
        display_alumni_table(alumni_df)

def display_alerts(alumni_df, disasters, threshold_km):
    """Display proximity alerts section."""
    st.subheader("Proximity Alerts")
    
    if not disasters:
        st.info("No disaster data available for alerts")
        return
    
    try:    
        alerts = calculate_proximity_alerts(alumni_df, disasters, threshold_km)
        
        if alerts:
            st.warning(f"⚠️ {len(alerts)} alerts within {threshold_km}km")
            for alert in alerts:
                with st.expander(f"🚨 {alert['alumni_name']} - {alert['disaster_type']}"):
                    st.write(f"Distance: {alert['distance']} km")
                    st.write(f"Location: {alert['location']}")
                    st.write(f"Disaster: {alert['disaster_description']}")
        else:
            st.info("✅ No alerts within the specified threshold")
    except Exception as e:
        logger.error(f"Error calculating alerts: {e}")
        st.error(f"Error calculating alerts: {e}")

def display_alumni_table(alumni_df):
    """Display alumni data table."""
    st.subheader("Alumni Overview")
    try:
        # Make sure required columns exist
        required_cols = ['Name', 'Location', 'Latitude', 'Longitude']
        missing_cols = [col for col in required_cols if col not in alumni_df.columns]
        
        if missing_cols:
            st.warning(f"Missing columns in data: {', '.join(missing_cols)}")
            valid_cols = [col for col in required_cols if col in alumni_df.columns]
            if valid_cols:
                st.dataframe(alumni_df[valid_cols].dropna(), hide_index=True)
            else:
                st.error("Cannot display alumni table: missing required columns")
        else:
            st.dataframe(alumni_df[required_cols].dropna(), hide_index=True)
    except Exception as e:
        logger.error(f"Error displaying alumni table: {e}")
        st.error(f"Error displaying alumni table: {e}")

if __name__ == "__main__":
    main()
"""Alumni Disaster Monitor Streamlit application."""
import streamlit as st
import pandas as pd
import logging
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
        alumni_df, metadata = load_alumni_data()
        
        if alumni_df is None or alumni_df.empty:
            st.error("Could not load alumni data. Please check data sources.")
            return
            
        show_data_summary(alumni_df, metadata)
    
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
        import threading
        
        # Set a flag for async checking
        db_status = {"connected": False, "count": 0, "error": None}
        
        # Function to check DB in background
        def check_db_connection():
            try:
                engine = get_engine()  # Lazy initialization
                if engine is not None:
                    with engine.connect() as conn:
                        result = conn.execute(text("SELECT COUNT(*) FROM alumni"))
                        db_status["count"] = result.scalar()
                        db_status["connected"] = True
            except Exception as e:
                db_status["error"] = str(e)
        
        # Start a thread with timeout
        thread = threading.Thread(target=check_db_connection)
        thread.daemon = True
        thread.start()
        thread.join(timeout=3)  # Wait max 3 seconds
        
        # Check result
        if db_status["connected"]:
            status_placeholder.success("✅ Connected to Database")
            st.sidebar.info(f"📊 {db_status['count']} alumni records")
        else:
            status_placeholder.warning("⚠️ Using CSV fallback")
            if db_status["error"]:
                st.sidebar.error(f"Error: {db_status['error']}")
    except Exception as e:
        status_placeholder.error(f"❌ Database error: {str(e)}")
        st.sidebar.info("Using CSV fallback")

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
        map_obj = create_map(alumni_df, disasters)
        st.info("Blue: Alumni locations | Red: Natural disasters")
        st_folium(map_obj, width=800)
    
    with col2:
        display_alerts(alumni_df, disasters, threshold_km)
        display_alumni_table(alumni_df)

def display_alerts(alumni_df, disasters, threshold_km):
    """Display proximity alerts section."""
    st.subheader("Proximity Alerts")
    
    if not disasters:
        st.info("No disaster data available for alerts")
        return
        
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

def display_alumni_table(alumni_df):
    """Display alumni data table."""
    st.subheader("Alumni Overview")
    st.dataframe(
        alumni_df[['Name', 'Location', 'Latitude', 'Longitude']].dropna(),
        hide_index=True
    )

if __name__ == "__main__":
    main()
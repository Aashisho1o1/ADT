"""Alumni Disaster Monitor Streamlit application."""
import streamlit as st
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Alumni Disaster Monitor",
    page_icon="🌍",
    layout="wide"
)

# Initialize session state
if "app_loaded" not in st.session_state:
    st.session_state.app_loaded = False

st.title("🌍 Alumni Natural Disaster Monitor")

# Get database URL from environment or secrets
def get_db_url():
    # Try environment variables first (for Hugging Face)
    db_url = os.environ.get("POSTGRES_URL")
    
    # If not found, try Streamlit secrets (for local development)
    if not db_url and hasattr(st, "secrets") and "postgres" in st.secrets:
        db_url = st.secrets.postgres.url
    
    return db_url

# SIMPLE MODE - Show minimal UI and database connection test
if not st.session_state.app_loaded:
    st.info("Welcome to the Alumni Disaster Monitor")
    
    st.sidebar.markdown("### System Status")
    db_status = st.sidebar.empty()
    db_status.warning("⚠️ Click Test Connection to verify setup")
    
    # Connection test
    if st.button("Test Database Connection"):
        db_url = get_db_url()
        if db_url:
            try:
                engine = create_engine(
                    db_url, 
                    pool_pre_ping=True,
                    connect_args={"connect_timeout": 5}
                )
                
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    st.success("✅ Database connection successful!")
                    db_status.success("✅ Database connected")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
                db_status.error("❌ Connection failed")
        else:
            st.error("No database URL found in environment or secrets")
    
    # Launch full app
    if st.button("Launch Full Application"):
        st.session_state.app_loaded = True
        st.rerun()

# FULL APPLICATION - Show complete disaster monitoring system
else:
    try:
        # Import modules
        from utils.data_loader import load_alumni_data
        from utils.disaster_monitor import fetch_eonet_data, filter_disasters_by_type
        from utils.map_handler import create_map, calculate_proximity_alerts
        import folium
        from streamlit_folium import st_folium
        
        # Sidebar filters
        st.sidebar.markdown("### Disaster Filters")
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
        
        # Simple mode button
        if st.sidebar.button("◀️ Return to Simple Mode"):
            st.session_state.app_loaded = False
            st.rerun()
        
        # Main dashboard layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Disaster Monitoring Map")
            
            # Load data
            with st.spinner("Loading data..."):
                alumni_df, metadata = load_alumni_data()
                disaster_data = fetch_eonet_data()
                filtered_disasters = filter_disasters_by_type(disaster_data, selected_types) if disaster_data else []
            
            # Show map if data is available
            if alumni_df is not None and not alumni_df.empty and filtered_disasters:
                map_obj = create_map(alumni_df, filtered_disasters)
                st.info("🔵 Alumni locations | 🔴 Natural disasters")
                st_folium(map_obj, width=800, height=600)
            else:
                st.warning("Insufficient data to display map")
        
        with col2:
            st.subheader("Proximity Alerts")
            
            if alumni_df is not None and filtered_disasters:
                alerts = calculate_proximity_alerts(alumni_df, filtered_disasters, proximity_threshold)
                
                if alerts:
                    st.warning(f"⚠️ {len(alerts)} alerts within {proximity_threshold}km")
                    for alert in alerts:
                        with st.expander(f"🚨 {alert['alumni_name']} - {alert['disaster_type']}"):
                            st.write(f"Distance: {alert['distance']} km")
                            st.write(f"Location: {alert['location']}")
                            st.write(f"Disaster: {alert['disaster_description']}")
                else:
                    st.success("✅ No alerts within the threshold")
    
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        if st.button("Return to Simple Mode"):
            st.session_state.app_loaded = False
            st.rerun()
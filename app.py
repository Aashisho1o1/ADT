"""Alumni Disaster Monitor Streamlit application."""
import streamlit as st
import os
import logging
from utils.helpers import get_db_url, create_db_engine, mask_url, init_session_state, show_debug_info, run_database_diagnosis
from utils.data_loader import load_alumni_data

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
init_session_state()

# Page title
st.title("🌍 Alumni Natural Disaster Monitor")

# SIMPLE MODE
if not st.session_state.app_loaded:
    st.info("App is starting in safe mode for deployment stability")
    
    # Sidebar status
    st.sidebar.markdown("### System Status")
    st.sidebar.warning("⚠️ Database connection deferred for stability")
    
    # Main content
    st.write("Welcome to the Alumni Disaster Monitor!")
    
    # Debugging (only if needed)
    if st.session_state.show_debugging:
        show_debug_info()
    
    # Database test button
    if st.button("Test Database Connection", key="test_db"):
        db_url = get_db_url()
        if not db_url:
            st.error("No database URL found in environment or secrets")
            
        else:
            from sqlalchemy import text
            st.success(f"Found database configuration: {mask_url(db_url)}")
            
            try:
                engine = create_db_engine(db_url)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM alumni"))
                    count = result.scalar()
                    st.success(f"✅ Connected! Found {count} alumni records")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
    
    # Diagnosis button
    if st.button("Diagnose Data Loading", key="diagnose"):
        run_database_diagnosis()
    
    # Full app button
    if st.button("Load Full Application", key="load_app"):
        st.session_state.app_loaded = True
        st.session_state.show_debugging = False
        st.rerun()

# FULL APPLICATION MODE
else:
    try:
        # Import modules
        import pandas as pd
        from utils.disaster_monitor import fetch_eonet_data, filter_disasters_by_type
        from utils.map_handler import create_map, calculate_proximity_alerts
        from streamlit_folium import st_folium
        
        # Sidebar
        with st.sidebar:
            st.markdown("### Disaster Filters")
            
            disaster_types = ["Wildfires", "Severe Storms", "Volcanoes", "Earthquakes"]
            selected_types = st.multiselect("Select Types", disaster_types, default=disaster_types)
            
            proximity_threshold = st.slider("Alert Threshold (km)", 50, 1000, 200, 50)
            
            if st.button("◀️ Simple Mode", key="simple_btn"):
                st.session_state.app_loaded = False
                st.rerun()
        
        # Main content
        col1, col2 = st.columns([3, 1])
        
        # Map column
        with col1:
            st.subheader("🗺️ Disaster Monitoring Map")
            
            # Load data
            with st.spinner("Loading data..."):
                alumni_df, metadata = load_alumni_data()
                disaster_data = fetch_eonet_data()
                filtered_disasters = filter_disasters_by_type(disaster_data, selected_types) if disaster_data else []
            
            # Show data info  
            if metadata:
                st.success(f"Loaded {metadata.get('total_records', 0)} records from {metadata.get('source')}")
            
            # Create map if data is available
            if alumni_df is not None and not alumni_df.empty and filtered_disasters:
                map_obj = create_map(alumni_df, filtered_disasters)
                st_folium(map_obj, width=800, height=600)
            else:
                st.warning("Insufficient data to display map")
        
        # Alert column  
        with col2:
            st.subheader("⚠️ Proximity Alerts")
            
            if alumni_df is not None and not alumni_df.empty and filtered_disasters:
                alerts = calculate_proximity_alerts(alumni_df, filtered_disasters, proximity_threshold)
                
                if alerts:
                    st.warning(f"{len(alerts)} alerts within {proximity_threshold}km")
                    for alert in alerts:
                        with st.expander(f"🚨 {alert['alumni_name']} - {alert['disaster_type']}"):
                            st.write(f"Distance: {alert['distance']} km")
                            st.write(f"Location: {alert['location']}")
                            st.write(f"Disaster: {alert['disaster_description']}")
                else:
                    st.success("No alerts within the threshold")
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())
        
        if st.button("Return to Simple Mode", key="error_return"):
            st.session_state.app_loaded = False
            st.rerun()
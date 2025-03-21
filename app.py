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

# Initialize session state
if "app_loaded" not in st.session_state:
    st.session_state.app_loaded = False
if "show_debugging" not in st.session_state:
    st.session_state.show_debugging = True

st.title("🌍 Alumni Natural Disaster Monitor")

# Main content area - conditional on whether full app is loaded
if not st.session_state.app_loaded:
    st.info("App is starting in safe mode for Hugging Face deployment")
    
    # Create sidebar
    st.sidebar.markdown("### System Status")
    db_status = st.sidebar.empty()
    db_status.warning("⚠️ Database connection deferred for stability")
    
    # Main content area
    st.write("Welcome to the Alumni Disaster Monitor application!")
    st.write("This app helps track natural disasters near alumni locations.")
    
    # Debug secrets loading
    if st.session_state.show_debugging:
        with st.expander("Secrets Debugging", expanded=True):
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
    
    # Function to load the full application
    def load_full_app():
        st.session_state.app_loaded = True
        # Hide debugging info once full app is loaded
        st.session_state.show_debugging = False
        st.experimental_rerun()
    
    # Add button to enable full application mode
    st.button("Load Full Application", on_click=load_full_app)

else:
    # FULL APPLICATION MODE
    try:
        # Import required modules
        import pandas as pd
        import time
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
        
        # Add option to go back to simple mode
        if st.sidebar.button("Return to Simple Mode"):
            st.session_state.app_loaded = False
            st.session_state.show_debugging = True
            st.experimental_rerun()
        
        # Main application
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Disaster Monitoring Map")
            
            # Load data with spinner
            with st.spinner("Loading alumni data..."):
                alumni_df, metadata = load_alumni_data()
            
            with st.spinner("Fetching disaster data..."):
                disaster_data = fetch_eonet_data()
                filtered_disasters = filter_disasters_by_type(disaster_data, selected_types) if disaster_data else []
                if filtered_disasters:
                    st.success(f"Found {len(filtered_disasters)} disasters matching selected types")
                else:
                    st.info("No disasters found for the selected types")
            
            # Create and display map
            if alumni_df is not None and not alumni_df.empty and filtered_disasters:
                map_obj = create_map(alumni_df, filtered_disasters)
                st.info("Blue: Alumni locations | Red: Natural disasters")
                st_folium(map_obj, width=800, height=600)
            elif alumni_df is None or alumni_df.empty:
                st.error("No alumni data available. Please check your database connection.")
            else:
                st.warning("No disaster data to display on the map.")
        
        with col2:
            st.subheader("Proximity Alerts")
            
            if alumni_df is not None and not alumni_df.empty and filtered_disasters:
                alerts = calculate_proximity_alerts(alumni_df, filtered_disasters, proximity_threshold)
                
                if alerts:
                    st.warning(f"⚠️ {len(alerts)} alerts within {proximity_threshold}km")
                    for alert in alerts:
                        with st.expander(f"🚨 {alert['alumni_name']} - {alert['disaster_type']}"):
                            st.write(f"Distance: {alert['distance']} km")
                            st.write(f"Location: {alert['location']}")
                            st.write(f"Disaster: {alert['disaster_description']}")
                else:
                    st.success("✅ No alerts within the specified threshold")
            else:
                st.info("Data unavailable for alerts")
            
            # Show data summary
            if metadata:
                st.subheader("Data Summary")
                st.info(f"""
                📊 Alumni Data: {metadata.get('total_records', 0)} total records
                Source: {metadata.get('source', 'unknown')}
                """)
    
    except Exception as e:
        st.error(f"Error in full application: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        
        # Add button to return to simple mode
        if st.button("Return to Simple Mode"):
            st.session_state.app_loaded = False
            st.experimental_rerun()
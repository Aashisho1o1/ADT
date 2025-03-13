import streamlit as st
import pandas as pd
from utils.data_loader import load_alumni_data
from utils.disaster_monitor import fetch_eonet_data, filter_disasters_by_type
from utils.map_handler import create_map, calculate_proximity_alerts
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Alumni Disaster Monitor",
    page_icon="🌍",
    layout="wide"
)

def main():
    st.title("🌍 Alumni Natural Disaster Monitor")

    # Sidebar filters
    st.sidebar.header("Disaster Filters")
    disaster_types = ["Wildfires", "Severe Storms", "Volcanoes", "Earthquakes"]
    selected_types = st.sidebar.multiselect(
        "Select Disaster Types",
        disaster_types,
        default=disaster_types
    )

    proximity_threshold = st.sidebar.slider(
        "Proximity Alert Threshold (km)",
        min_value=50,
        max_value=1000,  # Increased max value for global coverage
        value=200,  # Increased default value
        step=50
    )

    # Load alumni data
    with st.spinner('Loading alumni data...'):
        try:
            # Updated to handle the new return format
            alumni_df, metadata = load_alumni_data()
            
            if alumni_df is None:
                st.error("Could not load alumni data. Please check the database connection.")
                return
                
            # Display data quality metrics
            if metadata:
                st.success(f"Loaded {metadata['total_records']} alumni records")
                
                # Display info about coordinates
                if metadata['invalid_coords'] > 0:
                    st.info(f"""
                    📊 Alumni Data Summary:
                    - Total Records: {metadata['total_records']}
                    - Records with Valid Coordinates: {metadata['total_records'] - metadata['invalid_coords']}
                    - Records with Default Coordinates: {metadata['invalid_coords']}
                    """)
            
        except Exception as e:
            st.error(f"Error loading alumni data: {str(e)}")
            return

    # Fetch disaster data
    with st.spinner('Fetching disaster data...'):
        try:
            disaster_data = fetch_eonet_data()
            if not disaster_data:
                st.warning("No current disaster data available")
                return

            filtered_disasters = filter_disasters_by_type(disaster_data, selected_types)
            st.success(f"Found {len(filtered_disasters)} disasters matching selected types")
        except Exception as e:
            st.error(f"Error fetching disaster data: {str(e)}")
            return

    # Create columns for map and data
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Disaster Monitoring Map")
        st.info("Blue markers: Alumni locations | Red markers: Natural disasters")
        map_obj = create_map(alumni_df, filtered_disasters)
        st_folium(map_obj, width=800)

    with col2:
        st.subheader("Proximity Alerts")
        alerts = calculate_proximity_alerts(alumni_df, filtered_disasters, proximity_threshold)

        if alerts:
            st.warning(f"⚠️ Found {len(alerts)} alerts within {proximity_threshold}km")
            for alert in alerts:
                with st.expander(f"🚨 {alert['alumni_name']} - {alert['disaster_type']}"):
                    st.write(f"Distance: {alert['distance']} km")
                    st.write(f"Location: {alert['location']}")
                    st.write(f"Disaster: {alert['disaster_description']}")
        else:
            st.info("✅ No alerts within the specified threshold.")

        st.subheader("Alumni Overview")
        if alumni_df is not None and not alumni_df.empty:
            st.dataframe(
                alumni_df[['Name', 'Location', 'Latitude', 'Longitude']].dropna(),
                hide_index=True
            )
        else:
            st.warning("No alumni data available to display.")

if __name__ == "__main__":
    main()
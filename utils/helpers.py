"""Helper functions for the Alumni Disaster Monitor app."""
import os
import streamlit as st
from sqlalchemy import create_engine, text
import time

def get_db_url():
    """Get database URL from environment or secrets."""
    # Try environment variables first (for Hugging Face)
    url = os.environ.get("POSTGRES_URL")
    
    # If not found, try Streamlit secrets (for local development)
    if not url and hasattr(st, "secrets") and "postgres" in st.secrets:
        try:
            url = st.secrets.postgres.url
        except:
            pass
        
    return url

def create_db_engine(url, timeout=5):
    """Create a database engine with proper settings."""
    if not url:
        return None
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": timeout}
    )

def mask_url(url):
    """Mask sensitive parts of a URL."""
    if not url:
        return "[no url]"
    return "...@" + url.split("@")[-1] if "@" in url else "[masked]"

def init_session_state():
    """Initialize all session state variables with defaults."""
    defaults = {
        "app_loaded": False,
        "show_debugging": True
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_debug_info():
    """Show condensed debug information."""
    with st.expander("System Information", expanded=False):
        # Check file existence
        streamlit_dir = ".streamlit"
        secrets_file = os.path.join(streamlit_dir, "secrets.toml")
        file_exists = os.path.exists(secrets_file)
        
        # Check secrets
        has_secrets = hasattr(st, "secrets") 
        has_postgres = has_secrets and "postgres" in dir(st.secrets)
        
        # Environment vars
        env_vars = {k: "[MASKED]" for k in os.environ if "POSTGRES" in k or "NASA" in k}
        
        # Show info
        st.json({
            "Files": {
                "secrets.toml exists": file_exists
            },
            "Database Access": {
                "Environment Variables": bool(env_vars),
                "Streamlit Secrets": has_secrets,
                "Postgres Section": has_postgres
            },
            "Environment Variables": list(env_vars.keys())
        })

def run_database_diagnosis():
    """Run comprehensive database diagnosis."""
    from utils.data_loader import load_alumni_data
    
    st.info("Testing data loading pipeline...")
    start_time = time.time()
    df, metadata = load_alumni_data()
    duration = time.time() - start_time
    
    if df is None:
        st.error("❌ Data loading failed")
        return
        
    # Success path
    st.success(f"✅ Data loaded in {duration:.2f}s | " +
               f"Source: {metadata.get('source', 'unknown')} | " +
               f"Records: {metadata.get('total_records', 0)}")
    
    # Show valid coordinates count
    valid_count = df['Has_Valid_Coords'].sum() if 'Has_Valid_Coords' in df.columns else 0
    st.info(f"Records with valid coordinates: {valid_count}")
    
    # Show sample data in expander
    with st.expander("Sample Data"):
        st.dataframe(df.head())
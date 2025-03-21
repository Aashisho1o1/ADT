import os
import streamlit as st

def get_db_url():
    """Get database URL from Streamlit secrets or environment variables"""
    # Try Streamlit secrets first (works locally and on Streamlit Cloud)
    try:
        return st.secrets["postgres"]["url"]
    except Exception:
        # Try environment variables (works on Hugging Face)
        return os.environ.get("POSTGRES_URL")
        
def get_nasa_api_key():
    """Get NASA API key from Streamlit secrets or environment variables"""
    # Try Streamlit secrets
    try:
        return st.secrets["nasa"]["api_key"]
    except Exception:
        # Try environment variables
        return os.environ.get("NASA_API_KEY")
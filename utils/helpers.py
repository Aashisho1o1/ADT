import os
import streamlit as st
from sqlalchemy import create_engine

def get_db_url():
    """Get database URL from environment or secrets."""
    # Try environment variables first (for Hugging Face)
    url = os.environ.get("POSTGRES_URL")
    
    # If not found, try Streamlit secrets (for local development)
    if not url and hasattr(st, "secrets") and "postgres" in st.secrets:
        url = st.secrets.postgres.url
        
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
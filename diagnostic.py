import streamlit as st
import os
import sys
import pandas as pd

st.set_page_config(page_title="Diagnostic App", page_icon="🔧")
st.title("Deployment Diagnostic")

# Show basic environment info
st.write("## System Information")
st.json({
    "Python Version": sys.version,
    "Platform": sys.platform,
    "Working Directory": os.getcwd(),
    "Files in Directory": os.listdir(".")[:20]  # Show first 20 files to avoid cluttering the UI
})

# Show installed packages
st.write("## Installed Packages")
try:
    import pkg_resources
    packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])
    st.code("\n".join(packages[:50]))  # Show first 50 packages
    st.info(f"Total packages: {len(packages)}")
except Exception as e:
    st.error(f"Error listing packages: {e}")

# Check for Streamlit secrets
st.write("## Secrets Check")
try:
    keys = list(st.secrets.keys())
    if "postgres" in keys:
        st.success("✅ Found 'postgres' in secrets")
        if "url" in st.secrets.postgres:
            masked_url = "...@" + st.secrets.postgres.url.split("@")[-1] if "@" in st.secrets.postgres.url else "[masked]"
            st.success(f"✅ Found database URL ending with {masked_url}")
        else:
            st.error("❌ 'url' not found in postgres secrets")
    else:
        st.error("❌ 'postgres' not found in secrets")
    
    st.info(f"Available secret sections: {', '.join(keys)}")
except Exception as e:
    st.error(f"Error checking secrets: {e}")
    
# Check database connection (without actually connecting)
st.write("## Database Connection Check")
try:
    from sqlalchemy import __version__ as sa_version
    st.info(f"SQLAlchemy version: {sa_version}")
    
    from utils.database import get_connection_string
    conn_string = get_connection_string()
    if conn_string:
        masked = "...@" + conn_string.split("@")[-1] if "@" in conn_string else "[masked]"
        st.success(f"✅ Found connection string ending with {masked}")
    else:
        st.error("❌ No connection string found")
except Exception as e:
    st.error(f"Error during database check: {e}")

st.success("Diagnostic completed successfully!") 
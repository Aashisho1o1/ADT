import streamlit as st
import os
import sys

st.set_page_config(page_title="Environment Debug")

st.title("Environment Debug")

# Print Python version
st.write(f"Python Version: {sys.version}")
st.write(f"Platform: {sys.platform}")

# Print environment variables (hiding sensitive info)
env_vars = {}
for key, value in os.environ.items():
    if any(x in key.lower() for x in ["secret", "token", "password", "key", "url"]):
        env_vars[key] = "***REDACTED***"
    else:
        env_vars[key] = value

st.subheader("Environment Variables")
st.json(env_vars)

# Safely check for secrets
st.subheader("Streamlit Secrets")
try:
    # Get all secret sections
    secret_sections = list(st.secrets.keys())
    st.write(f"Found {len(secret_sections)} secret sections: {', '.join(secret_sections)}")
    
    # Check for postgres section
    if "postgres" in secret_sections:
        st.success("✅ Found 'postgres' section in secrets")
        if "url" in st.secrets.postgres:
            conn_str = st.secrets.postgres.url
            masked = f"...@{conn_str.split('@')[-1]}" if "@" in conn_str else "[masked]"
            st.success(f"✅ Found database URL ending with: {masked}")
        else:
            st.error("❌ Missing 'url' in postgres section")
except Exception as e:
    st.error(f"Error accessing secrets: {str(e)}")

st.success("App loaded successfully!") 
import streamlit as st
import pandas as pd
import os
import sys
import traceback
from sqlalchemy import create_engine, inspect

st.set_page_config(page_title="Diagnostics", page_icon="🔍")

# Diagnostic functions
def test_database_connection():
    try:
        # Try to get database URL
        db_url = None
        
        # Try from secrets
        try:
            db_url = st.secrets["postgres"]["url"]
            st.success("✅ Found database URL in Streamlit secrets")
        except Exception as e:
            st.error(f"❌ Could not find database URL in secrets: {str(e)}")
            
            # Try from environment
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                st.success("✅ Found database URL in environment variables")
            else:
                st.error("❌ No database URL found in environment variables")
        
        if not db_url:
            return False
        
        # Create test connection
        st.info(f"Attempting to connect to database...")
        engine = create_engine(db_url)
        
        # Test connection with timeout
        conn = engine.connect()
        result = conn.execute("SELECT 1")
        one = result.scalar()
        conn.close()
        
        if one == 1:
            st.success("✅ Successfully connected to database")
            
            # Show schema info
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            st.success(f"Found tables: {', '.join(tables)}")
            
            # Check for alumni table
            if "alumni" in tables:
                conn = engine.connect()
                result = conn.execute("SELECT COUNT(*) FROM alumni")
                count = result.scalar()
                conn.close()
                st.success(f"✅ Found {count} records in alumni table")
            else:
                st.error("❌ No alumni table found in database")
            
            return True
        return False
        
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        st.code(traceback.format_exc())
        return False

def main():
    st.title("🔍 Alumni Disaster Monitor - Diagnostics")
    
    st.write("This diagnostic tool helps identify deployment issues.")
    
    st.header("1. Environment Information")
    st.json({
        "Python Version": sys.version,
        "Working Directory": os.getcwd(),
        "Environment Variables": {k: "***" if "key" in k.lower() or "url" in k.lower() or "password" in k.lower() else v 
                                 for k, v in os.environ.items()}
    })
    
    st.header("2. Database Connection")
    db_success = test_database_connection()
    
    st.header("3. File System Access")
    st.subheader("CSV Files")
    paths_to_check = [
        'assets/sample_alumni.csv',
        'assets/simplified_alumni.csv',
        'assets/combo3.csv',
        'attached_assets/combo3.csv',
        'attached_assets/combo 3.csv'
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            st.success(f"✅ Found: {path} ({os.path.getsize(path)} bytes)")
        else:
            st.error(f"❌ Not found: {path}")
    
    st.header("4. Next Steps")
    if db_success:
        st.success("Database connection is working. Try deploying your main app again.")
    else:
        st.error("""
        Database connection is failing. Recommendations:
        1. Check your Neon database settings - ensure it's active and accessible
        2. Verify your Streamlit secrets have the correct postgres.url value
        3. Deploy with a CSV fallback mechanism or fix the database connection
        """)

if __name__ == "__main__":
    main() 
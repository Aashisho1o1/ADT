import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st
import pandas as pd
import os.path

# Load environment variables for local development
load_dotenv()

# Create Base class
Base = declarative_base()

# Alumni model definition
class Alumni(Base):
    __tablename__ = "alumni"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    last_updated = Column(DateTime)

# Try to get database URL from Streamlit secrets first, then environment
def get_connection_string():
    try:
        return st.secrets["postgres"]["url"]
    except:
        # Fallback for local development (use environment variables)
        return os.getenv("DATABASE_URL")

# Engine and session factory
try:
    # Try to create database connection
    db_url = get_connection_string()
    if db_url:
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
    else:
        # Setup dummy placeholders if no database connection
        engine = None
        SessionLocal = None
        def get_db():
            yield None
            
except Exception as e:
    st.warning(f"Database connection failed: {str(e)}. Using CSV fallback.")
    engine = None
    SessionLocal = None
    def get_db():
        yield None

class DisasterEvent(Base):
    __tablename__ = "disaster_events"

    id = Column(Integer, primary_key=True, index=True)
    eonet_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    disaster_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)

def init_db():
    """Initialize the database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        st.success("Database initialized successfully")
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        raise e
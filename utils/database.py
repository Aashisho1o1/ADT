"""Database connection and model definitions for the Alumni Disaster Monitor app."""
import os
from contextlib import contextmanager
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit as st
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Base class
Base = declarative_base()

# Model definitions
class Alumni(Base):
    """Alumni database model."""
    __tablename__ = "alumni"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    last_updated = Column(DateTime)

class DisasterEvent(Base):
    """Disaster event database model."""
    __tablename__ = "disaster_events"
    id = Column(Integer, primary_key=True, index=True)
    eonet_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    disaster_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)

# Database connection
def get_connection_string():
    """Get database connection string with proper fallbacks."""
    # Try Streamlit secrets first
    try:
        return st.secrets["postgres"]["url"]
    except Exception as e:
        logger.info(f"Streamlit secrets not available: {e}")
    
    # Try environment variable fallback
    return os.environ.get("DATABASE_URL")

# Global variables
engine = None
SessionLocal = None

def get_engine():
    """Lazy initialize database engine only when needed"""
    global engine
    if engine is None:
        connection_string = get_connection_string()
        if connection_string:
            try:
                engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    pool_recycle=1800,
                    connect_args={"connect_timeout": 10}
                )
            except Exception as e:
                logger.error(f"Database connection error: {e}")
    return engine

# Initialize database connection
try:
    connection_string = get_connection_string()
    if connection_string:
        engine = create_engine(
            connection_string, 
            pool_pre_ping=True,         # Check connection before using
            pool_recycle=1800,          # Recycle connections after 30 min
            connect_args={"connect_timeout": 10}  # 10 second connection timeout
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database connection initialized")
    else:
        logger.warning("No database connection string found")
        engine, SessionLocal = None, None
except Exception as e:
    logger.error(f"Database connection error: {e}")
    engine, SessionLocal = None, None

@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    if SessionLocal is None:
        yield None
        return
        
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def init_database():
    """Initialize database tables."""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        return True
    return False

# Legacy generator for compatibility
def get_db():
    """Session generator for backwards compatibility."""
    if SessionLocal is None:
        yield None
        return
        
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# No CSV files found
logger.error("No CSV files found")
# Return an empty DataFrame with required columns
empty_df = pd.DataFrame({
    'Name': ['Sample User'],
    'Location': ['Default Location'],
    'Latitude': [0],
    'Longitude': [0],
    'Has_Valid_Coords': [False]
})
return empty_df, {"total_records": 0, "invalid_coords": 0, "source": "default"}
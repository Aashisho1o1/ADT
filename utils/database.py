import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st
import pandas as pd
import os.path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # First try Streamlit secrets
        db_url = st.secrets["postgres"]["url"]
        logger.info("Using database URL from Streamlit secrets")
        return db_url
    except Exception as e:
        logger.info(f"Could not get URL from Streamlit secrets: {e}")
        
        # Fallback to environment variable
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            logger.info("Using database URL from environment variables")
            return db_url
        
        logger.warning("No database URL found in secrets or environment!")
        return None

# Initialize engine with proper connection pooling
try:
    connection_string = get_connection_string()
    if connection_string:
        # Add connection pooling parameters
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,  # Validates connections before using them
            pool_recycle=3600,   # Recycle connections after 1 hour
            pool_size=5,         # Start with 5 connections in the pool
            max_overflow=10      # Allow up to 10 additional connections
        )
        logger.info("Database engine initialized successfully with connection pooling")
    else:
        logger.error("No connection string available - database will not be functional")
        engine = None
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    engine = None

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database dependency
def get_db():
    if engine is None:
        logger.error("Cannot create database session: engine is None")
        raise Exception("Database engine not initialized")
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
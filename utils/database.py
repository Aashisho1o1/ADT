from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import streamlit as st

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    st.error("Database URL not found in environment variables")
    raise Exception("Database URL not configured")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Alumni(Base):
    __tablename__ = "alumni"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    last_updated = Column(DateTime)

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

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
import os
import sys

# Set your Neon database URL as an environment variable
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_EJYSd2IA0lbp@ep-cold-scene-a6mv9l89-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"


# Import your existing functions
from utils.database import Base, engine
from utils.init_db import init_database
from utils.load_sample_data import load_sample_alumni

if __name__ == "__main__":
    print("Loading sample data into Neon database...")
    
    # Initialize database if needed
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    # Load sample data
    print("Adding sample records...")
    load_sample_alumni()
    
    print("Data loading complete!")
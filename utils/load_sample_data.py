from sqlalchemy import create_engine
from .database import Base, Alumni, engine
from datetime import datetime
import pandas as pd

def load_sample_alumni():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Sample alumni data
    sample_data = [
        {
            "name": "John Doe",
            "location": "Tokyo, Japan",
            "latitude": 35.6762,
            "longitude": 139.6503,
            "last_updated": datetime.now()
        },
        {
            "name": "Jane Smith",
            "location": "Osaka, Japan",
            "latitude": 34.6937,
            "longitude": 135.5023,
            "last_updated": datetime.now()
        },
        # Add more sample data as needed
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(sample_data)
    
    # Insert into database
    df.to_sql('alumni', engine, if_exists='append', index=False)
    
if __name__ == "__main__":
    load_sample_alumni() 
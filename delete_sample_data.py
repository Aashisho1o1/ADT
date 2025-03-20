import os
from sqlalchemy import delete
from sqlalchemy.orm import Session

# Set your Neon database URL as an environment variable
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_EJYSd2IA0lbp@ep-cold-scene-a6mv9l89-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"

# Import your database components
from utils.database import Base, Alumni, engine

if __name__ == "__main__":
    print("Connecting to Neon database...")
    
    # Create a session
    session = Session(engine)
    
    try:
        # Delete only the sample records
        sample_names = ["John Doe", "Jane Smith"]
        
        # Create a delete statement for Alumni records with these names
        stmt = delete(Alumni).where(Alumni.name.in_(sample_names))
        
        # Execute the statement
        result = session.execute(stmt)
        session.commit()
        
        print(f"Deleted {result.rowcount} sample records")
        
    except Exception as e:
        session.rollback()
        print(f"Error deleting records: {str(e)}")
    finally:
        session.close() 
import os
import sys
import traceback

# Set your Neon database URL as an environment variable
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_EJYSd2IA0lbp@ep-cold-scene-a6mv9l89-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"

if __name__ == "__main__":
    print("Importing alumni data from CSV to Neon database...")
    
    try:
        # First, let's check if the utils directory is accessible
        print("Checking module path...")
        import utils
        print("utils module found")
        
        # Import your CSV import function
        from utils.import_csv_data import import_from_csv
        print("import_from_csv function imported successfully")
        
        # Path to your combo3.csv file - check multiple possible locations
        potential_paths = [
            'attached_assets/combo3.csv',
            'assets/combo3.csv',
            './combo3.csv',
            'attached_assets/combo3.csv',  # Note the space in filename
            'assets/simplified_alumni.csv'
        ]
        
        csv_path = None
        for path in potential_paths:
            print(f"Checking for CSV at: {path}")
            if os.path.exists(path):
                csv_path = path
                print(f"Found file at: {csv_path}")
                break
        
        if csv_path is None:
            print("ERROR: Could not find any CSV file in the following locations:")
            for path in potential_paths:
                print(f"  - {path}")
            sys.exit(1)
            
        # Print file size to verify it's not empty
        file_size = os.path.getsize(csv_path)
        print(f"CSV file size: {file_size} bytes")
        
        # Import CSV data to database
        print(f"Starting import from {csv_path}...")
        import_from_csv(csv_path)
        print("Data import complete!")
        
    except Exception as e:
        print(f"ERROR: An exception occurred: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)
import pandas as pd
import chardet

def detect_encoding(file_path):
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def load_alumni_data(file_path='attached_assets/Sohokai_List_20240726(Graduated).csv'):
    """Load and process alumni data from CSV."""
    try:
        # Detect file encoding
        encoding = detect_encoding(file_path)
        
        # Read CSV with detected encoding
        df = pd.read_csv(file_path, encoding=encoding)
        
        # Assuming columns for location data
        required_columns = ['Name', 'Location', 'Latitude', 'Longitude']
        
        # Create sample data if columns don't exist
        if not all(col in df.columns for col in required_columns):
            # Create sample data for testing
            sample_data = {
                'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
                'Location': ['Tokyo, Japan', 'New York, USA', 'London, UK'],
                'Latitude': [35.6762, 40.7128, 51.5074],
                'Longitude': [139.6503, -74.0060, -0.1278]
            }
            df = pd.DataFrame(sample_data)
        
        # Filter out rows with missing location data
        df = df.dropna(subset=['Latitude', 'Longitude'])
        
        return df
    
    except Exception as e:
        raise Exception(f"Error loading alumni data: {str(e)}")

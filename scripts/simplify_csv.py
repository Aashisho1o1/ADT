import pandas as pd
import chardet
import os

def simplify_csv():
    """Create a simplified version of the alumni data with essential columns."""
    try:
        print("Reading source file...")

        # Read the original file with encoding detection
        with open('attached_assets/combo 3.csv', 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            print(f"Detected encoding: {result['encoding']}")

        # Skip the first row which contains 'combo'
        df = pd.read_csv(
            'attached_assets/combo 3.csv',
            skiprows=1,  # Skip the 'combo' header
            encoding=result['encoding']
        )

        print("\nProcessing data...")
        print("Available columns:", df.columns.tolist())

        # Create output directory if it doesn't exist
        os.makedirs('assets', exist_ok=True)

        # Create name field by combining first and last names
        df['Name'] = df['original_First Name'] + ' ' + df['original_Prim_Last']

        # Create location field
        df['Location'] = df.apply(
            lambda row: f"{row['original_City']}, {row['original_State']}, {row['original_Country']}",
            axis=1
        )

        # Create simplified dataframe
        simplified_df = pd.DataFrame({
            'Name': df['Name'],
            'Location': df['Location'],
            'City': df['original_City'],
            'State': df['original_State'],
            'Country': df['original_Country'],
            'Postal': df['original_Postal'],
            'Latitude': df['lat'],
            'Longitude': df['lon']
        })

        # Remove any rows where coordinates are missing
        simplified_df = simplified_df.dropna(subset=['Latitude', 'Longitude'])

        # Save to new CSV
        output_path = 'assets/simplified_alumni.csv'
        simplified_df.to_csv(output_path, index=False)

        print(f"\nSuccessfully created simplified CSV at {output_path}")
        print(f"Total records: {len(simplified_df)}")
        print("\nFirst few rows:")
        print(simplified_df.head())

    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    simplify_csv()
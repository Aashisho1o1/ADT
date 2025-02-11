import pandas as pd
import chardet
import os

def simplify_csv():
    """Create a simplified version of the alumni data with essential columns."""
    try:
        print("Reading source file...")

        # Read the original file with encoding detection
        with open('attached_assets/combo.csv', 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            print(f"Detected encoding: {result['encoding']}")

        # Read CSV file with more flexible parsing
        df = pd.read_csv(
            'attached_assets/combo.csv',
            encoding=result['encoding'],
            comment='#',
            skipinitialspace=True,
            on_bad_lines='skip'  # Skip problematic lines
        )

        print("\nProcessing data...")
        print("Available columns:", df.columns.tolist())

        # Create output directory if it doesn't exist
        os.makedirs('assets', exist_ok=True)

        # Map the correct column names
        column_mapping = {
            'original_First Name': 'First Name',
            'original_Prim_Last': 'Last Name',
            'original_Address 1': 'Address',
            'original_City': 'City',
            'original_State': 'State',
            'original_Country': 'Country',
            'original_Postal': 'Postal',
            'lat': 'Latitude',
            'lon': 'Longitude'
        }

        # Select only the columns we need
        needed_columns = list(column_mapping.keys())
        available_columns = [col for col in needed_columns if col in df.columns]

        if not available_columns:
            raise ValueError("None of the required columns found in the CSV file")

        simplified_df = df[available_columns].copy()

        # Rename the columns
        simplified_df.columns = [column_mapping[col] for col in available_columns]

        # Remove any rows where all location fields are empty
        simplified_df = simplified_df.dropna(
            subset=['Latitude', 'Longitude'],
            how='all'
        )

        # Save to new CSV
        output_path = 'assets/simplified_alumni.csv'
        simplified_df.to_csv(output_path, index=False)

        print(f"\nSuccessfully created simplified CSV at {output_path}")
        print(f"Total records: {len(simplified_df)}")
        print("\nFirst few rows:")
        print(simplified_df.head())

    except FileNotFoundError:
        print("Error: Source file 'attached_assets/combo.csv' not found")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    simplify_csv()
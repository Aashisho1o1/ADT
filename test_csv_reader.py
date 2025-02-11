import pandas as pd
import chardet
import streamlit as st

def read_sohokai_csv():
    file_path = 'attached_assets/Sohokai_List_20240726(Graduated).csv'
    
    # Read the raw file to detect encoding
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        print(f"Detected encoding: {result}")
        
        # Try reading with detected encoding
        try:
            df = pd.read_csv(file_path, encoding=result['encoding'])
            print("Columns in the file:", df.columns.tolist())
            print("\nFirst few rows:")
            print(df.head())
            return df
        except Exception as e:
            print(f"Error reading CSV: {str(e)}")
            return None

if __name__ == "__main__":
    df = read_sohokai_csv()

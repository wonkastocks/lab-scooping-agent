import csv
import json
import os
import codecs
from pathlib import Path

def convert_csv_to_json(csv_file_path, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base filename without extension
    base_filename = Path(csv_file_path).stem
    json_file_path = os.path.join(output_dir, f"{base_filename}.json")
    
    print(f"Converting {csv_file_path} to {json_file_path}")
    
    # Try different encodings
    encodings = ['utf-8-sig', 'latin-1', 'windows-1252', 'cp1252']
    
    for encoding in encodings:
        try:
            # Open the CSV file with current encoding
            with open(csv_file_path, 'r', encoding=encoding) as csv_file:
                # Read CSV content
                csv_reader = csv.DictReader(csv_file)
                
                # Convert each row into a dictionary and add to a list
                data = []
                for row in csv_reader:
                    # Clean up any problematic characters in the data
                    clean_row = {}
                    for key, value in row.items():
                        if isinstance(value, str):
                            # Remove any non-printable characters
                            clean_row[key] = ''.join(char for char in value if char.isprintable() or char in '\n\r\t')
                        else:
                            clean_row[key] = value
                    data.append(clean_row)
                
                # Write JSON data to file with UTF-8 encoding
                with open(json_file_path, 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, indent=2, ensure_ascii=False)
                
                print(f"Successfully converted {len(data)} records using {encoding} encoding")
                return True
                
        except UnicodeDecodeError:
            print(f"Failed with {encoding} encoding, trying next...")
            continue
        except Exception as e:
            print(f"Error with {encoding} encoding: {str(e)}")
            continue
    
    print(f"Failed to convert {csv_file_path} with any encoding")
    return False

def main():
    # Define input and output paths
    input_dir = "/Users/walterbarr_1/Projects/lab-scooping-agent/Courses"
    output_dir = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES"
    
    # List of CSV files to convert
    csv_files = [
        "Constellation Lab Tracker(Conversion Tracker) (2).csv",
        "infosec_learning-content_export-2025-05-19t07-07-04.csv"
    ]
    
    # Convert each CSV file
    for csv_file in csv_files:
        csv_path = os.path.join(input_dir, csv_file)
        if os.path.exists(csv_path):
            convert_csv_to_json(csv_path, output_dir)
        else:
            print(f"File not found: {csv_path}")

if __name__ == "__main__":
    main()

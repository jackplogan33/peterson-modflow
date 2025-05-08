import os
import multiprocessing as mp
import numpy as np
import pandas as pd
import pyemu
import subprocess
import re

def fix_scientific_notation(value):
    if isinstance(value, str):
        return re.sub(r'(\d+)-(\d+)', r'\1e-\2', value)
    return value  # Return unchanged if not a string

def process_csv(file_path):
    try:
        df = pd.read_csv(file_path, dtype=str)  # Read as string to avoid automatic misinterpretation
        df = df.map(fix_scientific_notation)
        df = df.apply(pd.to_numeric)  # Convert columns back to numeric where possible
        df.to_csv(file_path, index=False)  # Save the fixed CSV
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    output_files = ['outputs/pfos_obs.csv', 'outputs/pfoa_obs.csv', 'outputs/pfhxs_obs.csv']

    os.chdir('./inputs')
    
    # Remove existing observation files
    for file in output_files:
        try:
            os.remove(file)
        except Exception:
            print(f'Error removing tmp file: {file}')

    # Run the mf6.exe executable
    try:
        subprocess.run(['../../bin/mf6', 'mfsim.nam'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running mf6.exe: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Process output CSVs
    for file in output_files:
        process_csv(file)

if __name__ == '__main__':
    mp.freeze_support()
    main()

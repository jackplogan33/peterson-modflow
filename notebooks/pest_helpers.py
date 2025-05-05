import pandas as pd
import shutil
import numpy as np
import re
import flopy
from pathlib import Path

def create_temp_workspace(
    model_dir: str, 
    template_dir: str, 
    subdirs: list[str] =["org", "mult"]
):
    """Copy model directory and create subdirectories for PEST template workspace.

    Parameters:
    -----------
    model_dir: str
        Absolute or relative path to top model workspace.
        Must hold all required files to run the model.

    template_dir: str
        Absolute or relative path to top template workspace.
        Will copy *all* files and folder from `model_dir` and paste
        under `template_dir`

    subdirs: list[str]
        Subdirectories to create in `template_dir`. Defaults to 
        'org' and 'mult'.
    """
    template_path = Path(template_dir)  # Turn tempdir into an absolute path

    # Remove files in temp path if it already exists
    if template_path.exists(): shutil.rmtree(template_path)

    # Copy contents of model dir to temp
    shutil.copytree(model_dir, template_path)

    # Make subdirectories
    for subdir in subdirs:
        (template_path / subdir).mkdir()

    print(f"Workspace set up at: {template_path.resolve()}")

def _closest_time(time, mod_times, used_times):
    """Internal function to find closest model time for an observation"""
    mod_times_np = np.array(mod_times)
    available = np.array([t for t in mod_times_np if t not in used_times])
    if available.size == 0:
        closest_time = mod_times_np[np.argmin(np.abs(mod_times_np - time))]
    else:
        closest_time = available[np.argmin(np.abs(available - time))]
    used_times.add(closest_time)
    return closest_time

def align_observed_to_output_times(obs, output):
    """Aligh obs df to model times"""
    mod_times = output['time'].tolist()
    
    used_times = set()
    obs = obs.copy()
    obs['time'] = obs['time'].apply(lambda t: _closest_time(t, mod_times, used_times))
    obs.drop_duplicates(subset=['time'], inplace=True)
    return obs

def _scientific_notation(value):
    if isinstance(value, str):
        return re.sub(r'(\d+)-(\d+)', r'\1e-\2', value)
    return value  # Return unchanged if not a string

def fix_scientific_notation(filepath: str | Path, output_path: str | Path = None):
    """
    Reads a CSV, fixes scientific notation formatting (e.g., 1-100 ➜ 1e-100),
    converts all values to numeric, and saves the corrected file. 

    Parameters:
    -----------
    
    filepath (str | Path): 
        Path to CSV with broken scientific notation.
            
    output_path (str | Path, optional): 
        Path to save output CSV. Only pass if not overwriting `filepath`.
        Defaults to overwriting original CSV.
    """
    filepath = Path(filepath)
    if output_path is None:
        output_path = filepath

    # Read all data as strings to avoid parse errors
    df = pd.read_csv(filepath, dtype=str)

    # Apply fix to every element
    df_fixed = df.map(_scientific_notation)

    # Convert all values to numeric (float/int)
    df_fixed = df_fixed.apply(pd.to_numeric)

    # Save the fixed CSV
    df_fixed.to_csv(output_path, index=False)

def write_ins(
    df: pd.DataFrame, 
    path: str, 
    solute: str,
    nan_value: int | float = -999
):
    """Write the PEST++ instructional file with observation data

    Paramters:
    ----------
    df: pd.DataFrame
        long name dataframe with columns 'time', 'well', and 'value'

    path: str
        path to write INS file to. Place it in the template file

    solute: str
        flag to indicate the solute for this INS file and the observations

    nan_value: int | float
        Observations to pass as 'dum' to the INS file.
    """
    ins_lines = ['pif ~', 'l1']

    for time, group in df.groupby('time'):
        ins_line =  'l1'
        for well, value in zip(group['well'], group['value']):
            if value == nan_value:
                ins_line += ' ~,~ !dum! '

            else:
                ins_line += f' ~,~ !{well}_{time}_{solute}! '

        ins_lines.append(ins_line)

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ins_lines))


def write_external_obs(df, path, solute, k=0.002, forecast_val=-888, nan_val=-999):
    """Write observational file with weights.

    Parameters:
    -----------
    df: pd.DataFrame
        Long name dataframe

    k: float | int
        obs weight scalar

    path: str
        path to obs file

    forecast_val: int | float
        If this value is read, will create an observation with weight 0.
        Allows compatibility with the forecasting functionality

    nan_val: int | float
        If this value is read, no observation is created
    """
    obs_data = []

    df = df[df['value'] != nan_val]

    for time, group in df.groupby('time'):
        for _, row in group.iterrows():
            # Construct a new row for each observation
            new_row = {
                "obsnme": f"{row['well']}_{time}_{solute}",  # Observation name: wellname_time_solute
                "obsval": row["value"],                  # Observation value: the value in the 'value' column
                "weight": 1 /(row["value"] * k),         # Observation weight = sigma = 1/kC
                "obgnme": "cnc"                          # Observation group: always 'cnc'
            }
                
            if row['value'] == forecast_val:
                new_row['weight'] = 0

            obs_data.append(new_row)

    obs_data_df = pd.DataFrame(obs_data)
    obs_data_df.to_csv(path, index=False)
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

def write_tpl(path, zones, param, solute):
    """Write the PEST++ Template file

    Parameters:
    -----------
    path: str
        path to tpl

    zones: np.ndarray
        zone array

    param: str
        parameter to write. Must be one of {'kd', 'theta', 'thetaim', 'rhob'}.
        kd: distance coefficient
        theta: mobile porosity
        thetaim: immobile porosity
        rhob: bulk density

    solute: str
        string indicating solute name. **Only used for kd.** 
        If writing writing other param, pass `solute="all"`
    """
    if param not in {'kd', 'theta', 'thetaim', 'rhob'}:
        raise ValueError(f"write_tpl() receive invalid value for param: {param}")
    
    with open(path, 'w', encoding='utf-8') as tpl:
        tpl.write('ptf ~\n')  # header for TPL file

        # Iterate through each line of the array
        for row in zones:
            # Initialize line for TPL 
            line = []
            for val in row:  # Iterate through values in data
                # If value is zero, leave as is
                if val == 0: line.append(f'{val}')

                # If value is an integer, add to file
                elif val.is_integer():
                    if param == 'kd':
                        line.append(f'~{solute.upper()}_{param.upper()}{int(val)}~')
                        
                    else:
                        line.append(f'~{param.upper()}{int(val)}~')

                # All else, set invalid
                else: line.append(f'~{param}_invalid~')
            
            # Join each value as space delimited, write to file, create newline
            tpl.write(' '.join(line) + '\n')

def write_cnc_tpl(cnc_path, tpl_path, mult_map):
    # Read the original file's contents
    with open(cnc_path, 'r') as file:
        file_contents = file.read().splitlines()

    modified_lines = ['pft ~']  # Store file lines, start with pest header
    period_block = False        # Initialize period block var
    
    # Iterate through the lines of the file
    for line in file_contents:
        stripped = line.strip()
        
        # Check if we are in a period block
        if stripped.startswith('BEGIN period'):
            period_block = True
            continue
        elif stripped.startswith('END period'):
            period_block = False
            continue

        # check if in a period block, the line exists, and is not a comment
        if period_block and stripped and not stripped.startswith('#'):
            split = line.split()  # Parse line data

            if len(split) == 6:   # 6 length line is a CNC entry
                layer, row, col = split[0:3]  # Extract cellid
                conc = split[3]               # Concentration val
                mult = split[4]               # Multiplier value
                boundname = split[5]          # Boundname

                if boundname in mult_map.keys():
                    # Access new multiplier from map
                    mult = mult_map[boundname]

                line = f"  {layer} {row} {col}  {conc:<18} {mult:<10} {boundname}"
                
        modified_lines.append(line)
                
    # Save the updated contents to a new file
    with open(tpl_path, 'w') as f:
        f.write('\n'.join(modified_lines))


def write_control_file(
    file_path,
    parameter_group_file,
    parameter_file,
    obs_files,  # Accepts list[str]
    model_command,
    input_file,
    output_file,
    options=None  # Optional control keywords
):
    """Writes the PEST++ Control file for Version 2

    Parameters:
    -----------
    file_path: str
        
    """
    if isinstance(obs_files, str):
        obs_files = [obs_files]

    default_options = {
        "pestmode": "estimation",
        "noptmax": "10",
        "svdmode": "1",
        "maxsing": "10000000",
        "eigthresh": "1e-06",
        "eigwrite": "1",
        "parcov": "peterson_tran.cov",
        "ies_num_reals": "250",
        "ies_num_threads": "74",
        "ies_multimodal_alpha": "0.25",
        "ies_n_iter_reinflate": "3",
    }
    options = options or default_options

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("pcf version=2\n")

        # CONTROL DATA
        f.write("* control data keyword\n")
        for key, value in options.items():
            f.write(f"{key:<40}{value}\n")

        # PARAMETER GROUP
        f.write("* parameter groups external\n")
        f.write(f"{parameter_group_file}\n")

        # PARAMETER DATA
        f.write("* parameter data external\n")
        f.write(f"{parameter_file}\n")

        # OBSERVATION DATA
        f.write("* observation data external\n")
        for obs in obs_files:
            f.write(f"{obs}\n")

        # MODEL COMMAND
        f.write("* model command line\n")
        f.write(f"{model_command}\n")

        # MODEL INPUT/OUTPUT
        f.write("* model input external\n")
        f.write(f"{input_file}\n")
        f.write("* model output external\n")
        f.write(f"{output_file}\n")
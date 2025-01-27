import numpy as np
import pandas as pd

def parse_well_file(filepath):
    """Parse a single well file to extract metadata and time-series data."""
    with open(filepath, 'r') as file:
        lines = file.readlines()
    
    # Extract metadata
    well_name = lines[0].split(":")[1].strip()
    easting = float(lines[1].split(":")[1].strip())
    northing = float(lines[2].split(":")[1].strip())
    
    # Extract time-series data
    data = pd.read_csv(filepath, skiprows=3)  # Skip header lines
    data.columns = ['days', 'height', 'factor']
    
    return {
        'well_name': well_name,
        'easting': easting,
        'northing': northing,
        'data': data
    }

def locate_well_rotated(easting, northing, xorigin, yorigin, delr, delc, nrow, ncol, rotation_degrees):
    # Convert rotation angle to radians
    theta = np.radians(rotation_degrees)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    # Translate coordinates to the grid origin
    dx = easting - xorigin
    dy = northing - yorigin

    # Apply the rotation transformation
    x_grid = dx * cos_theta + dy * sin_theta
    y_grid = -dx * sin_theta + dy * cos_theta

    # Calculate row and column
    col = int(x_grid // delr)  # Assumes uniform cell widths
    row = int((nrow * delc - y_grid) // delc)  # Top-to-bottom grid

    # Check bounds
    if 0 <= row < nrow and 0 <= col < ncol:
        return row, col
    else:
        print('outside domain')
        return None  # Well is outside the model domain

def match_to_model_times(well, sim_times):
    """Match well observation times to nearest simulation times."""
    times = well['data']['days'].values  # Observation times
    heads = well['data']['height'].values  # Observed head values
    
    # Find nearest simulation time for each observation
    matched_data = []
    for obs_time, head in zip(times, heads):
        nearest_time_idx = (abs(sim_times - obs_time)).argmin()
        matched_time = sim_times[nearest_time_idx]
        matched_data.append((matched_time, head))
    
    return matched_data
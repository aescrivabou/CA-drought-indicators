# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 21:51:35 2024

@author: armen
"""

import time
import subprocess
import sys
from tqdm import tqdm

def execute_and_time(script_path):
    """
    Execute a Python script and measure its execution time
    
    Parameters
    ----------
    script_path : str
        The file path of the Python script to be executed
    """
    start_time = time.time()
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing the script: {e}")
        return
    end_time = time.time()
    execution_time_minutes = (end_time - start_time) / 60
    print(f"{script_path} execution time: {round(execution_time_minutes, 1)} minutes")


script_paths = [
    'pr_pet_obtain_regional_summaries.py',  # 3.1 prcp and et
    'pr_pet_map_indicators.py',             # 3.1 prcp and et
    'pr_and_et_indicators.py',              # 3.1 prcp and et
    'surface_water_drought_indicator.py',   # 3.3 surface water drought indicator
    'groundwater_drought.py',               # 3.4 Groundwater status
    'streamflow_indicator.py',              # 3.5 streamflow conditions
    'imports_indicator.py'                  # 3.6 imports indicator
]

for script_path in tqdm(script_paths, desc='Executing scripts'):
    execute_and_time(script_path)
    print(f'{script_path} complete')
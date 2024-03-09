# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 12:12:31 2024

@author: armen
"""
import os
import pandas as pd
import geopandas as gpd
import rasterio as rio
import xarray as xr
import numpy as np
import datetime
import calendar
from percentile_average_function import func_for_tperiod

import timeit

def measure_script_execution(script_path):
    # Read the script code
    with open(script_path, 'r') as script_file:
        script_code = script_file.read()

    # Define a function to execute the script
    def execute_script():
        exec(script_code)

    # Measure the execution time using timeit
    execution_time_minutes = timeit.timeit(execute_script, number=1) / 60  # Convert seconds to minutes

    print(f"Script execution time: {round(execution_time_minutes, 1)} minutes")


#%% 3.1
script_path = 'pr_pet_obtain_regional_summaries.py'
measure_script_execution(script_path)

script_path = 'pr_and_et_indicators.py'
measure_script_execution(script_path)
#%% 3.3 surface water drought indicator
script_path = 'surface_water_drought_indicator.py'
measure_script_execution(script_path)

#%% 3.4 Groundwater status
script_path = 'groundwater_drought.py'
measure_script_execution(script_path)

#%% 3.5 streamflow conditions
script_path = 'streamflow_indicator.py'
measure_script_execution(script_path)

#%% 3.6 imports indicator
script_path = 'imports_indicator.py'
measure_script_execution(script_path)

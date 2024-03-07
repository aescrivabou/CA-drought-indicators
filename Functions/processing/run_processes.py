# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 12:12:31 2024

@author: armen
"""


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



#%%
import pandas as pd
sflow_percentile = pd.read_csv ('../../Data/Processed/streamflow_indicator/streamflow_individual_gages_indicator.csv', index_col=0)
sflow_directory = r'../../Data\Downloaded/usgs/streamflow_daily_data.csv'
sflow_data = pd.read_csv(sflow_directory, index_col=0)
sflow_data = sflow_data.rename(columns={'datetime': 'date'})

#%%
def get_dates (df, df_new, date_column):
    df[date_column] = pd.to_datetime(df[date_column])
    df_new[date_column] = pd.to_datetime(df_new[date_column])
    start_date = df[date_column].min()
    end_date = df[date_column].max()
    new_start_date = df_new[date_column].min()
    new_end_date = df_new[date_column].max()
    print(f"Start Date: {start_date}\nEnd Date: {end_date}\nStart Date: {new_start_date}\nEnd Date: {new_end_date}")
    
get_dates(sflow_data, sflow_percentile, 'date')

#%%



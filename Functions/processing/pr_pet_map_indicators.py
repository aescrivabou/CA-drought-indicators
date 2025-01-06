# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 11:03:18 2024

@author: armen
"""
import pandas as pd
import geopandas as gpd
import xarray as xr
import numpy as np
from datetime import datetime
from percentile_average_function import func_for_tperiod
from tqdm import tqdm
import os

def get_region_percentile (hr = 'Sacramento River',analysis_period = '1Y',value_column = 'precipitation_amount', 
                           baseline_start_year = 1991, baseline_end_year = 2020, analysis_start_year = 1987, analysis_end_year = 2024,
                           input_directory = '../../Datasets/pr/', hr_directory = r"../../Datasets/HRs/i03_Hydrologic_Regions.shp", output_directory = '../../Outputs/all_regions_2yr_percentile/',
                           ):
    """
    Calculates the percentiles of each grid cell in a given hydrologic region over a base period.
    
    Parameters
    ----------
    hr : str, optional
        The name of the hydrologic region to analyze
    analysis_period : str
        It's the time window of the analysis for the percentiles or averages
    value_column : str, optional
        The name of the column in the dataset containing the values for which percentiles will be calculated
    baseline_start_year: int
        The start year of the baseline period for obtaining percentiles with a fixed period
    baseline_end_year: int
        The start year of the baseline period for obtaining percentiles with a fixed period
    analysis_start_year : int
        The start year of the analysis period
    analysis_end_year : int
        The end year of the analysis period
    input_directory : str, optional
        The directory containing the input dataset
    hr_directory : str, optional
        The directory containing the shapefile of hydrologic regions
    output_directory : str
        The directory where the output files will be saved
    
    Returns
    -------
    dataframe
        The dataframe contains the calculated percentiles for each time period and grid cell
    # The function also saves the calculated percentiles to the specified output directory in nc format
        
    """
    
    if value_column == 'precipitation_amount':
        file_start = 'pr_'
    if value_column == 'potential_evapotranspiration':
        file_start = 'pet_'
    
    hrs = gpd.read_file(hr_directory).to_crs("EPSG:4326")
    hrs = hrs[hrs['HR_NAME'] == hr]
    minx, miny, maxx, maxy = hrs.geometry.total_bounds    
    
    input_folder = input_directory
    variable_df = pd.DataFrame()
    for year_n in range(analysis_start_year, analysis_end_year+1): 
        filepath = input_folder + file_start + '%s' %(year_n) + '.nc'
        ds = xr.open_dataset(filepath)
        da = ds[value_column].sel(lon=slice(minx, maxx),lat=slice(maxy, miny))
        da_monthly =da.groupby('day.month').sum('day')
        da_monthly = da_monthly.rio.write_crs("EPSG:4326")
        da_clip = da_monthly.rio.clip(hrs.geometry)
        df = da_clip.to_dataframe().reset_index()
        df['year'] = year_n
        df['date'] = pd.to_datetime(dict(year=df.year, month=df.month, day=1))
        df['cell'] = df.lon.astype(str) + "_" + df.lat.astype(str)
        variable_df = pd.concat([variable_df,df]).reset_index(drop=True)
        print(year_n)
        
    
    unique_cells = np.unique(variable_df['cell'])
    
    percentile = pd.DataFrame()
    for i in tqdm(unique_cells):
        one_cell = variable_df.loc[variable_df.cell == i]
        if one_cell[value_column].isna().any()==True:
            pass
        
        else:
            one_cell_perc = func_for_tperiod(one_cell, 
                                date_column = 'date', value_column = value_column, 
                                input_timestep = 'M', analysis_period = analysis_period,
                                function = 'percentile', grouping_column='cell',
                                correcting_no_reporting = False, correcting_column = 'capacity',
                                baseline_start_year = baseline_start_year, baseline_end_year = baseline_end_year,
                                remove_zero = False)
    
            percentile = pd.concat([percentile, one_cell_perc])
        
    # os.makedirs(output_directory, exist_ok=True)
    # prec_df.to_csv(f"{output_directory}/{hr}_pr_data.csv")
    # percentile.to_csv(f"{output_directory}/{hr}_pr_percentile.csv")
    percentile.set_index(['lat','lon','date'], inplace=True)
    # df_xarray = percentile.to_xarray()
    # df_xarray.to_netcdf(f"{output_directory}/{hr}_"+file_start+"percentile.nc")
    
    return percentile

shape_path_filename = '../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp'
hrs = gpd.read_file(shape_path_filename).to_crs("EPSG:4326")
hr_regions = hrs['HR_NAME'].unique()
current_year = datetime.now().year

pr_prctl_hr_rgns = []
for hr in hr_regions:
    prctl_hr  = get_region_percentile(analysis_period = '1Y',hr = hr, baseline_start_year = 1991, baseline_end_year = 2020, analysis_start_year = 1987, analysis_end_year = current_year,
                                            input_directory = '../../Data/Downloaded/pr/', hr_directory = '../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp', 
                                            output_directory = '../../Data/Processed/pr_pet_gridded_indicators/',
                                            value_column = 'precipitation_amount')
    pr_prctl_hr_rgns.append (prctl_hr)

et_prctl_hr_rgns = []
for hr in hr_regions:
    prctl_hr  = get_region_percentile(analysis_period = '1Y',hr = hr, baseline_start_year = 1991, baseline_end_year = 2020, analysis_start_year = 1987, analysis_end_year = current_year,
                                            input_directory = '../../Data/Downloaded/pet/', hr_directory = '../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp', 
                                            output_directory = '../../Data/Processed/pr_pet_gridded_indicators/',
                                            value_column = 'potential_evapotranspiration')
    prctl_hr['percentile'] = 1 - prctl_hr['percentile']
    et_prctl_hr_rgns.append (prctl_hr)

os.makedirs('../../Data/Processed/pr_pet_gridded_indicators', exist_ok=True)

pr_prctl_allrgns = pd.concat(pr_prctl_hr_rgns)
pr_prctl_xarray = pr_prctl_allrgns.to_xarray()
pr_prctl_xarray.to_netcdf('../../Data/Processed/pr_pet_gridded_indicators/pr_percentile.nc')

pet_prctl_allrgns = pd.concat(et_prctl_hr_rgns)
pet_prctl_xarray = pet_prctl_allrgns.to_xarray()
pet_prctl_xarray.to_netcdf('../../Data/Processed/pr_pet_gridded_indicators/pet_percentile.nc')
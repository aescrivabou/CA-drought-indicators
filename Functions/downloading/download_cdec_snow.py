#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 15:52:46 2023

@author: alvar
"""

import pandas as pd
from tqdm import tqdm
import os
snotels = pd.read_csv('../../Data/Input_Data/cdec/snotels3.csv')

def download_snow_data(startdate='01-01-1991', enddate='12-31-2023', stations = snotels): 
    """Downloads raw snow data
    
    Parameters
    ----------
    startyear : integer
        The beginning of the date range (format: MM-DD-YYYY)
    endyear : integer
        The end of the date range (format: MM-DD-YYYY)
    stations = list 
        The list of snow station names to be downloaded
    
    Returns
    -------
    datafiles
        Selected indicators over the date range specified, organized
        by subfolder in the listed directory
    dataframe
        Dataframe of the indicator over the date range specified
    """
    
    sensor_num = 82
    dur_code = 'D'
    snotels = stations
    
    snow = pd.DataFrame()
    for stn_name in tqdm(snotels.station):
        url = f'https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={stn_name}&SensorNums={sensor_num}&dur_code={dur_code}&Start={startdate}&End={enddate}'
        datasnow01 = pd.read_csv(url, on_bad_lines='skip')
        snow = pd.concat([snow, datasnow01])
    
    snow['DATE TIME'] = pd.to_datetime(snow['DATE TIME'])
    
    # calculate April 1st 'normal' for each sensor
    snow['month'] = snow['DATE TIME'].dt.month
    snow['year'] = snow['DATE TIME'].dt.year
    snow['day'] = snow['DATE TIME'].dt.day
    
    snow['VALUE'] = pd.to_numeric(snow['VALUE'], errors='coerce')
    return snow

def snow_percentile(snow):
    """ Calculates regional monthly average percentiles of April 1st Snow Water Equivalent (SWE) 
        based on snow station daily data, using a baseline period from 1991 to 2020.
    
    Parameters
    ----------
    snow : dataFrame
        The dataFrame containing snow station data
    
    Returns
    -------
    dataframe
        Updated DataFrame (`snow`) with station ID information added
    dataframe
        DataFrame (`regional`) containing regional average percentiles for April 1st SWE
    """
    snow = snow.iloc[:,:12] # we cross out columns that are assosiated with snow regional percnetile calculation as it will be performed in this function
    snow_normal = snow.loc[(snow['month'] == 4) & (snow['day'] == 1)]
    snow_normal = snow_normal.dropna(subset=['VALUE'])
    snow_normal = snow_normal[(snow_normal["DATE TIME"] >= "1991-01-01") & (snow_normal["DATE TIME"] <= "2021-12-31")]
    
    snow_normal_ave = snow_normal.groupby(['STATION_ID']).mean(numeric_only=True).reset_index()
    snow_normal_ave = snow_normal_ave[['STATION_ID', 'VALUE']]
    snow_normal_ave = snow_normal_ave.rename(columns={'VALUE': 'normal'})
    merged = pd.merge(snow, snow_normal_ave, on='STATION_ID')
    
    # calculate a percentile for each daily SWC value
    merged['percent_normal'] = merged['VALUE']/merged['normal']
    
    # calculate monthly ave of the 'percentiles'
    all = pd.merge(merged, snotels, left_on='STATION_ID', right_on='station')
    basin = all.groupby(['Basin','year','month']).mean(numeric_only=True).reset_index()
    basin = basin[['Basin', 'year', 'month', 'percent_normal']]
    
    regions = snotels.groupby(['Basin', 'HR']).mean(numeric_only=True).reset_index()
    basin_HR = pd.merge(basin, regions, on='Basin')
    
    # multiply average percentile by Margulis' estimate for April 1st regional SWE (converted to AF)
    basin_HR['SWC'] = basin_HR['percent_normal']*basin_HR['aprilmean']*810714
    basin_HR = basin_HR[['Basin', 'HR', 'year', 'month', 'percent_normal', 'aprilmean', 'SWC']]
    
    # summarize by region
    regional = basin_HR.groupby(['HR','year','month']).sum().reset_index()
    regional['HR_NAME']=regional.HR
    regional = regional[['HR_NAME', 'year', 'month', 'SWC']]
    
    snow = pd.merge(snow, snotels, left_on='STATION_ID', right_on='station')
    
    return snow,regional
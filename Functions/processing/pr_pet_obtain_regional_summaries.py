#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 16:53:31 2023

@author: alvar
"""

import os
import pandas as pd
import geopandas as gpd
import rasterio as rio
import xarray as xr
import numpy as np
import datetime
import calendar

shape_path_filename = '../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp'
hrs = gpd.read_file(shape_path_filename).to_crs("EPSG:4326")
hrs.HR_NAME


centralcoast = "HR_NAME=='Central Coast'"
coloradoriver = "HR_NAME=='Colorado River'"
northcoast = "HR_NAME=='North Coast'"
northlahontan = "HR_NAME=='North Lahontan'"
sacramento = "HR_NAME=='Sacramento River'"
sanfrancisco = "HR_NAME=='San Francisco Bay'"
sanjoaquinriver = "HR_NAME=='San Joaquin River'"
southcoast = "HR_NAME=='South Coast'"
southlahontan = "HR_NAME=='South Lahontan'"
tularelake = "HR_NAME=='Tulare Lake'"

hr_series = [centralcoast, coloradoriver, northcoast, northlahontan, sacramento,
             sanfrancisco, sanjoaquinriver, southcoast, southlahontan, tularelake]
hr_long_series = ['Central Coast', 'Colorado River', 'North Coast', 'North Lahontan',
                  'Sacramento River', 'San Francisco Bay', 'San Joaquin River',
                  'South Coast', 'South Lahontan', 'Tulare Lake']
hr_code = ['CC', 'CR', 'NC', 'NL', 'SR', 'SF', 'SJ', 'SC', 'SL', 'TL']
                  

## function to summary regional indicators
# inputs: downloaded gridded indicator data and hydrologic region shapefile
# output: regional monthly indicators for pet, aet, precip, max temp, and mean temp

def obtainregionalsummary(input_folder = '../../Data/Downloaded/',
             region = centralcoast, 
             name = 'Central Coast', 
             indicators = ['pr', 'pet'],
             startyear = 2019, startmonth = 1,
             endyear = 2021, endmonth = 12,
             directory = '../../Data/Processed/',
             output_filename = 'processed_grided_indicators.csv'): 

    """Summarizing hydro-climatic data at a hydrologic region
    
    Parameters
    ----------
    region :
    name :
    indicators : list
        Potential hydroclimatic variables include:
            'aet' : actual evapotranspiration (source: TERRACLIMATE; format: netCDF)
            'pr' : precipitation (source: gridMET; format: netCDF)
            'pet' : estimated evapotranspiration (source: gridMET; format: netCDF)
            'tmmx' : temperature (maximum) (source: gridMET; format: netCDF)
            'tmean' : temperature (mean) (source: PRISM; format: bil)
    startyear : integer
        The beginning of the date range
    endyear : integer
        The end of the date range
    directory = str
        The path to the directory where the data will be downloaded
        
    
    Returns
    -------
    datafiles
        TBD
        
    """
    
    year = list(range(startyear, endyear))
    count = endyear - startyear
    
    # read hydrologic region shapefile
    shape_path_filename = '../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp'
    #shape_path_filename = r'W:/Projects/NIDIS/Data//HRs/Hydrologic_Regions.shp'
    
    # read hydrologic region
    hr = gpd.read_file(shape_path_filename).to_crs("EPSG:4326").query(region)
    minx, miny, maxx, maxy = hr.geometry.total_bounds    

    ### clip and summarize monthly indicators by hydrologic region

    allindicators = pd.DataFrame(columns=['date'])
    
    ## evapotranspiration (daily)
    
    if 'pet' in indicators:
    
        # this loop takes daily estimated evapotranspiration data from gridMET in mm and generates a monthly mean across the hydrologic region
        
        pet = pd.DataFrame(columns=['date', 'pet_value'])
        
        for i in range(count):
            filepath = input_folder +'pet/pet_' + '%s' %(year[i]) + '.nc'
            ds = xr.open_dataset(filepath)
            start = str(datetime.date(year[i], startmonth, 1))
            end = str(datetime.date(year[i], endmonth, calendar.monthrange(year[i],endmonth)[1]))
            date = pd.date_range(start, end)
            for m in date:
                t = '%s' %(m)
                da = ds["potential_evapotranspiration"].sel(day=t,lon=slice(minx, maxx),lat=slice(maxy, miny))
                da = da.rio.write_crs("EPSG:4326")
                da_clip = da.rio.clip(hr.geometry)
                mean = np.nanmean(da_clip.values)
                pet.loc['%s' %(m)] = ['%s' %(m), mean]
            ds.close()
        
        # summarize by month
        
        pet['date'] = pd.to_datetime(pet['date'])    
        pet['month'] = pet['date'].dt.month
        pet['year'] = pet['date'].dt.year
        pet['day'] = 1
        pet['date']= pd.to_datetime(pet[['year','month','day']])
        pet = pet.groupby(['year', 'month'])['pet_value'].sum().reset_index()
        pet['day'] = 1
        pet['date']= pd.to_datetime(pet[['year','month','day']])
        pet = pet.drop(['year','month','day'], axis=1)
        pet = pet[['date', 'pet_value']]
        
        allindicators = allindicators.merge(pet, how='outer', on='date')

    ##precipitaiton (daily)
    if 'pr' in indicators:
        
        precipitation = pd.DataFrame(columns=['date', 'pr_value'])
        
        for i in range(count):
            filepath = input_folder +'pr/pr_' + '%s' %(year[i]) + '.nc'
            ds = xr.open_dataset(filepath)
            start = str(datetime.date(year[i], startmonth, 1))
            end = str(datetime.date(year[i], endmonth, calendar.monthrange(year[i],endmonth)[1]))
            date = pd.date_range(start, end)
            for m in date:
                t = '%s' %(m)
                da = ds["precipitation_amount"].sel(day=t,lon=slice(minx, maxx),lat=slice(maxy, miny))
                da = da.rio.write_crs("EPSG:4326")
                da_clip = da.rio.clip(hr.geometry)
                mean = np.nanmean(da_clip.values)
                precipitation.loc['%s' %(m)] = ['%s' %(m), mean]
            ds.close()
    
        #summarize by month
        
        precipitation['date'] = pd.to_datetime(precipitation['date'])    
        precipitation['month'] = precipitation['date'].dt.month
        precipitation['year'] = precipitation['date'].dt.year
        precipitation = precipitation.groupby(['year', 'month'])['pr_value'].sum().reset_index()
        precipitation['day'] = 1
        precipitation['date']= pd.to_datetime(precipitation[['year','month','day']])
        precipitation = precipitation.drop(['year','month','day'], axis=1)
        
        allindicators = allindicators.merge(precipitation, how='outer', on='date')
        
        
    allindicators.to_csv(directory + output_filename)
        


for i in range(10):
    obtainregionalsummary(input_folder = '../../Data/Downloaded/',
             region = hr_series[i], 
             name = hr_long_series[i], 
             indicators = ['pr', 'pet'],
             startyear = 1990, startmonth = 1,
             endyear = 2023, endmonth = 12,
             directory = '../../Data/Processed/gridded/',
             output_filename = hr_code[i] + '_processed_grided_indicators_1990_2022.csv')

for i in range(10):
    obtainregionalsummary(input_folder = '../../Data/Downloaded/',
             region = hr_series[i], 
             name = hr_long_series[i], 
             indicators = ['pr', 'pet'],
             startyear = 2023, startmonth = 1,
             endyear = 2024, endmonth = 5,
             directory = '../../Data/Processed/gridded/',
             output_filename = hr_code[i] + '_processed_grided_indicators_2023.csv')

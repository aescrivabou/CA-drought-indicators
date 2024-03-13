#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 10:17:54 2023

@author: alvar
"""

## install packages

import pandas as pd
import os
from tqdm import tqdm
from datetime import datetime
from dateutil.relativedelta import relativedelta

## define downloading function
def download_reservoir_data(
             startdate = '1-1-1991',
             enddate = '12-31-2023',
             directory = '../NIDIS/Data/Processed/cdec/',
             stations = 'nan'): 

    """Downloads raw reservoir data
    
    Parameters
    ----------
    startyear : integer
        The beginning of the date range
    endyear : integer
        The end of the date range
    directory = str
        The path to the directory where the data will be downloaded
        
    
    Returns
    -------
    datafiles
        Selected indicators over the date range specified, organized
        by subfolder in the listed directory
        
    Note: The monthly data uses data for the last day of the month: we are updating this
    value as the first day of the following month to be consistent with the snow data
    """

       
    # import sensor list    
    reservoirstations = stations
    reservoircapacity = pd.read_csv('../../Data/Input_Data/cdec/reservoir_capacity.csv')
    
    # reservoirs
    reservoirstations = reservoirstations.rename(columns={'ID': 'station'})
    reservoirstations = reservoirstations.rename(columns={'Station_Name': 'name'})
    reservoirstations = reservoirstations[['station','name', 'Latitude','Longitude', 'River_Basin', 'HR_NAME']].reset_index(drop=True)
    
    reservoirs = pd.DataFrame()

    startdate = datetime.strptime(startdate, '%m-%d-%Y')
    startdate = startdate - relativedelta(months=1)
    startdate = startdate.strftime('%m-%d-%Y')
    enddate = datetime.strptime(enddate, '%m-%d-%Y')
    enddate = enddate - relativedelta(months=1)
    enddate = enddate.strftime('%m-%d-%Y')
    
    sensor_num = 15
    dur_code = 'M' #monthly
    reservoirs = pd.DataFrame()
    for stn_name in tqdm(reservoirstations.station):
        url = f'https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={stn_name}&SensorNums={sensor_num}&dur_code={dur_code}&Start={startdate}&End={enddate}'
        datares01 = pd.read_csv(url, on_bad_lines='skip')
        reservoirs = pd.concat([reservoirs, datares01])
    
    #Updating value of mothly data (last day of the month) as first day of the following month
    reservoirs['DATE TIME'] = pd.to_datetime(reservoirs['DATE TIME'])
    reservoirs['DATE TIME'] = reservoirs['DATE TIME'] + pd.DateOffset(months = 1)
    reservoirs['month'] = reservoirs['DATE TIME'].dt.month
    reservoirs['year'] = reservoirs['DATE TIME'].dt.year
    reservoirs.columns = map(str.lower, reservoirs.columns)
    reservoirs = reservoirs.rename(columns={'station_id': 'station'})
    reservoirs = reservoirs.merge(reservoirstations, on='station')
    reservoirs = reservoirs.merge(reservoircapacity, on = 'station' , how = 'outer')
    
    reservoirs['date'] = pd.to_datetime(dict(year=reservoirs.year, month=reservoirs.month, day=1))
    reservoirs['year'] = reservoirs['date'].dt.year
    #Subseting data for the actual year we want to start
    startdate = pd.to_datetime(startdate)
    startyear = startdate.year
    reservoirs = reservoirs.loc[reservoirs.year>startyear-1]
    reservoirs = reservoirs[['station', 'sensor_type', 'value', 'data_flag', 'units', 'date', 'month', 'year', 'name', 
                             'Latitude', 'Longitude', 'River_Basin', 'HR_NAME' , 'capacity']]
    reservoirs = reservoirs.dropna(subset=['sensor_type'])
    
    return reservoirs
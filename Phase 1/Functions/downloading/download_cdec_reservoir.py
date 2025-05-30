#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 10:17:54 2023

@author: alvar
"""

## install packages

from ulmo import cdec
import pandas as pd
import os


## define downloading function
def download_reservoir_data(
             startyear = 2019,
             endyear = 2021,
             directory = '../NIDIS/Data/Processed/cdec/'): 

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

    ## download reservoir data from cdec

    # create subfolder for downloaded files
    subfolder = "reservoir"
    path = os.path.join(directory, subfolder)
    os.mkdir(path)
       
    # import sensor list    
    reservoirstations = pd.read_csv('../../Data/Input_Data/cdec/reservoirstations_hrs.csv')
    reservoircapacity = pd.read_csv('../../Data/Input_Data/cdec/reservoir_capacity.csv')
    
    # reservoirs
    reservoirstations = reservoirstations.rename(columns={'ID': 'station'})
    reservoirstations = reservoirstations.rename(columns={'Station_Name': 'name'})
    reservoirstations = reservoirstations[['station','name', 'Latitude','Longitude', 'River_Basin', 'HR_NAME']].reset_index(drop=True)
    
    reservoirs = pd.DataFrame()
    startdate = str(startyear-1) + '-01-01' #We use the previous year because data is for the last day of the month (and we update this as the first day of the following month)
    enddate = str(endyear) + '-12-31'
    
    for station in reservoirstations.station:
        try:
            datares01 = cdec.historical.get_data(station_ids=[station],sensor_ids=[15],resolutions=['monthly'], start = startdate , end = enddate)
            if bool(datares01[list(datares01.keys())[0]]) == True:
                datares01 = datares01[list(datares01.keys())[0]]['RESERVOIR STORAGE'].reset_index()
                reservoirs = pd.concat([reservoirs, datares01])
        except ValueError:
            print('Error with station :' + station)
    del datares01
    
    reservoirs = reservoirs.rename(columns={'station_id': 'station'})
    #Updating value of mothly data (last day of the month) as first day of the following month
    reservoirs['DATE TIME'] = reservoirs['DATE TIME'] + pd.DateOffset(months = 1)
    reservoirs['month'] = reservoirs['DATE TIME'].dt.month
    reservoirs['year'] = reservoirs['DATE TIME'].dt.year
    reservoirs = reservoirs.merge(reservoirstations, on='station')
    reservoirs = reservoirs.merge(reservoircapacity, on = 'station' , how = 'outer')
    reservoirs['date'] = pd.to_datetime(dict(year=reservoirs.year, month=reservoirs.month, day=1))
    reservoirs['year'] = reservoirs['date'].dt.year
    #Subseting data for the actual year we want to start
    reservoirs = reservoirs.loc[reservoirs.year>startyear-1]
    reservoirs = reservoirs[['station', 'sensor_type', 'value', 'data_flag', 'units', 'date', 'month', 'year', 'name', 
                             'Latitude', 'Longitude', 'River_Basin', 'HR_NAME' , 'capacity']]
    reservoirs = reservoirs.dropna(subset=['sensor_type'])
    reservoirs.to_csv(directory + 'reservoir/reservoirs.csv')


# Download all data
download_reservoir_data(
             startyear = 1991,
             endyear = 2023,
             directory = '../../Data/Downloaded/cdec/')
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 02:35:57 2024

@author: armen
"""
import pandas as pd
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import os

# get functions for downloading data
from download_cdec_snow import download_snow_data, snow_percentile
from download_usgs_streamflow import download_streamflow_data
from download_pr_pet_gridded_data import download_pr_pet_data
from download_cdec_reservoir import download_reservoir_data

def download_data(parameter_type, startdate, enddate, directory, stations):
    """
    Download data for a specified parameter type from a data source over a given date range.
    
    Parameters
    ----------
    parameter_type : str
        The type of parameter to download data.
    startdate : str
        The start date of the data download period. Format: 'YYYY-MM-DD'
    enddate : str
        The end date of the data download period. Format: 'YYYY-MM-DD'
    directory : str
        The directory path where the downloaded data will be saved
    stations : list 
        The list of streamflow station names to be downloaded
    
    Returns
    -------
    dataFrame
        A dataframe containing the downloaded data.
    """
    
    if parameter_type == 'snow':
        data = download_snow_data(startdate, enddate, stations)
    elif parameter_type == 'streamflow':
        data = download_streamflow_data(startdate, enddate, stations)
    elif parameter_type == 'reservoir':
        data = download_reservoir_data(startdate, enddate, directory, stations)
    elif parameter_type == 'prcp and et':
        data = download_pr_pet_data(indicators = ['pr', 'pet'], startyear = startdate, endyear = enddate, directory = '../../Data/Downloaded/')
    else:
        raise ValueError("Invalid parameter_type. Supported values are 'snow' or 'streamflow'.")
    return data

def load_or_download_data(parameter_type, startdate, enddate, directory, stations):
    """Load data from a local directory if available; otherwise, download it for a specified parameter type over a given date range.
    
    Parameters
    ----------
    parameter_type : str
        The type of parameter to download data.
    startdate : str
        The start date of the data download period. Format: 'YYYY-MM-DD'
    enddate : str
        The end date of the data download period. Format: 'YYYY-MM-DD'
    directory : str
        The directory path where the downloaded data will be saved
    stations : list 
        The list of streamflow station names to be downloaded
    
    Returns
    -------
    dataFrame
        A dataframe containing the loaded or downloaded data.
    """
    file_path = directory
    if parameter_type != 'prcp and et':
        if os.path.exists(file_path) :
            df = pd.read_csv(file_path,index_col=0, low_memory=False)
            print(f'{parameter_type} data exists')
        else:
            os.makedirs(os.path.dirname(directory), exist_ok=True)
            df = download_data(parameter_type, startdate, enddate, directory, stations)
        return df
    if parameter_type == 'prcp and et':
        if os.path.exists(file_path):
            files_in_directory = os.listdir(directory)
        if os.path.exists(file_path) == False:
            os.makedirs(directory, exist_ok=True)
            download_data(parameter_type, startdate, enddate, directory, stations)
    else:
        pass

def add_new_data (df, parameter_type, date_column, id_column, directory, stations): 
    """Add new data to an existing dataframe for a specified parameter

    Parameters
    ----------
    df : dataframe
        The existing dataframe to which new data will be added.
    parameter_type : str
        The type of parameter to download data
    date_column : str
        The column label of the datetime column
    id_column : str
        The column label containing the IDs or names of the stations in the exeisting dataframe
    directory : str
        The directory path where the downloaded data will be saved
    stations = list 
        A list containing names or IDs of the stations we want to download
    
    Returns
    -------
    dataFrame
        The updated dataframe with the newly added data.
    """
    if parameter_type != 'prcp and et':
        startdate = df[date_column].max()
        startdate = pd.to_datetime(startdate).tz_localize(None) + relativedelta(days=1) # An additional day is included to ensure that the new data start on the day following
        enddate = pd.to_datetime(date.today())
        if startdate >= enddate:
            print('Data is up to date')
            return df
        else:
            if parameter_type in ('snow', 'streamflow'):
                startdate = startdate.strftime("%Y-%m-%d")
                enddate = enddate.strftime("%Y-%m-%d")
            
            if parameter_type == 'reservoir':
                startdate = startdate.strftime("%m-%d-%Y")
                enddate = enddate.strftime("%m-%d-%Y")
            
            df_append = download_data(parameter_type, startdate, enddate, directory, stations)
            df_new = pd.concat([df, df_append])
            df_new[date_column] = pd.to_datetime(df_new[date_column], format='mixed')
            df_new = df_new.sort_values(by=[id_column, date_column], ascending=[True, True])
            df_new[date_column] = df_new[date_column].astype(str)
            print(f'dates downloaded: {startdate}, {enddate}')
            return df_new

    if parameter_type == 'prcp and et':
        files_in_directory = os.listdir(pr_pet_directory)
        latest_file = max(files_in_directory)
        latest_year = int(latest_file.split('_')[1].split('.')[0])
        current_year = datetime.now().year
        for year in range(latest_year, current_year + 1):
            download_data(parameter_type, latest_year, current_year, directory, stations)

def get_dates (df, df_new, date_column):
    df[date_column] = pd.to_datetime(df[date_column])
    df_new[date_column] = pd.to_datetime(df_new[date_column])
    start_date = df[date_column].min()
    end_date = df[date_column].max()
    new_end_date = df_new[date_column].max()
    print(f"Start Date: {start_date}\nEnd Date: {end_date}\nNew End Date: {new_end_date}")
    

# snow data is daily
snotels = pd.read_csv('../../Data/Input_Data/cdec/snotels3.csv')
# snotels = snotels.iloc[:5,:]

snow_directory = '../../Data/Downloaded/cdec/snow/snow_stations.csv'
snow_regional_directory = '../../Data/Downloaded/cdec/snow/SnowRegional.csv'
snow_data = load_or_download_data(parameter_type='snow', directory=snow_directory , 
                                  startdate='01-01-1991', enddate='12-31-2023', stations=snotels) #month-day-year

snow_data_new = add_new_data (df = snow_data, parameter_type = 'snow', date_column = 'DATE TIME', id_column = 'STATION_ID', directory= snow_directory, stations = snotels)
get_dates (snow_data, snow_data_new, 'DATE TIME')

snow_data_new, snow_regional = snow_percentile(snow_data_new)


snow_data_new.to_csv(snow_directory)
snow_regional.to_csv(snow_regional_directory)


# sf data is daily
strmflw_stations = pd.read_csv("../../Data/Input_Data/usgs/sg_usgs_hr.csv")
# strmflw_stations = strmflw_stations.iloc[:5,:]

strmflw_directory = r'..\..\Data\Downloaded/usgs/streamflow_daily_data.csv'
strmflw_data = load_or_download_data(parameter_type='streamflow', directory=strmflw_directory, 
                                  startdate='1991-01-01' , enddate='2023-12-31', stations=strmflw_stations) #year-month-day

strmflw_data_new = add_new_data (df = strmflw_data, parameter_type = 'streamflow', date_column = 'datetime', id_column = 'site_no', directory= strmflw_directory, stations = strmflw_stations)
get_dates (strmflw_data, strmflw_data_new, 'datetime')
strmflw_data_new.to_csv(strmflw_directory)


# reservoir data is monthly
rsvr_stations= pd.read_csv('../../Data/Input_Data/cdec/reservoirstations_hrs.csv')
# rsvr_stations = rsvr_stations.iloc[:5,:]
rsvr_directory = '../../Data/Downloaded/cdec/reservoir/reservoirs.csv'
rsvr_data = load_or_download_data(parameter_type='reservoir', directory=rsvr_directory , 
                                  startdate='1-1-1991', enddate='12-1-2023', stations=rsvr_stations) #month-day-year #necesseray to keep the days 1 

rsvr_data_new = add_new_data (df = rsvr_data, parameter_type = 'reservoir', 
                                     date_column = 'date', id_column = 'station', directory= rsvr_directory, stations = rsvr_stations)
get_dates (rsvr_data, rsvr_data_new, 'date')
rsvr_data_new.to_csv(rsvr_directory)


# pet and pr is monthly
pr_pet_directory = '../../Data/Downloaded/pr'
pr_pet_data = load_or_download_data(parameter_type='prcp and et', directory = pr_pet_directory, 
                                  startdate=1987 , enddate=2024, stations='nan')
pr_pet_data_new = add_new_data (df = pr_pet_data, parameter_type = 'prcp and et', 
                                date_column = 'nan', id_column = 'nan', directory= pr_pet_directory, stations = 'nan')

# GW data is periodic
gw_script_path = 'download_gw.py'
gw_script_content = open(gw_script_path).read()
exec(gw_script_content)
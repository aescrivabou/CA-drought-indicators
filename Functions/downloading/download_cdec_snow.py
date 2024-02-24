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

def download_snow_data(startdate, enddate, stations = snotels): 
    # import snotel list     

    sensor_num = 82
    dur_code = 'D'
    snotels = stations
    
    snow = pd.DataFrame()
    for stn_name in tqdm(snotels.station):
        url = f'https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={stn_name}&SensorNums={sensor_num}&dur_code={dur_code}&Start={startdate}&End={enddate}'
        datasnow01 = pd.read_csv(url, on_bad_lines='skip')
        snow = pd.concat([snow, datasnow01])
    
    # snow = pd.read_csv("C:/Users/armen/Desktop/snow.csv")
    snow['DATE TIME'] = pd.to_datetime(snow['DATE TIME'])
    
    # calculate April 1st 'normal' for each sensor
    snow['month'] = snow['DATE TIME'].dt.month
    snow['year'] = snow['DATE TIME'].dt.year
    snow['day'] = snow['DATE TIME'].dt.day
    
    snow['VALUE'] = pd.to_numeric(snow['VALUE'], errors='coerce')
    return snow

def snow_percentile(snow):
    
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

#%%
# sample of how snow data is downloaded and subsequently appending the new data to the pre-existing dataset
# import pandas as pd
# from datetime import datetime
# import os
# from dateutil.relativedelta import relativedelta
# from download_data import download_data, load_or_download_data

# snotels = pd.read_csv('../../Data/Input_Data/cdec/snotels3.csv')
# snotels = snotels.iloc[:5,:]
# snow_directory = '../../Data/Downloaded/cdec/snow/snow_stations.csv'

# snow_data = load_or_download_data(directory=snow_directory, parameter_type='snow', startdate='1-2-2022', enddate='12-31-2023', stations=snotels)


# def append_new_data (df, parameter_type, date_column, id_column, directory, stations): 
#     last_row = df.iloc[-1]
#     startdate = last_row[date_column]
#     startdate = pd.to_datetime(startdate) + relativedelta(days=1) # 1 day is added because i want the new data to start the day after
#     enddate = startdate  + relativedelta(months=1) - relativedelta(days=1) # 1 day is subtracted because i want the new data to be end of the month
#     startdate = startdate.strftime("%Y-%m-%d")
#     enddate = enddate.strftime("%Y-%m-%d")
    
#     df_append = download_data(parameter_type, startdate = startdate, enddate = enddate, stations = stations)
#     df_new = pd.concat([df, df_append])
#     df_new = df_new.sort_values(by=[id_column, date_column], ascending=[True, True])
#     # snow_data_new = snow_percentile(snow_data_new)
    
#     return df_new

# snow_data_new = append_new_data (snow_data, parameter_type = 'snow', date_column = 'DATE TIME', id_column = 'STATION_ID', directory= snow_directory, stations = snotels)

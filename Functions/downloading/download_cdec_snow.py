#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 15:52:46 2023

@author: alvar
"""

import pandas as pd
from tqdm import tqdm
import os

# import snotel list     
snotels = pd.read_csv('../../Data/Input_Data/cdec/snotels3.csv')


startdate = '1-1-1991'
enddate = '6-1-2023'
sensor_num = 82
dur_code = 'D'

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

snow['VALUE'] = pd.to_numeric(snow['VALUE'], errors='coerce') # this line is added because the values are objects not floats in 
snow_normal = snow.loc[(snow['month'] == 4) & (snow['day'] == 1)]
snow_normal = snow_normal.dropna(subset=['VALUE'])
snow_normal_ave = snow_normal.groupby(['STATION_ID']).mean(numeric_only=True).reset_index() #numeric_only=True was added. In previous it used to worked, however in latest versions of pandas numeric_only=False.
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


os.makedirs('../../Data/Downloaded/cdec/snow/', exist_ok=True)
snow.to_csv(os.path.join('../../Data/Downloaded/cdec/snow/snow_stations.csv'))
regional.to_csv(os.path.join('../../Data/Downloaded/cdec/snow/SnowRegional.csv'))
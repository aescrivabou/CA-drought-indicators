#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 15:52:46 2023

@author: alvar
"""

## snow data

from ulmo import cdec
import pandas as pd



# import snotel list     
snotels = pd.read_csv('../../Data/Input_Data/cdec/snotels3.csv')
df = snotels

# pull daily snow water content data for defined period
startdate = '1-1-1991'
enddate = '6-1-2023'

snow = pd.DataFrame()


for station in snotels.station:
    try:
        datasnow01 = cdec.historical.get_data(station_ids=[station],sensor_ids=[82],resolutions=['daily'], start = startdate , end = enddate)
        if bool(datasnow01[list(datasnow01.keys())[0]]) == True:
            datasnow01 = datasnow01[list(datasnow01.keys())[0]]['SNOW'].reset_index()
            snow = pd.concat([snow, datasnow01])
    except ValueError:
        print('Error with station :' + station)
del datasnow01


# calculate April 1st 'normal' for each sensor
snow['month'] = snow['DATE TIME'].dt.month
snow['year'] = snow['DATE TIME'].dt.year
snow['day'] = snow['DATE TIME'].dt.day

snow_normal = snow.loc[(snow['month'] == 4) & (snow['day'] == 1)]
snow_normal = snow_normal.dropna(subset=['value'])
snow_normal_ave = snow_normal.groupby(['station_id']).mean().reset_index()
snow_normal_ave = snow_normal_ave[['station_id', 'value']]
snow_normal_ave = snow_normal_ave.rename(columns={'value': 'normal'})
merged = pd.merge(snow, snow_normal_ave, on='station_id')

# calculate a percentile for each daily SWC value
merged['percent_normal'] = merged['value']/merged['normal']

# calculate monthly ave of the 'percentiles'
all = pd.merge(merged, snotels, left_on='station_id', right_on='station')
basin = all.groupby(['Basin','year','month']).mean().reset_index()
basin = basin[['Basin', 'year', 'month', 'percent_normal']]

regions = snotels.groupby(['Basin', 'HR']).mean().reset_index()
basin_HR = pd.merge(basin, regions, on='Basin')

# multiply average percentile by Margulis' estimate for April 1st regional SWE (converted to AF)
basin_HR['SWC'] = basin_HR['percent_normal']*basin_HR['aprilmean']*810714
basin_HR = basin_HR[['Basin', 'HR', 'year', 'month', 'percent_normal', 'aprilmean', 'SWC']]

# summarize by region
regional = basin_HR.groupby(['HR','year','month']).sum().reset_index()
regional['HR_NAME']=regional.HR
regional = regional[['HR_NAME', 'year', 'month', 'SWC']]

snow = pd.merge(snow, snotels, left_on='station_id', right_on='station')
snow.to_csv('../../Data/Downloaded/cdec/snow/snow_stations.csv')
regional.to_csv('../../Data/Downloaded/cdec/snow/SnowRegional.csv')


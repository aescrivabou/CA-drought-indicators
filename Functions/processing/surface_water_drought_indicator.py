#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  8 22:49:49 2023

@author: alvar
"""

import pandas as pd
import os
from percentile_average_function import func_for_tperiod


#reading reservoir and snow data
reservoir_data = pd.read_csv('../../Data/Downloaded/cdec/reservoir/reservoirs.csv')
snow_data = pd.read_csv('../../Data/Downloaded/cdec/snow/SnowRegional.csv')
reservoir_data['value'] = pd.to_numeric(reservoir_data['value'], errors='coerce')

#converting date to datetime
reservoir_data['date'] = pd.to_datetime(reservoir_data.date)
snow_data['date'] = pd.to_datetime(dict(year=snow_data.year, month=snow_data.month, day=1))

#First we obtain the percentiles for individual reservoirs
res_ind = func_for_tperiod(reservoir_data, date_column = 'date', value_column = 'value',
                          input_timestep = 'M', analysis_period = '1M',function = 'percentile',
                          grouping_column='station', correcting_no_reporting = False,
                          baseline_start_year = 1991, baseline_end_year = 2020)

#Then we obtain the aggregated values at the hydrologic region scale for storage
res_hr = func_for_tperiod(reservoir_data, date_column = 'date', value_column = 'value',
                          input_timestep = 'M', analysis_period = '1M',function = 'percentile',
                          grouping_column='HR_NAME', correcting_no_reporting = True,
                          correcting_column = 'capacity',baseline_start_year = 1991, 
                          baseline_end_year = 2020)

#Correcting date after obtaining aggregated data per hydrologic region
res_hr['month'] = res_hr['date'].dt.month
res_hr['year'] = res_hr['date'].dt.year
res_hr['date'] = pd.to_datetime(dict(year=res_hr.year, month=res_hr.month, day=1))
#Remove negative numbers to snow data
snow_data.loc[snow_data.SWC<0,'SWC']=0

#snow_percentile
snow_perc = func_for_tperiod(snow_data, date_column = 'date', value_column = 'SWC',
                          input_timestep = 'M', analysis_period = '1M',function = 'percentile',
                          grouping_column='HR_NAME', correcting_no_reporting = False,
                          baseline_start_year = 1991, baseline_end_year = 2020)
snow_perc['snow_pctl'] = snow_perc['percentile']
snow_perc = snow_perc[['date', 'HR_NAME', 'SWC', 'snow_pctl']]

#Obtaining total storage as sum of reservoir storage and snow
total_storage = res_hr.merge(snow_data, on=['date', 'HR_NAME'], how = 'outer')
total_storage['total_storage'] = total_storage.corrected_value + total_storage.SWC
total_storage.loc[total_storage.SWC.isna()==True,'total_storage'] = total_storage.corrected_value
total_storage.loc[(total_storage.date<'1999-12-01') & (total_storage.HR_NAME=='South Coast'),'total_storage'] = total_storage.value

total_storage['res_percentile'] = total_storage['percentile']
total_storage['reservoir_storage'] = total_storage['value']
total_storage_for_calculation = total_storage[['date','reservoir_storage', 'res_percentile','total_storage', 'HR_NAME']]


tot_stor_perc = func_for_tperiod(total_storage_for_calculation, date_column = 'date', value_column = 'total_storage',
                          input_timestep = 'M', analysis_period = '1M',function = 'percentile',
                          grouping_column='HR_NAME', correcting_no_reporting = False,
                          baseline_start_year = 1991, baseline_end_year = 2020)

tot_stor_perc = tot_stor_perc.merge(snow_perc, on = ['date', 'HR_NAME'], how = 'outer')
tot_stor_perc.loc[tot_stor_perc.snow_pctl.isna() == True, 'snow_pctl'] = 0.5

tot_stor_perc = tot_stor_perc.rename(columns={'percentile': 'SWDI'})

os.makedirs('../../Data/Processed/surface_water_drougth_indicator/', exist_ok=True)
res_ind.to_csv('../../Data/Processed/surface_water_drougth_indicator/individual_reservoir_percentiles.csv')
tot_stor_perc.to_csv('../../Data/Processed/surface_water_drougth_indicator/total_storage_percentiles.csv')
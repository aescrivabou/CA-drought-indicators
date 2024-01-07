#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 18:20:45 2023

@author: alvar
"""

import pandas as pd
from percentile_average_function import func_for_tperiod
import numpy as np

sflow_data = pd.read_csv('../../Data/Downloaded/usgs/streamflow_daily_data.csv',index_col=0)
sflow_data['date'] = pd.to_datetime(sflow_data.datetime)
sflow_data = sflow_data[['date', '00060_Mean', '00060_Mean_cd', 'site_no','lat', 'lon', 'HR_NAME']]
sflow_data = sflow_data.rename(columns={"00060_Mean": 'flow'})
sflow_data.loc[sflow_data.flow<0] = np.nan



sflow_percentile = func_for_tperiod(df=sflow_data, date_column = 'date', value_column = 'flow',
                     input_timestep = '1D', analysis_period = '3M',
                     function = 'percentile', grouping_column= 'site_no',
                     correcting_no_reporting = False,
                     baseline_start_year = 1991, baseline_end_year = 2020,
                     remove_zero=False)


site_hr = sflow_data[['site_no', 'HR_NAME']]
site_hr = site_hr.drop_duplicates()

sflow_percentile = sflow_percentile.merge(site_hr, on='site_no')
sflow_pctl_regional = sflow_percentile.groupby(['HR_NAME','date']).median().reset_index()

sflow_pctl_regional = sflow_pctl_regional.rename(columns={'percentile':'median_percentile'})

sflow_pctl_regional_corr = func_for_tperiod(df=sflow_pctl_regional, date_column = 'date', value_column = 'median_percentile',
                     input_timestep = '1M', analysis_period = '1M',
                     function = 'percentile', grouping_column= 'HR_NAME',
                     correcting_no_reporting = False,
                     baseline_start_year = 1991, baseline_end_year = 2020,
                     remove_zero=False)

sflow_percentile.to_csv('../../Data/Processed/streamflow_indicator/streamflow_individual_gages_indicator.csv')
sflow_pctl_regional_corr.to_csv('../../Data/Processed/streamflow_indicator/streamflow_regional_indicator.csv')
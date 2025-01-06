#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 18:20:45 2023

@author: alvar
"""
"""
Description:
    This script calculates streamflow indicator for each hydrologic region (HR).
        The script performs the following tasks:
        1. Calculates monthly streamflow percentile values from daily for each gage using a 3 month analysis period.
        2. Computes the median streamflow values for each HR.
        3. Apply correction to streamflow percentile values by calculating percentile with a 1 month analysis period. 
        (reason we apply this correction is because medium values will hover around half values and there will be no zeroes or ones (extremes) 
         and thus by calclating percentile of this median percentiles we are strechting out the median values to be between 0 and 1) 
        3. Applies a correction to the streamflow percentile values by calculating percentiles using a 1-month analysis period.
        (This correction is applied because median values tend to cluster around the middle of the range, resulting in fewer 
         extreme values (near 0 or 1) - By recalculating percentiles of these median values, we distribute the median values
         more evenly between 0 and 1)
"""
import pandas as pd
from percentile_average_function import func_for_tperiod
import numpy as np
import os

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

os.makedirs('../../Data/Processed/streamflow_indicator/', exist_ok=True)
sflow_percentile.to_csv('../../Data/Processed/streamflow_indicator/streamflow_individual_gages_indicator.csv')
sflow_pctl_regional_corr.to_csv('../../Data/Processed/streamflow_indicator/streamflow_regional_indicator.csv')
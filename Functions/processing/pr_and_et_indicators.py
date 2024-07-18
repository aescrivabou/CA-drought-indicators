#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 16:24:46 2023

@author: alvar
"""

import pandas as pd
from percentile_average_function import func_for_tperiod


hr_ids = ['CC', 'CR', 'NC', 'NL', 'SC', 'SF', 'SJ', 'SL', 'SR', 'TL']
hrs = ['Central Coast', 'Colorado River', 'North Coast', 'North Lahontan',
       'South Coast', 'San Francisco Bay', 'San Joaquin River', 'South Lahontan',
       'Sacramento River', 'Tulare Lake']

all_hr_data = pd.DataFrame()
for hrid in hr_ids:
    data_hr = pd.read_csv('../../Data/Processed/gridded/' + hrid +'_processed_grided_indicators_1990_2022.csv')
    data_hr2 = pd.read_csv('../../Data/Processed/gridded/' + hrid + '_processed_grided_indicators_2023.csv')
    data_hr = pd.concat([data_hr, data_hr2]).reset_index(drop=True)
    data_hr['hrid']=hrid
    del data_hr2
    all_hr_data = pd.concat([all_hr_data,data_hr]).reset_index(drop=True)

all_hr_data['date'] = pd.to_datetime(all_hr_data.date)

hr_df = pd.DataFrame()
hr_df['hrid'] = hr_ids
hr_df['HR_NAME'] = hrs

all_hr_data = all_hr_data.merge(hr_df, on='hrid')

all_hr_data['pet_minus_pr'] = all_hr_data.pet_value - all_hr_data.pr_value
all_hr_data.loc[all_hr_data['pet_minus_pr']<0,'pet_minus_pr'] = 0

pr_percentile = func_for_tperiod(df=all_hr_data, date_column = 'date', value_column = 'pr_value',
                     input_timestep = 'M', analysis_period = '1Y',
                     function = 'percentile', grouping_column= 'HR_NAME',
                     correcting_no_reporting = False,
                     baseline_start_year = 1991, baseline_end_year = 2020,
                     remove_zero=False)

et_percentile = func_for_tperiod(df=all_hr_data, date_column = 'date', value_column = 'pet_value',
                     input_timestep = 'M', analysis_period = '1Y',
                     function = 'percentile', grouping_column= 'HR_NAME',
                     correcting_no_reporting = False,
                     baseline_start_year = 1991, baseline_end_year = 2020,
                     remove_zero=False)

et_minus_pr_percentile = func_for_tperiod(df=all_hr_data, date_column = 'date', value_column = 'pet_minus_pr',
                     input_timestep = 'M', analysis_period = '1Y',
                     function = 'percentile', grouping_column= 'HR_NAME',
                     correcting_no_reporting = False,
                     baseline_start_year = 1991, baseline_end_year = 2020,
                     remove_zero=False)
pr_percentile['pr_value_in'] = pr_percentile['pr_value']/25.4
et_percentile['pet_value_in'] = et_percentile['pet_value']/25.4

# Adjust percentile to indicate drought conditions: higher values typically mean higher ET, but for drought indication, we use 1 - percentile to highlight severity as lower values now indicate drier conditions.
et_percentile['percentile'] = 1 - et_percentile.percentile
et_minus_pr_percentile['percentile'] = 1 - et_minus_pr_percentile.percentile

pr_percentile.to_csv('../../Data/Processed/pr_pet_hr_indicators/pr_percentile.csv')
et_percentile.to_csv('../../Data/Processed/pr_pet_hr_indicators/pet_percentile.csv')
et_minus_pr_percentile.to_csv('../../Data/Processed/pr_pet_hr_indicators/pet_minus_pr_percentile.csv')
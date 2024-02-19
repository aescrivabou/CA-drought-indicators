#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 15:58:06 2023

@author: alvar
"""
# I AM ADDING THIS (trial 2145s6sdv)
#changes here as well
import numpy as np
import pandas as pd
import dataretrieval.nwis as nwis


## inport streamgage site list

stations = pd.read_csv("../../Data/Input_Data/usgs/sg_usgs_hr.csv")
stations.update(stations[['site']].astype(str))
sites = list(stations['site'])


streamflow_all = pd.DataFrame()

for n in np.arange(0, 2400, 1):
    print(n)
    try:
        streamflow_data = nwis.get_record(sites=sites[n:n+1], service='dv',  start='1991-01-01', end='2023-04-01', parameterCd = "00060")
    except:
        streamflow_data = pd.DataFrame()
        pass
    streamflow_all = pd.concat([streamflow_all, streamflow_data])
    
streamflow_all = streamflow_all.reset_index()
streamflow_all = streamflow_all.merge(stations, left_on='site_no', right_on='site')
streamflow_all.to_csv('../../Data/Downloaded/usgs/streamflow_daily_data.csv')

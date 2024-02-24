#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 15:58:06 2023

@author: alvar
"""

import numpy as np
import pandas as pd
import dataretrieval.nwis as nwis
import os
from tqdm import tqdm, trange

def download_streamflow_data(
             startdate = '1-1-1991',
             enddate = '12-1-2023',
             stations = 'nan',
             ): 

    ## import streamgage site list
    
    # stations = pd.read_csv("../../Data/Input_Data/usgs/sg_usgs_hr.csv")
    stations.update(stations[['site']].astype(str))
    sites = list(stations['site'])
    
    
    streamflow_all = pd.DataFrame()
    
    for n in trange(len(stations)):
    # for n in np.arange(0, len(stations), 1):
        # print(n)
        try:
            streamflow_data = nwis.get_record(sites=sites[n:n+1], service='dv',  start=startdate, end=enddate, parameterCd = "00060")
        except:
            streamflow_data = pd.DataFrame()
            pass
        streamflow_all = pd.concat([streamflow_all, streamflow_data])
        
    streamflow_all = streamflow_all.reset_index()
    streamflow_all = streamflow_all.merge(stations, left_on='site_no', right_on='site')
    
    return streamflow_all
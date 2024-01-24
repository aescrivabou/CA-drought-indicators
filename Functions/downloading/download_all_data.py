# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 02:35:57 2024

@author: armen
"""

import pandas as pd
import numpy as np
import dataretrieval.nwis as nwis
from datetime import datetime

#%%
#streamflow
stations = pd.read_csv("../../Data/Input_Data/usgs/sg_usgs_hr.csv")
stations.update(stations[['site']].astype(str))
sites = list(stations['site'])

streamflow_all = pd.read_csv('../../Data/Downloaded/usgs/streamflow_daily_data.csv', index_col=0)

#%%
startdate = streamflow_all.loc[streamflow_all.index[-1],'datetime']
enddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

streamflow_all_add = pd.DataFrame()
for n in np.arange(0, len(stations), 1):
    print(n)
    try:
        streamflow_all_add = nwis.get_record(sites=sites[n:n+1], service='dv',  start=startdate, end=enddate, parameterCd = "00060")
    except:
        streamflow_all_add = pd.DataFrame()
        pass

streamflow_all_new = pd.concat([streamflow_all, streamflow_all_add])

#%%
script_path = 'data_download_usgs.py'

# Execute the script using exec
with open(script_path, 'r') as script_file:
    script_code = script_file.read()
    exec(script_code)
#%%
#snow and resevoir

#%%
#pet and pr
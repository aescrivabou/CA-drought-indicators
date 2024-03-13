# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 22:04:53 2024

@author: armen
"""

import pandas as pd
import os
directory_path = '../../Data/Downloaded/groundwater/periodic_gwl_bulkdatadownload'
os.makedirs(directory_path, exist_ok=True)

gw_stations = pd.read_csv('https://data.cnra.ca.gov/dataset/dd9b15f5-6d08-4d8c-bace-37dc761a9c08/resource/af157380-fb42-4abf-b72a-6f9f98868077/download/stations.csv')
gw_stations.to_csv('../../Data/Downloaded/groundwater/periodic_gwl_bulkdatadownload/stations.csv')

gw_measurments = pd.read_csv('https://data.cnra.ca.gov/dataset/dd9b15f5-6d08-4d8c-bace-37dc761a9c08/resource/bfa9f262-24a1-45bd-8dc8-138bc8107266/download/measurements.csv')
gw_measurments.to_csv('../../Data/Downloaded/groundwater/periodic_gwl_bulkdatadownload/measurements.csv')

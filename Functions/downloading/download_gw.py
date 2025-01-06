# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 22:04:53 2024

@author: armen
"""

import pandas as pd
import requests
from io import StringIO

url="https://data.cnra.ca.gov/dataset/dd9b15f5-6d08-4d8c-bace-37dc761a9c08/resource/af157380-fb42-4abf-b72a-6f9f98868077/download/stations.csv"
headers = {'User-Agent': 'Mozilla/5.0'}
req = requests.get(url, headers=headers)
data = StringIO(req.text)
gw_stations = pd.read_csv(data, low_memory=False)
gw_stations.to_csv('../../Data/Downloaded/groundwater/periodic_gwl_bulkdatadownload/stations.csv')

url='https://data.cnra.ca.gov/dataset/dd9b15f5-6d08-4d8c-bace-37dc761a9c08/resource/bfa9f262-24a1-45bd-8dc8-138bc8107266/download/measurements.csv'
headers = {'User-Agent': 'Mozilla/5.0'}
req = requests.get(url, headers=headers)
data = StringIO(req.text)
gw_measurments = pd.read_csv(data, low_memory=False)
gw_measurments.to_csv('../../Data/Downloaded/groundwater/periodic_gwl_bulkdatadownload/measurements.csv')
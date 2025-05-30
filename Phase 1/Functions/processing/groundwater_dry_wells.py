#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  2 14:30:48 2023

@author: alvar
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 16:15:06 2023

@author: alvar
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
import scipy
from scipy.stats import shapiro, norm, skewnorm, gamma
from sklearn.cluster import KMeans
import geopandas as gpd
import mapclassify
import contextily as ctx
from datetime import date, timedelta
import seaborn as sns
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates
import math
from PIL import Image
from matplotlib import rcParams
from cycler import cycler
import rasterio
from rasterio.plot import show
import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging
from rasterio.transform import Affine



#Data from: https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements
gwdata = pd.read_csv('../../Data/Input_Data/groundwater/periodic_gwl_bulkdatadownload/measurements.csv')
stations = pd.read_csv('../../Data/Input_Data/groundwater/periodic_gwl_bulkdatadownload/stations.csv')

#Adding hydrologic region to gwdata
hr = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp')
hr = hr.to_crs('epsg:4326')
stations_gdf = gpd.GeoDataFrame(stations, geometry=gpd.points_from_xy(stations.longitude, stations.latitude))
stations_gdf = stations_gdf.set_crs('epsg:4326')
stations_gdf = gpd.sjoin(stations_gdf, hr)

#Mergind data with stations
gwdata = gwdata.merge(stations_gdf, on='site_code')
gwdata = gwdata.loc[gwdata.gse_gwe<300]


#Well completion report data. Data from: https://data.cnra.ca.gov/dataset/well-completion-reports
datawells = pd.read_csv('../../Data/Input_Data/groundwater/oswcr_bulkdatadownload/OSWCR.csv' , encoding = 'latin=1')
welltype = pd.read_csv('../../Data/Input_Data/groundwater/wellusetype.csv')
datawells = datawells.merge(welltype, on = 'PLANNEDUSEFORMERUSE')

domesticwells = datawells.loc[datawells.supplytype == 'domestic']
domesticwells['DECIMALLONGITUDE'] = pd.to_numeric(domesticwells['DECIMALLONGITUDE'],errors='coerce')
domesticwells['DECIMALLATITUDE'] = pd.to_numeric(domesticwells['DECIMALLATITUDE'],errors='coerce')
domesticwells['TOTALCOMPLETEDDEPTH'] = pd.to_numeric(domesticwells['TOTALCOMPLETEDDEPTH'],errors='coerce')
domesticwells['date'] = pd.to_datetime(domesticwells['DATEWORKENDED'],errors='coerce')
domesticwells['year'] = domesticwells['date'].dt.year


domesticwells_gdf = gpd.GeoDataFrame(domesticwells, geometry=gpd.points_from_xy(domesticwells.DECIMALLONGITUDE, domesticwells.DECIMALLATITUDE))
domesticwells_gdf = domesticwells_gdf.set_crs('epsg:4326')
domesticwells_gdf = gpd.sjoin(domesticwells_gdf, hr, op = 'within')


#Adding temporal data to stations
gwdata['msmt_date'] = pd.to_datetime(gwdata['msmt_date'])
gwdata['year']=gwdata['msmt_date'].dt.year
gwdata['semester']=1
gwdata.loc[gwdata['msmt_date'].dt.month>6,'semester']=2



#Krigging from gw elevation data for HR and year
def gw_krig(gwdata = gwdata, hr_name = 'San Joaquin River', yr_n = 2022, res = 0.01):
    df = gwdata.loc[(gwdata.HR_NAME==hr_name)]
    df = df.loc[(df.year==yr_n) & (df.semester==2)]
    
    hr_shp = hr.loc[hr.HR_NAME==hr_name]
    #min_xhr, min_yhr, max_xhr, max_yhr = hr_shp.total_bounds
    
    gwelev_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    gwelev_gdf.crs = hr_shp.crs
    min_xpt, min_ypt, max_xpt, max_ypt = gwelev_gdf.total_bounds
    
    # Horizontal and vertical cell counts should be the same
    res = 0.01
    XX_pk_krig = np.arange(min_xpt, max_xpt+res, res)
    YY_pk_krig = np.arange(min_ypt, max_ypt+res, res)
    
    data_elevations = df[['longitude','latitude','gse_gwe']].reset_index(drop=True)
    data_elevations = data_elevations.loc[data_elevations.gse_gwe>0].to_numpy()
    
    # Generate ordinary kriging object
    OK = OrdinaryKriging(
        data_elevations[:, 0],
        data_elevations[:, 1],
        data_elevations[:, 2],
        variogram_model = "exponential",
        verbose = False,
        enable_plotting = False,
    )
    
    try:
        Z_pk_krig, sigma_squared_p_krig = OK.execute("grid", XX_pk_krig, YY_pk_krig)
    except:
        Z_pk_krig = np.nan
    return Z_pk_krig

raster_df = gw_krig()

def obtain_cell_value(raster=raster_df , res=0.01, x_coord = -118, y_coord=36, min_xpt =-120, min_ypt=36, max_xpt=-118, max_ypt=40):
    
    min_lat = min_ypt - (res/2)
    
    min_lon = min_xpt - (res/2)
    
    cell_y = math.floor((y_coord - min_lat)/res)
    cell_x = math.floor((x_coord - min_lon)/res)
    
    try:
        return raster[cell_y,cell_x]
    except:
        return np.nan
    
def wells_at_risk(gwdata = gwdata, hr_name = 'San Joaquin River', yr_n = 2022, res = 0.01, well_df=domesticwells_gdf, raster=raster_df):
    
    df = gwdata.loc[(gwdata.HR_NAME==hr_name)]
    df = df.loc[(df.year==yr_n) & (df.semester==2)]   
    hr_shp = hr.loc[hr.HR_NAME==hr_name]
    gwelev_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    gwelev_gdf.crs = hr_shp.crs
    min_xpt, min_ypt, max_xpt, max_ypt = gwelev_gdf.total_bounds
    
    sel_wells = well_df
    sel_wells = sel_wells.loc[sel_wells.HR_NAME == hr_name]

    sel_wells = sel_wells.dropna(subset=['TOTALCOMPLETEDDEPTH'])
    
    sel_wells = sel_wells.loc[sel_wells.year<yr_n] #only the wells that were already completed
    
    sel_wells['gw_level'] = sel_wells.apply(lambda row : obtain_cell_value(raster,res,row['DECIMALLONGITUDE'],row['DECIMALLATITUDE'],min_xpt, min_ypt, max_xpt, max_ypt), axis = 1)
    
    sel_wells['failed'] = 0
    sel_wells.loc[sel_wells.gw_level>sel_wells.TOTALCOMPLETEDDEPTH,'failed']=1
    sel_wells['atrisk'] = 0
    sel_wells.loc[sel_wells.gw_level > sel_wells.TOTALCOMPLETEDDEPTH - 30,'atrisk']=1
    
    return sel_wells

#San Joaquin River wells
sjr_wells_hist = []
for yr in np.arange(1991,2023):
    print(yr)
    raster_df = gw_krig(hr_name = 'San Joaquin River', yr_n = yr)
    sjr_wells_hist.append(wells_at_risk(hr_name = 'San Joaquin River', yr_n = yr))
    
    
#San Joaquin River wells
tulare_wells_hist = []
for yr in np.arange(1991,2023):
    print(yr)
    raster_df = gw_krig(hr_name = 'Tulare Lake', yr_n = yr)
    tulare_wells_hist.append(wells_at_risk(hr_name = 'Tulare Lake', yr_n = yr))


counter = 0
a = pd.DataFrame()
b = pd.DataFrame()
total_at_risk_sjr = []
for yr in np.arange(1991,2023):
    a = sjr_wells_hist[counter][['WCRNUMBER','atrisk']].reset_index(drop=True)
    total_risk_sjr = total_at_risk_sjr.append(a.atrisk.sum())
    a = a.rename(columns={'atrisk':'atrisk_'+str(yr)})
    if counter == 0:
        b = a
    if counter>0:
        b = b.merge(a, on =  'WCRNUMBER', how='outer')
    counter = counter+1
    
counter = 0
a = pd.DataFrame()
b = pd.DataFrame()
total_at_risk_tul = []
for yr in np.arange(1991,2023):
    a = tulare_wells_hist[counter][['WCRNUMBER','atrisk']].reset_index(drop=True)
    total_risk_tul = total_at_risk_tul.append(a.atrisk.sum())
    a = a.rename(columns={'atrisk':'atrisk_'+str(yr)})
    if counter == 0:
        b = a
    if counter>0:
        b = b.merge(a, on =  'WCRNUMBER', how='outer')
    counter = counter+1




#Function to export krigged data
#Based on https://pygis.io/docs/e_interpolation.html
def export_kde_raster(Z, res, min_x, max_x, min_y, max_y, proj, filename):
    '''Export and save a kernel density raster.'''

    # Get resolution
    xres = res#(max_x - min_x) / len(XX)
    yres = res#(max_y - min_y) / len(YY)

    # Set transform
    transform = Affine.translation(min_x - xres / 2, min_y - yres / 2) * Affine.scale(xres, yres)

    # Export array as raster
    with rasterio.open(
            filename,
            mode = "w",
            driver = "GTiff",
            height = Z.shape[0],
            width = Z.shape[1],
            count = 1,
            dtype = Z.dtype,
            crs = proj,
            transform = transform,
    ) as new_dataset:
            new_dataset.write(Z, 1)



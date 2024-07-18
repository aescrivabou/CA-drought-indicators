# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 11:09:05 2023

@author: spenc
"""

###  Develop surface water dashboard

#  Import packages
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from datetime import datetime
import math
from PIL import Image
import contextily as ctx
import os
import xarray as xr
from pykrige.ok import OrdinaryKriging
directory_path = '../../Data/Visuals/dashboards'
os.makedirs(directory_path, exist_ok=True)

#  Import real data and indicator visualization function
from dashboard_auxiliar_functions import vis_data_indicator, dial, color_function_df, convert_input_date_format

#  Define general parameters for matplotlib formatting
ppic_coltext = '#333333'
ppic_colgrid = '#898989'
ppic_colors = ['#e98426','#649ea5','#0d828a','#776972','#004a80','#3e7aa8','#b44b27','#905a78','#d2aa1d','#73a57a','#4fb3ce']

#  Define US drought monitor color scheme
dm_colors_dial = [(1,1,1,1), (189/255,190/255,192/255,1), (255/255,255/255,0,1), (252/255,211/255,127/255,1), (255/255,170/255,0,1), (230/255,0,0,1), (115/255,0,0,1), (57/255,57/255,57/255,1)]

#  Define function for surface water dashboard visualizations
def vis_sw_dashboard(hr='San Joaquin River', date='2001-04', hydrograph_length=10):
    
    """This function generates the surface water dashboard
    
    Parameters
    ----------
    
    hr : str
        Hydrologic region name: 'Central Coast', 'Colorado River', 'North Coast',
        'North Lahontan', 'Sacramento River', 'San Francisco Bay', 'San Joaquin River',
        'South Coast', 'South Lahontan', 'Tulare Lake'
    date : str
        The date for which the dashboard is presented. Format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY'
    hydrograph_length : integer
        Years of data presented in the hydrographs
        
    Returns
    -------
    figure
        the dashboard for surface water availability (including the SWDI)
    """
    
    df = pd.read_csv('../../Data/Processed/surface_water_drougth_indicator/total_storage_percentiles.csv')
    df_rsv = pd.read_csv('../../Data/Processed/surface_water_drougth_indicator/individual_reservoir_percentiles.csv')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3857')
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    #  Convert dataframe date to datetime type
    df.date = pd.to_datetime(df.date, format='%Y-%m-%d')
       
    #  Modify HR regions shapefile to properly facilitate plotting
    hr_shapes = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    
    #  Subset only for hydrologic region of interest
    df = df[df.HR_NAME==hr]
    
    #  Modify individual reservoirs data to properly facilitate plotting
    df_rsv.date = pd.to_datetime(df_rsv.date, format='%Y-%m-%d')
    df_rsv = df_rsv[df_rsv.date==date]
    df_rsv = df_rsv[(~df_rsv.Longitude.isna()) & (~df_rsv.Latitude.isna())]
    df_rsv = gpd.GeoDataFrame(df_rsv, geometry=gpd.points_from_xy(df_rsv.Longitude, df_rsv.Latitude)).set_crs('epsg:4326').to_crs('epsg:3857')
    df_rsv = gpd.clip(df_rsv, hr_shapes)
    df_rsv['capacity_scaled'] = df_rsv.capacity/7000
    # df_rsv['color_pctl'] = color_function_df(df_rsv, 'corrected_percentile')
    df_rsv['color_pctl'] = color_function_df(df_rsv, 'percentile')

    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure()
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of reservoir status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    hr_shapes.plot(ax=ax1, edgecolor='green', color='darkseagreen', alpha=0.7)
    df_rsv.plot(ax=ax1, markersize=df_rsv.capacity_scaled, color = df_rsv.color_pctl, edgecolor = 'grey', alpha = 0.75)
    ctx.add_basemap(ax=ax1, attribution_size=1)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Current reservoir conditions', fontsize = 9, fontweight = 'bold')

    
    #  Second create the drought monitor dial
    arrow_index = 100*df.SWDI[(df.date==date) & (df.HR_NAME==hr)].iloc[0]
    fig0, axs = plt.subplots()
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax2 = fig.add_subplot(grid[0:3, 3:7])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax2.imshow(im)
    ax2.grid(False)
    ax2.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax2.set_title('Regional surface water drought indicator\n(reservoir storage plus snowpack)', fontsize = 9, fontweight = 'bold')

    
    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=df, date=date, hr=hr, data=['reservoir_storage', 'SWC'], ind=None, hydrograph_length=10, plot_title = 'Evolution of water stored in reservoirs and snowpack')
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=df, date=date, hr=hr, data=['reservoir_storage', 'SWC'], ind='SWDI', hydrograph_length=10, plot_title = 'Evolution of the surface water drought indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    
    plt.savefig('../../Data/Visuals/dashboards/sw_dashboard.pdf')
    
#  Define function for imports
def vis_imports_dashboard(date='2001-04', hydrograph_length = 10):
    
    """This function generates the water dashboard for Delta imports
    
    Parameters
    ----------
    date : str
        The specific date of interest for the plot. Format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY'
    hydrograph_length : integer
        Years of data presented in the hydrographs
        
    Returns
    -------
    figure
        the dashboard for exports from the Delta (including the SWDI)
    """
    
    
    df = pd.read_csv('../../Data/Processed/imports/total_storage_percentiles.csv')
    df_rsv = pd.read_csv('../../Data/Processed/imports/individual_reservoir_percentiles.csv')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3857')
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    #  Convert dataframe date to datetime type
    df.date = pd.to_datetime(df.date, format='mixed')
    
    #  Modify HR regions shapefile to properly facilitate plotting
    hr_shapes1 = hr_shapes[(hr_shapes.HR_NAME)=='Sacramento River']
    hr_shapes2 = hr_shapes[(hr_shapes.HR_NAME)=='San Joaquin River']
    hr_shapes = pd.concat([hr_shapes1,hr_shapes2])
    
    #  Modify individual reservoirs data to properly facilitate plotting
    df_rsv.date = pd.to_datetime(df_rsv.date, format='%Y-%m-%d')
    df_rsv = df_rsv[df_rsv.date==date]
    df_rsv = df_rsv[(~df_rsv.Longitude.isna()) & (~df_rsv.Latitude.isna())]
    df_rsv = gpd.GeoDataFrame(df_rsv, geometry=gpd.points_from_xy(df_rsv.Longitude, df_rsv.Latitude)).set_crs('epsg:4326').to_crs('epsg:3857')
    df_rsv = gpd.clip(df_rsv, hr_shapes)
    df_rsv['capacity_scaled'] = df_rsv.capacity/7000
    df_rsv['color_pctl'] = color_function_df(df_rsv, 'corrected_percentile')
    
    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure()
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of reservoir status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    hr_shapes.plot(ax=ax1, edgecolor='green', color='darkseagreen', alpha=0.7)
    df_rsv.plot(ax=ax1, markersize=df_rsv.capacity_scaled, color = df_rsv.color_pctl, edgecolor = 'grey', alpha = 0.75)
    ctx.add_basemap(ax=ax1, attribution_size=0)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Current reservoir conditions', fontsize = 9, fontweight = 'bold')

    #  Second create the drought monitor dial
    arrow_index = 100*df.SWDI[(df.date==date)].iloc[0]
    fig0, axs = plt.subplots()
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax2 = fig.add_subplot(grid[0:3, 3:7])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax2.imshow(im)
    ax2.grid(False)
    ax2.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax2.set_title('Delta surface water drought indicator\n(reservoir storage plus snowpack)', fontsize = 9, fontweight = 'bold')

    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=df, date=date, data=['reservoir_storage', 'SWC'], ind=None, hydrograph_length=10, plot_title = 'Evolution of water stored in reservoirs and snowpack')
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=df, date=date, data=['reservoir_storage', 'SWC'], ind='SWDI', hydrograph_length=10, plot_title = 'Evolution of the surface water drought indicator')
    
    #  Add figure title
    plt.suptitle("Delta exporting basins\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    
    plt.savefig('../../Data/Visuals/dashboards/imports_dashboard.pdf')


#  Define function for surface water dashboard visualizations
def vis_gw_dashboard(hr='San Joaquin River', date='2010-03', hydrograph_length=10):
    
    """This function generates the groundwater dashboard
    
    Parameters
    ----------
    
    hr : str
        Hydrologic region name: 'Central Coast', 'Colorado River', 'North Coast',
        'North Lahontan', 'Sacramento River', 'San Francisco Bay', 'San Joaquin River',
        'South Coast', 'South Lahontan', 'Tulare Lake'
    date : str
        The date for which the dashboard is presented. Format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY' 
        (Works only for M = 3 (March) or 9 (September))
    hydrograph_length : integer
        Years of data presented in the hydrographs
        
    Returns
    -------
    figure
        the dashboard for groundwater availability
    """
    
    
    df = pd.read_csv('../../Data/Processed/groundwater/state_wells_regional_analysis.csv')
    df_wells = pd.read_csv('../../Data/Processed/groundwater/state_wells_individual_analysis.csv')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:4326')
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    #  Convert dataframe date to datetime type
    df.date = pd.to_datetime(df.date, format='%Y-%m-%d')
       
    #  Modify HR regions shapefile to properly facilitate plotting
    hr_shapes = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    minx, miny, maxx, maxy = hr_shapes.total_bounds
    
    #  Subset only for hydrologic region of interest
    df = df[df.HR_NAME==hr]
    
    #  Modify individual reservoirs data to properly facilitate plotting
    df_wells.date = pd.to_datetime(df_wells.date, format='%Y-%m-%d')
    df_wells = df_wells[df_wells.date==date]
    df_wells = df_wells[(~df_wells.longitude.isna()) & (~df_wells.latitude.isna())]
    df_wells = gpd.GeoDataFrame(df_wells, geometry=gpd.points_from_xy(df_wells.longitude, df_wells.latitude)).set_crs('epsg:4326')
    df_wells = gpd.clip(df_wells, hr_shapes)
    df_wells['color_pctl'] = color_function_df(df_wells, 'pctl_cumgwchange')
    df_wells = df_wells.dropna(subset=['pctl_cumgwchange'])
    
    # Perform Ordinary Kriging
    coordinates = df_wells[['latitude', 'longitude']].values
    gw_change = df_wells['pctl_cumgwchange'].values
    grid_lon = np.linspace(minx, maxx, 100)
    grid_lat = np.linspace(miny, maxy, 100)
    ok = OrdinaryKriging(coordinates[:, 1], coordinates[:, 0], gw_change, variogram_model='exponential')
    z, ss = ok.execute('grid', grid_lon, grid_lat)
    ds = xr.Dataset(
        {"elevation": (("latitude", "longitude"), z),},
        coords={
            "latitude": grid_lat,
            "longitude": grid_lon,})
    ds = ds.rio.write_crs("EPSG:4326")
    ds_clip = ds.rio.clip(hr_shapes.geometry)

    #create a buffer zone around the wells for krigging
    ds_clip = ds_clip.rio.reproject("EPSG:3857")
    df_wells = df_wells.to_crs('epsg:3857')
    hr_shapes = hr_shapes.to_crs('epsg:3857')
    buffer_distance_meters = 10 * 1609.34
    df_wells_buffered = df_wells.copy()
    df_wells_buffered['geometry'] = df_wells_buffered.geometry.buffer(buffer_distance_meters)
    ds_clip_buffered = ds_clip.rio.clip(df_wells_buffered.geometry)
    ds_clip = ds_clip_buffered.rio.reproject("EPSG:4326")
    ds_clip = ds_clip.rename_vars({'x': 'latitude', 'y': 'longitude'})
    df_wells = df_wells.to_crs('epsg:4326')
    hr_shapes = hr_shapes.to_crs('epsg:4326')

    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure()
    grid = plt.GridSpec(nrows=11, ncols=6, hspace=1.0, wspace=1.0)

    #  First create the map of groundwater status
    ax1 = fig.add_subplot(grid[0:6, 0:3])
    colors = [(230/255,0,0,1), (255/255,170/255,0,1), (252/255,211/255,127/255,1), (255/255,255/255,0,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1)]
    custom_cmap = ListedColormap(colors)
    hr_shapes.plot(ax=ax1, edgecolor='green', facecolor='none', alpha=1)
    ctx.add_basemap(ax=ax1, crs='EPSG:4326', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    img = ax1.contourf(ds_clip.latitude, ds_clip.longitude, ds_clip.elevation, cmap=custom_cmap, levels=[0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 1.0], alpha=0.7)
    df_wells.plot(ax=ax1, markersize=2.5, color=df_wells.color_pctl, edgecolor=None, alpha=1)
    # cbar = plt.colorbar(img, ax=ax1, orientation='horizontal')
    cbar = plt.colorbar(img, ax=ax1, orientation='horizontal', ticks=[0, 0.1, 0.2, 0.3, 0.5, 1.0])

    bbox_ax = ax1.get_position()
    cbar.ax.tick_params(labelsize=8)
    cbar.ax.set_position([bbox_ax.x0, bbox_ax.y1 - 0.32, bbox_ax.width, 0.02])
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Groundwater elevation\nindicator for individual wells', fontsize = 9, fontweight = 'bold')

    
    #  Second create the drought monitor dial for indicator "pctl_cumgwchange_corr"
    arrow_index = 100*df.pctl_cumgwchange_corr[(df.date==date) & (df.HR_NAME==hr)].iloc[0]
    fig0, axs = plt.subplots()  #  Add figure for indicator semicircle
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax2 = fig.add_subplot(grid[0:3, 3:6])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax2.imshow(im)
    ax2.grid(False)
    ax2.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax2.set_title('Regional groundwater elevation indicator', fontsize = 9, fontweight = 'bold')
    
    #  Third create the drought monitor dial for indicator "pctl_cumgwchange_corr"
    arrow_index = 100*df.pctl_gwchange_corr[(df.date==date) & (df.HR_NAME==hr)].iloc[0]
    fig0, axs = plt.subplots()  #  Add figure for indicator semicircle
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax3 = fig.add_subplot(grid[3:6, 3:6])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax3.imshow(im)
    ax3.grid(False)
    ax3.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax3.set_title('Regional pumping intesity indicator', fontsize = 9, fontweight = 'bold')
    
    # #  Fourth create the real data plot
    ax4 = fig.add_subplot(grid[6:8, 0:])    
    vis_data_indicator(ax=ax4, df=df, date=date, hr=hr, data=None, ind='pctl_cumgwchange_corr', hydrograph_length=10, plot_title = 'Evolution of the groundwater elevation indicator')
    
    #  Fifth create the indicator plot
    ax5 = fig.add_subplot(grid[9:11, 0:])
    vis_data_indicator(ax=ax5, df=df, date=date, hr=hr, data=None, ind='pctl_gwchange_corr', hydrograph_length=10, plot_title = 'Evolution of the groundwater pumping intensity indicator')
    
    #  Add figure title
    plt.suptitle(hr+ " - " + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)

    plt.savefig('../../Data/Visuals/dashboards/gw_dashboard.pdf')


#  Define function for surface water dashboard visualizations
def vis_streamflow_dashboard(hr='San Joaquin River', date='2011-11', hydrograph_length=10):
    
    """This function generates the streamflow dashboard
    
    Parameters
    ----------
    
    hr : str
        Hydrologic region name: 'Central Coast', 'Colorado River', 'North Coast',
        'North Lahontan', 'Sacramento River', 'San Francisco Bay', 'San Joaquin River',
        'South Coast', 'South Lahontan', 'Tulare Lake'
    date : str
        The date for which the dashboard is presented. Format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY'
    hydrograph_length : integer
        Years of data presented in the hydrographs
        
    Returns
    -------
    figure
        the dashboard for streamflow availability
    """
    
    
    df = pd.read_csv('../../Data/Processed/streamflow_indicator/streamflow_regional_indicator.csv')
    df_gages = pd.read_csv('../../Data/Processed/streamflow_indicator/streamflow_individual_gages_indicator.csv')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3857')
    rivers_shape = gpd.read_file('../../Data/Input_Data/Major_Rivers/NHD_Major_Rivers.shp').to_crs('epsg:3857')
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')


    #  Create function for properly converting datetime with timezones removed
    df.date = df.date.str[:10]
    df_gages.date = df_gages.date.str[:10]
    
    def df_field_to_datetime(df, df_date_column='date'):
        df['date'] = pd.to_datetime(df[df_date_column])
        df = df.set_index('date')
        try:
            df = df.tz_convert(tz='UTC')
        except:
            pass
        df = df.reset_index(drop=False)
        return df
    
    df = df_field_to_datetime(df)
    df_gages = df_field_to_datetime(df_gages)

    
    #  Modify HR regions shapefile to properly facilitate plotting
    hr_shapes = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    
    #  Subset only for hydrologic region of interest
    df = df[df.HR_NAME==hr]
    
    #  Modify individual gages data to properly facilitate plotting
    df_gages = df_gages[df_gages.date==date]
    df_gages = df_gages[(~df_gages.lon.isna()) & (~df_gages.lat.isna())]
    df_gages = gpd.GeoDataFrame(df_gages, geometry=gpd.points_from_xy(df_gages.lon, df_gages.lat)).set_crs('epsg:4326').to_crs('epsg:3857')
    df_gages = gpd.clip(df_gages, hr_shapes)
    df_gages['color_pctl'] = color_function_df(df_gages, 'percentile')
    
    #Modify rivers
    rivers_shape = gpd.clip(rivers_shape, hr_shapes)

    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure()
    grid = plt.GridSpec(nrows=4, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of streamflow status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    hr_shapes.plot(ax=ax1, edgecolor='green', color='darkseagreen', alpha=0.7, zorder=1)
    rivers_shape.plot(ax=ax1,color='cornflowerblue', alpha = 0.75, zorder=2)
    df_gages.plot(ax=ax1, markersize=25, color=df_gages.color_pctl, edgecolor='Grey', alpha=0.8, zorder=3)
    ctx.add_basemap(ax=ax1, attribution_size=0)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Current streamflow conditions', fontsize = 9, fontweight = 'bold')

    #  Second create the drought monitor dial for indicator "percentile"
    arrow_index = 100*df.percentile[(df.date==date) & (df.HR_NAME==hr)].iloc[0]
    fig0, axs = plt.subplots()  #  Add figure for indicator semicircle
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax2 = fig.add_subplot(grid[0:3, 3:7])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax2.imshow(im)
    ax2.grid(False)
    ax2.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax2.set_title('Streamflow indicator', fontsize = 9, fontweight = 'bold')

    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=df, date=date, hr=hr, data=None, ind='percentile', hydrograph_length=10, plot_title = 'Evolution of the regional streamflow indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    
    plt.savefig('../../Data/Visuals/dashboards/streamflow_dashboard.pdf')

def vis_pr_dashboard(hr='San Joaquin River', date='2001-04', hydrograph_length=10):
    
    """This function generates the precipitation dashboard
    
    Parameters
    ----------
    
    hr : str
        Hydrologic region name: 'Central Coast', 'Colorado River', 'North Coast',
        'North Lahontan', 'Sacramento River', 'San Francisco Bay', 'San Joaquin River',
        'South Coast', 'South Lahontan', 'Tulare Lake'
    The date for which the dashboard is presented. Format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY'
    hydrograph_length : integer
        Years of data presented in the hydrographs
        
    Returns
    -------
    figure
        the dashboard for precipitation availability
    """
    
    df = pd.read_csv('../../Data/Processed/pr_pet_hr_indicators/pr_percentile.csv')
    ds_pr = xr.open_dataset(r'../../Data/Processed/pr_pet_gridded_indicators/pr_percentile.nc')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:4326')
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    #  Convert dataframe date to datetime type
    df.date = pd.to_datetime(df.date, format='%Y-%m-%d')
       
    #  Modify HR regions shapefile to properly facilitate plotting
    hr_shapes = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    
    #  Subset only for hydrologic region of interest
    df = df[df.HR_NAME==hr]
    
    #  Modify precipitation percentile data to properly facilitate plotting
    ds_pr = ds_pr.rio.write_crs("EPSG:4326") # clipping is  working for epsg:4326 and not for 3857
    ds_pr = ds_pr.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
    ds_pr_prc_clip = ds_pr.rio.clip(hr_shapes.geometry)
    ds_pr_prc_clip = ds_pr_prc_clip.transpose('date', 'lat', 'lon')
    # Extract relevant variables for pr percentile data
    lon = ds_pr_prc_clip.lon.values
    lat = ds_pr_prc_clip.lat.values
    dates = ds_pr_prc_clip.date.values
    variable_to_plot = ds_pr_prc_clip.percentile.values
    dates = ds_pr_prc_clip['date']
    dates_df = dates.to_dataframe()
    dates_df.drop(columns=['date','spatial_ref'],inplace=True)
    dates_df.reset_index(inplace=True)
    time_index = dates_df.index[dates_df['date'] == date.strftime('%Y-%m-%d')].tolist()[0]
    variable_2d = variable_to_plot[time_index,:, :]
        
    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure()
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of precipitation status and add precipitation percentile
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    colors = [(230/255,0,0,1), (255/255,170/255,0,1), (252/255,211/255,127/255,1), (255/255,255/255,0,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1)]
    custom_cmap = ListedColormap(colors)
    hr_shapes.plot(ax=ax1, edgecolor='green', facecolor='none', alpha=1)
    ctx.add_basemap(ax=ax1, crs='EPSG:4326', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    img = ax1.contourf(lon, lat, variable_2d, cmap=custom_cmap, levels=[0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 1.0], alpha=0.7)
    cbar = plt.colorbar(img, ax=ax1, orientation='horizontal', ticks=[0, 0.1, 0.2, 0.3, 0.5, 1.0])
    bbox_ax = ax1.get_position()
    cbar.ax.tick_params(labelsize=8)
    cbar.ax.set_position([bbox_ax.x0, bbox_ax.y1 - 0.22, bbox_ax.width, 0.02])
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    ax1.set_title('Current precipitation condition', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial
    arrow_index = 100*df.percentile[(df.date==date) & (df.HR_NAME==hr)].iloc[0]
    fig0, axs = plt.subplots()
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax2 = fig.add_subplot(grid[0:3, 3:7])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax2.imshow(im)
    ax2.grid(False)
    ax2.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax2.set_title('Precipitation indicator', fontsize = 9, fontweight = 'bold')
    
    
    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=df, date=date, hr=hr, data=['pr_value'], ind=None, hydrograph_length=10, plot_title = 'Evolution of Precipitation')
   
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=df, date=date, hr=hr, data=None, ind='percentile', hydrograph_length=10, plot_title = 'Evolution of the regional precipitation indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    
    plt.savefig('../../Data/Visuals/dashboards/pr_dashboard.pdf')
    
#  Define function for surface water dashboard visualizations
def vis_et_dashboard(hr='San Joaquin River', date='2001-04', hydrograph_length=10):
    
    """This function generates the evapotranspiration dashboard
    
    Parameters
    ----------
    
    hr : str
        Hydrologic region name: 'Central Coast', 'Colorado River', 'North Coast',
        'North Lahontan', 'Sacramento River', 'San Francisco Bay', 'San Joaquin River',
        'South Coast', 'South Lahontan', 'Tulare Lake'
    The date for which the dashboard is presented. Format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY'
    hydrograph_length : integer
        Years of data presented in the hydrographs
        
    Returns
    -------
    figure
        the dashboard for evapotranspiration availability
    """
    
    df = pd.read_csv('../../Data/Processed/pr_pet_hr_indicators/pet_percentile.csv')
    ds_prcntl = xr.open_dataset(r'../../Data/Processed/pr_pet_gridded_indicators/pet_percentile.nc')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:4326')
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    #  Convert dataframe date to datetime type
    df.date = pd.to_datetime(df.date, format='%Y-%m-%d')
       
    #  Modify HR regions shapefile to properly facilitate plotting
    hr_shapes = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    
    #  Subset only for hydrologic region of interest
    df = df[df.HR_NAME==hr]
    
    #  Modify et percentile data to properly facilitate plotting
    ds_prcntl = ds_prcntl.rio.write_crs("EPSG:4326") # clipping is  working for epsg:4326 and not for 3857
    ds_prcntl = ds_prcntl.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
    ds_prcntl_clip = ds_prcntl.rio.clip(hr_shapes.geometry)
    ds_prcntl_clip = ds_prcntl_clip.transpose('date', 'lat', 'lon')
    # Extract relevant variables for et percentile data
    lon = ds_prcntl_clip.lon.values
    lat = ds_prcntl_clip.lat.values
    dates = ds_prcntl_clip.date.values
    variable_to_plot = ds_prcntl_clip.percentile.values
    dates = ds_prcntl_clip['date']
    dates_df = dates.to_dataframe()
    dates_df.drop(columns=['date','spatial_ref'],inplace=True)
    dates_df.reset_index(inplace=True)
    time_index = dates_df.index[dates_df['date'] == date.strftime('%Y-%m-%d')].tolist()[0]
    variable_2d = variable_to_plot[time_index,:, :]
        
    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure()
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of et status and add evapotranspiration percentile
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    colors = [(230/255,0,0,1), (255/255,170/255,0,1), (252/255,211/255,127/255,1), (255/255,255/255,0,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1)]
    custom_cmap = ListedColormap(colors)
    hr_shapes.plot(ax=ax1, edgecolor='green', facecolor='none', alpha=1)
    ctx.add_basemap(ax=ax1, crs='EPSG:4326', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    img = ax1.contourf(lon, lat, variable_2d, cmap=custom_cmap, levels=[0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 1.0], alpha=0.7)
    cbar = plt.colorbar(img, ax=ax1, orientation='horizontal', ticks=[0, 0.1, 0.2, 0.3, 0.5, 1.0])
    bbox_ax = ax1.get_position()
    cbar.ax.tick_params(labelsize=8)
    cbar.ax.set_position([bbox_ax.x0, bbox_ax.y1 - 0.22, bbox_ax.width, 0.02])
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    ax1.set_title('Current evapotranspiration condition', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial
    arrow_index = 100*df.percentile[(df.date==date) & (df.HR_NAME==hr)].iloc[0]
    fig0, axs = plt.subplots()
    dial(arrow_index=arrow_index, ax=axs, figname='myDial')
    plt.close(fig0)
    ax2 = fig.add_subplot(grid[0:3, 3:7])  #  Add gauge for indicator
    im = Image.open('myDial.png')
    ax2.imshow(im)
    ax2.grid(False)
    ax2.axis('off')
    plt.xticks([])
    plt.yticks([])
    ax2.set_title('Evapotranspiration indicator', fontsize = 9, fontweight = 'bold')
    
    
    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=df, date=date, hr=hr, data=['pet_value'], ind=None, hydrograph_length=10, plot_title = 'Evolution of evapotranspiration')
   
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=df, date=date, hr=hr, data=None, ind='percentile', hydrograph_length=10, plot_title = 'Evolution of the regional evapotranspiration indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    
    plt.savefig('../../Data/Visuals/dashboards/pet_dashboard.pdf')    

# vis_sw_dashboard(hr='San Joaquin River', date='2022-03', hydrograph_length=10)
# vis_streamflow_dashboard(hr='Sacramento River', date='2022-03', hydrograph_length=10)
# vis_gw_dashboard(hr='San Joaquin River', date='2022-03', hydrograph_length=10) 
# vis_imports_dashboard(date='2022-03', hydrograph_length = 10)
# vis_pr_dashboard(hr='San Joaquin River', date='2017-03', hydrograph_length=10)
vis_et_dashboard(hr='San Joaquin River', date='2018-02', hydrograph_length=10)

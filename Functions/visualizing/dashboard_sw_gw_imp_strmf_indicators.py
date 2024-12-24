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
import rioxarray
from pykrige.ok import OrdinaryKriging
directory_path = '../../Data/Visuals/dashboards'
os.makedirs(directory_path, exist_ok=True)
#  Import real data and indicator visualization function
from dashboard_auxiliar_functions import vis_data_indicator, dial, color_function_df, convert_input_date_format

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
    
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    
    # load files
    hr_rsvr_prc_df = pd.read_csv('../../Data/Processed/surface_water_drougth_indicator/total_storage_percentiles.csv')
    df_ind_rsv_hr = pd.read_csv('../../Data/Processed/surface_water_drougth_indicator/individual_reservoir_percentiles.csv')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3310')
    ca_boundary = hr_shapes.dissolve() 
    
    # Subset the dataframe to include only data for the hydrologic region of interest and select HR regions
    hr_rsvr_prc_df = hr_rsvr_prc_df[hr_rsvr_prc_df.HR_NAME==hr]
    hr_shapes_res = hr_shapes[hr_shapes.HR_NAME==hr]
    
    
    #  Modify regional reservoirs data to properly facilitate plotting
    hr_rsvr_prc_df.date = pd.to_datetime(hr_rsvr_prc_df.date, format='%Y-%m-%d')
    hr_rsvr_prc_df['color_pctl'] = color_function_df(hr_rsvr_prc_df, 'SWDI')  # Assign colors based on percentile for plotting
    date_colors = hr_rsvr_prc_df.loc[hr_rsvr_prc_df.date == date, ['HR_NAME', 'color_pctl']] # Extract colors for the specified date, grouped by hydrologic region
    hr_res_colors = date_colors.set_index('HR_NAME')['color_pctl'].to_dict()
    
    #  Modify individual reservoirs data to properly facilitate plotting
    df_ind_rsv_hr.date = pd.to_datetime(df_ind_rsv_hr.date, format='%Y-%m-%d')
    df_ind_rsv_hr = df_ind_rsv_hr[df_ind_rsv_hr.date==date]
    df_ind_rsv_hr = df_ind_rsv_hr[(~df_ind_rsv_hr.Longitude.isna()) & (~df_ind_rsv_hr.Latitude.isna())] # Remove points with missing locations
    df_ind_rsv_hr = gpd.GeoDataFrame(df_ind_rsv_hr, geometry=gpd.points_from_xy(df_ind_rsv_hr.Longitude, df_ind_rsv_hr.Latitude)) # convert to gdf  
    df_ind_rsv_hr = df_ind_rsv_hr.set_crs('epsg:4326').to_crs('epsg:3310') 
    df_ind_rsv_hr = gpd.clip(df_ind_rsv_hr, hr_shapes_res) #do this if you want to keep reservoirs in california only
    df_ind_rsv_hr['capacity_scaled'] = df_ind_rsv_hr.capacity/7000
    df_ind_rsv_hr['color_pctl'] = color_function_df(df_ind_rsv_hr, 'percentile') # Assign colors based on percentile for plotting
    
    
    fig = plt.figure(figsize=(8, 7))
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of reservoir status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    # for hr_name, color in hr_res_colors.items():
    #     hr_shapes_res[hr_shapes_res['HR_NAME'] == hr_name].plot(
    #         ax=ax1, color=color, alpha=0.5, edgecolor='black', linewidth=1
    #     )
    hr_shapes_res.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 5)
    df_ind_rsv_hr.plot(ax=ax1, markersize=df_ind_rsv_hr.capacity_scaled, color = df_ind_rsv_hr.color_pctl, edgecolor = 'grey', alpha = 0.6)
    ctx.add_basemap(ax=ax1, crs='EPSG:3310', attribution_size=1,source=ctx.providers.CartoDB.Positron)

    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Reservoir conditions', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial
    arrow_index = 100*hr_rsvr_prc_df.SWDI[(hr_rsvr_prc_df.date==date) & (hr_rsvr_prc_df.HR_NAME==hr)].iloc[0]
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
    vis_data_indicator(ax=ax3, df=hr_rsvr_prc_df, date=date, hr=hr, data=['reservoir_storage', 'SWC'], ind=None, hydrograph_length=10, plot_title = 'Evolution of water stored in reservoirs and snowpack')
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=hr_rsvr_prc_df, date=date, hr=hr, data=['reservoir_storage', 'SWC'], ind='SWDI', hydrograph_length=10, plot_title = 'Evolution of the surface water drought indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/sw_dashboard.pdf')
    
#  Define function for delta visualizations 
def vis_imports_dashboard(date='2001-04', hydrograph_length = 10):
    
    """This function generates the surface water dashboard for Delta imports
    
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

    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3310')
    
    #delta
    delta_rsvr_prc_df = pd.read_csv('../../Data/Processed/imports/total_storage_percentiles.csv')
    ind_rsv_delta_df = pd.read_csv('../../Data/Processed/imports/individual_reservoir_percentiles.csv')
    
    #  Modify delta HR regions shapefile to properly facilitate plotting
    hr_shapes_sac = hr_shapes[(hr_shapes.HR_NAME)=='Sacramento River']
    hr_shapes_sj = hr_shapes[(hr_shapes.HR_NAME)=='San Joaquin River']
    hr_shapes_delta = pd.concat([hr_shapes_sac,hr_shapes_sj]).dissolve() 
    ca_boundary = hr_shapes.dissolve() 
    
    #  Modify individual reservoirs data to properly facilitate plotting of delta
    ind_rsv_delta_df.date = pd.to_datetime(ind_rsv_delta_df.date, format='mixed')
    ind_rsv_delta_df = ind_rsv_delta_df[ind_rsv_delta_df.date==date]
    ind_rsv_delta_df = ind_rsv_delta_df[(~ind_rsv_delta_df.Longitude.isna()) & (~ind_rsv_delta_df.Latitude.isna())]  # Remove points with missing locations
    ind_rsv_delta_df = gpd.GeoDataFrame(ind_rsv_delta_df, geometry=gpd.points_from_xy(ind_rsv_delta_df.Longitude, ind_rsv_delta_df.Latitude)) # convert to gdf  
    ind_rsv_delta_df = ind_rsv_delta_df.set_crs('epsg:4326').to_crs('epsg:3310')
    ind_rsv_delta_df = gpd.clip(ind_rsv_delta_df, hr_shapes)
    ind_rsv_delta_df['capacity_scaled'] = ind_rsv_delta_df.capacity/7000
    ind_rsv_delta_df['color_pctl'] = color_function_df(ind_rsv_delta_df, 'corrected_percentile') # Assign colors based on percentile for plotting
    
    #  Modify regional delta data to properly facilitate plotting
    delta_rsvr_prc_df.date = pd.to_datetime(delta_rsvr_prc_df.date, format='mixed')
    delta_rsvr_prc_df['color_pctl'] = color_function_df(delta_rsvr_prc_df, 'SWDI')
    color_delta = str(delta_rsvr_prc_df.loc[delta_rsvr_prc_df.date == date, 'color_pctl'].iloc[0])
    delta_colors = dict(zip(delta_rsvr_prc_df['export_basin'], color_delta))
    
    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure(figsize=(8, 7))
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of reservoir status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    # ca_boundary.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 5)
    # hr_shapes_delta.plot(ax=ax1, color = color_delta, alpha=0.5, edgecolor='gray', linewidth=0.75)
    hr_shapes_delta.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 6)
    ind_rsv_delta_df.plot(ax=ax1, markersize=ind_rsv_delta_df.capacity_scaled, color = ind_rsv_delta_df.color_pctl, edgecolor = 'grey', alpha = 0.6)
    ctx.add_basemap(ax=ax1, crs='EPSG:3310', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Delta reservoir condition', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial
    arrow_index = 100*delta_rsvr_prc_df.SWDI[(delta_rsvr_prc_df.date==date)].iloc[0]
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
    vis_data_indicator(ax=ax3, df=delta_rsvr_prc_df, date=date, data=['reservoir_storage', 'SWC'], ind=None, hydrograph_length=10, plot_title = 'Evolution of water stored in reservoirs and snowpack')
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=delta_rsvr_prc_df, date=date, data=['reservoir_storage', 'SWC'], ind='SWDI', hydrograph_length=10, plot_title = 'Evolution of the surface water drought indicator')

    #  Add figure title
    plt.suptitle("Delta exporting basins\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/imports_dashboard.pdf')

#  Define function for groundwater visualizations
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
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3310')
    
    #GW
    hr_gw_prc_df = pd.read_csv('../../Data/Processed/groundwater/state_wells_regional_analysis.csv')
    df_wells = pd.read_csv('../../Data/Processed/groundwater/state_wells_individual_analysis.csv')
    hr_shapes_gw = hr_shapes
    
    
    # Subset data to include only the hydrologic region of interest
    hr='San Joaquin River' 
    hr_shapes_gw = hr_shapes_gw[hr_shapes_gw.HR_NAME==hr]
    hr_gw_prc_df = hr_gw_prc_df[hr_gw_prc_df.HR_NAME==hr]
    
    minx, miny, maxx, maxy = hr_shapes_gw.total_bounds
    
    #  Modify regional gw data to properly facilitate plotting
    hr_gw_prc_df.date = pd.to_datetime(hr_gw_prc_df.date, format='%Y-%m-%d')
    hr_gw_prc_df['color_pctl'] = color_function_df(hr_gw_prc_df, 'pctl_gwchange_corr')
    date_colors = hr_gw_prc_df.loc[hr_gw_prc_df.date == date, ['HR_NAME', 'color_pctl']]
    hr_gw_colors = date_colors.set_index('HR_NAME')['color_pctl'].to_dict()
    
    #  Modify individual gw data to properly facilitate plotting
    df_wells.date = pd.to_datetime(df_wells.date, format='%Y-%m-%d')
    df_wells = df_wells[df_wells.date==date]
    df_wells = df_wells[(~df_wells.longitude.isna()) & (~df_wells.latitude.isna())]
    df_wells = gpd.GeoDataFrame(df_wells, geometry=gpd.points_from_xy(df_wells.longitude, df_wells.latitude)).set_crs('epsg:4326').to_crs('epsg:3310')
    df_wells = gpd.clip(df_wells, hr_shapes_gw)
    df_wells['color_pctl'] = color_function_df(df_wells, 'pctl_gwelev')
    df_wells = df_wells.dropna(subset=['pctl_cumgwchange'])
    df_wells['x'] = df_wells.geometry.x
    df_wells['y'] = df_wells.geometry.y
    
    # Perform Ordinary Kriging
    coordinates = df_wells[['x', 'y']].values  # x: longitude, y: latitude
    gw_change = df_wells['pctl_gwelev'].values
    grid_x = np.linspace(minx, maxx, 100)  # x-coordinates (longitude)
    grid_y = np.linspace(miny, maxy, 100)  # y-coordinates (latitude)
    ok = OrdinaryKriging(coordinates[:, 0], coordinates[:, 1], gw_change, variogram_model='spherical')
    z, ss = ok.execute('grid', grid_x, grid_y)  
    ds = xr.Dataset(
        {"elevation": (("y", "x"), z)}, 
        coords={"x": grid_x, "y": grid_y},)
    ds = ds.rio.write_crs("EPSG:3310")
    ds = ds.rio.clip(hr_shapes_gw.geometry)
    
    #create a buffer zone around the wells for krigging
    buffer_distance_meters = 10 * 1609.34
    df_wells_buffered = df_wells.copy()
    df_wells_buffered['geometry'] = df_wells_buffered.geometry.buffer(buffer_distance_meters)
    ds = ds.rio.clip(df_wells_buffered.geometry)
    
    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure(figsize=(8, 7))
    grid = plt.GridSpec(nrows=11, ncols=6, hspace=1.0, wspace=1.0)
    
    #  First create the map of groundwater status
    ax1 = fig.add_subplot(grid[0:6, 0:3])
    # for hr_name, color in hr_gw_colors.items():
    #     hr_shapes_gw[hr_shapes_gw['HR_NAME'] == hr_name].plot(ax=ax1, color=color, edgecolor='gray',alpha=0.5, linewidth=0.75, zorder = 5)
    hr_shapes_gw.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 5)
    colors = [(230/255,0,0,1), (255/255,170/255,0,1), (252/255,211/255,127/255,1), (255/255,255/255,0,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1), (189/255,190/255,192/255,1)]
    custom_cmap = ListedColormap(colors)
    ctx.add_basemap(ax=ax1, crs='EPSG:3310', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    img = ax1.contourf(ds.x, ds.y, ds.elevation, cmap=custom_cmap, levels=[0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 1.0], alpha=0.7)
    df_wells.plot(ax=ax1, markersize=2.5, color=df_wells.color_pctl, edgecolor=None, alpha=1)
    bbox_ax = ax1.get_position()
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Groundwater pumping elevation \ncondition', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial for indicator "pctl_gwelev"
    arrow_index = 100*hr_gw_prc_df.pctl_gwelev[(hr_gw_prc_df.date==date) & (hr_gw_prc_df.HR_NAME==hr)].iloc[0]
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
    
    #  Third create the drought monitor dial for indicator "pctl_gwchange_corr"
    arrow_index = 100*hr_gw_prc_df.pctl_gwchange_corr[(hr_gw_prc_df.date==date) & (hr_gw_prc_df.HR_NAME==hr)].iloc[0]
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
    
    #  Fourth create the real data plot
    ax4 = fig.add_subplot(grid[6:8, 0:])    
    vis_data_indicator(ax=ax4, df=hr_gw_prc_df, date=date, hr=hr, data=None, ind='pctl_gwelev', hydrograph_length=10, plot_title = 'Evolution of the groundwater elevation indicator')
    
    #  Fifth create the indicator plot
    ax5 = fig.add_subplot(grid[9:11, 0:])
    vis_data_indicator(ax=ax5, df=hr_gw_prc_df, date=date, hr=hr, data=None, ind='pctl_gwchange_corr', hydrograph_length=10, plot_title = 'Evolution of the groundwater pumping intensity indicator')
    
    plt.suptitle(hr+ " - " + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/gw_dashboard.pdf')

#  Define function for streamflow visualizations
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
    
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3310')
    
    
    hr_sf_prc_df = pd.read_csv('../../Data/Processed/streamflow_indicator/streamflow_regional_indicator.csv')
    df_gages = pd.read_csv('../../Data/Processed/streamflow_indicator/streamflow_individual_gages_indicator.csv')
    rivers_shape = gpd.read_file('../../Data/Input_Data/Major_Rivers/NHD_Major_Rivers.shp').to_crs('epsg:3310')
    hr_shapes_sf = hr_shapes
    
    rivers_shape = gpd.read_file(r"C:\Users\armen\Desktop\nidis\ploting files\rivers_shape\rivers_shape.shp").to_crs('epsg:3310')
    
    #  Create function for properly converting datetime with timezones removed
    hr_sf_prc_df.date = hr_sf_prc_df.date.str[:10]
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
    
    hr_sf_prc_df = df_field_to_datetime(hr_sf_prc_df)
    df_gages = df_field_to_datetime(df_gages)
    
    # Subset data to include only the hydrologic region of interest
    hr_shapes_sf = hr_shapes_sf[hr_shapes_sf.HR_NAME==hr].dissolve(by='HR_NAME')
    hr_sf_prc_df = hr_sf_prc_df[hr_sf_prc_df.HR_NAME==hr]
    rivers_shape = gpd.clip(rivers_shape, hr_shapes_sf)
    
    #  Modify regional sf data to properly facilitate plotting
    hr_sf_prc_df['color_pctl'] = color_function_df(hr_sf_prc_df, 'percentile')
    date_colors = hr_sf_prc_df.loc[hr_sf_prc_df.date == date, ['HR_NAME', 'color_pctl']]
    hr_colors_sf = date_colors.set_index('HR_NAME')['color_pctl'].to_dict()
    
    #  Modify individual gages data to properly facilitate plotting
    df_gages = df_gages[df_gages.date==date]
    df_gages = df_gages[(~df_gages.lon.isna()) & (~df_gages.lat.isna())]
    df_gages = gpd.GeoDataFrame(df_gages, geometry=gpd.points_from_xy(df_gages.lon, df_gages.lat)).set_crs('epsg:4326').to_crs('epsg:3310')
    df_gages = gpd.clip(df_gages, hr_shapes_sf)
    df_gages['color_pctl'] = color_function_df(df_gages, 'percentile')

    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure(figsize=(8, 7))
    grid = plt.GridSpec(nrows=4, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of streamflow status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    hr_shapes_sf.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 5)
    # for hr_name, color in hr_colors_sf.items():
    #     hr_shapes[hr_shapes['HR_NAME'] == hr_name].plot(
    #         ax=ax1, color=color, alpha=0.5, edgecolor='green', linewidth=1
    #     )
    rivers_shape.plot(ax=ax1,color='cornflowerblue', alpha = 0.75, zorder=2)
    df_gages.plot(ax=ax1, markersize=20, color=df_gages.color_pctl, edgecolor='Grey', alpha=0.6, zorder=3)
    ctx.add_basemap(ax=ax1, crs='EPSG:3310', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    [ax1.spines[edge].set_visible(True) for edge in ['right', 'bottom', 'top', 'left']]
    ax1.set_title('Streamflow conditions', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial for indicator "percentile"
    arrow_index = 100*hr_sf_prc_df.percentile[(hr_sf_prc_df.date==date) & (hr_sf_prc_df.HR_NAME==hr)].iloc[0]
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
    ax2.set_title('Streamflow indicator', fontsize = 9, fontweight = 'bold', y=1.1)
    pos = ax2.get_position()
    
    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=hr_sf_prc_df, date=date, hr=hr, data=None, ind='percentile', hydrograph_length=10, plot_title = 'Evolution of the regional streamflow indicator')
    
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/streamflow_dashboard.pdf')
    
#  Define function for precipitation visualizations
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
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3310')
    
    #load files
    ds_pr = xr.open_dataset(r'../../Data/Processed/pr_pet_gridded_indicators/pr_percentile.nc')
    
    hr_shapes_pr = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    
    #  clipping pr percentile gridded data to selected hydrologic region (this step has been done already, dont run it!)
    ds_pr = ds_pr.rio.write_crs("EPSG:4326") # clipping is  working for epsg:4326 and not for 3857
    ds_pr = ds_pr.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
    ds_pr = ds_pr.transpose('date', 'lat', 'lon')
    ds_pr  = ds_pr[['percentile']]  # Keep only the percentile variable
    ds_pr = ds_pr.rename({'lon': 'x', 'lat': 'y'})
    ds_pr = ds_pr.rio.reproject("EPSG:3310")
    ds_pr = ds_pr.rio.clip(hr_shapes_pr.geometry)
    ds_pr = ds_pr
    
    #  Modify pr and et local data to properly facilitate plotting
    lon_pr = ds_pr.x.values
    lat_pr = ds_pr.y.values
    dates = ds_pr.date.values
    variable_to_plot = ds_pr.percentile.values
    dates_df = ds_pr['date'].to_dataframe()
    dates_df = dates_df.drop(columns=['date','spatial_ref']).reset_index()
    time_index = dates_df.index[dates_df['date'] == date.strftime('%Y-%m-%d')].tolist()[0]
    variable_2d_pr = variable_to_plot[time_index,:, :]
    
    #  Modify regional pr and et data to properly facilitate plotting
    hr_pr_prc_df = pd.read_csv(r'../../Data/Processed/pr_pet_hr_indicators/pr_percentile.csv')
    hr_pr_prc_df.date = pd.to_datetime(hr_pr_prc_df.date, format='%Y-%m-%d')
    
    hr_pr_prc_df_selected_data = hr_pr_prc_df.loc[hr_pr_prc_df.date == date]
    hr_pr_prc_df_selected_data['color_pctl'] = color_function_df(hr_pr_prc_df_selected_data, 'percentile')  # Assign colors based on percentile for plotting
    date_colors = hr_pr_prc_df_selected_data.loc[hr_pr_prc_df_selected_data.date == date, ['HR_NAME', 'color_pctl']] # Extract colors for the specified date, grouped by hydrologic region
    hr_pr_colors = date_colors.set_index('HR_NAME')['color_pctl'].to_dict()
    
    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure(figsize=(8, 7))
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of pr status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    colors = [
        (230/255, 0, 0),                   # Red
        (255/255, 170/255, 0),             # Orange
        (252/255, 211/255, 127/255),       # Light Orange
        (255/255, 255/255, 0),             # Yellow
        (171/255, 217/255, 233/255),       # Light Blue
        (116/255, 173/255, 209/255),       # Blue
        (69/255, 117/255, 180/255),        # Darker Blue
        (128/255, 0, 128/255)              # Purple
    ] 
    custom_cmap = ListedColormap(colors)
    
    # for hr_name, color in hr_pr_colors.items():
    #     hr_shapes[hr_shapes['HR_NAME'] == hr_name].plot(ax=ax1, color=color, edgecolor='gray',alpha=0.5, linewidth=0.75, zorder = 5)
    hr_shapes_pr.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 5)
    ctx.add_basemap(ax=ax1, crs='EPSG:3310', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    img = ax1.contourf(lon_pr, lat_pr, variable_2d_pr, cmap=custom_cmap, levels=[0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 1.0], alpha=0.6)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    ax1.set_title('Precipitation condition', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial
    arrow_index = 100*hr_pr_prc_df.percentile[(hr_pr_prc_df.date==date) & (hr_pr_prc_df.HR_NAME==hr)].iloc[0]
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
    ax2.set_title('Precipitation indicator', fontsize = 9, fontweight = 'bold', y=1.1)
    
    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=hr_pr_prc_df, date=date, hr=hr, data=['pr_value'], ind=None, hydrograph_length=10, plot_title = 'Evolution of Precipitation')
       
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=hr_pr_prc_df, date=date, hr=hr, data=None, ind='percentile', hydrograph_length=10, plot_title = 'Evolution of the regional precipitation indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/pr_dashboard.pdf')
    
#  Define function for evapotranspiration visualizations
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
        
    date = convert_input_date_format(date)
    date = datetime.strptime(date, '%Y-%m-%d')
    hr_shapes = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp').to_crs('epsg:3310')
    
    #load files
    ds_pet = xr.open_dataset(r'../../Data/Processed/pr_pet_gridded_indicators/pet_percentile.nc')
    
    hr_shapes_pet = hr_shapes[hr_shapes.HR_NAME==hr].dissolve(by='HR_NAME')
    
    #  clipping pr percentile gridded data to selected hydrologic region (this step has been done already, dont run it!)
    ds_pet = ds_pet.rio.write_crs("EPSG:4326") # clipping is  working for epsg:4326 and not for 3857
    ds_pet = ds_pet.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
    ds_pet = ds_pet.transpose('date', 'lat', 'lon')
    ds_pet  = ds_pet[['percentile']]  # Keep only the percentile variable
    ds_pet = ds_pet.rename({'lon': 'x', 'lat': 'y'})
    ds_pet = ds_pet.rio.reproject("EPSG:3310")
    ds_pet = ds_pet.rio.clip(hr_shapes_pet.geometry)
    
    #  Modify pr and et local data to properly facilitate plotting
    lon_pet = ds_pet.x.values
    lat_pet = ds_pet.y.values
    dates = ds_pet.date.values
    variable_to_plot = ds_pet.percentile.values
    dates_df = ds_pet['date'].to_dataframe()
    dates_df = dates_df.drop(columns=['date','spatial_ref']).reset_index()
    time_index = dates_df.index[dates_df['date'] == date.strftime('%Y-%m-%d')].tolist()[0]
    variable_2d_pet = variable_to_plot[time_index,:, :]
    
    #  Modify regional pr and et data to properly facilitate plotting
    hr_pet_prc_df = pd.read_csv(r'../../Data/Processed/pr_pet_hr_indicators/pet_percentile.csv')
    hr_pet_prc_df.date = pd.to_datetime(hr_pet_prc_df.date, format='%Y-%m-%d')
    
    hr_pet_prc_df_selected_data = hr_pet_prc_df.loc[hr_pet_prc_df.date == date]
    hr_pet_prc_df_selected_data['color_pctl'] = color_function_df(hr_pet_prc_df_selected_data, 'percentile')  # Assign colors based on percentile for plotting
    date_colors = hr_pet_prc_df_selected_data.loc[hr_pet_prc_df_selected_data.date == date, ['HR_NAME', 'color_pctl']] # Extract colors for the specified date, grouped by hydrologic region
    hr_pet_colors = date_colors.set_index('HR_NAME')['color_pctl'].to_dict()
    

    #  Create figure objects and develop gridding system to implement components of dashboard
    fig = plt.figure(figsize=(8, 7))
    grid = plt.GridSpec(nrows=5, ncols=7, hspace=1.0, wspace=1.0)
    
    #  First create the map of et status
    ax1 = fig.add_subplot(grid[0:3, 0:3])
    colors = [
        (230/255, 0, 0),                   # Red
        (255/255, 170/255, 0),             # Orange
        (252/255, 211/255, 127/255),       # Light Orange
        (255/255, 255/255, 0),             # Yellow
        (171/255, 217/255, 233/255),       # Light Blue
        (116/255, 173/255, 209/255),       # Blue
        (69/255, 117/255, 180/255),        # Darker Blue
        (128/255, 0, 128/255)              # Purple
    ] 
    custom_cmap = ListedColormap(colors)
    
    # for hr_name, color in hr_pr_colors.items():
    #     hr_shapes[hr_shapes['HR_NAME'] == hr_name].plot(ax=ax1, color=color, edgecolor='gray',alpha=0.5, linewidth=0.75, zorder = 5)
    hr_shapes_pet.plot(ax=ax1, edgecolor='gray', facecolor='none', alpha=0.5, linewidth=0.75, zorder = 5)
    ctx.add_basemap(ax=ax1, crs='EPSG:3310', attribution_size=1,source=ctx.providers.CartoDB.Positron)
    img = ax1.contourf(lon_pet, lat_pet, variable_2d_pet, cmap=custom_cmap, levels=[0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 1.0], alpha=0.6)
    ax1.get_xaxis().set_visible(False), ax1.get_yaxis().set_visible(False)
    ax1.set_title('Evapotranspiration condition', fontsize = 9, fontweight = 'bold')
    
    #  Second create the drought monitor dial
    arrow_index = 100*hr_pet_prc_df.percentile[(hr_pet_prc_df.date==date) & (hr_pet_prc_df.HR_NAME==hr)].iloc[0]
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
    ax2.set_title('Evapotranspiration indicator', fontsize = 9, fontweight = 'bold', y=1.1)
    
    #  Third create the real data plot
    ax3 = fig.add_subplot(grid[3, 0:])
    vis_data_indicator(ax=ax3, df=hr_pet_prc_df, date=date, hr=hr, data=['pet_value'], ind=None, hydrograph_length=10, plot_title = 'Evolution of Evapotranspiration') 
    
    #  Fourth create the indicator plot
    ax4 = fig.add_subplot(grid[4, 0:])
    vis_data_indicator(ax=ax4, df=hr_pet_prc_df, date=date, hr=hr, data=None, ind='percentile', hydrograph_length=10, plot_title = 'Evolution of the regional evapotranspiration indicator')
    
    #  Add figure title
    plt.suptitle(hr+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/pet_dashboard.pdf')   

vis_sw_dashboard(hr='San Joaquin River', date='2022-03', hydrograph_length=10)
vis_imports_dashboard(date='2022-03', hydrograph_length = 10)
vis_streamflow_dashboard(hr='Sacramento River', date='2022-03', hydrograph_length=10)
vis_gw_dashboard(hr='San Joaquin River', date='2022-03', hydrograph_length=10) 
vis_pr_dashboard(hr='San Joaquin River', date='2022-03', hydrograph_length=10)
vis_et_dashboard(hr='San Joaquin River', date='2022-03', hydrograph_length=10)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 17 21:09:37 2023

@author: alvar
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 22:49:07 2021

@author: escriva
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
import scipy
from scipy.stats import shapiro, norm, skewnorm
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

import matplotlib.patches as mpatch
from matplotlib.patches import FancyBboxPatch


#Hydrologic regions
hr = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp')
hr = hr.to_crs('epsg:4326')

#Read indicators
pr_indicator = pd.read_csv('../../Data/Processed/pr_pet_hr_indicators/pr_percentile.csv')
pet_indicator = pd.read_csv('../../Data/Processed/pr_pet_hr_indicators/pet_percentile.csv')
sw_indicator = pd.read_csv('../../Data/Processed/surface_water_drougth_indicator/total_storage_percentiles.csv')
gw_indicator = pd.read_csv('../../Data/Processed/groundwater/state_wells_regional_analysis.csv')
sflow_indicator = pd.read_csv('../../Data/Processed/streamflow_indicator/streamflow_regional_indicator.csv')
imports_indicator = pd.read_csv('../../Data/Processed/imports/total_storage_percentiles.csv')
imports_indicator = imports_indicator.rename(columns={'SWDI': 'SWDI_imports'})
#Import basins
imp_basins = ['San Joaquin River', 'Tulare Lake', 'South Coast']
imp_basins2 = pd.concat([imports_indicator,imports_indicator,imports_indicator]).reset_index(drop=True)
imp_basins2['HR_NAME']= imp_basins[0]
imp_basins2.loc[600:1200, 'HR_NAME'] = imp_basins[1]
imp_basins2.loc[1200:1800, 'HR_NAME'] = imp_basins[2]
imports_indicator = imp_basins2
del imp_basins2


#To datetime
sflow_indicator['date'] = sflow_indicator.date.str[:10]
def df_field_to_datetime(df, df_date_column='date'):
    df['date'] = pd.to_datetime(df[df_date_column])
    df = df.set_index('date')
    try:
        df = df.tz_convert(tz='UTC')
    except:
        pass
    df = df.reset_index(drop=True)
    return df
    
indicator_dfs = [pr_indicator, pet_indicator, sw_indicator, gw_indicator, sflow_indicator, imports_indicator]
for ind in indicator_dfs:
    df_field_to_datetime(ind)
    
    
#Merging a dataframe with indicators
indicator_columns = ['percentile', 'percentile', 'SWDI', 'pctl_cumgwchange_corr', 'percentile', 'SWDI_imports']
indicator_names = ['Precipitation', 'Evapotranspiration', 'Surface Water', 'Groundwater', 'Streamflow', 'Imports']
df_indicators = pd.DataFrame()
for i in range(6):
    df_indicator = indicator_dfs[i]
    df_indicator = df_indicator[['date', 'HR_NAME', indicator_columns[i]]]
    df_indicator = df_indicator.rename(columns={indicator_columns[i]:indicator_names[i]})
    if i==0:
        df_indicators = df_indicator
    else:
        df_indicators = df_indicators.merge(df_indicator, on = ['date', 'HR_NAME'], how='outer').reset_index(drop=True)
    del df_indicator

df_indicators['Groundwater'] = df_indicators['Groundwater'].interpolate()
df_indicators = df_indicators.loc[df_indicators.date>='1-1-1991'].reset_index(drop=True)
df_indicators = df_indicators.loc[df_indicators.date<'4-1-2023'].reset_index(drop=True)



#PPIC colors, formats and default parameters for figures
ppic_coltext = '#333333'
ppic_colgrid = '#898989'
ppic_colors = ['#e98426','#649ea5','#0d828a','#776972','#004a80','#3e7aa8','#b44b27','#905a78','#d2aa1d','#73a57a','#4fb3ce']

params = {
   'axes.labelsize': 10,
   'axes.labelweight': "bold",
   'font.size': 10,
   'legend.fontsize': 10,
   'xtick.labelsize': 10,
   'ytick.labelsize': 10,
   'text.usetex': False,
   'font.family': "Arial",
   'text.color' : ppic_coltext,
   'axes.labelcolor' : ppic_coltext,
   'xtick.color' : ppic_coltext,
   'ytick.color': ppic_coltext,
   'grid.color' : ppic_colgrid,
   'figure.figsize': [7, 5],
   'axes.prop_cycle' : cycler(color=ppic_colors)
   }
rcParams.update(params)


#US Drought colors
colors = [(1,1,1,1), (189/255,190/255,192/255,1) , (255/255,255/255,0,1) , (252/255,211/255,127/255,1) , (255/255,170/255,0,1) , (230/255,0,0,1) , (115/255,0,0,1) , (57/255,57/255,57/255,1)]




#400-element array with 0-200 for colored half and 201-400 for white half
dcolors = np.zeros(400)
dcolors[0:100]=1
dcolors[100:140]=2
dcolors[140:160]=3
dcolors[160:180]=4
dcolors[180:200]=5

#Create color palette
colpal = np.zeros([400,4])
for i in range(400):
    colpal[i] = colors[int(dcolors[i])]

 
# create labels at desired locations
# note that the pie plot plots from right to left
labels = [' ']*len(colpal)
labels[190] = 'Extreme\ndrought'
labels[170] = 'Severe\ndrought'
labels[150] = 'Moderate\ndrought'
labels[120] = 'Abnormally\ndry'
labels[50] = 'Not in\ndrought' 

 
# function plotting a colored dial
def dial(arrow_index, colpal, labels, ax, figname = 'myDial'):

    pie_wedge_collection = ax.pie(np.ones(len(colpal)), colors=colpal, labels=labels,
                                  textprops = {'horizontalalignment' : 'center'}, labeldistance = 1.2)
     
    i=0
    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor((colpal[i]))
        i=i+1
 
    # create a white circle to make the pie chart a dial
    my_circle=plt.Circle( (0,0), 0.4, color='white')
    ax.add_artist(my_circle)   

    # create the arrow, pointing at specified index
    arrow_angle = (2*arrow_index/float(len(colpal)/2))*3.14159
    arrow_x = .8*math.cos(arrow_angle)
    arrow_y = .8*math.sin(arrow_angle)
    my_arrow = plt.arrow(0,0,-arrow_x*.01,arrow_y*.01, width=.02, head_width=.05,
                         head_length=0.975, fc=colors[7], ec=colors[7])
    ax.add_artist(my_arrow)
    circlecenter = plt.Circle((0,0),0.04,color = colors[7])    
    ax.add_artist(circlecenter)
    
    ax.set_aspect('equal')
    plt.savefig(figname + '.png', bbox_inches='tight')

    # open figure and crop bottom half
    im = Image.open(figname + '.png')
    width, height = im.size

    im = im.crop((0, height/32  , width, int(height/1.9))).save(figname + '.png')

def color_function(indicator = 0.5):
    if indicator<0.1:
        color = colors[5]
    elif indicator<0.2:
        color = colors[4]
    elif indicator<0.3:
        color = colors[3]
    elif indicator<0.5:
        color = colors[2]
    else:
        color = colors[1]
    return color
        


def main_dashboard(region='Sacramento River', date='31-1-2021'):
    
    if region in imp_basins:
        numb_ind = 6
    else:
        numb_ind = 5
        
    
    #putting spatial files together
    regionshape = hr.loc[hr.HR_NAME==region]
    regionshape = regionshape.to_crs(epsg=3857)
        
    #Now the dashboard
    fig = plt.figure(figsize=(7,3.5))
    grid = plt.GridSpec(3, numb_ind, hspace=0.5)


    #Generating map
    for i in range(numb_ind):
        indicator = df_indicators.loc[(df_indicators.date == date) & (df_indicators.HR_NAME==region), indicator_names[i]].reset_index(drop=True)[0]
        ax = fig.add_subplot(grid[:2,i])
        regionshape.plot(ax=ax,alpha=0.5, edgecolor= 'k', color = color_function(indicator))
        ctx.add_basemap(ax, attribution_size=1)
        plt.xticks([])
        plt.yticks([])
        plt.axis('off')
        ax.set_title(indicator_names[i] , y=-0.25, fontsize=8)
  
    for i in np.arange(numb_ind):
        indicator = df_indicators.loc[(df_indicators.date == date) & (df_indicators.HR_NAME==region), indicator_names[i]].reset_index(drop=True)[0]
        fig0, axs = plt.subplots()
        arrow_index = indicator * 100
        dial(arrow_index, colpal, labels, axs, figname = 'map' + str(i))
        plt.close(fig0)
        
        #Gauge 1: Groundwater level
        ax = fig.add_subplot(grid[2, i-numb_ind])
        im = Image.open('map' + str(i) + '.png')
        ax.imshow(im)
        ax.grid(False)
        ax.axis('off')
        plt.xticks([])
        plt.yticks([])
 
    plt.suptitle(region+ "\n" + pd.to_datetime(date).strftime('%b %Y'), fontsize=16)
    plt.savefig('../../Data/Visuals/dashboards/combined_dashboard.pdf')

    

# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 11:08:17 2023

@author: spenc
"""

###  Develop hydrograph plot of data and time series of drought indicator

#  Import packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from matplotlib import rcParams
from cycler import cycler
import math
from PIL import Image

#  Define function for developing visualizations
def vis_data_indicator(ax, subplot, df, date, hr=None, data=None, ind=None, hydrograph_length=10):
    
    """TBD
    
    Parameters
    ----------
    ax : str
        TBD
    subplot : integer
        TBD
        
    Returns
    -------
    figure
        A temporal plot of the hydrograph or indicators to include in the dash
    """
    
    #  Define general parameters for matplotlib formatting
    ppic_coltext = '#333333'
    ppic_colgrid = '#898989'
    ppic_colors = ['#e98426','#649ea5','#0d828a','#776972','#004a80','#3e7aa8','#b44b27','#905a78','#d2aa1d','#73a57a','#4fb3ce']
    
    params = {
       'axes.labelsize': 8,
       'axes.labelweight': 'bold',
       'font.size': 8,
       'legend.fontsize': 8,
       'xtick.labelsize': 8,
       'ytick.labelsize': 8,
       'text.usetex': False,
       'font.family': 'Arial',
       'text.color' : ppic_coltext,
       'axes.labelcolor' : ppic_coltext,
       'xtick.color' : ppic_coltext,
       'ytick.color': ppic_coltext,
       'grid.color' : ppic_colgrid,
       'figure.figsize': [7.0, 7],
       'axes.prop_cycle' : cycler(color=ppic_colors)
       }
    
    rcParams.update(params)

    #  Define US drought monitor color scheme
    dm_colors = [(189/255,190/255,192/255,1), (255/255,255/255,0,1), (252/255,211/255,127/255,1), (255/255,170/255,0,1), (230/255,0,0,1), (115/255,0,0,1), (57/255,57/255,57/255,1)]
    
    #  Define title of the plot
    if data == ['reservoir_storage', 'SWC']:
        if ind == None:
            plot_title = 'Evolution of water stored in reservoirs and snowpack'
        else:
            plot_title = 'Evolution of the surface water drought indicator'
    if ind == 'pctl_cumgwchange_corr':
        plot_title = 'Evolution of the groundwater elevation indicator'
    if ind == 'pctl_gwchange_corr':
        plot_title = 'Evolution of the groundwater pumping intensity indicator'
    if ind == 'percentile':
        plot_title = 'Evolution of the regional streamflow indicator'
    
    #  Define timeframe as ten years from the date provided
    date2, date1 = date, datetime(year=date.year - hydrograph_length, month=date.month, day=date.day)
    df = df[df.date.between(date1, date2)]
    
    #  Subset only for hydrologic region of interest
    if hr is not None:
        df = df[df.HR_NAME==hr]
    
    #  Convert real data to millions of acre-feet
    if data is not None:
        for d in data:
            df[d] = df[d].fillna(0)
            df[d] = df[d]/1000000
    
    #  Add subplot modifier for determining legend location
    if subplot==True:
        bbox = -0.45
    else:
        bbox = -0.15
    #  If indicator is called as None, create real data plot
    if ind==None:
        #  Plot real data line and fill vertically
        if type(data)=='string':
            df.plot(kind='line', ax=ax, x='date', y=data, color='dodgerblue', legend=False)
            plt.fill_between(df['date'].dt.to_pydatetime(), 0, df[data], color='dodgerblue')
            plt.legend([data], title=None, frameon=False, loc='center', bbox_to_anchor=(0.5, bbox))
        else:
            df['data3'] = df[data[0]]+df[data[1]]
            df.plot(kind='line', ax=ax, x='date', y='data3', color='orange', legend=False)
            df.plot(kind='line', ax=ax, x='date', y=data[0], color='dodgerblue', legend=False)
            plt.fill_between(df['date'].dt.to_pydatetime(), 0, df['data3'], color='orange')
            plt.fill_between(df['date'].dt.to_pydatetime(), 0, df[data[0]], color='dodgerblue')
            plt.legend([data[1], data[0]], title=None, ncols=2, frameon=False, loc='center', bbox_to_anchor=(0.5, -0.55),fontsize=7)
            
        #  Formatting
        ax.set_xlabel(None)
        ax.set_ylabel('Millions of acre-feet', fontsize=8)
        ax.set_title(plot_title, fontsize=9, fontweight = 'bold')
        #if hr is not None:
        #    ax.set_title(label=data[0]+' '+hr, fontdict={'fontweight':'bold'})
        #else:
        #    ax.set_title(label=data[0]+' Delta exporting basins', fontdict={'fontweight':'bold'})

        [ax.spines[edge].set_visible(False) for edge in ['right', 'bottom', 'top', 'left']]
        ax.tick_params(axis='both', which='major', labelsize=8)
    
    #  If indicator is called as a valid entry, create indicator plot
    else:
        #  Plot indicator data line and fill drought status bins horizontally
        df.plot(kind='line', ax=ax, x='date', y=ind, color='dodgerblue', legend=False)
        plt.fill_between(df['date'].dt.to_pydatetime(), 0.3, 0.5, color=dm_colors[1], alpha=1.0)
        plt.fill_between(df['date'].dt.to_pydatetime(), 0.2, 0.3, color=dm_colors[2], alpha=1.0)
        plt.fill_between(df['date'].dt.to_pydatetime(), 0.1, 0.2, color=dm_colors[3], alpha=1.0)
        plt.fill_between(df['date'].dt.to_pydatetime(), 0.0, 0.1, color=dm_colors[4], alpha=1.0)
        plt.fill_between(df['date'].dt.to_pydatetime(), 0.5, df[ind], color='dodgerblue', alpha=0.5)
        
        #  Add a dummy plot to generate legend -- not working, unsure why? could probably optimize this part of code
        # dummy = pd.DataFrame({'name':['Abnormally dry', 'Moderate drought', 'Severe drought', 'Extreme drought', ind], 'x':[date1, date1, date1, date1, date1], 'y':[0, 0, 0, 0, 0]})
        # dummy.plot.scatter(ax=ax, x='x', y='y', s=0.0, legend=False).legend(title=None, ncols=5, frameon=False, loc='center', bbox_to_anchor=(0.5, -0.25))
        plt.legend([ind, 'Abnormally dry', 'Moderate drought', 'Severe drought', 'Extreme drought'], title=None, ncols=5, frameon=False, loc='center', bbox_to_anchor=(0.5, -0.55),fontsize = 7)
        
        #  Formatting
        ax.set_xlabel(None)
        ax.set_ylabel('Percentile', fontsize = 8)
        ax.set_ylim([0.0, 1.0])
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.set_title(plot_title, fontsize=9, fontweight = 'bold')
        #if hr is not None:
        #    ax.set_title(label=ind+' '+hr, fontdict={'fontweight':'bold'}, fontsize=8)
        #else:
        #    ax.set_title(label=ind+' Delta exporting basins', fontdict={'fontweight':'bold'}, fontsize=8)
        [ax.spines[edge].set_visible(False) for edge in ['right', 'bottom', 'top', 'left']]
        
        
#This second part includes a function that creates the dial

# function plotting a colored dial
def dial(arrow_index, ax, figname = 'myDial'):#, ax):
    
    #  Define general parameters for matplotlib formatting
    ppic_coltext = '#333333'
    ppic_colgrid = '#898989'
    ppic_colors = ['#e98426','#649ea5','#0d828a','#776972','#004a80','#3e7aa8','#b44b27','#905a78','#d2aa1d','#73a57a','#4fb3ce']
    
    params = {
       'axes.labelsize': 14,
       'axes.labelweight': 'bold',
       'font.size': 14,
       'legend.fontsize': 14,
       'xtick.labelsize': 14,
       'ytick.labelsize': 14,
       'text.usetex': False,
       'font.family': 'Arial',
       'text.color' : ppic_coltext,
       'axes.labelcolor' : ppic_coltext,
       'xtick.color' : ppic_coltext,
       'ytick.color': ppic_coltext,
       'grid.color' : ppic_colgrid,
       'figure.figsize': [7.0, 7],
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

    pie_wedge_collection = ax.pie(np.ones(len(colpal)), colors=colpal, labels=labels,
                                  textprops = {'horizontalalignment' : 'center'}, labeldistance = 1.2)
     
    i=0
    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor((colpal[i]))
        i=i+1
 
    # create a white circle to make the pie chart a dial
    my_circle = plt.Circle((0,0), 0.4, color='white')
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
     
    # crop bottom half of figure of image to keep, (0,0) in python images is the top left corner
    im = im.crop((0, height/50  , width, int(height/1.9))).save(figname + '.png')

#US Drought colors
colors = [(1,1,1,1), (189/255,190/255,192/255,1) , (255/255,255/255,0,1) , (252/255,211/255,127/255,1) , (255/255,170/255,0,1) , (230/255,0,0,1) , (115/255,0,0,1) , (57/255,57/255,57/255,1)]

def color_function(indicator = 0.5):
    colors = [(1,1,1,1), (189/255,190/255,192/255,1) , (255/255,255/255,0,1) , (252/255,211/255,127/255,1) , (255/255,170/255,0,1) , (230/255,0,0,1) , (115/255,0,0,1) , (57/255,57/255,57/255,1)]
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

def color_function_df(df, df_field = 'corrected_percentile'):
    drought_col = ['#bfc0c0', '#ffff00', '#ffd37f', '#e69800', '#e60000', '#730000']
    df['color_pctl'] = drought_col[0]
    df.loc[df[df_field]<0.5, 'color_pctl'] = drought_col[1]
    df.loc[df[df_field]<0.3, 'color_pctl'] = drought_col[2]
    df.loc[df[df_field]<0.2, 'color_pctl'] = drought_col[3]
    df.loc[df[df_field]<0.1, 'color_pctl'] = drought_col[4]
    return df['color_pctl']


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
from datetime import datetime, timedelta
from matplotlib import rcParams
from cycler import cycler
import math
from PIL import Image
import calendar


#  Define function for developing visualizations
def vis_data_indicator(ax, df, date, hr=None, data=None, ind=None, hydrograph_length=10, plot_title = 'Evolution of a variable'):
    
    """ Creates a temporal plot of a variable or indicator based on the selected hydrograph plot
    
    Parameters
    ----------
    ax : str
        The axes object to plot on
    df : str
        The dataframe containing the data to be plotted
    date : str
        The specific date of interest for the plot. Format: yyyy-mm
    hr : str
        The hydrologic region of interest for the plot
    data : list
        The name(s) of the variable(s), provided as a list of strings.
    ind : str
        The name of the indicator column
    hydrograph_length : integer
        The length of the hydrograph period in years, measured backward from the selected date.
        For example, if the date is 2021-10 and hydrograph_length is 10 years, the plot will include data from 2011-10 to 2021-10.
    plot_title : str
        The title of the plot
        
    Returns
    -------
    figure
        A temporal plot of the hydrograph or indicators to include in the dash
    """
    #  Define US drought monitor color scheme
    dm_colors = [(189/255,190/255,192/255,1), (255/255,255/255,0,1), (252/255,211/255,127/255,1), (255/255,170/255,0,1), (230/255,0,0,1), (115/255,0,0,1), (57/255,57/255,57/255,1)]
    
    #  Define timeframe as ten years from the date provided
    date2, date1 = date, datetime(year=date.year - hydrograph_length, month=date.month, day=date.day)
    df = df[df.date.between(date1, date2)]
    
    #  Subset only for hydrologic region of interest
    if hr is not None:
        df = df[df.HR_NAME==hr]
    
    #  Convert real data to millions of acre-feet
    if data == ['reservoir_storage', 'SWC']:
        for d in data:
            df.loc[:, d] = df.loc[:, d].fillna(0)
            df.loc[:, d] = df.loc[:, d] / 1000000
    
    #  If indicator is called as None, create real data plot
    if ind==None:
        no_inp = len(data)
        if no_inp == 1:
            #  Plot real data line and fill vertically
            df.plot(kind='line', ax=ax, x='date', y=data, color='dodgerblue', legend=False)
            ax.fill_between(df['date'].values, 0, df[data[0]], color='dodgerblue')

        if no_inp == 2:
            #  Plot real data line and fill vertically
            if type(data)=='string':
                df.plot(kind='line', ax=ax, x='date', y=data, color='dodgerblue', legend=False)
                ax.fill_between(df['date'].values, 0, df[data], color='dodgerblue')
                ax.legend([data], title=None, frameon=False, loc='center', bbox_to_anchor=(0.5, -.45))
            else:
                df.loc[:,'data3'] = df.loc[:,data[0]] + df.loc[:,data[1]]
                df.plot(kind='line', ax=ax, x='date', y='data3', color='orange', legend=False)
                df.plot(kind='line', ax=ax, x='date', y=data[0], color='dodgerblue', legend=False)
                ax.fill_between(df['date'].values, 0, df['data3'], color='orange')
                ax.fill_between(df['date'].values, 0, df[data[0]], color='dodgerblue')
                ax.legend([data[1], data[0]], title=None, ncols=2, frameon=False, loc='center', bbox_to_anchor=(0.5, -0.55),fontsize=7)
            
        #  Formatting
        ax.set_xlabel(None)
        if data == ['reservoir_storage', 'SWC']:
            ax.set_ylabel('Millions of acre-feet', fontsize=8)
        else:
            ax.set_ylabel('Inches per month', fontsize=8)
        ax.set_title(plot_title, fontsize=9, fontweight = 'bold')
        [ax.spines[edge].set_visible(False) for edge in ['right', 'bottom', 'top', 'left']]
        ax.tick_params(axis='both', which='major', labelsize=8)
    
    #  If indicator is called as a valid entry, create indicator plot
    else:
        #  Plot indicator data line and fill drought status bins horizontally
        df.plot(kind='line', ax=ax, x='date', y=ind, color='dodgerblue', legend=False)
        ax.fill_between(df['date'].values, 0.3, 0.5, color=dm_colors[1], alpha=1.0)
        ax.fill_between(df['date'].values, 0.2, 0.3, color=dm_colors[2], alpha=1.0)
        ax.fill_between(df['date'].values, 0.1, 0.2, color=dm_colors[3], alpha=1.0)
        ax.fill_between(df['date'].values, 0.0, 0.1, color=dm_colors[4], alpha=1.0)
        ax.fill_between(df['date'].values, 0.5, df[ind], color='dodgerblue', alpha=0.5)
        ax.legend([ind, 'Abnormally dry', 'Moderate drought', 'Severe drought', 'Extreme drought'], title=None, ncols=5, frameon=False, loc='center', bbox_to_anchor=(0.5, -0.55),fontsize = 7)
        
        #  Formatting
        ax.set_xlabel(None)
        ax.set_ylabel('Percentile', fontsize = 8)
        ax.set_ylim([0.0, 1.0])
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.set_title(plot_title, fontsize=9, fontweight = 'bold')
        [ax.spines[edge].set_visible(False) for edge in ['right', 'bottom', 'top', 'left']]
        
        
#This second part includes a function that creates the dial

# function plotting a colored dial
def dial(arrow_index, ax, figname = 'myDial'):
        
    """ Creates a dial plot of the percentile of the hydrologic region 
    
    Parameters
    ----------
    arrow_index : series
        The indicator percentile of the hydrologic region for the selected time period. Percentile should be converted to percentage
    ax : str
        The axes object to plot on
    figname : str
        The name of the figure
        
    Returns
    -------
    figure
        A dial plot of indicator percenitle of the hydrologic region
    """
    #US Drought colors
    colors = [
            (230/255, 0, 0, 1),                   # Red
            (255/255, 170/255, 0, 1),             # Orange
            (252/255, 211/255, 127/255, 1),       # Light Orange
            (255/255, 255/255, 0, 1),             # Yellow
            (171/255, 217/255, 233/255, 1),       # Light Blue
            (116/255, 173/255, 209/255, 1),       # Blue
            (69/255, 117/255, 180/255, 1),        # Darker Blue
            (128/255, 0, 128/255, 1),              # Purple
            (1, 1, 1, 1), # white
            (57/255, 57/255, 57/255, 1)] # dark gray
    

    # 400-element array with 0-200 for colored half and 201-400 for white half
    dcolors = np.zeros(400)
    dcolors[0:20] = 7
    dcolors[20:40] = 6
    dcolors[40:60] = 5
    dcolors[60:100] = 4
    dcolors[100:140] = 3
    dcolors[140:160] = 2
    dcolors[160:180] = 1
    dcolors[180:200] = 0
    dcolors[200:400] = 8

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
                         head_length=0.975, fc=colors[-1], ec=colors[-1])
    ax.add_artist(my_arrow)
    circlecenter = plt.Circle((0,0),0.04,color = colors[-1])    
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

def convert_input_date_format (date_str):
    """
    Input: String in the format: 'YYYY-MM' or 'MM-YYYY' or 'YYYY-M' or 'M-YYYY'.

    Returns:
        str: String representing the last day of the month in 'YYYY-MM-DD' format.
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m')
        date_obj.strftime('%Y%m%d')
    except ValueError:
        date_obj = datetime.strptime(date_str, '%m-%Y')
        date_obj.strftime('%Y%m%d')
    last_day_of_month = calendar.monthrange(date_obj.year, date_obj.month)[1]
    last_day_date = date_obj.replace(day=last_day_of_month)
    last_day_date = last_day_date.strftime('%Y-%m-%d')
    return last_day_date
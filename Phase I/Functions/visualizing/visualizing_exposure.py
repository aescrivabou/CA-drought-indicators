#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  4 22:25:08 2023

@author: alvar
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




#Hydrologic regions
hr = gpd.read_file('../../Data/Input_Data/HRs/i03_Hydrologic_Regions.shp')
hr = pd.concat([hr[1:8],hr[9:12]]).reset_index(drop=True)
hr = hr.to_crs('epsg:4326')

#Population
population = pd.read_csv('../../Data/Input_Data/Exposure&Vulnerability/population_hr_hist_exposure.csv')
hr = hr.merge(population,on='HR_NAME')

#Crop revenues
crop_rev = pd.read_csv('../../Data/Input_Data/Exposure&Vulnerability/crop_revenues_hr.csv')
hr = hr.merge(crop_rev,on='HR_NAME')

#Fig 1
centroids = hr.copy()
centroids.geometry = hr.centroid
centroids['size'] = centroids['Pop_1980'] / 10000

fig1 , ax1  = plt.subplots(1,1,figsize=(5,5))
hr.plot(ax = ax1, facecolor='lightgrey', edgecolor='dimgrey')
centroids.plot(ax = ax1, markersize='size', alpha = 0.8 , color = 'sandybrown', edgecolor='chocolate')

#Second legend: bubble size
l1 = plt.scatter([],[], s=(1/10000)*500000, facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
l2 = plt.scatter([],[], s=(1/10000)*2500000,facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
l3 = plt.scatter([],[], s=(1/10000)*10000000, facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
lableg = ["500,000", "2.5 million", "10 million"]
from matplotlib.legend import Legend
leg2 = Legend(ax1, [l1, l2, l3], lableg, bbox_to_anchor=(0.6, 0.55), frameon = True, fancybox = True, facecolor = 'white',  edgecolor = 'none' , framealpha = 1 , labelspacing = 2.5 , handletextpad=1.25 , borderpad=1.5 , title='Population' )
ax1.add_artist(leg2)

ax1.axis('off')
plt.suptitle('Population in 1980', fontsize = 14, fontweight='bold')
plt.savefig('population_1980.png', dpi=600)


centroids['size'] = centroids['Pop_2000'] / 10000

fig2 , ax2  = plt.subplots(1,1,figsize=(5,5))
hr.plot(ax = ax2, facecolor='lightgrey', edgecolor='dimgrey')
centroids.plot(ax = ax2, markersize='size', alpha = 0.8 , color = 'sandybrown', edgecolor='chocolate')

#Second legend: bubble size
l1 = plt.scatter([],[], s=(1/10000)*500000, facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
l2 = plt.scatter([],[], s=(1/10000)*2500000,facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
l3 = plt.scatter([],[], s=(1/10000)*10000000, facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
lableg = ["500,000", "2.5 million", "10 million"]
from matplotlib.legend import Legend
leg2 = Legend(ax2, [l1, l2, l3], lableg, bbox_to_anchor=(0.6, 0.55), frameon = True, fancybox = True, facecolor = 'white',  edgecolor = 'none' , framealpha = 1 , labelspacing = 2.5 , handletextpad=1.25 , borderpad=1.5 , title='Population' )
ax2.add_artist(leg2)

ax2.axis('off')
plt.suptitle('Population in 2000', fontsize = 14, fontweight='bold')
plt.savefig('population_2000.png', dpi=600)


centroids['size'] = centroids['Pop_2020'] / 10000

fig3 , ax3  = plt.subplots(1,1,figsize=(5,5))
hr.plot(ax = ax3, facecolor='lightgrey', edgecolor='dimgrey')
centroids.plot(ax = ax3, markersize='size', alpha = 0.8 , color = 'sandybrown', edgecolor='chocolate')
#Second legend: bubble size
l1 = plt.scatter([],[], s=(1/10000)*500000, facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
l2 = plt.scatter([],[], s=(1/10000)*2500000,facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
l3 = plt.scatter([],[], s=(1/10000)*10000000, facecolors = 'sandybrown', edgecolors='chocolate', alpha = 0.8)
lableg = ["500,000", "2.5 million", "10 million"]
from matplotlib.legend import Legend
leg2 = Legend(ax3, [l1, l2, l3], lableg, bbox_to_anchor=(0.6, 0.55), frameon = True, fancybox = True, facecolor = 'white',  edgecolor = 'none' , framealpha = 1 , labelspacing = 2.5 , handletextpad=1.25 , borderpad=1.5 , title='Population' )
ax3.add_artist(leg2)
ax3.axis('off')
plt.suptitle('Population in 2020', fontsize = 14, fontweight='bold')
plt.savefig('population_2020.png', dpi=600)



#Fig 4
centroids = hr.copy()
centroids.geometry = hr.centroid
centroids['size'] = centroids['Crop_revenues'] / 15

fig4 , ax4  = plt.subplots(1,1,figsize=(5,5))
hr.plot(ax = ax4, facecolor='lightgrey', edgecolor='dimgrey')
centroids.plot(ax = ax4, markersize='size', alpha = 0.8 , color = 'yellowgreen', edgecolor='olivedrab')
ax1.axis('off')
plt.suptitle('Crop revenues by hydrologic region', fontsize = 14, fontweight='bold')

#Second legend: bubble size
l1 = plt.scatter([],[], s=(1/15)*1000, facecolors = 'yellowgreen', edgecolors='olivedrab', alpha = 0.8)
l2 = plt.scatter([],[], s=(1/15)*5000,facecolors = 'yellowgreen', edgecolors='olivedrab', alpha = 0.8)
l3 = plt.scatter([],[], s=(1/15)*10000, facecolors = 'yellowgreen', edgecolors='olivedrab', alpha = 0.8)
lableg = ["$1 billion", "$5 billion", "$10 billion"]
from matplotlib.legend import Legend
leg2 = Legend(ax4, [l1, l2, l3], lableg, bbox_to_anchor=(0.6, 0.55), frameon = True, fancybox = True, facecolor = 'white',  edgecolor = 'none' , framealpha = 1 , labelspacing = 1.5 , handletextpad=1.25 , borderpad=1.5 , title='Crop revenues' )
ax4.add_artist(leg2)
ax4.axis('off')
plt.savefig('crop_revenues.png', dpi=600)


#Fig 4

hr['perc_perennials']  = pd.Series(["{0:.0f}%".format(val * 100) for val in hr['perennial_share']], index = hr.index)

fig5 , ax5  = plt.subplots(1,1,figsize=(5,5))
hr.plot(ax = ax5, facecolor='lightgrey', edgecolor='dimgrey')
hr.plot(column = 'perennial_share', ax = ax5, alpha = 0.4, cmap = 'RdYlGn_r')
ax1.axis('off')
plt.suptitle('Share of perennials by hydrologic region', fontsize = 14, fontweight='bold')
hr.apply(lambda x: ax5.annotate(text=x['perc_perennials'], xy=x.geometry.centroid.coords[0], ha='center', fontweight='bold' ), axis=1)

ax5.axis('off')
plt.savefig('perennial_share.png', dpi=600)



# =============================================================================
# centroids = world.copy()
# centroids.geometry = world.centroid
# centroids['size'] = centroids['pop_est'] / 1000000
# =============================================================================

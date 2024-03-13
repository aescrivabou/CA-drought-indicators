#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 16:36:51 2023

@author: alvar
"""

## install packages

import urllib
import zipfile
import os


## define downloading function
def download_pr_pet_data(indicators = ['pr', 'pet'],
             startyear = 1980,
             endyear = 2023,
             directory = '../../Data/Downloaded/'): 

    """Downloads raw hydroclimatic data 
    
    Parameters
    ----------
    indicators : list
        Potential hydroclimatic variables include:
            'pr' : precipitation (source: gridMET; format: netCDF; units: mm)
            'pet' : estimated evapotranspiration (source: gridMET; format: netCDF; units: mm)
    startyear : integer
        The beginning of the date range
    endyear : integer
        The end of the date range
    directory = str
        The path to the directory where the data will be downloaded
        
    
    Returns
    -------
    datafiles
        Selected indicators over the date range specified, organized
        by subfolder in the listed directory
        
    """
    
    year = list(range(startyear, endyear+1))
           
    ## downloading precipitation from gridMET
    
    if 'pr' in indicators:
        
        # create subfolder for downloaded files
        subfolder = "pr"
        path = os.path.join(directory, subfolder)
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)
        
        variables = ['pr']
        
        # loop to download files over defined period
        for i in variables:
            for j in year:
                url = 'https://www.northwestknowledge.net/metdata/data/' + '%s' %(i + '_') + '%s' %(j) + '.nc'
                filename = directory + '%s' %(i + '/') + '%s' %(i +'_') + '%s' %(j) + '.nc'
                urllib.request.urlretrieve(url, filename)
    
    ## downloading evapotranspiration from gridMET
    
    if 'pet' in indicators:
        
        # create subfolder for downloaded files
        subfolder = "pet"
        path = os.path.join(directory, subfolder)
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)

        
        variables = ['pet']
        
        # loop to download files over defined period
        for i in variables:
            for j in year:
                url = 'https://www.northwestknowledge.net/metdata/data/' + '%s' %(i + '_') + '%s' %(j) + '.nc'
                filename = directory + '%s' %(i + '/') + '%s' %(i +'_') + '%s' %(j) + '.nc'
                urllib.request.urlretrieve(url, filename)
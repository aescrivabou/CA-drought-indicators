# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 14:58:03 2021

@author: escriva
"""

import pandas as pd
import numpy as np
from scipy import stats
import datetime as dt
   
    
def func_for_tperiod(df, date_column = 'date', value_column = 'VALUE',
                     input_timestep = 'D', analysis_period = '1D',
                     function = 'percentile', grouping_column=None,
                     correcting_no_reporting = False, correcting_column = 'capacity',
                     baseline_start_year = 1991, baseline_end_year = 2020,
                     remove_zero = True):
    
    
    """Obtains percentiles or averages for each time window (analysis
    period) independently to avoid seasonality problems
    
    Parameters
    ----------
    df : dataframe
        The input dataframe that has a datetime and a value column to obtain
        the percentiles
    date_column : str
        The column label of the datetime column
    value_column : str
        The column label of the columns with the values
    input_timestep : str
        It's the timestep of the date_column in the dataframe. It only accepts
        'D' (for daily) or 'M' (for monthly)
    analysis_period : str
        It's the time window of the analysis for the percentiles or averages
        or other functions. It can be:
            "1D": daily analysis
            "1W": weekly analysis
            "2W": two-week analysis (14 days)
            "1M": monthly analysis
            "2M": two-monthl analysis
            "3M": three-month analysis
            "6M": six-month analysis
            "1Y": annual analysis
            "2Y": two-year analysis
            "3Y": three-year analysis
            "5Y": five-year analysis
    function : str
        The function to be obtained. By default percentile, but it can also
        be average
    grouping_column: str,optional
        The column label for groups (such as each station, each hydrologic region
        etc.) to obtain percentiles independently
    correcting_no_reporting : if True, weights the percentile function by 'weighting_column'
        to account for stations not reporting data some months
    correcting_column = the column to weight the percentiles. To obtain storage
        percentiles, we use the ratio of water stored with respect the capacity
        of the reservoir to obtain the percentile
    baseline_start_year = to obtain percentiles with a fixed baseline, this
        parameter indicates the beginning of the baseline
    baseline_end_year = to obtain percentiles with a fixed baseline, this
        parameter indicates the end of the baseline
    
    Returns
    -------
    dataframe
        the original dateframe adding the percentiles for the temporal period
    """
    
    #First we define a dictionary for combining the analysis_period and the input_timestep
    period_dict = {"1D": ['D', 1],
                   "1W": ['D', 7],
                   "2W": ['D', 14],
                   "1M": ['M', 1],
                   "2M": ['M', 2],
                   "3M": ['M', 3],
                   "6M": ['M', 6],
                   "1Y": ['M', 12],
                   "2Y": ['M', 24],
                   "3Y": ['M', 36],
                   "5Y": ['M', 60]                   
                   }
    
    if remove_zero == True:
        df = df.loc[df[value_column] != 0]
    df = df[df[value_column].notna()]
    
    if grouping_column is not None:
        df['reporting']=1
        df = df.groupby([grouping_column, date_column]).sum().reset_index()
        if correcting_no_reporting == True:
            df['percentage_of_reporting'] = df[value_column]/df[correcting_column]
            
    
    newdf = pd.DataFrame()
    for group in np.unique(df[grouping_column]):
        dfgroup = df.loc[df[grouping_column]==group]
    
        if (period_dict[analysis_period][0] == "D") and (input_timestep == 'M'):
            raise NameError('For the selected analysis_period, the input_timestep has to be daily (D)')
        elif (period_dict[analysis_period][0] == "D") and (input_timestep == 'D'):
            dfgroup = dfgroup.groupby(pd.Grouper(key=date_column, freq="1D")).mean().reset_index()
        else:
            dfgroup = dfgroup.groupby(pd.Grouper(key=date_column, freq="1M")).mean(numeric_only=True).reset_index()
            
        #Add a column with the average value for the period of analysis
        dfgroup['value_period'] = dfgroup[value_column].rolling(period_dict[analysis_period][1]).mean(nan='Ignore')
        dfgroup['month'] = pd.DatetimeIndex(dfgroup[date_column]).month
        if period_dict[analysis_period][0] == "M":
            dfgroup['day']=1
        elif period_dict[analysis_period][0] == "D":
            dfgroup['day'] = pd.DatetimeIndex(dfgroup[date_column]).day
        
        dfgroup[grouping_column]= group
        #Percentiles or averages
        for monthnumber in np.arange(1,13):
            for daynumber in np.unique(dfgroup.day):
                dfmonth = dfgroup.loc[(dfgroup.month == monthnumber) & (dfgroup.day == daynumber)]
                if function == 'percentile':
                    if (baseline_start_year is not None) & (baseline_end_year is not None):
                        dfmonth_for_arr = dfmonth.loc[(dfmonth[date_column].dt.year>(baseline_start_year-1)) & (dfmonth[date_column].dt.year<(baseline_end_year+1))]
                        arr = dfmonth_for_arr['value_period']
                        dfmonth[function] = 0.01*stats.percentileofscore(arr, dfmonth['value_period'])
                        if correcting_no_reporting==True:
                            arr2 = dfmonth_for_arr['percentage_of_reporting']
                            dfmonth['corrected_percentile'] = 0.01*stats.percentileofscore(arr2, dfmonth['percentage_of_reporting'])
                            dfmonth['corrected_value'] = dfmonth['percentage_of_reporting'] * dfmonth.capacity.max()
                    else:
                        dfmonth[function] = dfmonth.value_period.rank(pct=True)
                elif function == 'average':
                    dfmonth[function] = dfmonth.value_period
                newdf = pd.concat([newdf, dfmonth])
                newdf = newdf.sort_values(by=date_column).reset_index(drop=True)
        
    #Return result
    newdf['day'] = pd.DatetimeIndex(newdf[date_column]).day
    if grouping_column is not None:
        newdf = newdf.sort_values(by = [grouping_column, date_column]).reset_index(drop=True)
    return newdf
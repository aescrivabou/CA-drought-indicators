#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 10:36:28 2023

@author: alvar
"""

import pandas as pd
import matplotlib.pyplot as plt

#DWR's Water Balance Data downloaded from: https://data.cnra.ca.gov/dataset/water-plan-water-balance-data

WB_2002 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2002-HR.csv')
WB_2003 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2003-HR.csv')
WB_2004 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2004-HR.csv')
WB_2005 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2005-HR.csv')
WB_2006 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2006-HR.csv')
WB_2007 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2007-HR.csv')
WB_2008 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2008-HR.csv')
WB_2009 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2009-HR.csv')
WB_2010 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2010-HR.csv')
WB_2011 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2011-HR.csv')
WB_2012 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2012-HR.csv')
WB_2013 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2013-HR.csv')
WB_2014 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2014-HR.csv')
WB_2015 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2015-HR.csv')
WB_2016 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2016-HR.csv')
WB_2018 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2018-HR.csv')
WB_2019 = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CA-DWR-WaterBalance-Level2-DP-1000-2019-HR.csv')

crosswalk = pd.read_csv('../Data/Input_Data/DWR_WaterBalances/CrosswalkSupplyCategories.csv') 

df = pd.concat([WB_2002,WB_2003, WB_2004, WB_2005, WB_2006, WB_2007, WB_2008,
                WB_2009, WB_2010, WB_2011, WB_2012, WB_2013, WB_2014, WB_2015,
                WB_2016, WB_2018, WB_2019])
df = df.merge(crosswalk, on='CategoryD', how = 'outer')
df = df.rename(columns = {"KAcreFt":"taf"})

Years = [2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2018,2019]
Region = list(df['HR'].unique())

def select_hr_year(df, hr='Sacramento River', year = 2011, output = 'supply', sector = None):
    """TBD
    
    Parameters
    ----------
    df : dataframe
        The input dataframe that has all the supply portfolios data (df above)
    hr : str
        The hydrologic region
    year : integer
        The year to do the calculations
    output : str
        The output to be calculated. Can be "supply" to obtain the supply portfolio,
        or "use" to obtain the percentages of use per sector
    sector: str
        The sector. If None, we the calculations are for all the sectors, it can
        be also 'Agricultural' or 'Urban', to obtain specific portfolios for
        these sectors
    Returns
    -------
    dataframe
        The supply portfolio or sectoral use for the given year and hydrologic
        region
    """
    
    newdf = df.loc[(df.HR == hr) & (df.Year == year)]
    if sector is not None:
        newdf = newdf.loc[newdf.CategoryA == sector]
    if output == 'supply':
        newdf = newdf.groupby('SupplyCategory').sum()
        newdf.Year = year
    elif output == 'use':
        newdf= newdf.groupby('UseCategory').sum()
        newdf.Year = year
        
    newdf = newdf.sort_values(by='taf', ascending = False)
    if sector is None:
        newdf['sector'] = 'All'
    else:
        newdf['sector'] = sector
    if output == 'use':
        newdf = newdf.drop(columns='sector')    
    newdf['HR']=hr
    return newdf

supply_portfolios = pd.DataFrame()

for reg in Region:
    for sector in [None]: #, 'Agriculture', 'Urban']:
        for year in Years:
            supply_portfolios= pd.concat([supply_portfolios, select_hr_year(df,
                                        hr=reg, year=year, sector = sector)])
urban_portfolios = pd.DataFrame()
for reg in Region:
    for sector in ['Urban']:
        for year in Years:
            urban_portfolios= pd.concat([urban_portfolios, select_hr_year(df,
                                        hr=reg, year=year, sector = sector)])
            
ag_portfolios = pd.DataFrame()
for reg in Region:
    for sector in ['Agriculture']:
        for year in Years:
            ag_portfolios= pd.concat([ag_portfolios, select_hr_year(df,
                                        hr=reg, year=year, sector = sector)])


sectoral_use = pd.DataFrame()
for reg in Region:
    for sector in [None]: #, 'Agriculture', 'Urban']:
        for year in Years:
            sectoral_use = pd.concat([sectoral_use, select_hr_year(df,hr=reg,
                                    year=year, output = 'use', sector = sector)])

avg_sup_portfolios = supply_portfolios.reset_index().groupby(['HR','SupplyCategory']).mean().reset_index()
avg_sup_portfolios = avg_sup_portfolios.drop(columns = 'Year')
avg_sectoral_use = sectoral_use.reset_index().groupby(['HR','UseCategory']).mean().reset_index()
avg_sectoral_use = avg_sectoral_use.drop(columns = 'Year')

supply_portfolios.to_csv('../Data/Processed/supply_portfolios/supply_portfolios.csv')
avg_sup_portfolios.to_csv('../Data/Processed/supply_portfolios/avg_supply_portfolios.csv')

urban_portfolios.to_csv('../Data/Processed/supply_portfolios/urban_portfolios.csv')

ag_portfolios.to_csv('../Data/Processed/supply_portfolios/ag_portfolios.csv')

sectoral_use.to_csv('../Data/Processed/supply_portfolios/sectoral_use.csv')
avg_sectoral_use.to_csv('../Data/Processed/supply_portfolios/avg_sectoral_use.csv')




# =============================================================================
# 
# 
# for i in Years:
#     for j in Region:
#         subset = df[(df["Year"] == i) & (df["HR"] == '%s' %(j))]
# 
#         #agriculture
#         ag = [[i, '%s' %(j), 'ag', 'Local Deliveries', subset['KAcreFt'][(subset['D'] == "SPL1A")].sum()], 
#               [i, '%s' %(j), 'ag', 'Local Imported Deliveries', subset['KAcreFt'][(subset['D'] == "SPL3A")].sum()],
#               [i, '%s' %(j), 'ag', 'Colorado River Deliveries', subset['KAcreFt'][(subset['D'] == "SPL11A")].sum()],
#               [i, '%s' %(j), 'ag', 'CVP Base Deliveries', subset['KAcreFt'][(subset['D'] == "SPL13A")].sum()], 
#               [i, '%s' %(j), 'ag', 'CVP Project Deliveries', subset['KAcreFt'][(subset['D'] == "SPL14A")].sum()],
#               [i, '%s' %(j), 'ag', 'Other Federal Deliveries', subset['KAcreFt'][(subset['D'] == "SPL15A")].sum()], 
#               [i, '%s' %(j), 'ag', 'SWP Deliveries', subset['KAcreFt'][(subset['D'] == "SPL12A")].sum()], 
#               [i, '%s' %(j), 'ag', 'Water from Refineries', subset['KAcreFt'][(subset['D'] == "SPL17A")].sum()], 
#               [i, '%s' %(j), 'ag', 'Groundwater Net Withdrawal', (subset['KAcreFt'][(subset['D'] == "SPL4A") |
#                                                                                    (subset['D'] == "SPL5A") |
#                                                                                    (subset['D'] == "SPL6A")].sum()) - 
#                                                                    (subset['KAcreFt'][(subset['D'] == "AG5") |
#                                                                                    (subset['D'] == "AG7") |
#                                                                                    (subset['D'] == "AG22")].sum())],
#               [i, '%s' %(j), 'ag', 'Deep Percolation of Surface and GW', subset['KAcreFt'][(subset['D'] == "AG5") |
#                                                                                            (subset['D'] == "AG7") |
#                                                                                            (subset['D'] == "AG22")].sum()], 
#               [i, '%s' %(j), 'ag', 'Return Flow from Carryover Storage', subset['KAcreFt'][(subset['D'] == "SPL2D1")].sum()], 
#               [i, '%s' %(j), 'ag', 'Reuse Surface Water', subset['KAcreFt'][(subset['D'] == "AG8") |
#                                                                                      (subset['D'] == "AG21")].sum()], 
#               [i, '%s' %(j), 'ag', 'Recycled Water', 'na'],
#               [i, '%s' %(j), 'ag', 'Desalination', subset['KAcreFt'][(subset['D'] == "SPL16A") |
#                                                                               (subset['D'] == "SPL10A")].sum()],  
#               [i, '%s' %(j), 'ag', 'Inflow Drainage from other HR', subset['KAcreFt'][(subset['D'] == "SPL2C1") |
#                                                                                            (subset['D'] == "SPL18A") |
#                                                                                            (subset['D'] == "SPL19A")].sum()]]
#         #urban
#         urban = [[i, '%s' %(j), 'urban', 'Local Deliveries', subset['KAcreFt'][(subset['D'] == "SPL1C")].sum()], 
#               [i, '%s' %(j), 'urban', 'Local Imported Deliveries', subset['KAcreFt'][(subset['D'] == "SPL3C")].sum()],
#               [i, '%s' %(j), 'urban', 'Colorado River Deliveries', subset['KAcreFt'][(subset['D'] == "SPL11C")].sum()],
#               [i, '%s' %(j), 'urban', 'CVP Base Deliveries', subset['KAcreFt'][(subset['D'] == "SPL13C")].sum()],
#               [i, '%s' %(j), 'urban', 'CVP Project Deliveries', subset['KAcreFt'][(subset['D'] == "SPL14C")].sum()],
#               [i, '%s' %(j), 'urban', 'Other Federal Deliveries', subset['KAcreFt'][(subset['D'] == "SPL15C")].sum()], 
#               [i, '%s' %(j), 'urban', 'SWP Deliveries', subset['KAcreFt'][(subset['D'] == "SPL12C")].sum()], 
#               [i, '%s' %(j), 'urban', 'Water from Refineries', subset['KAcreFt'][(subset['D'] == "SPL17C")].sum()], 
#               [i, '%s' %(j), 'urban', 'Groundwater Net Withdrawal', (subset['KAcreFt'][(subset['D'] == "SPL4C") |
#                                                                                  (subset['D'] == "SPL5C") |
#                                                                                  (subset['D'] == "SPL6C")].sum()) -
#                                                                                (subset['KAcreFt'][(subset['D'] == "URB12") |
#                                                                                  (subset['D'] == "URB14") |
#                                                                                    (subset['D'] == "URB30")].sum())],
#               [i, '%s' %(j), 'urban', 'Deep Percolation of Surface and GW', subset['KAcreFt'][(subset['D'] == "URB12") |
#                                                                                            (subset['D'] == "URB14") |
#                                                                                            (subset['D'] == "URB30")].sum()], 
#               [i, '%s' %(j), 'urban', 'Return Flow from Carryover Storage', subset['KAcreFt'][(subset['D'] == "SPL2D3")].sum()], 
#               [i, '%s' %(j), 'urban', 'Reuse Surface Water', subset['KAcreFt'][(subset['D'] == "URB15A") |
#                                                                                      (subset['D'] == "URB29")].sum()], 
#               [i, '%s' %(j), 'urban', 'Recycled Water', subset['KAcreFt'][(subset['D'] == "URB15B") |
#                                                                                      (subset['D'] == "URB15C")].sum()],
#               [i, '%s' %(j), 'urban', 'Desalination', subset['KAcreFt'][(subset['D'] == "SPL16C") |
#                                                                               (subset['D'] == "SPL10C")].sum()],  
#               [i, '%s' %(j), 'urban', 'Inflow Drainage from other HR', subset['KAcreFt'][(subset['D'] == "SPL2C3") |
#                                                                                            (subset['D'] == "SPL18C") |
#                                                                                            (subset['D'] == "SPL19C")].sum()]]
#         #managed wetlands
#         wetlands = [[i, '%s' %(j), 'wetlands', 'Local Deliveries', subset['KAcreFt'][(subset['D'] == "SPL1B")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Local Imported Deliveries', subset['KAcreFt'][(subset['D'] == "SPL3B")].sum()],
#               [i, '%s' %(j), 'wetlands', 'Colorado River Deliveries', subset['KAcreFt'][(subset['D'] == "SPL11B")].sum()],
#               [i, '%s' %(j), 'wetlands', 'CVP Base Deliveries', subset['KAcreFt'][(subset['D'] == "SPL13B")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'CVP Project Deliveries', subset['KAcreFt'][(subset['D'] == "SPL14B")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Other Federal Deliveries', subset['KAcreFt'][(subset['D'] == "SPL15B")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'SWP Deliveries', subset['KAcreFt'][(subset['D'] == "SPL12B")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Water from Refineries', subset['KAcreFt'][(subset['D'] == "SPL17B")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Groundwater Net Withdrawal', (subset['KAcreFt'][(subset['D'] == "SPL4B") |
#                                                                                    (subset['D'] == "SPL5B") |
#                                                                                    (subset['D'] == "SPL6B")].sum()) - 
#                                                                            (subset['KAcreFt'][(subset['D'] == "MW3") |
#                                                                                    (subset['D'] == "MW5") |
#                                                                                    (subset['D'] == "MW20")].sum())],
#               [i, '%s' %(j), 'wetlands', 'Deep Percolation of Surface and GW', subset['KAcreFt'][(subset['D'] == "MW3") |
#                                                                                            (subset['D'] == "MW5") |
#                                                                                            (subset['D'] == "MW20")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Return Flow from Carryover Storage', subset['KAcreFt'][(subset['D'] == "SPL2D2")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Reuse Surface Water', subset['KAcreFt'][(subset['D'] == "MW6") |
#                                                                                      (subset['D'] == "MW19")].sum()], 
#               [i, '%s' %(j), 'wetlands', 'Recycled Water', 'na'],
#               [i, '%s' %(j), 'wetlands', 'Desalination', subset['KAcreFt'][(subset['D'] == "SPL16B") |
#                                                                               (subset['D'] == "SPL10B")].sum()],  
#               [i, '%s' %(j), 'wetlands', 'Inflow Drainage from other HR', subset['KAcreFt'][(subset['D'] == "SPL2C2") |
#                                                                                            (subset['D'] == "SPL18B")].sum()]]
#         #instream flow
#         instream = [[i, '%s' %(j), 'instream', 'Local Deliveries', subset['KAcreFt'][(subset['D'] == "SPL1D")].sum()], 
#               [i, '%s' %(j), 'instream', 'Local Imported Deliveries', subset['KAcreFt'][(subset['D'] == "SPL3D")].sum()],
#               [i, '%s' %(j), 'instream', 'Colorado River Deliveries', subset['KAcreFt'][(subset['D'] == "SPL11D")].sum()],
#                [i, '%s' %(j), 'instream', 'CVP Base Deliveries', subset['KAcreFt'][(subset['D'] == "SPL13D")].sum()], 
#               [i, '%s' %(j), 'instream', 'CVP Project Deliveries', subset['KAcreFt'][(subset['D'] == "SPL14D")].sum()],
#               [i, '%s' %(j), 'instream', 'Other Federal Deliveries', subset['KAcreFt'][(subset['D'] == "SPL15D")].sum()], 
#               [i, '%s' %(j), 'instream', 'SWP Deliveries', subset['KAcreFt'][(subset['D'] == "SPL12D")].sum()], 
#               [i, '%s' %(j), 'instream', 'Water from Refineries', subset['KAcreFt'][(subset['D'] == "SPL17D")].sum()], 
#               [i, '%s' %(j), 'instream', 'Groundwater Net Withdrawal', subset['KAcreFt'][(subset['D'] == "SPL4D") |
#                                                                                            (subset['D'] == "SPL5D") |
#                                                                                            (subset['D'] == "SPL6D")].sum()],
#               [i, '%s' %(j), 'instream', 'Deep Percolation of Surface and GW', 'na'], 
#               [i, '%s' %(j), 'instream', 'Return Flow from Carryover Storage', 'na'], 
#               [i, '%s' %(j), 'instream', 'Reuse Surface Water', subset['KAcreFt'][(subset['D'] == "IFR2")].sum()], 
#               [i, '%s' %(j), 'instream', 'Recycled Water', 'na'],
#               [i, '%s' %(j), 'instream', 'Desalination', subset['KAcreFt'][(subset['D'] == "SPL16D") |
#                                                                               (subset['D'] == "SPL10D")].sum()],  
#               [i, '%s' %(j), 'instream', 'Inflow Drainage from other HR', subset['KAcreFt'][(subset['D'] == "SPL2C4") |
#                                                                                            (subset['D'] == "SPL18D")].sum()]]
#         #wild and scenic flows
#         wild = [[i, '%s' %(j), 'wild', 'Local Deliveries', subset['KAcreFt'][(subset['D'] == "SPL1E")].sum()], 
#               [i, '%s' %(j), 'wild', 'Local Imported Deliveries', subset['KAcreFt'][(subset['D'] == "SPL3E")].sum()],
#               [i, '%s' %(j), 'wild', 'Colorado River Deliveries', subset['KAcreFt'][(subset['D'] == "SPL11E")].sum()],
#               [i, '%s' %(j), 'wild', 'CVP Base Deliveries', subset['KAcreFt'][(subset['D'] == "SPL13E")].sum()], 
#               [i, '%s' %(j), 'wild', 'CVP Project Deliveries', subset['KAcreFt'][(subset['D'] == "SPL14E")].sum()],
#               [i, '%s' %(j), 'wild', 'Other Federal Deliveries', subset['KAcreFt'][(subset['D'] == "SPL15E")].sum()], 
#               [i, '%s' %(j), 'wild', 'SWP Deliveries', subset['KAcreFt'][(subset['D'] == "SPL12E")].sum()], 
#               [i, '%s' %(j), 'wild', 'Water from Refineries', subset['KAcreFt'][(subset['D'] == "SPL17E")].sum()], 
#               [i, '%s' %(j), 'wild', 'Groundwater Net Withdrawal', subset['KAcreFt'][(subset['D'] == "SPL4E") |
#                                                                                            (subset['D'] == "SPL5E") |
#                                                                                            (subset['D'] == "SPL6E")].sum()],
#               [i, '%s' %(j), 'wild', 'Deep Percolation of Surface and GW', 'na'], 
#               [i, '%s' %(j), 'wild', 'Return Flow from Carryover Storage', 'na'], 
#               [i, '%s' %(j), 'wild', 'Reuse Surface Water', subset['KAcreFt'][(subset['D'] == "WSR2")].sum()], 
#               [i, '%s' %(j), 'wild', 'Recycled Water', 'na'], 
#               [i, '%s' %(j), 'wild', 'Desalination', subset['KAcreFt'][(subset['D'] == "SPL16E")].sum()],  
#               [i, '%s' %(j), 'wild', 'Inflow Drainage from other HR', subset['KAcreFt'][(subset['D'] == "SPL2C5") |
#                                                                                            (subset['D'] == "SPL18E")].sum()]]
#         #required delta outflow
#         delta = [[i, '%s' %(j), 'delta', 'Local Deliveries', subset['KAcreFt'][(subset['D'] == "SPL1F")].sum()], 
#               [i, '%s' %(j), 'delta', 'Local Imported Deliveries', subset['KAcreFt'][(subset['D'] == "SPL3F")].sum()],
#               [i, '%s' %(j), 'delta', 'Colorado River Deliveries', subset['KAcreFt'][(subset['D'] == "SPL11F")].sum()],
#               [i, '%s' %(j), 'delta', 'CVP Base Deliveries', subset['KAcreFt'][(subset['D'] == "SPL13F")].sum()], 
#               [i, '%s' %(j), 'delta', 'CVP Project Deliveries', subset['KAcreFt'][(subset['D'] == "SPL14F")].sum()],
#               [i, '%s' %(j), 'delta', 'Other Federal Deliveries', subset['KAcreFt'][(subset['D'] == "SPL15F")].sum()], 
#               [i, '%s' %(j), 'delta', 'SWP Deliveries', subset['KAcreFt'][(subset['D'] == "SPL12F")].sum()], 
#               [i, '%s' %(j), 'delta', 'Water from Refineries', subset['KAcreFt'][(subset['D'] == "SPL17F")].sum()], 
#               [i, '%s' %(j), 'delta', 'Groundwater Net Withdrawal', subset['KAcreFt'][(subset['D'] == "SPL4F") |
#                                                                                            (subset['D'] == "SPL5F") |
#                                                                                            (subset['D'] == "SPL6F")].sum()],
#               [i, '%s' %(j), 'delta', 'Deep Percolation of Surface and GW', 'na'], 
#               [i, '%s' %(j), 'delta', 'Return Flow from Carryover Storage', 'na'], 
#               [i, '%s' %(j), 'delta', 'Reuse Surface Water', 'na'], 
#               [i, '%s' %(j), 'delta', 'Recycled Water', 'na'],
#               [i, '%s' %(j), 'delta', 'Desalination', subset['KAcreFt'][(subset['D'] == "SPL16F")].sum()],  
#               [i, '%s' %(j), 'delta', 'Inflow Drainage from other HR', subset['KAcreFt'][(subset['D'] == "SPL2C6") |
#                                                                                            (subset['D'] == "SPL18F")].sum()]]
#         rows = ag + urban + wetlands + instream + wild + delta
#         data = pd.DataFrame(rows, columns=['Year', 'HR', 'Sector' , 'Source' , 'AF'])
#         portfolios = portfolios.append(data)
#         
# 
# #average
# water = pd.to_numeric(portfolios["AF"], errors='coerce')
# portfolios['water'] = water
# summary = portfolios.groupby(["HR", "Sector", "Source"]).mean()
# byyear = pd.pivot_table(portfolios,columns=["Year"],index=["HR","Sector","Source"])
# 
# # =============================================================================
# # #export
# # df.to_csv('W:/Projects/NIDIS/Data/DWR Supply Portfolios/waterbalances.csv')
# # portfolios.to_csv('W:/Projects/NIDIS/Data/DWR Supply Portfolios/portfolios.csv')
# # summary.to_csv('W:/Projects/NIDIS/Data/DWR Supply Portfolios/portfolio_summary.csv')
# # =============================================================================
# 
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:09:38 2023

@author: alvar
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

#1. PUTTING INDICATORS DATA TOGETHER

#Reading indicators data
surface_data = pd.read_csv('../../Data/Processed/surface_water_drougth_indicator/total_storage_percentiles.csv')
surface_data['date'] = pd.to_datetime(surface_data.date)
gwdata = pd.read_csv('../../Data/Processed/groundwater/state_wells_regional_analysis.csv')
gwdata['date']=pd.to_datetime(gwdata.date)
imports = pd.read_csv('../../Data/Processed/imports/total_storage_percentiles.csv')
imports['date']=pd.to_datetime(imports.date)
imports = imports.loc[imports.export_basin=='delta_basin']
imports = imports.rename(columns={'res_percentile':'res_percentile_imports', 'SWDI':'SWDI_imports', 'snow_pctl': 'snow_pctl_imports'})

#Reading evapotranspiration
et_data = pd.read_csv('../../Data/Processed/pr_pet_hr_indicators/pet_percentile.csv')
et_data['date']=pd.to_datetime(et_data.date)
et_data['wy'] = et_data.date.dt.year
et_data.loc[et_data.date.dt.month>9, 'wy'] = et_data.date.dt.year + 1
et_wy = et_data.loc[et_data.HR_NAME == 'San Joaquin River']
et_wy = et_wy.groupby('wy').mean().reset_index()
et_wy = et_wy.loc[et_wy.wy>1990]
et_wy['anomaly']= et_wy.value_period/et_wy.value_period.mean()

#Adding water year to indicators and grouping by water year
surface_data['wy'] = surface_data.date.dt.year
surface_data.loc[surface_data.date.dt.month>9, 'wy'] = surface_data.date.dt.year + 1
#obtain data for water years
surface_data_wy = surface_data.groupby(['HR_NAME' ,'wy']).mean().reset_index()
surface_data_wy = surface_data_wy[['HR_NAME', 'wy', 'res_percentile', 'SWDI', 'snow_pctl']]
#gw data
gwdata['wy'] = gwdata.date.dt.year
gwdata.loc[gwdata.date.dt.month>9, 'wy'] = gwdata.date.dt.year + 1
#gw data for water year
gwdata_wy = gwdata.loc[gwdata.semester==2].reset_index(drop = True)
gwdata_wy = gwdata_wy.loc[gwdata_wy.stat == 'median']
gwdata_wy = gwdata_wy[['HR_NAME', 'pctl_gwchange_corr', 'pctl_cumgwchange_corr', 'reporting2', 'wy', 'gwchange']]
#same for imports
imports['wy'] = imports.date.dt.year
imports.loc[imports.date.dt.month>9, 'wy'] = imports.date.dt.year + 1
#obtain data for water years
imports_wy = imports.groupby(['export_basin' ,'wy']).mean().reset_index()
imports_wy = imports_wy[['export_basin', 'wy', 'res_percentile_imports', 'SWDI_imports', 'snow_pctl_imports']]


#2. MERGING INDICATORS WITH SUPPLY PORTFOLIO (INCLUDING MODIFYING CVP DATA)

#Reading supply portfolio data (data is for water years)
supply_portfolios = pd.read_csv('../../Data/Processed/supply_portfolios/supply_portfolios.csv')

#Merging data for one hydro region
def merging_hydro_region_data(df1 = supply_portfolios, df2 = surface_data_wy, 
                              df3 = gwdata_wy, hr = 'San Joaquin River'):
    hr_data = df1.loc[df1.HR == hr].reset_index(drop=True)
    hr_data = hr_data.pivot(index = 'SupplyCategory', columns = 'Year', values = 'taf')
    hr_data = hr_data.transpose().reset_index()
    hr_data = hr_data.merge(df2.loc[df2.HR_NAME==hr].reset_index(drop=True), left_on = 'Year', right_on = 'wy')
    hr_data = hr_data.merge(df3.loc[df3.HR_NAME==hr].reset_index(drop=True), on = ['wy','HR_NAME'])
    return hr_data

sjr_data = merging_hydro_region_data()
sjr_data = sjr_data.merge(imports_wy, on='wy')

#Separating CVP data into local sources and imports
cvp_data = pd.read_csv('../../Data/Input_Data/DWR_WaterBalances/cvp_annual_wy.csv')
cvp_data = cvp_data.rename(columns={'year': 'wy'})
cvp_data = cvp_data.rename(columns={'deliveries_wy_weighted': 'cvp_af'})
cvp_data['source'] = 'delta_imports'
cvp_data.loc[(cvp_data.cvp_branch=='Friant-Kern Canal') | (cvp_data.cvp_branch=='Madera Canal and Millerton Lake'), 'source'] = 'local_sj'
cvp_data.loc[(cvp_data.cvp_branch=='Sacramento River') | (cvp_data.cvp_branch=='Tehama-Colusa Canal'), 'source'] = 'local_sac'
cvp_data = cvp_data.groupby(['wy','source', 'hydrologic_region']).sum().reset_index()
sjv_imports = cvp_data.loc[(cvp_data.source=='delta_imports')]
sjv_imports = sjv_imports.loc[sjv_imports.hydrologic_region=='San Joaquin River']
sjv_imports = sjv_imports[['wy','cvp_af']]

sjr_data = sjr_data.merge(sjv_imports, on = 'wy')
sjr_data['cvp_af'] = 0.001*sjr_data.cvp_af
sjr_data['extra_federal'] = sjr_data.Federal - sjr_data.cvp_af
sjr_data['final_local'] = sjr_data.extra_federal + sjr_data.LocalSupplies
sjr_data['final_imports']=sjr_data.cvp_af + sjr_data.SWP
sjr_data = sjr_data.merge(et_wy[['wy','anomaly']],on='wy')


#3. OBTAINING PARAMETERS TO ESTIMTE SUPPLIES AS A FUNCTION OF INDICATORS

#Obtaining parameters for the supplies
#Fitting local supplies
y = sjr_data.final_local

x = sjr_data[['SWDI']]
x['log_swdi']=np.log(sjr_data.SWDI)
x = sm.add_constant(x)

model = sm.OLS(y, x)
results = model.fit()
print(results.summary())
res_y = results.predict(x)


#Fitting imports
y2 = sjr_data.final_imports

x2 = sjr_data[['SWDI_imports']]
x2['SWDI_imports_log'] = np.log(sjr_data.SWDI)

x2 = sm.add_constant(x2)
model2 = sm.OLS(y2, x2)
results2 = model2.fit()
print(results2.summary())
res_y2 = results2.predict(x2)


sjresults = sjr_data[['wy','final_local','final_imports']]
sjresults['est_local'] = res_y
sjresults['est_imports'] = res_y2

sjresults = sjresults.set_index('wy')

#Fitting groundwater
y3 = sjr_data.Groundwater

x3 = sjr_data[['pctl_gwchange_corr']]
x3['surf_water'] = res_y + res_y2
x3 = x3[['surf_water', 'pctl_gwchange_corr']]

x3 = sm.add_constant(x3)
model3 = sm.OLS(y3, x3)
results3 = model3.fit()
print(results3.summary())
res_y3 = results3.predict(x3)


sjlocal = sjr_data[['wy','final_local']]
sjimports = sjr_data[['wy', 'final_imports']]
sjgw = sjr_data[['wy', 'Groundwater', 'gwchange']]
                   
sjlocal['est_local'] = res_y
sjimports['est_imports'] = res_y2
sjgw['est_gw'] = res_y3

sjlocal = sjlocal.set_index('wy')
sjimports = sjimports.set_index('wy')
sjgw = sjgw.set_index('wy')

#4. OBTAINING DEMAND ANOMALY AND SUSTAINABLE GROUNDWATER USE
sjresults = sjresults.merge(sjgw, left_index = True, right_index = True)
et_wy_sel = et_wy[['wy','anomaly']]
sjresults = sjresults.merge(et_wy_sel,left_index=True, right_on='wy')
sjresults['total_deliveries'] = sjresults.est_local + sjresults.est_imports + sjresults.est_gw
sjresults['demand_anomaly'] = sjresults.total_deliveries.mean() * (1 - sjresults.anomaly)

#Fitting overdraft
y4 = sjresults.Groundwater

x4 = sjresults[['gwchange']]

x4 = sm.add_constant(x4)
model4 = sm.OLS(y4, x4)
results4 = model4.fit()
print(results4.summary())
res_y4 = results4.predict(x4)

sjresults['overdraft_limit'] = results4.params[0]
sjresults['change_gw_storage'] = - (sjresults.est_gw - sjresults.overdraft_limit)
sjresults['eff_deliveries']= sjresults.total_deliveries + sjresults.demand_anomaly + sjresults.change_gw_storage
sjresults['shortages']= sjresults.eff_deliveries.max() - sjresults.eff_deliveries


#5. OBTAINNING SYSTEM DROUGHT INDICATOR FOR THE WHOLE SERIES
#Complex
drought_indicators = surface_data.loc[surface_data.HR_NAME=='San Joaquin River'].reset_index(drop=True)[['date', 'SWDI']]
drought_indicators = drought_indicators.merge(imports[['date', 'SWDI_imports']], on = 'date')
drought_indicators = drought_indicators.merge(gwdata.loc[gwdata.HR_NAME=='San Joaquin River'].reset_index(drop=True)[['date', 'pctl_gwchange_corr']], on = 'date', how = 'outer')
drought_indicators['pctl_gwchange_corr'] = drought_indicators['pctl_gwchange_corr'].interpolate()
drought_indicators['SWDI_imports_log'] = np.log(drought_indicators.SWDI_imports)
drought_indicators['log_swdi'] = np.log(drought_indicators.SWDI)
drought_indicators = drought_indicators.merge(et_data.loc[et_data.HR_NAME=='San Joaquin River'].reset_index(drop=True)[['date', 'value_period']], on = 'date', how = 'outer')


#Estimating local sources
#x1prim = drought_indicators[['SWDI_x', 'SWDI_x_sq']]
x1prim = drought_indicators[['SWDI', 'log_swdi']]
x1prim = sm.add_constant(x1prim)
drought_indicators['est_local'] = results.predict(x1prim)

#Estimating imports
x2prim = drought_indicators[['SWDI_imports','SWDI_imports_log']]
x2prim = sm.add_constant(x2prim)
drought_indicators['est_imports'] = results2.predict(x2prim)

#Estimating groundwater
x3prim = drought_indicators[['pctl_gwchange_corr']]
x3prim['surf_water'] = drought_indicators.est_local + drought_indicators.est_imports
x3prim = x3prim[['surf_water', 'pctl_gwchange_corr']]
x3prim = sm.add_constant(x3prim)
drought_indicators['est_gw'] = results3.predict(x3prim)

#Est total deliveries
drought_indicators['total_deliveries'] = drought_indicators.est_local + drought_indicators.est_imports + drought_indicators.est_gw

#Demand anomaly
drought_indicators['anomaly'] = drought_indicators.value_period/drought_indicators.value_period.mean()
drought_indicators['demand_anomaly'] = drought_indicators.total_deliveries * (1 - drought_indicators.anomaly)

#Overdraft
drought_indicators['overdraft_limit'] = results4.params[0]
drought_indicators['change_gw_storage'] = - (drought_indicators.est_gw - drought_indicators.overdraft_limit)
drought_indicators['eff_deliveries']= drought_indicators.total_deliveries + drought_indicators.demand_anomaly + drought_indicators.change_gw_storage
drought_indicators['shortages'] = drought_indicators.eff_deliveries.max() - drought_indicators.eff_deliveries

#wy data
drought_indicators['wy'] = drought_indicators.date.dt.year
drought_indicators.loc[drought_indicators.date.dt.month>9, 'wy'] = drought_indicators.date.dt.year + 1
drought_indicators_wy = drought_indicators.groupby('wy').mean()

from percentile_average_function import func_for_tperiod

drought_indicators = drought_indicators.dropna()
drought_indicators['id'] = 'complex'

drought_portfolio_percentile = func_for_tperiod(drought_indicators, date_column = 'date', value_column = 'shortages',
                                                input_timestep = 'M', analysis_period = '1M', function = 'percentile',
                                                grouping_column='id', correcting_no_reporting = False, correcting_column = 'capacity',
                                                baseline_start_year = 2001, baseline_end_year = 2020,remove_zero = False)

drought_portfolio_percentile['percentile'] = 1 - drought_portfolio_percentile.percentile


# =============================================================================
# #Fitting local supplies
# y = new_sjv.cvp_delta
# 
# x = new_sjv[['SWDI_x']]
# x['SWDI_x_sq'] = (new_sjv.SWDI_x)**2
# x = sm.add_constant(x)
# 
# model = sm.OLS(y, x)
# results = model.fit()
# print(results.summary())
# res_y = results.predict(x)
# 
# plt.scatter(y, res_y)
# =============================================================================

# =============================================================================
# #Fitting imports
# y2 = new_sjv.cvp_delta
# x2 = new_sjv[['SWDI_x', 'SWDI_y']]
# x2['SWDI_x_sq'] = (new_sjv.SWDI_x)**2
# x2['SWDI_y_sq'] = (new_sjv.SWDI_y)**2
# 
# x2 = sm.add_constant(x2)
# model2 = sm.OLS(y2, x2)
# results2 = model2.fit()
# print(results2.summary())
# res_y2 = results2.predict(x2)
# plt.scatter(y2, res_y2)
# =============================================================================


# =============================================================================
# #Regional Analysis San Joaquin
# SJRdata = supply_portfolios.loc[supply_portfolios.HR == 'San Joaquin River'].reset_index()
# SJRpivot = SJRdata.pivot(index = 'SupplyCategory', columns = 'Year', values = 'taf')
# SJRtrans = SJRpivot.transpose()
# SJRtrans = SJRtrans.drop(columns = ['Colorado', 'Desalination', 'Other', 'TransfersImports', 'TransfersInternal'])
# SJRmain = SJRtrans[['LocalSupplies', 'Federal' , 'Groundwater']]
# 
# #Merging with
# =============================================================================


# =============================================================================
# SoCaldata = supply_portfolios.loc[supply_portfolios.HR == 'South Coast'].reset_index()
# SoCalpivot = SoCaldata.pivot(index = 'SupplyCategory', columns = 'Year', values = 'taf')
# SoCaltrans = SoCalpivot.transpose()
# SoCalmain = SoCaltrans[['LocalSupplies', 'Groundwater' , 'Colorado', 'SWP' , 'Imports', 'Desalination']]
# =============================================================================

"""
#Plotting donut for San Joaquin River
plt.pie(avg_sup_portfolios.loc[avg_sup_portfolios.HR == 'San Joaquin River', 'taf'], labels = avg_sup_portfolios.loc[avg_sup_portfolios.HR == 'San Joaquin River', 'SupplyCategory'])
my_circle=plt.Circle( (0,0), 0.7, color='white')
p=plt.gcf()
p.gca().add_artist(my_circle)
"""

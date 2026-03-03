# -*- coding: utf-8 -*-
"""
Created on Thu Nov 27 15:47:51 2025

@author: rlhulskamp
"""

# this script calculates erosion and accretion area and quantifies volumes
# between epochs and relative to the first epoch
# normalised to nr of days

# import packages
import os
import os.path
import numpy as np
import rasterio
import pandas as pd
import glob

dif_between = # \08_DIFs\01_between\*.tif
dif_first =# \08_DIFs\02_first\*.tif

#%% volume change between measurements

dif_paths = glob.glob(dif_between)

start_date = []
end_date = []
for m in range(len(dif_paths)):
    date = dif_paths[m].split('\\')[-1].split('_')[0]
    start_date.append(date)
    date = dif_paths[m].split('\\')[-1].split('_')[1]
    end_date.append(date)
    
df_between = pd.DataFrame(columns = ['start_date', 'end_date', 
                                   'b_area_tot', 'b_area_acc', 'b_area_ero', 
                                   'b_vol_acc', 'b_vol_ero',
                                   'b_vol_net', 'b_vol_gross'])
df_between['start_date'] = start_date
df_between['end_date'] = end_date

df_at = []
df_aa = []
df_ae = []
df_va = []
df_ve = []
df_vn = []
df_vg = []

for m in range(len(dif_paths)):
    # load dtm
    with rasterio.open(os.path.join(dif_paths[m])) as src:
        dif = src.read(1).astype(float)
        pixelsize = src.transform.a # in [m]
        
    area_tot = np.count_nonzero(~np.isnan(dif))*pixelsize*pixelsize
    
    # filter on accreting pixels
    acc = dif[dif > 0]
    
    # area accreting
    area_acc = len(acc) * (pixelsize * pixelsize) # [m2]
    area_acc_p = area_acc / area_tot * 100 # [%]
    
    # volume accreting
    vol_acc = (acc * pixelsize * pixelsize).sum() # [m3]
    
    # filter on eroding pixels
    ero = dif[dif < 0]
    
    # area accreting
    area_ero = len(ero) * (pixelsize * pixelsize) # [m2]
    area_ero_p = area_ero / area_tot * 100 # [%]
    
    # volume accreting
    vol_ero = (ero * pixelsize * pixelsize).sum() # [m3]
    
    vol_net = vol_acc + vol_ero # [m3]
    vol_gross = abs(vol_acc) + abs(vol_ero) #[ms]
    
    df_at.append(area_tot)
    df_aa.append(area_acc_p)
    df_ae.append(area_ero_p)
    df_va.append(vol_acc)
    df_ve.append(vol_ero)
    df_vn.append(vol_net)
    df_vg.append(vol_gross)
    
df_between['b_area_tot'] = df_at
df_between['b_area_acc'] = df_aa
df_between['b_area_ero'] = df_ae
df_between['b_vol_acc'] = df_va
df_between['b_vol_ero'] = df_ve
df_between['b_vol_net'] = df_vn
df_between['b_vol_gross'] = df_vg

### normalise data
df_between_norm = df_between.copy()

# convert dates
df_between_norm["YYYYMMDD_S"] = pd.to_datetime(df_between_norm["start_date"], format='%Y%m%d')
df_between_norm["YYYYMMDD_E"] = pd.to_datetime(df_between_norm["end_date"], format='%Y%m%d')

# calculate nr of days between each measurement
df_between_norm["dt"] = df_between_norm["YYYYMMDD_E"] - df_between_norm["YYYYMMDD_S"]

# convert nr of days to float
df_between_norm["dt_float"] = df_between_norm["dt"].dt.days.astype(float)

# compute volume change per day
df_between_norm["vol_acc_dT"] = df_between_norm["b_vol_acc"] / df_between_norm["dt_float"] #[m3/day]
df_between_norm["vol_ero_dT"] = df_between_norm["b_vol_ero"] / df_between_norm["dt_float"] #[m3/day]
df_between_norm["vol_net_dT"] = df_between_norm["b_vol_net"] / df_between_norm["dt_float"] #[m3/day]
df_between_norm["vol_gross_dT"] = df_between_norm["b_vol_gross"] / df_between_norm["dt_float"] #[m3/day]

#%% volume change relative to first measurement

dif_paths = glob.glob(dif_first)

start_date = []
end_date = []
for m in range(len(dif_paths)):
    date = dif_paths[m].split('\\')[-1].split('_')[0]
    start_date.append(date)
    date = dif_paths[m].split('\\')[-1].split('_')[1]
    end_date.append(date)
    
df_first = pd.DataFrame(columns = ['start_date', 'end_date', 
                                   'f_area_tot', 'f_area_acc', 'f_area_ero', 
                                   'f_vol_acc', 'f_vol_ero'])
df_first['start_date'] = start_date
df_first['end_date'] = end_date

df_at = []
df_aa = []
df_ae = []
df_va = []
df_ve = []

for m in range(len(dif_paths)):
    # load dtm
    with rasterio.open(os.path.join(dif_paths[m])) as src:
        dif = src.read(1).astype(float)
        pixelsize = src.transform.a # in [m]
        
    area_tot = np.count_nonzero(~np.isnan(dif))*pixelsize*pixelsize
    
    # filter on accreting pixels
    acc = dif[dif > 0]
    
    # area accreting
    area_acc = len(acc) * (pixelsize * pixelsize) # [m2]
    area_acc_p = area_acc / area_tot * 100 # [%]
    
    # volume accreting
    vol_acc = (acc * pixelsize * pixelsize).sum() # [m3]
    
    # filter on eroding pixels
    ero = dif[dif < 0]
    
    # area accreting
    area_ero = len(ero) * (pixelsize * pixelsize) # [m2]
    area_ero_p = area_ero / area_tot * 100 # [%]
    
    # volume accreting
    vol_ero = (ero * pixelsize * pixelsize).sum() # [m3]
    
    df_at.append(area_tot)
    df_aa.append(area_acc_p)
    df_ae.append(area_ero_p)
    df_va.append(vol_acc)
    df_ve.append(vol_ero)
    
df_first['f_area_tot'] = df_at
df_first['f_area_acc'] = df_aa
df_first['f_area_ero'] = df_ae
df_first['f_vol_acc'] = df_va
df_first['f_vol_ero'] = df_ve
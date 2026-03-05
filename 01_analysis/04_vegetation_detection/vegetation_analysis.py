# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 11:22:22 2025

@author: rlhulskamp
"""

# this script calculates the average height for vegetation pixels and how
# that changes over time (determined through the dems of difs)

# import packages
import os
import os.path
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import rasterio
from rasterio.mask import mask
import pandas as pd
import seaborn as sns
import geopandas as gpd
import json
import glob

# loc of dem maps
dem_lst = glob.glob(#\01_DEMs\*.tif")

# loc of veg map (gli_otsu)
veg_map = # \03_vegetation_detection\VEG_20241009.tif

# open vegetation map
with rasterio.open(veg_map) as src:
    veg = src.read(1).astype(np.float32)
    
# mask: 1 for veg==1, other 0
veg_mask = (veg == 1).astype(np.float32)

# derive start date 
start_date = []
for m in range(len(dem_lst)):
    date = dem_lst[m].split('\\')[-1].split('_')[0]
    start_date.append(date)
    
# create dataframe
df = pd.DataFrame(columns = ['start_date', 
                             'total_area',
                             'veg_total_area',
                             'perc_veg_area',
                             'veg_mean_height',
                             'veg_min_height'])

# set start and end date in df
df['start_date'] = start_date

# define df's for vegetation statistics
df_total_area = []
df_veg_total_area = []
df_perc_veg_area = []
df_veg_mean_height = []
df_veg_min_height = []

# loop over dems to calculate statistics
for m in range(len(dem_lst)):
    
    # load dem
    with rasterio.open(dem_lst[m]) as src:
        dem = src.read(1).astype(np.float32)
        
        # save pixelsize and no data
        pixelsize = src.transform.a # in [m]
        no_data = src.nodata
        
    # replace no_data with nan
    dem[dem == no_data] = 0
    
    # clip dem to veg map
    dem_veg = dem * veg_mask
        
    # compute total (non) vegetated area
    area_tot = np.count_nonzero(dem) * pixelsize * pixelsize # [m2]
    veg_area_tot = np.count_nonzero(dem_veg) * pixelsize * pixelsize # [m2]
    
    # percentage of area vegetated
    perc_veg = veg_area_tot / area_tot *100 #[%]
    
    # compute average height of vegetated pixels (ignore nan and 0 values)
    mean_height = np.nanmean(np.where(dem_veg == 0, np.nan, dem_veg))
    
    # compute min height of vegetated pixels (ignore nan and 0 values)
    min_height = np.nanmin(np.where(dem_veg == 0, np.nan, dem_veg))
    
    df_total_area.append(area_tot)
    df_veg_total_area.append(veg_area_tot)
    df_perc_veg_area.append(perc_veg)
    df_veg_mean_height.append(mean_height)
    df_veg_min_height.append(min_height)
    
df['total_area'] = df_total_area
df['veg_total_area'] = df_veg_total_area
df['perc_veg_area'] = df_perc_veg_area
df['veg_mean_height'] = df_veg_mean_height
df['veg_min_height'] = df_veg_min_height


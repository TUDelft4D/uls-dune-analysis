# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 10:17:50 2026

@author: rlhulskamp
"""

# this script computes vegetation coverage and mean elevation per gridcell of 
# 10 x 10 m for total study area
# the grid is derived in qgis

# import packages
import os
import os.path
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob


#%% load data

# grid
grid_loc = # \10_aoi\grid_10_10.geojson
grid = gpd.read_file(grid_loc)

# dem
dem_paths = glob.glob(# \01_DEMs*.tif)

# dif
dif_paths = glob.glob(# \08DIFs\01_between\*.tif)

# veg
veg_loc = # \03_vegetation_detection\VEG_20241009.tif
veg = rasterio.open(veg_loc)
    
#%% compute

df_all = []

for d in range(len(dif_paths)):
    
    dif = rasterio.open(dif_paths[d])
    
    # save variables
    dzm = [] # mean elevation change between first and second measurement
    dva = [] # accreting volume
    dve = [] # eroding volume
    dvn = [] # net volume
    dvg = [] # gross volume
    vc = [] # vegetation cover
    
    # loop over all gridcells
    for g in range(len(grid)):
        print(g)
        
        # extract geometry of gridcell
        geometry = [grid['geometry'][g]]
        
        # clip dif to gridcell
        clip_dif, clip_dif_transform = mask(dif, 
                                            geometry, 
                                            crop = True,
                                            nodata = dif.nodata)
        
        # save dem values of gridcell
        dif_clip = clip_dif[0]
        dif_clip[dif_clip == dif.nodata] = np.nan
        
        # compute average elevation of gridcell
        dz_mean = np.nanmean(dif_clip)
        dv_acc = (dif_clip[dif_clip > 0] * 0.25*0.25).sum()
        dv_ero = (dif_clip[dif_clip < 0] * 0.25*0.25).sum()
        dv_net = dv_acc + dv_ero
        dv_gross = dv_acc + abs(dv_ero)
        
        # clip veg to gridcell
        clip_v, clip_v_transform = mask(veg, 
                                        geometry, 
                                        crop = True,
                                        nodata = dem.nodata)
        
        # save dem values of gridcell
        veg_clip = clip_v[0]
        
        # compute vegetation pixels in gridcell
        veg_pix = len(veg_clip[veg_clip == 1]) # number of veg pixels
        sand_pix = len(veg_clip[veg_clip == 2]) # number of sand pixels
        veg_cov = (veg_pix / (veg_pix + sand_pix) * 100
                   if (veg_pix + sand_pix) != 0
                   else 0)
        
        # save variables
        dzm.append(dz_mean)
        dva.append(dv_acc)
        dve.append(dv_ero)
        dvn.append(dv_net)
        dvg.append(dv_gross)
        vc.append(veg_cov)
        
    df = pd.DataFrame({"dz_mean":  dzm,
                       "dv_acc":   dva,
                       "dv_ero":   dve,
                       "dv_net":   dvn,
                       "dv_gross": dvg,
                       "veg_cov":  vc})
    
    df_all.append(df)
    
output_folder = # \06_csv_parameters\vegcover_dzmean

for i, df in enumerate(df_all):
    df.to_csv(os.path.join(output_folder, f'vegcov_dz_{i}.csv'),
              index=False)

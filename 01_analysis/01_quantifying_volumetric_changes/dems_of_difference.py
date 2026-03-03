# -*- coding: utf-8 -*-
"""
Created on Tue Nov 25 16:03:49 2025

@author: rlhulskamp
"""

# this script computes the difference dems of the study area
# it substracts dem(n) from dem(n+1)
# it saves the difference dem as a new tiff file

# import packages
import os
import os.path
import numpy as np
import rasterio

# location of elevation maps
dem_loc = # \01_DEMs

# list elevation maps
dem_lst = os.listdir(dem_loc)

#%% difference between each measurement

for m in range(len(dem_lst)-1):
    # load dem
    with rasterio.open(os.path.join(dem_loc, dem_lst[m])) as src:
        dem0 = src.read(1)  # Read first (and only) band
        meta = src.meta.copy()
        no_data = src.nodata
        dem0[dem0 == no_data] = np.nan
        
    with rasterio.open(os.path.join(dem_loc, dem_lst[m+1])) as src:
        dem1 = src.read(1)  # Read first (and only) band
        no_data = src.nodata
        dem1[dem1 == no_data] = np.nan
        
    # compute difference dem
    dif = dem1 - dem0

    ### save tif
    # filename = dem_lst[m].split('_')[0] + '_' + dem_lst[m+1].split('_')[0] + '_dif.tif'
    # meta.update(dtype='float32', count=1, nodata=np.nan)
    # with rasterio.open(filename, 'w', **meta) as dst:
    #     dst.write(dif.astype('float32'), 1)
    
#%% difference between each measurement relative to first measurement

for m in range(len(dem_lst)-1):
    # load dem
    with rasterio.open(os.path.join(dem_loc, dem_lst[0])) as src:
        dem0 = src.read(1)  # Read first (and only) band
        meta = src.meta.copy()
        no_data = src.nodata
        dem0[dem0 == no_data] = np.nan
        
    with rasterio.open(os.path.join(dem_loc, dem_lst[m+1])) as src:
        dem1 = src.read(1)  # Read first (and only) band
        no_data = src.nodata
        dem1[dem1 == no_data] = np.nan
        
    # compute difference dem
    dif = dem1 - dem0

    ### save tif
    # filename = dem_lst[0].split('_')[0] + '_' + dem_lst[m+1].split('_')[0] + '_dif.tif'
    # meta.update(dtype='float32', count=1, nodata=np.nan)
    # with rasterio.open(filename, 'w', **meta) as dst:
    #     dst.write(dif.astype('float32'), 1)


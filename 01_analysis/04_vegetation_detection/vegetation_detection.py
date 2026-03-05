# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 14:44:25 2025

@author: rlhulskamp
"""

# this script uses the green leaf index to detect vegetation from an rgb image

# import packages
import os
import matplotlib.pyplot as plt
import os.path
import numpy as np
from skimage import filters
import rasterio
from matplotlib.colors import ListedColormap, BoundaryNorm
from rasterio.mask import mask
    
#%% calculate green leaf index

# location of rgbs
rgb_loc = #\02_RGB\RGB_20241009.tif

# open rgb image
with rasterio.open(rgb_lst[v]) as src:
    R = src.read(1).astype(np.float32)
    G = src.read(2).astype(np.float32)
    B = src.read(3).astype(np.float32)
    
# Replace zeros with NaN
R[R == 0] = np.nan
G[G == 0] = np.nan
B[B == 0] = np.nan

# compute gli
num = (2 * G) - R - B
den = (2 * G) + R + B
eps = 1e-10
gli = num / (den + eps)   # float array, range between [-1, +1]
       
# plot
plt.imshow(gli, cmap='RdYlGn')
plt.show()
    
# save gli image
filename = ###
with rasterio.open(filename, 
                   'w', 
                   driver = "GTiff",
                   height = gli.shape[0],
                   width = gli.shape[1],
                   count = 1,
                   dtype = "float32",
                   crs = src.crs,
                   transform = src.transform) as dst:
    dst.write((gli).astype('float32'), 1)
        
#%% compute otsu and classify image

# location of gli tifs
gli_loc = # \03_vegetation_detection\GLI_20241009.tif

# open gli image
with rasterio.open(gli_lst[v]) as src:
    gli = src.read(1).astype(np.float32)

# mask nans
mask = gli[~np.isnan(gli)]

# compute otsu's threshold
otsu_threshold = filters.threshold_otsu(mask)

# compute otsu's image
# gli > otsu = veg (1), gli < otsu = sand (2)
otsu_im = (gli > otsu_threshold).astype(int) + (gli < otsu_threshold).astype(int) * 2

# plot
plt.figure(figsize=(15, 15))

# define colors
colors = ['white', '#33a02c', '#fdbf6f']
cmap = ListedColormap(colors)
norm = BoundaryNorm([0, 1, 2, 3], cmap.N)

plt.imshow(otsu_im, cmap = cmap, norm = norm)
plt.show()

# save gli_otsu image
filename = ###
with rasterio.open(filename, 
                   'w', 
                   driver = "GTiff",
                   height = gli.shape[0],
                   width = gli.shape[1],
                   count = 1,
                   dtype = "float32",
                   crs = src.crs,
                   transform = src.transform) as dst:
    dst.write((otsu_im).astype('float32'), 1)
        

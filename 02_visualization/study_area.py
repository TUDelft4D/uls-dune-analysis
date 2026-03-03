# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 15:01:49 2026

@author: rlhulskamp
"""

# this code plots maps of the aoi of the zandmotor study area

# import packages
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.transforms import Affine2D

plt.style.use('seaborn-v0_8')
   
# input:
rgb_loc = # \02_RGB\2024_rgb_RWS_clipped.tif
hill_loc = # \07_hillshades\20240607_mean_hillshade.tif
dem_loc = # \01_DEMs\20240607_mean.tif
veg_loc = # \03_vegetation_detections\20241009_gli_otsu.tif

# rgb
with rasterio.open(rgb_loc) as src:
    rgb = src.read([1, 2, 3])
    rgb_bounds = src.bounds

rgb = np.moveaxis(rgb, 0, -1).astype(float) / 255.0

extent_rgb = [rgb_bounds.left, rgb_bounds.right, rgb_bounds.bottom, rgb_bounds.top]

rgb_x_center = (rgb_bounds.left + rgb_bounds.right) / 2
rgb_y_center = (rgb_bounds.bottom + rgb_bounds.top) / 2

# hill
with rasterio.open(hill_loc) as src:
    hill = src.read(1)
    hill_bounds = src.bounds
    
hill = hill.astype(float) 
hill[hill == 0] = np.nan

extent_hill = [hill_bounds.left, hill_bounds.right, hill_bounds.bottom, hill_bounds.top]

hill_x_center = (hill_bounds.left + hill_bounds.right) / 2
hill_y_center = (hill_bounds.bottom + hill_bounds.top) / 2

# dem
with rasterio.open(dem_loc) as src:
    dem = src.read(1, masked = True)
    dem_bounds = src.bounds
    dem = dem.filled(np.nan)
    
extent_dem = [dem_bounds.left, dem_bounds.right, dem_bounds.bottom, dem_bounds.top]

dem_x_center = (dem_bounds.left + dem_bounds.right) / 2
dem_y_center = (dem_bounds.bottom + dem_bounds.top) / 2

# veg
with rasterio.open(veg_loc) as src:
    veg = src.read(1)
    veg_bounds = src.bounds
    
extent_veg = [veg_bounds.left, veg_bounds.right, veg_bounds.bottom, veg_bounds.top]

veg_x_center = (veg_bounds.left + veg_bounds.right) / 2
veg_y_center = (veg_bounds.bottom + veg_bounds.top) / 2

degrees = 48.7

fig = plt.figure(figsize=(12, 6))
ax = fig.add_axes([0.05,  0.05, 0.9,  0.9])
cax = fig.add_axes([0.92, 0.05, 0.02, 0.9]) # [left, bottom, width, height]

# rgb
ax.imshow(rgb,
          extent = extent_rgb,
          origin = 'upper',
          transform = Affine2D().rotate_deg_around(rgb_x_center, rgb_y_center, -degrees) + ax.transData)

# hillshade
ax.imshow(hill,
          cmap="gray",
          vmin = 0,
          vmax = 255,
          extent = extent_hill,
          transform = Affine2D().rotate_deg_around(hill_x_center, hill_y_center, -degrees) + ax.transData,
          origin="upper")

# dif
dem_im = ax.imshow(dem, 
                   cmap = 'Spectral_r', 
                   vmin = 2, 
                   vmax = 9,
                   alpha = 0.8,
                   extent = extent_dem,
                   transform = Affine2D().rotate_deg_around(dem_x_center, dem_y_center, -degrees) + ax.transData,
                   origin = 'upper')

# colorbar dif
cbar = fig.colorbar(dem_im, cax=cax)
cbar.set_label('Elevation [m]', fontsize=15)
cbar.ax.tick_params(labelsize=13)

# labels
ax.set_xlabel("X [m]", fontsize = 15)
ax.set_ylabel("Y [m]", fontsize = 15)

# limits
ax.set_xlim(rgb_x_center - 397.023 - 100, rgb_x_center + 391.962 + 100)
ax.set_xticks(np.arange(rgb_x_center - 397.023 - 100, rgb_x_center + 391.962 + 100, 100))
ax.set_xticklabels(np.linspace(0 - 100, 700 + 100, 10).astype(int), fontsize=15)

ax.set_ylim(rgb_y_center - 154.091 - 100, rgb_y_center + 191.611 + 100)
ax.set_yticks(np.arange(rgb_y_center - 154.091 - 100, rgb_y_center + 191.611 + 100, 100))
ax.set_yticklabels(np.linspace(0 - 100, 300 + 100, 6).astype(int), fontsize=15)
    
# north arrow
ax.text(0.94, 0.14, u'\u25B2 \nN ',
        ha='center', va='top',
        transform=ax.transAxes,
        fontsize=15,
        family='Arial',
        rotation=-degrees)

plt.show()

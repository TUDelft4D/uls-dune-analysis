# -*- coding: utf-8 -*-
"""
Created on Wed Feb 11 09:55:10 2026

@author: rlhulskamp
"""

# this script plots vegetation classification example

# import packages
import numpy as np
import rasterio
from matplotlib.transforms import Affine2D
import matplotlib.pyplot as plt
import os
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from shapely.affinity import rotate
import glob
import geopandas as gpd
import pandas as pd
from windrose import WindroseAxes

plt.style.use('seaborn-v0_8')

# input:
rgb_loc = # \02_RGB\20241009_rgb.tif
gli_loc = # \03_vegetation_detections\20241009_gli.tif
veg_loc = # \03_vegetation_detections\20241009_gli_otsu.tif

# rgb
with rasterio.open(rgb_loc) as src:
    rgb = src.read([1, 2, 3]).astype(float)
    rgb_bounds = src.bounds
    
rgb = np.transpose(rgb, (1, 2, 0))
rgb /= rgb.max()

extent_rgb = [rgb_bounds.left, rgb_bounds.right, rgb_bounds.bottom, rgb_bounds.top]

rgb_x_center = (rgb_bounds.left + rgb_bounds.right) / 2
rgb_y_center = (rgb_bounds.bottom + rgb_bounds.top) / 2

# gli
with rasterio.open(gli_loc) as src:
    gli = src.read(1)
    gli_bounds = src.bounds
    
gli = gli.astype(float) 

extent_gli = [gli_bounds.left, gli_bounds.right, gli_bounds.bottom, gli_bounds.top]

gli_x_center = (gli_bounds.left + gli_bounds.right) / 2
gli_y_center = (gli_bounds.bottom + gli_bounds.top) / 2

# veg
with rasterio.open(veg_loc) as src:
    veg = src.read(1)
    veg_bounds = src.bounds
    
extent_veg = [veg_bounds.left, veg_bounds.right, veg_bounds.bottom, veg_bounds.top]

veg_x_center = (veg_bounds.left + veg_bounds.right) / 2
veg_y_center = (veg_bounds.bottom + veg_bounds.top) / 2

colors_veg = ['green', # veg
              'lemonchiffon'] # sand
cmap_veg = ListedColormap(colors_veg)
norm = BoundaryNorm([1, 2, 3], cmap_veg.N)

degrees = 48.7
letters = ['(a)', '(b)', '(c)']

### plot

fig, ax = plt.subplots(1, 3, figsize=(12, 4), sharey=True)

### rgb
axs = 0
    
ax[axs].imshow(rgb,
               extent = extent_rgb,
               origin = 'upper',
               transform = Affine2D().rotate_deg_around(rgb_x_center, rgb_y_center, -degrees) + ax[axs].transData)

### gli
axs = 1

gli_im = ax[axs].imshow(gli,
               cmap='viridis',
               vmin = 0,
               vmax = 0.1,
               extent = extent_gli,
               transform = Affine2D().rotate_deg_around(gli_x_center, gli_y_center, -degrees) + ax[axs].transData,
               origin="upper")

### veg
axs = 2

veg_im = ax[axs].imshow(veg, 
                        cmap = cmap_veg,
                        norm = norm,
                        # alpha = 0.8,
                        extent = extent_veg,
                        transform = Affine2D().rotate_deg_around(veg_x_center, veg_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')


# labels and text
ax[0].set_xlabel("X [m]", fontsize = 15)
ax[1].set_xlabel("X [m]", fontsize = 15)
ax[2].set_xlabel("X [m]", fontsize = 15)
ax[0].text(0.05, 0.975, letters[0], ha = 'center', va = 'top', transform = ax[0].transAxes, fontsize = 15, family = 'Arial')
ax[1].text(0.05, 0.975, letters[1], ha = 'center', va = 'top', transform = ax[1].transAxes, fontsize = 15, family = 'Arial', c = 'white')
ax[2].text(0.05, 0.975, letters[2], ha = 'center', va = 'top', transform = ax[2].transAxes, fontsize = 15, family = 'Arial')
ax[0].set_ylabel("Y [m]", fontsize = 15)

# limits
for a in ax:
    a.set_xlim(rgb_x_center + 150, rgb_x_center + 200)
    a.set_xticks(np.arange(rgb_x_center + 150, rgb_x_center + 200, 10))
    a.set_xticklabels(np.linspace(0, 40, 5).astype(int), fontsize=15)

    a.set_ylim(rgb_y_center + 0, rgb_y_center + 50)
    a.set_yticks(np.arange(rgb_y_center + 0, rgb_y_center + 50, 10))
    a.set_yticklabels(np.linspace(0, 40, 5).astype(int), fontsize=15)

# north arrow
ax[0].text(0.94, 0.14, u'\u25B2 \nN ', ha='center', va='top', transform=ax[0].transAxes, fontsize=15, family='Arial', rotation=-degrees)
ax[1].text(0.94, 0.14, u'\u25B2 \nN ', ha='center', va='top', transform=ax[1].transAxes, fontsize=15, family='Arial', rotation=-degrees, c = 'white')
ax[2].text(0.94, 0.14, u'\u25B2 \nN ', ha='center', va='top', transform=ax[2].transAxes, fontsize=15, family='Arial', rotation=-degrees)

plt.tight_layout()

# colourbars
# gli
cax_gli = fig.add_axes([0.3825, -0.075, 0.2775, 0.05]) # [left, bottom, width, height]
cbar_gli = fig.colorbar(gli_im, cax=cax_gli,  orientation='horizontal')
cbar_gli.set_label("GLI [-]", fontsize=15)
cbar_gli.ax.tick_params(labelsize=12)

# veg
cax_veg = fig.add_axes([0.6975, -0.075, 0.2775, 0.05]) # [left, bottom, width, height]
cbar_veg = fig.colorbar(veg_im, cax=cax_veg, orientation='horizontal')
cbar_veg.set_ticks([1.5, 2.5])
cbar_veg.set_ticklabels(['Vegetation', 'Sand'])
cbar_veg.set_label('Classes', fontsize=15)
cbar_veg.ax.tick_params(labelsize= 12)

plt.show()

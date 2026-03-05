# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 09:09:55 2026

@author: rlhulskamp
"""

# this script plots summer vs winter maps

# import packages
import numpy as np
import rasterio
from matplotlib.transforms import Affine2D
import matplotlib.pyplot as plt
import os
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
import geopandas as gpd

plt.style.use('seaborn-v0_8')

# input:
rgb_loc = # \02_RGB\2024_rgb_RWS_clipped.tif
hill_loc = # \07_hillshades\hillshade_20240607.tif"
dif_win = # \08_DIFs\01_between\20241115_20250214_dif.tif"
dif_sum = # \08_DIFs\01_between\20250514_20250617_dif.tif"

#%% 

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

# dif
with rasterio.open(dif_sum) as src:
    dif = src.read(1)
    dif_bounds = src.bounds
    
extent_dif = [dif_bounds.left, dif_bounds.right, dif_bounds.bottom, dif_bounds.top]

dif_x_center = (dif_bounds.left + dif_bounds.right) / 2
dif_y_center = (dif_bounds.bottom + dif_bounds.top) / 2

# rotation
degrees = 48.7

#%% plot!

fig, ax = plt.subplots(1, 2, figsize=(20, 10), sharey=True)

fontsize = 20

### dif winter
axs = 0 

# rgb
ax[axs].imshow(rgb,
               extent = extent_rgb,
               origin = 'upper',
               transform = Affine2D().rotate_deg_around(rgb_x_center, rgb_y_center, -degrees) + ax[axs].transData)

# hillshade
ax[axs].imshow(hill,
               cmap="gray",
               vmin = 0,
               vmax = 255,
               extent = extent_hill,
               transform = Affine2D().rotate_deg_around(hill_x_center, hill_y_center, -degrees) + ax[axs].transData,
               origin="upper")

# dif
with rasterio.open(dif_win) as src:
    dif = src.read(1)
dif_im = ax[axs].imshow(dif, 
                        cmap = 'RdBu', 
                        vmin = -0.5, 
                        vmax = 0.5,
                        alpha = 0.8,
                        extent = extent_dif,
                        transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

### dif summer
axs = 1

# rgb
ax[axs].imshow(rgb,
               extent = extent_rgb,
               origin = 'upper',
               transform = Affine2D().rotate_deg_around(rgb_x_center, rgb_y_center, -degrees) + ax[axs].transData)

# hillshade
ax[axs].imshow(hill,
               cmap="gray",
               vmin = 0,
               vmax = 255,
               extent = extent_hill,
               transform = Affine2D().rotate_deg_around(hill_x_center, hill_y_center, -degrees) + ax[axs].transData,
               origin="upper")

# dif
with rasterio.open(dif_sum) as src:
    dif = src.read(1)
dif_im = ax[axs].imshow(dif, 
                        cmap = 'RdBu', 
                        vmin = -0.5, 
                        vmax = 0.5,
                        alpha = 0.8,
                        extent = extent_dif,
                        transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# labels
ax[0].set_xlabel("X [m]", fontsize = fontsize)
ax[1].set_xlabel("X [m]", fontsize = fontsize)
ax[0].set_ylabel("Y [m]", fontsize = fontsize)

# limits
for a in ax:
    a.set_xlim(rgb_x_center - 397.023, rgb_x_center + 391.962)
    a.set_xticks(np.arange(rgb_x_center - 397.023, rgb_x_center + 391.962, 100))
    a.set_xticklabels(np.linspace(0, 700, 8).astype(int), fontsize= fontsize -3)

    a.set_ylim(rgb_y_center - 154.091, rgb_y_center + 191.611)
    a.set_yticks(np.arange(rgb_y_center - 154.091, rgb_y_center + 191.611, 100))
    a.set_yticklabels(np.linspace(0, 300, 4).astype(int), fontsize= fontsize -3)
    
    # north arrow
    a.text(
        0.94, 0.14, u'\u25B2 \nN ',
        ha='center', va='top',
        transform=a.transAxes,
        fontsize=fontsize,
        family='Arial',
        rotation=-degrees)
    
# colorbar dif
cbar = fig.colorbar(dif_im, 
                    ax=ax[1], 
                    orientation='vertical', 
                    fraction=0.021, 
                    pad=0.02)
cbar.set_label('Elevation difference [m]', fontsize= fontsize)
cbar.ax.tick_params(labelsize= fontsize - 3)


ax[0].text(0.04, 0.95, '(a)', ha = 'center', va = 'top', 
            transform = ax[0].transAxes, fontsize = fontsize,# fontweight='bold',
            family = 'Arial')
ax[1].text(0.04, 0.95, '(b)', ha = 'center', va = 'top', 
            transform = ax[1].transAxes, fontsize = fontsize,# fontweight='bold',
            family = 'Arial')

plt.show()


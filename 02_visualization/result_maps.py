# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 13:41:32 2026

@author: rlhulskamp
"""

# this script plots result maps: (a) dem of difference, (b) clusters, (c) vegetation

# import packages
import numpy as np
import rasterio
from matplotlib.transforms import Affine2D
import matplotlib.pyplot as plt
import os
from matplotlib.colors import ListedColormap, BoundaryNorm
import geopandas as gpd

plt.style.use('seaborn-v0_8')

# input:
rgb_loc = # \02_RGB\2024_rgb_RWS_clipped.tif
hill_loc = # \07_hillshades\20240607_mean_hillshade.tif
dif_loc = # \08_DIFs\02_first\20240607_20250617_dif.tif
cluster_loc = # \04_clusters\merged_clusters.tif
veg_loc = # \03_vegetation_detections\20241009_gli_otsu.tif
marked_areas_loc = # \10_aoi\aoi_mark_areas.geojson
marked_letters_loc = # \10_aoi\aoi_mark_areas_letters.geojson

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
with rasterio.open(dif_loc) as src:
    dif = src.read(1)
    dif_bounds = src.bounds
    
extent_dif = [dif_bounds.left, dif_bounds.right, dif_bounds.bottom, dif_bounds.top]

dif_x_center = (dif_bounds.left + dif_bounds.right) / 2
dif_y_center = (dif_bounds.bottom + dif_bounds.top) / 2

# cluster
with rasterio.open(cluster_loc) as src:
    cluster = src.read(1)
    cluster_bounds = src.bounds
    
extent_cluster = [cluster_bounds.left, cluster_bounds.right, cluster_bounds.bottom, cluster_bounds.top]

cluster_x_center = (cluster_bounds.left + cluster_bounds.right) / 2
cluster_y_center = (cluster_bounds.bottom + cluster_bounds.top) / 2

# veg
with rasterio.open(veg_loc) as src:
    veg = src.read(1)
    veg_bounds = src.bounds
    
extent_veg = [veg_bounds.left, veg_bounds.right, veg_bounds.bottom, veg_bounds.top]

veg_x_center = (veg_bounds.left + veg_bounds.right) / 2
veg_y_center = (veg_bounds.bottom + veg_bounds.top) / 2

# marked areas
gdf = gpd.read_file(marked_areas_loc)
boxes = []
for geom in gdf.geometry:
    xmin, ymin, xmax, ymax = geom.bounds
    boxes.append([xmin, xmax, ymin, ymax])

# rotation
degrees = 48.7

### plot

fig, ax = plt.subplots(3, 1, figsize=(8.3, 11.7), sharex=True)

fontsize = 11

### (a) total change
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
dif_im = ax[axs].imshow(dif, 
                        cmap = 'RdBu', 
                        vmin = -0.5, 
                        vmax = 0.5,
                        alpha = 0.8,
                        extent = extent_dif,
                        transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# colorbar dif
cbar = fig.colorbar(dif_im, 
                    ax=ax[axs], 
                    orientation='vertical', 
                    fraction=0.021, 
                    pad=0.02)
cbar.set_label('Elevation difference [m]', fontsize= fontsize)
cbar.ax.tick_params(labelsize= fontsize - 1)

### (b) clusters
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

# cluster
colors_cluster = ['tab:cyan',   # C4
                  'tab:orange', # C2
                  'red',        # C1
                  'tab:purple', # C5
                  'gold']       # C3
cmap_cluster = ListedColormap(colors_cluster)
norm = BoundaryNorm([0, 1, 2, 3, 4, 5], cmap_cluster.N)
cluster_im = ax[axs].imshow(cluster, 
                            cmap = cmap_cluster,
                            norm = norm,
                            alpha = 0.8,
                            extent = extent_cluster,
                            transform = Affine2D().rotate_deg_around(cluster_x_center, cluster_y_center, -degrees) + ax[axs].transData,
                            origin = 'upper')

# cluster colorbar
logical_order = [3, 0, 4, 1, 2]
logical_colors = [colors_cluster[i] for i in logical_order]
cmap_dummy = ListedColormap(logical_colors)
norm_dummy = BoundaryNorm([0, 1, 2, 3, 4, 5], len(logical_colors))
cbar_cluster = fig.colorbar(plt.cm.ScalarMappable(norm=norm_dummy, cmap=cmap_dummy),
                            ax=ax[axs],
                            orientation='vertical',
                            fraction=0.021,
                            pad=0.02)

cbar_cluster.set_ticks([0.5, 1.5, 2.5, 3.5, 4.5])
cbar_cluster.set_ticklabels(['Erosion', 'Stable', 'Low acc', 'Medium acc', 'High acc'])
cbar_cluster.set_ticklabels(['C5', 'C4', 'C3', 'C2', 'C1'])
cbar_cluster.set_label('Cluster', fontsize= fontsize)
cbar_cluster.ax.tick_params(labelsize= fontsize -1)


### (c) vegetation
axs = 2

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

# vegetation
colors_veg = [(1, 1, 1, 0), # nans
              'green', # veg
              'lemonchiffon'] # sand
cmap_veg = ListedColormap(colors_veg)
norm = BoundaryNorm([0, 1, 2, 3], cmap_veg.N)
veg_im = ax[axs].imshow(veg, 
                        cmap = cmap_veg,
                        norm = norm,
                        alpha = 0.8,
                        extent = extent_veg,
                        transform = Affine2D().rotate_deg_around(veg_x_center, veg_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# vegetation colorbar
cbar_veg = fig.colorbar(
    veg_im,
    ax=ax[axs],
    orientation='vertical',
    fraction=0.021,
    pad=0.02
)

# center ticks on categories
cbar_veg.set_ticks([1.5, 2.5])
cbar_veg.set_ticklabels(['Vegetation', 'Sand'], rotation = 90)
cbar_veg.ax.set_ylim(1, 3)
cbar_veg.set_label('Classes', fontsize=fontsize)
cbar_veg.ax.tick_params(labelsize= fontsize -1)

# plot marked areas on top of maps
for a in ax:
    for geom in gdf.geometry:
        a.plot(*geom.exterior.xy,
               color='black',
               linewidth=1,
               transform= Affine2D().rotate_deg_around(rgb_x_center, rgb_y_center, -degrees) + a.transData)

gdf_l = gpd.read_file(marked_letters_loc)
for i, ax_i in enumerate(ax):  # loop over all subplot axes
    for idx, row in gdf_l.iterrows():
        x, y = row.geometry.x, row.geometry.y
        ax_i.text(
            x, y, row.area,
            fontsize= fontsize -1,
            fontweight='bold',
            color='black',
            transform=Affine2D().rotate_deg_around(rgb_x_center, rgb_y_center, -degrees) + ax_i.transData,
            ha='center',
            va='center')

# labels
ax[2].set_xlabel("X [m]", fontsize = fontsize)
ax[0].set_ylabel("Y [m]", fontsize = fontsize)
ax[1].set_ylabel("Y [m]", fontsize = fontsize)
ax[2].set_ylabel("Y [m]", fontsize = fontsize)

# limits
for a in ax:
    a.set_xlim(rgb_x_center - 397.023, rgb_x_center + 391.962)
    a.set_xticks(np.arange(rgb_x_center - 397.023, rgb_x_center + 391.962, 100))
    a.set_xticklabels(np.linspace(0, 700, 8).astype(int), fontsize= fontsize -1)

    a.set_ylim(rgb_y_center - 154.091, rgb_y_center + 191.611)
    a.set_yticks(np.arange(rgb_y_center - 154.091, rgb_y_center + 191.611, 100))
    a.set_yticklabels(np.linspace(0, 300, 4).astype(int), fontsize= fontsize -1)
    
    # north arrow
    a.text(
        0.94, 0.14, u'\u25B2 \nN ',
        ha='center', va='top',
        transform=a.transAxes,
        fontsize=fontsize,
        family='Arial',
        rotation=-degrees)


ax[0].text(0.04, 0.95, '(a)', ha = 'center', va = 'top', 
            transform = ax[0].transAxes, fontsize = fontsize,# fontweight='bold',
            family = 'Arial')
ax[1].text(0.04, 0.95, '(b)', ha = 'center', va = 'top', 
            transform = ax[1].transAxes, fontsize = fontsize,# fontweight='bold',
            family = 'Arial')
ax[2].text(0.04, 0.95, '(c)', ha = 'center', va = 'top', 
            transform = ax[2].transAxes, fontsize = fontsize,# fontweight='bold',
            family = 'Arial')

plt.tight_layout()
plt.show()


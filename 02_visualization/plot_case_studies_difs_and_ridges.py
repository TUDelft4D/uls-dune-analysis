# -*- coding: utf-8 -*-
"""
Created on Tue Feb 24 13:30:02 2026

@author: rlhulskamp
"""

# this script plots case study maps

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
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# input:
rgb_loc = # \02_RGB\RGB_20241009.tif
hill_paths = sorted(glob.glob(# 07_hillshades\*.tif"))
dif_paths = sorted(glob.glob(# 08_DIFs\01_between\*.tif"))
veg_loc = # \03_vegetation_detection\VEG_20241009.tif"
dem_paths = sorted(glob.glob(# 01_DEMs\*.tif"))
crest_loc = sorted(glob.glob(# \05_ridge_lines\02_ridge_lines\*.gpkg"))
cluster_loc = # \04_clusters\KMEANS_CLUSTERS_K5.tif"
dif_tot = # \08_DIFs\02_first\20240607_20250617_dif.tif"
knmi_loc = # \09_meteo_data\wind_precipitation_hourly.txt"

#%% raster data

# rgb
with rasterio.open(rgb_loc) as src:
    rgb = src.read([1, 2, 3])
    rgb_bounds = src.bounds

rgb = np.moveaxis(rgb, 0, -1).astype(float) / 255.0

extent_rgb = [rgb_bounds.left, rgb_bounds.right, rgb_bounds.bottom, rgb_bounds.top]

rgb_x_center = (rgb_bounds.left + rgb_bounds.right) / 2
rgb_y_center = (rgb_bounds.bottom + rgb_bounds.top) / 2

# hill
with rasterio.open(hill_paths[0]) as src:
    hill = src.read(1)
    hill_bounds = src.bounds
    
hill = hill.astype(float) 
hill[hill == 0] = np.nan

extent_hill = [hill_bounds.left, hill_bounds.right, hill_bounds.bottom, hill_bounds.top]

hill_x_center = (hill_bounds.left + hill_bounds.right) / 2
hill_y_center = (hill_bounds.bottom + hill_bounds.top) / 2

# dif
with rasterio.open(dif_paths[0]) as src:
    dif = src.read(1)
    dif_bounds = src.bounds
    
extent_dif = [dif_bounds.left, dif_bounds.right, dif_bounds.bottom, dif_bounds.top]

dif_x_center = (dif_bounds.left + dif_bounds.right) / 2
dif_y_center = (dif_bounds.bottom + dif_bounds.top) / 2

# veg
with rasterio.open(veg_loc) as src:
    veg = src.read(1)
    veg_bounds = src.bounds
    
extent_veg = [veg_bounds.left, veg_bounds.right, veg_bounds.bottom, veg_bounds.top]

veg_x_center = (veg_bounds.left + veg_bounds.right) / 2
veg_y_center = (veg_bounds.bottom + veg_bounds.top) / 2

colors_veg = [(1, 1, 1, 0), # nans
              'green', # veg
              (1, 1, 1, 0)] # sand
cmap_veg = ListedColormap(colors_veg)
norm = BoundaryNorm([0, 1, 2, 3], cmap_veg.N)

# cluster
with rasterio.open(cluster_loc) as src:
    cluster = src.read(1)
    cluster_bounds = src.bounds
    
extent_cluster = [cluster_bounds.left, cluster_bounds.right, cluster_bounds.bottom, cluster_bounds.top]

cluster_x_center = (cluster_bounds.left + cluster_bounds.right) / 2
cluster_y_center = (cluster_bounds.bottom + cluster_bounds.top) / 2

#%% knmi data

# load meteo data
df_knmi = pd.read_csv(knmi_loc, skiprows = 46) 

# convert date to datetime-string
df_knmi["YYYYMMDD"] = pd.to_datetime(df_knmi["YYYYMMDD"], format='%Y%m%d')

# select variables of interest (windspeed and winddirection) and drop nan values
df_knmi = df_knmi[["YYYYMMDD", "DDVEC", "FHVEC", "RH"]].replace(r'^\s*$', np.nan, regex=True).dropna()

# convert variables to floats
df_knmi['FHVEC'] = df_knmi["FHVEC"].astype(np.float64)/10 # Vector mean windspeed (in m/s)
df_knmi['DDVEC'] = df_knmi["DDVEC"].astype(np.float64) # Vector mean wind direction in degrees (360=north; 90=east; 180=south; 270=west; 0=calm/variable)
df_knmi['RH'] = df_knmi["RH"].astype(np.float64)/10 # Daily precipitation amount (in mm)
df_knmi['RH'] = df_knmi['RH'].replace(-0.1, 0.05)

#%% settings

degrees = 48.7

fontsize = 15

col_letters = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)', '(g)', '(h)']
row_numbers = ['(i)', '(ii)', '(iii)', '(iv)', '(v)']


#%% plot: both case studies in 1 plot inlcude wind and crest lines

fig, ax = plt.subplots(5, 8, figsize=(32, 20))
plt.subplots_adjust(left=0.05,
                    right=0.97,
                    top=0.95,
                    bottom=0.05,
                    wspace=0.05,
                    hspace=0.05)

### windroses
for i in range(len(dif_paths)):

    axs = 0, i+1
    
    start_date = dif_paths[i].split('\\')[-1].split('_')[0]
    end_date   = dif_paths[i].split('\\')[-1].split('_')[1]
    
    mask = ((df_knmi["YYYYMMDD"] >= start_date) &
            (df_knmi["YYYYMMDD"] <= end_date))
    
    df_knmi_doi = df_knmi.loc[mask]
    df_knmi_doi_threshold = df_knmi_doi[df_knmi_doi["FHVEC"] >= 8]
    
    # rotate winddirection
    ddvec_rot =  (df_knmi_doi_threshold['DDVEC'] + degrees) %360
    
    # replace subplot with windrose
    pos = ax[axs].get_position()
    ax[axs].remove()
    ax_wr = WindroseAxes(fig, pos)
    fig.add_axes(ax_wr)
    ax[axs] = ax_wr
    
    ax_wr.bar(ddvec_rot,
              df_knmi_doi_threshold["FHVEC"],
              nsector=int(360 / 15),
              bins=[8, 10, 12],
              normed=False,
              opening=0.8, 
              edgecolor='white',
              # alpha=0.7,
              cmap=plt.cm.viridis)
    
    ax_wr.set_yticklabels([])
    
    ax_wr.set_thetagrids(
        angles=[0+degrees, 90+degrees, 180+degrees, 270+degrees],
        labels=['N', 'E', 'S', 'W'])
    
    ax_wr.grid(True)
    
    ax_wr.set_ylim(0, 5)
    ax_wr.set_yticks([])
    
ax_wr.legend(title="Wind speed [m/s]", 
             loc= "upper left", #"center", 
             bbox_to_anchor=(-7.525, 0.7),
             fontsize=fontsize-2,    
             title_fontsize=fontsize) 


### north difs

for i in range(len(dif_paths)):

    axs = 1, i+1
    
    # dif
    with rasterio.open(dif_paths[i]) as src:
        dif = src.read(1)
    dif_im = ax[axs].imshow(dif, 
                            cmap = 'RdBu', 
                            vmin = -0.5, 
                            vmax = 0.5,
                            extent = extent_dif,
                            transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                            origin = 'upper')
    
    # veg on top
    veg_im = ax[axs].imshow(veg, 
                            cmap = cmap_veg,
                            norm = norm,
                            extent = extent_veg,
                            transform = Affine2D().rotate_deg_around(veg_x_center, veg_y_center, -degrees) + ax[axs].transData,
                            origin = 'upper')

    
    # xlims and y lims
    ax[axs].set_xlim(rgb_x_center + 391.962-100, rgb_x_center + 391.962)
    ax[axs].set_xticks(np.arange(rgb_x_center + 391.962-100, rgb_x_center + 391.962, 20))
    ax[axs].set_xticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)

    ax[axs].set_ylim(rgb_y_center - 154.091 + 200, rgb_y_center - 154.091 + 300)
    ax[axs].set_yticks(np.arange(rgb_y_center - 154.091 + 200, rgb_y_center - 154.091 + 300, 20))
    ax[axs].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)
        
# ylabels
ax[1, 0].set_ylabel("Y [m]", fontsize = fontsize)

### north total dif
axs = 1,0
with rasterio.open(dif_tot) as src:
    dif = src.read(1)
dif_im = ax[axs].imshow(dif, 
                        cmap = 'RdBu', 
                        vmin = -0.5, 
                        vmax = 0.5,
                        extent = extent_dif,
                        transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# veg on top
veg_im = ax[axs].imshow(veg, 
                        cmap = cmap_veg,
                        norm = norm,
                        extent = extent_veg,
                        transform = Affine2D().rotate_deg_around(veg_x_center, veg_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# xlims and y lims
ax[axs].set_xlim(rgb_x_center + 391.962-100, rgb_x_center + 391.962)
ax[axs].set_xticks(np.arange(rgb_x_center + 391.962-100, rgb_x_center + 391.962, 20))
ax[axs].set_xticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)

ax[axs].set_ylim(rgb_y_center - 154.091 + 200, rgb_y_center - 154.091 + 300)
ax[axs].set_yticks(np.arange(rgb_y_center - 154.091 + 200, rgb_y_center - 154.091 + 300, 20))
ax[axs].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)



### north crests

for i in range(len(dif_paths)):
    axs = 2, i+1
    
    # # hillshade
    with rasterio.open(hill_paths[i+1]) as src:
        hill = src.read(1)
    hill = hill.astype(float) 
    hill[hill == 0] = np.nan
    
    ax[axs].imshow(hill,
                   cmap="gray",
                   vmin = 100,
                   vmax = 200,
                   extent = extent_hill,
                   transform = Affine2D().rotate_deg_around(hill_x_center, hill_y_center, -degrees) + ax[axs].transData,
                   origin="upper")
    
    # crests
    gdf = gpd.read_file(crest_loc[i+1]) 
    gdf_rot = gdf.copy()
    gdf_rot["geometry"] = gdf_rot.geometry.apply(lambda geom: rotate(geom,
                                                                     -degrees,
                                                                     origin=(veg_x_center, veg_y_center)))
    gdf_rot.plot(ax=ax[axs],
                 color="magenta",
                 linewidth=0.5,
                 zorder=10)
    
    
    # xlims and y lims
    ax[axs].set_xlim(rgb_x_center + 391.962-100, rgb_x_center + 391.962)
    ax[axs].set_xticks(np.arange(rgb_x_center + 391.962-100, rgb_x_center + 391.962, 20))
    ax[axs].set_xticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)

    ax[axs].set_ylim(rgb_y_center - 154.091 + 200, rgb_y_center - 154.091 + 300)
    ax[axs].set_yticks(np.arange(rgb_y_center - 154.091 + 200, rgb_y_center - 154.091 + 300, 20))
    ax[axs].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)
        
# ylabels
ax[2, 1].set_ylabel("Y [m]", fontsize = fontsize)



### south difs
    
for i in range(len(dif_paths)):

    axs = 3, i+1
    
    # dif
    with rasterio.open(dif_paths[i]) as src:
        dif = src.read(1)
    dif_im = ax[axs].imshow(dif, 
                            cmap = 'RdBu', 
                            vmin = -0.5, 
                            vmax = 0.5,
                            extent = extent_dif,
                            transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                            origin = 'upper')
    
    # veg on top
    veg_im = ax[axs].imshow(veg, 
                            cmap = cmap_veg,
                            norm = norm,
                            extent = extent_veg,
                            transform = Affine2D().rotate_deg_around(veg_x_center, veg_y_center, -degrees) + ax[axs].transData,
                            origin = 'upper')
    
    # xlims and y lims
    ax[axs].set_xlim(rgb_x_center - 397.023+100, rgb_x_center - 397.023+200)
    ax[axs].set_xticks(np.arange(rgb_x_center - 397.023+100, rgb_x_center - 397.023+200, 20))
    ax[axs].set_xticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)

    ax[axs].set_ylim(rgb_y_center - 154.091 + 40, rgb_y_center - 154.091 + 140)
    ax[axs].set_yticks(np.arange(rgb_y_center - 154.091 + 40, rgb_y_center - 154.091 + 140, 20))
    ax[axs].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)
    
# ylabels
ax[3, 0].set_ylabel("Y [m]", fontsize = fontsize)
ax[3, 0].set_xlabel("X [m]", fontsize = fontsize)

### south total dif
axs = 3,0
with rasterio.open(dif_tot) as src:
    dif = src.read(1)
dif_im = ax[axs].imshow(dif, 
                        cmap = 'RdBu', 
                        vmin = -0.5, 
                        vmax = 0.5,
                        extent = extent_dif,
                        transform = Affine2D().rotate_deg_around(dif_x_center, dif_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# veg on top
veg_im = ax[axs].imshow(veg, 
                        cmap = cmap_veg,
                        norm = norm,
                        extent = extent_veg,
                        transform = Affine2D().rotate_deg_around(veg_x_center, veg_y_center, -degrees) + ax[axs].transData,
                        origin = 'upper')

# xlims and y lims
ax[axs].set_xlim(rgb_x_center - 397.023+100, rgb_x_center - 397.023+200)
ax[axs].set_xticks(np.arange(rgb_x_center - 397.023+100, rgb_x_center - 397.023+200, 20))
ax[axs].set_xticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)

ax[axs].set_ylim(rgb_y_center - 154.091 + 40, rgb_y_center - 154.091 + 140)
ax[axs].set_yticks(np.arange(rgb_y_center - 154.091 + 40, rgb_y_center - 154.091 + 140, 20))
ax[axs].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)



### south crests
for i in range(len(dif_paths)):
    
    axs = 4, i+1
    
    # hillshade
    with rasterio.open(hill_paths[i+1]) as src:
        hill = src.read(1)
    hill = hill.astype(float) 
    hill[hill == 0] = np.nan
    
    ax[axs].imshow(hill,
                   cmap="gray",
                   vmin = 100,
                   vmax = 200,
                   extent = extent_hill,
                   transform = Affine2D().rotate_deg_around(hill_x_center, hill_y_center, -degrees) + ax[axs].transData,
                   origin="upper")
    
    # crests
    gdf = gpd.read_file(crest_loc[i+1]) 
    gdf_rot = gdf.copy()
    gdf_rot["geometry"] = gdf_rot.geometry.apply(lambda geom: rotate(geom,
                                                                     -degrees,
                                                                     origin=(veg_x_center, veg_y_center)))
    gdf_rot.plot(ax=ax[axs],
                 color="magenta",
                 linewidth=0.5,
                 zorder=10)
    
    # xlabels
    ax[axs].set_xlabel("X [m]", fontsize = fontsize)
    
    # xlims and y lims
    ax[axs].set_xlim(rgb_x_center - 397.023+100, rgb_x_center - 397.023+200)
    ax[axs].set_xticks(np.arange(rgb_x_center - 397.023+100, rgb_x_center - 397.023+200, 20))
    ax[axs].set_xticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)

    ax[axs].set_ylim(rgb_y_center - 154.091 + 40, rgb_y_center - 154.091 + 140)
    ax[axs].set_yticks(np.arange(rgb_y_center - 154.091 + 40, rgb_y_center - 154.091 + 140, 20))
    ax[axs].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)
        
# ylabels
ax[4, 1].set_ylabel("Y [m]", fontsize = fontsize)

# ticks and labels
for i in [1, 2, 3]:
    for j in [1,2,3,4,5,6,7]:
        ax[i, j].tick_params(labelbottom=False)
for j in range(2, ax.shape[1]):
    for i in range(ax.shape[0]):
        ax[i, j].tick_params(labelleft=False)
        
ax[1, 1].tick_params(labelleft=False)
ax[1, 3].tick_params(labelleft=False)

ax[1,2].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)
ax[1,4].set_yticklabels(np.linspace(0, 80, 5).astype(int), fontsize= fontsize)
        
# Indices to clear
empty_axes = [(0,0), (2,0), (4,0)]

for r, c in empty_axes:
    ax[r, c].clear()          # remove content
    ax[r, c].set_frame_on(False)
    ax[r, c].set_xticks([])
    ax[r, c].set_yticks([])
    ax[r, c].set_xlabel('')
    ax[r, c].set_ylabel('')

# north arrow
ax[0, 0].text(0.05, 0.95, u'\u25B2 \nN ', ha='left', va='top',
           transform=ax[0, 0].transAxes, fontsize= fontsize + 15, family='Arial',
           rotation=-degrees) 
    
# colorbar dif
pos = ax[0, 0].get_position()
cax_small = fig.add_axes([pos.x0 + pos.width * 0.65,   # move right (center it)
                          pos.y0,                     # same vertical position
                          pos.width * 0.1,           # smaller width
                          pos.height])                # full height
cbar = fig.colorbar(dif_im, 
                    cax=cax_small, 
                    orientation='vertical')
cbar.set_label('Elevation difference [m]', fontsize= fontsize)
cbar.ax.tick_params(labelsize= fontsize - 3)

# veg and crest legend
veg_patch = Patch(facecolor='green', edgecolor='none', label='Vegetation')
crest_line = Line2D([0], [0], color='magenta', lw=2, label='Ridges')
ax[0, 0].legend(handles=[veg_patch, crest_line],
               loc='upper left',
               bbox_to_anchor=(-0.02, 0.3),
               fontsize=fontsize,
               frameon=False)

# Column labels (above each column)
for j in range(ax.shape[1]):  # columns
    ax[0, j].text(0.5, 1.15, col_letters[j], 
                  ha='center', va='bottom', 
                  transform=ax[0, j].transAxes,
                  fontsize= fontsize) #, fontweight='bold')

# Row labels (left of each row)
for i in range(ax.shape[0]):  # rows
    ax[i, 0].text(-0.3, 0.5, row_numbers[i], 
                   ha='right', va='center',
                   transform=ax[i, 0].transAxes,
                   fontsize= fontsize) #, fontweight='bold', rotation=0)

plt.show()

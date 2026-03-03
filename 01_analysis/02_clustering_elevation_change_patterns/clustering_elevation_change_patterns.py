#!/usr/bin/env python
'''
Script to cluster a time series of DEMs into grouped elevation change patterns
'''

import numpy as np
import pandas as pd
import rasterio as rio
from glob import glob
import os
from pathlib import Path
from sklearn.cluster import KMeans



# load dems and stack into 3D array 
dems_folder = sorted(glob('01_DEMs/*_mean.tif'))

epochs = [Path(f).stem[:8] for f in dems_folder]


dems = []
hillshades = []
for i, (f, epoch) in enumerate(zip(dems_folder, epochs)):
    print(i, f, epoch)
    with rio.open(f) as src:
        dem = src.read(1)
        dem = np.where(dem == src.nodata, np.nan, dem)
        if i == 0:
            dems = np.ones((dem.shape[0], dem.shape[1], len(dems_folder))) * np.nan
            hillshades = np.ones((dem.shape[0], dem.shape[1], len(dems_folder))) * np.nan
        transform = src.transform
        hillshade = es.hillshade(dem, altitude=1)
        dems[:,:,i] = dem
        hillshades[:,:,i] = hillshade



# subtract first epoch to get changes only
dod = dems - dems[:,:,0][:,:,np.newaxis]



dod_consecutive = np.diff(dems, axis=2)




# kmans clustering of time series

n_clusters = 5

# reshape to 2D array (pixels, time)
X = dod.reshape(-1, dod.shape[2])
# remove rows with NaNs
mask = ~np.isnan(X).any(axis=1)
X_clean = X[mask]
# fit kmeans
kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X_clean)
# create empty array for labels
labels = np.full(X.shape[0], np.nan)
# assign labels to clean pixels
labels[mask] = kmeans.labels_
# reshape back to original shape
labels_2d = labels.reshape(dod.shape[0], dod.shape[1])


# Do kmeans for a range of cluster numbers and plot the variance
from sklearn.metrics import silhouette_score
cluster_range = range(2, 11)
variances = []
silhouette_scores = []
for i, n_clusters in enumerate(cluster_range):
    print(i)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X_clean)
    variances.append(kmeans.inertia_)

# plot variance
fig, ax = plt.subplots(1, 2, figsize=(12, 5))
ax[0].plot(cluster_range, variances, marker='o')
ax[0].set_title('KMeans Variance vs Number of Clusters')
ax[0].set_xlabel('Number of Clusters')
ax[0].set_ylabel('Variance (Inertia)')

# Convert epochs to datetime if needed
dates = pd.to_datetime(epochs)

# save cluster average height to csv
column_names = ['cluster1','cluster2','cluster3','cluster4','cluster5']

df_kmeans = pd.DataFrame(index=dates, columns=column_names)
df_kmeans.index.name = 'epoch'
df_kmeans.loc[dates, column_names] = kmeans.cluster_centers_.T
df_kmeans.sort_index(inplace=True)
df_kmeans.to_csv('06_csv_parameters/clusters.csv')


# export the cluster maps as geotiffs

out_file = '04_clusters/clusters.tif'
with rio.open(
    out_file,
    'w',
    driver='GTiff',
    height=labels_2d.shape[0],
    width=labels_2d.shape[1],
    count=1,
    dtype=labels_2d.dtype,
    crs=src.crs,
    transform=transform,
    nodata=np.nan
) as dst:
    dst.write(labels_2d, 1)


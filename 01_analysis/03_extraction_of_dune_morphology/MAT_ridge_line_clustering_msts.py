#!/usr/bin/env python
'''
Script to cluster the ridge points based on DBSCAN, and then compute connected ridgelines based on the Minimum Spanning Tree

'''
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import rasterio as rio
from glob import glob
import os
from pathlib import Path
from sklearn.decomposition import PCA
from shapely.geometry import LineString
import networkx as nx
from scipy.spatial import Delaunay


# ## Cluster separate dunes based on projected ridge points

ridge_point_file_list = sorted(glob('05_ridge_lines/ridge_points/*int_ridge.shp'))

ridge_point_file_list_epochs = [Path(f).stem[:8] for f in ridge_point_file_list]

print(f"computing clusters of dune ridges and connected ridgelines (forest graph) for epochs: \n {ridge_point_file_list_epochs}")

files = ridge_point_file_list
epochs = ridge_point_file_list_epochs



count_filter = 2 
radius_filter = 10000 
def load_with_tag(files, epochs, region):
    gdfs = []
    for f, epoch in zip(files, epochs):

        gdf = gpd.read_file(f)
        gdf = gdf.to_crs(epsg=28992)
        gdf["epoch"] = epoch
        gdf["date"] = pd.to_datetime(epoch)

        gdf["region"] = region

        # we filter the ridges on count if there is a ridge with only 1 count we do not use it as it is not reliable
        # it should at least be defined by two sides
        gdf = gdf[gdf['count'] > count_filter]
        gdf = gdf[gdf['r'] < radius_filter]

        # we also drop duplicate points
        gdf.drop_duplicates(subset=['X','Y'], inplace=True)
        gdf.reset_index(drop=True, inplace=True)
        gdfs.append(gdf)
    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
print("loading epochs")
gdf_ridges = load_with_tag(files, epochs, "south")


# now for every epoch we cluster points that lie close together using dbscan

from sklearn.cluster import DBSCAN
def cluster_ridges(gdf, eps=0.5, min_samples=10):
    xy = gdf[['X','Y']].values
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(xy)
    gdf['cluster'] = clustering.labels_
    return gdf
eps, min_samples = 1.0, 4 # for short-term 1.0, 4, for long-term  2.0, 2
for epoch, gdf in gdf_ridges.groupby('epoch'):
    print(f"clustering {epoch}")
    gdf_clustered = cluster_ridges(gdf, eps=eps, min_samples=min_samples)
    gdf_ridges.loc[gdf_clustered.index, 'cluster'] = gdf_clustered['cluster']
gdf_ridges['cluster'] = gdf_ridges['cluster'].astype(int)
gdf_ridges = gdf_ridges[gdf_ridges['cluster'] != -1].copy() # filter noise points 




# export a gpkg per epoch with cluster added
#for epoch, gdf in gdf_ridges.groupby('epoch'):
#    print(f"exporting clusters of {epoch}")
#    gdf.to_file(f'{epoch}_south_int_mat_count_filter_{count_filter}_clustered_dbscan_eps_{eps}_min_{min_samples}_minr_{radius_filter}.gpkg')


# ## create forests of connected component trees

# now we make a delaunay triangulation and minimum spanning tree

def clusters_to_msts(gdf_epoch):
    """
    Convert clustered points in one epoch into dicts of:
      - MST graphs
      - intermediate triangulation graphs (before pruning to MST).
    Noise points (cluster == -1) are added as isolated nodes.
    Returns: (msts, triangulations)
    """
    msts = {}
    triangulations = {}

    for cluster_id, group in gdf_epoch[gdf_epoch["cluster"] != -1].groupby("cluster"):
        points = group[["X", "Y"]].values
        n = len(points)

        # base graph with nodes
        G = nx.Graph()
        for idx, (x, y) in enumerate(points):
            G.add_node(idx, pos=(x, y))

        edges = set()

        if n == 1:
            pass
        elif n == 2:
            edges.add((0, 1))
        else:
            try:
                tri = Delaunay(points)
                for simplex in tri.simplices:
                    edges.update([(simplex[i], simplex[j]) for i in range(3) for j in range(i + 1, 3)])
            except:
                # degenerate case: connect in sorted order along longer axis
                range_x = points[:, 0].max() - points[:, 0].min()
                range_y = points[:, 1].max() - points[:, 1].min()
                sort_axis = 0 if range_x > range_y else 1
                order = np.argsort(points[:, sort_axis])
                for i in range(len(order) - 1):
                    edges.add((order[i], order[i + 1]))

        # add edges with Euclidean weights
        for i, j in edges:
            dist = np.linalg.norm(points[i] - points[j])
            G.add_edge(i, j, weight=dist)

        # store triangulation graph
        triangulations[cluster_id] = G.copy()

        # MST from the graph
        if len(G.nodes) > 0:
            mst = nx.minimum_spanning_tree(G, weight="weight")
            msts[cluster_id] = mst

    # handle noise points as isolated nodes
    noise = gdf_epoch[gdf_epoch["cluster"] == -1]
    for i, row in noise.iterrows():
        G = nx.Graph()
        G.add_node(0, pos=(row["X"], row["Y"]))
        msts[f"noise_{i}"] = G
        triangulations[f"noise_{i}"] = G.copy()

    return msts, triangulations


forests = {}
triangulations_all = {}
for epoch, gdf_epoch in gdf_ridges.groupby("epoch"):
    print(f"computing triangulation of {epoch}")
    msts, triangulations = clusters_to_msts(gdf_epoch)
    forests[epoch] = msts
    triangulations_all[epoch] = triangulations


def export_forest_to_gpkg(forest, epoch, filepath, min_subsegment_length=-1):
    """
    Export a forest (MSTs or triangulations) to a gpkg with polylines for each subsegment.
    """
    records = []

    for tree_id, T in forest.items():
        visited = set()
        for node in T.nodes:
            if T.degree(node) != 2:
                for neigh in T.neighbors(node):
                    if (node, neigh) in visited or (neigh, node) in visited:
                        continue
                    segment = [node, neigh]
                    visited.add((node, neigh))
                    prev, curr = node, neigh
                    while T.degree(curr) == 2:
                        next_nodes = [n for n in T.neighbors(curr) if n != prev]
                        if not next_nodes:
                            break
                        next_node = next_nodes[0]
                        segment.append(next_node)
                        visited.add((curr, next_node))
                        prev, curr = curr, next_node

                    if len(segment) >= min_subsegment_length:
                        coords = [T.nodes[n]["pos"] for n in segment]
                        line = LineString(coords)
                        records.append({"tree_id": tree_id, "epoch": epoch, "geometry": line})

    gdf = gpd.GeoDataFrame(records, crs="EPSG:28992")
    gdf.to_file(filepath)
    print(f"Exported {len(gdf)} subsegments for epoch {epoch} to {filepath}")

# Export MSTs
for epoch in forests.keys():
    print(f"exporting forest and triangulation of {epoch}")
    export_forest_to_gpkg(
        forests[epoch],
        epoch,
        f'05_ridge_lines/ridge_lines/msts_polylines_{epoch}_south_int_mat_count_filter_{count_filter}_clustered_dbscan_eps_{eps}_min_{min_samples}.gpkg'
    )


def analyze_tree(T):
    stats = {}

    # 1. Total tree length
    total_length = sum(nx.get_edge_attributes(T, "weight").values())
    stats["total_length"] = total_length

    # 2. Longest shortest path (diameter, weighted)
    lengths = dict(nx.all_pairs_dijkstra_path_length(T, weight="weight"))
    max_dist = 0
    max_pair = None
    for u, dists in lengths.items():
        for v, dist in dists.items():
            if dist > max_dist:
                max_dist = dist
                max_pair = (u, v)
    stats["longest_shortest_path"] = max_dist
    stats["diameter_pair"] = max_pair

    # 3. Ratio between longest shortest path and total length
    stats["diameter_ratio"] = max_dist / total_length if total_length > 0 else np.nan

    # 4. Degree statistics
    degrees = [d for _, d in T.degree()]
    stats["degree_mean"] = np.mean(degrees)
    stats["degree_median"] = np.median(degrees)
    stats["degree_max"] = np.max(degrees)
    stats["degree_min"] = np.min(degrees)
    stats["degree_distribution"] = degrees

    # 5. Orientation of longest ridge (via PCA on longest path coords)
    if max_pair:
        u, v = max_pair
        path = nx.shortest_path(T, source=u, target=v, weight="weight")
        coords = np.array([T.nodes[n]["pos"] for n in path])

        if len(coords) > 1:
            # PCA on path coordinates
            pca = PCA(n_components=2)
            pca.fit(coords)
            vec = pca.components_[0]   # first principal axis
            angle = (90 - np.degrees(np.arctan2(vec[1], vec[0]))) % 180

            stats["orientation_angle"] = angle

    # 6. Subsegments: paths from endpoints/branchpoints until next branchpoint/endpoint
    subsegments = []
    subsegment_orientations = []

    visited_edges = set()
    for node in T.nodes:
        if T.degree(node) != 2:  # endpoint or branchpoint
            for neighbor in T.neighbors(node):
                edge = tuple(sorted((node, neighbor)))
                if edge in visited_edges:
                    continue

                segment = [node, neighbor]
                visited_edges.add(edge)

                # walk until next non-degree-2 node
                while T.degree(segment[-1]) == 2:
                    next_nodes = [n for n in T.neighbors(segment[-1]) if n != segment[-2]]
                    if not next_nodes:
                        break
                    next_node = next_nodes[0]
                    segment.append(next_node)
                    visited_edges.add(tuple(sorted((segment[-2], next_node))))

                subsegments.append(segment)

                # inside analyze_tree, subsegment loop
                coords = np.array([T.nodes[n]["pos"] for n in segment])
                if coords.shape[0] >= 8:  # minimum points to compute orientation
                    pca = PCA(n_components=2)
                    pca.fit(coords)
                    vec = pca.components_[0]
                    angle = (90 - np.degrees(np.arctan2(vec[1], vec[0]))) % 180  # azimuth convention: 0=N, 90=E
                    subsegment_orientations.append(angle)
                else:
                    subsegment_orientations.append(np.nan)
    stats["n_subsegments"] = len(subsegments)
    stats["subsegments"] = subsegments
    stats["subsegment_orientations"] = subsegment_orientations
    return stats

def analyze_forest(forest, epoch):
    print(f'analysing forest {epoch}')
    tree_stats = {k: analyze_tree(T) for k, T in forest.items()}

    # collect values
    lengths = [s["total_length"] for s in tree_stats.values()]
    diameters = [s["longest_shortest_path"] for s in tree_stats.values()]
    diameter_ratios = [s["diameter_ratio"] for s in tree_stats.values() if not np.isnan(s["diameter_ratio"])]
    degrees_all = [d for s in tree_stats.values() for d in s["degree_distribution"]]
    orientations = [s["orientation_angle"] for s in tree_stats.values() if "orientation_angle" in s]
    subsegments = [s["n_subsegments"] for s in tree_stats.values()]

    forest_stats = {
        "n_trees": len(forest),
        "total_length": np.sum(lengths),
        "mean_tree_length": np.mean(lengths) if lengths else np.nan,
        "std_tree_length": np.std(lengths) if lengths else np.nan,

        "mean_diameter": np.mean(diameters) if diameters else np.nan,
        "std_diameter": np.std(diameters) if diameters else np.nan,

        "mean_diameter_ratio": np.mean(diameter_ratios) if diameter_ratios else np.nan,
        "std_diameter_ratio": np.std(diameter_ratios) if diameter_ratios else np.nan,

        "mean_degree": np.mean(degrees_all) if degrees_all else np.nan,
        "std_degree": np.std(degrees_all) if degrees_all else np.nan,
        "max_degree": np.max(degrees_all) if degrees_all else np.nan,

        "mean_orientation": np.mean(orientations) if orientations else np.nan,
        "std_orientation": np.std(orientations) if orientations else np.nan,

        "mean_subsegments": np.mean(subsegments) if subsegments else np.nan,
        "std_subsegments": np.std(subsegments) if subsegments else np.nan,
        "total_subsegments": np.sum(subsegments),
    }

    return tree_stats, forest_stats

all_tree_stats = {}
all_forest_stats = {}

for epoch in forests.keys():
    forest = forests[epoch]
    print(f"analyzing forest of epoch {epoch}")
    t_stats, f_stats = analyze_forest(forest, epoch)
    all_tree_stats[epoch] = t_stats
    all_forest_stats[epoch] = f_stats

df_forest_stats = pd.DataFrame.from_dict(all_forest_stats, orient="index")

# for every 15th quantile we count the number of ridgelines with that orientation, for each epoch
orientation_bins = np.arange(0, 181, 15)
orientation_counts = {}
for epoch, t_stats in all_tree_stats.items():
    angles = []
    for tree in t_stats.values():
        angles.extend([a for a in tree['subsegment_orientations'] if not np.isnan(a)])
    counts, _ = np.histogram(angles, bins=orientation_bins)
    orientation_counts[epoch] = counts
df_orientation_counts = pd.DataFrame.from_dict(orientation_counts, orient="index", columns=[f"{orientation_bins[i]}-{orientation_bins[i+1]}" for i in range(len(orientation_bins)-1)])
df_orientation_counts.to_csv('06_csv_parameters/ridge_orientation_counts_15deg.csv')


# -*- coding: utf-8 -*-
"""

this script plots the timeline of total volume change, derived volume change, and mean cluster elevation from the overview.csv file
and the polar plot of the orientation of ridge lines
"""
import os
import os.path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


plt.style.use('seaborn-v0_8')

df = pd.read_csv(
    "06_csv_parameters/overview.csv"
)


# convert date to datetime
df["epoch"] = pd.to_datetime(df["epoch"], format="%d/%m/%Y")

# create figure with 3 subplots
fig, axs = plt.subplots(
    3, 1,
    figsize=(8, 7),
    sharex=True,
    constrained_layout=True,
    height_ratios=[1, 1, 2]
)

# --------------------------
# (a) Total volume change
# --------------------------
df['total_volume'] = df['b_vol_acc'] + df['b_vol_ero']
df.loc[0, 'total_volume'] = 0
df['total_volume'] = np.cumsum(df['total_volume'])

axs[0].plot(
    df["epoch"],
    df['total_volume'],
    color='tab:blue',
    alpha=0.7
)

axs[0].set_ylabel('Volume change (m³)')

# panel label
axs[0].text(
    0.01, 0.95, '(a)',
    transform=axs[0].transAxes,
    fontsize=11,
    fontweight='bold',
    va='top'
)

# --------------------------
# (b) Volume change rates
# --------------------------
axs[1].bar(df["epoch"] - pd.Timedelta(days=7.5), df['vol_acc_dT'], width=5, label='Accretional', color='tab:blue', alpha=0.7) 
axs[1].bar(df["epoch"] - pd.Timedelta(days=2.5), -df['vol_ero_dT'], width=5, label='Erosional', color='tab:red', alpha=0.7) 
axs[1].bar(df["epoch"] + pd.Timedelta(days=7.5), df['vol_net_dT'], width=5, label='Net', color='tab:green', alpha=0.7) 
axs[1].bar(df["epoch"] + pd.Timedelta(days=2.5), df['vol_gross_dT'], width=5, label='Gross', color='tab:orange', alpha=0.7)

axs[1].set_ylabel('Volume change rate (m³/day)', loc='top')
axs[1].legend(loc='upper left', ncols=2, fontsize='small')

# panel label
axs[1].text(
    0.01, 0.65, '(b)',
    transform=axs[1].transAxes,
    fontsize=11,
    fontweight='bold',
    va='top'
)

# --------------------------
# (c) Mean elevation change
# --------------------------
cluster_names = [f'merged_cluster{i}' for i in range(1, 6)]
colors_clusters = [
    'tab:cyan',
    'tab:orange',
    'red',
    'tab:purple',
    'gold'
]

cluster_labels = [
    'C4',
    'C2',
    'C1',
    'C5',
    'C3'
]

for i, cluster_name in enumerate(cluster_names):
    axs[2].plot(
        df["epoch"],
        df[cluster_name],
        color=colors_clusters[i],
        marker='o',
        label=cluster_labels[i],
    )

# vegetation
axs[2].plot(
    df["epoch"],
    df["veg_mean_height"] - df["veg_mean_height"].iloc[0],
    marker='o',
    color='green',
    linestyle='--',
    label='Vegetation',
    alpha=0.7
)

axs[2].set_ylabel('Elevation change (m)')
axs[2].legend(loc='upper left', ncols=2, fontsize='small')

# panel label
axs[2].text(
    0.01, 0.76, '(c)',
    transform=axs[2].transAxes,
    fontsize=11,
    fontweight='bold',
    va='top'
)


axs[2].set_xticks(df["epoch"])
axs[2].set_xticklabels(
    df["epoch"].dt.strftime('%Y-%m-%d'),
    rotation=45,
    ha='right'
)


# align y-labels
fig.align_ylabels(axs)

plt.savefig(
    'combined_timeseries.png',
    dpi=300
)


# --------------------------
# Plot orientation of ridges polar plot
# --------------------------

ridge_columns =  [col for col in df.columns if 'ridge_orientation' in col]

# dates to Month Year in stead of YYYY-MM-DD
df['epoch_month_year'] = df['epoch'].dt.strftime('%b %Y')

fig2, axs2 = plt.subplots(2,4, subplot_kw={'projection': 'polar'}, figsize=(8,4), constrained_layout=True)
axs2 = axs2.flatten()
for i, epoch in enumerate(df['epoch']):
    # windrose for ridge orientation
    ax_ridge = axs2[i]
    df_epoch = df[df['epoch'] == epoch]

    # get ridge orientations
    # make polar histogram
    counts = []

    for col in ridge_columns:
        counts.extend(df_epoch[col])
    counts = np.array(counts)
    orientation_bins = np.arange(0, 181, 15) # 1 degree bins from 0 to 180
    angles = np.radians(orientation_bins[:-1])  # center of bins
    widths = np.radians(np.diff(orientation_bins))

    ax_ridge.bar(angles, counts, width=widths, bottom=0.0, alpha=0.7, edgecolor='k',align='edge')

    # also mirror
    ax_ridge.bar(angles + np.pi, counts, width=widths, bottom=0.0, alpha=0.7, edgecolor='k',align='edge')
    
    ax_ridge.set_ylim(0, max(df[ridge_columns].max())*1.1)
    ax_ridge.set_rlabel_position(ax_ridge.get_rlabel_position()-70)
    ax_ridge.set_title(f"{df[df['epoch'] == epoch]['epoch_month_year'].iloc[0]}", va='bottom', fontsize=8)
    ax_ridge.set_theta_zero_location('N')  # 0 degrees at top (north)
    ax_ridge.set_theta_direction(-1)       # clockwise
    ax_ridge.set_xticklabels([])
    # add a North label
    ax_ridge.text(0, ax_ridge.get_ylim()[1]*0.95, 'N', ha='center', va='center', fontsize=8, fontweight='bold')
    # Only keep rlabels for the first subplot
    if i != 0:
        ax_ridge.set_yticklabels([])

plt.savefig('ridge_orientations.png', dpi=300)
plt.show()


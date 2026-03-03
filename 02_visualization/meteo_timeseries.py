# -*- coding: utf-8 -*-
"""
Created on Fri Feb 20 16:35:04 2026

@author: rlhulskamp
"""

# this script plot the meteo data for the total study period

# import packages
import os
import os.path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates

plt.style.use('seaborn-v0_8')

knmi_data = # \09_meteo_data\knmi_330_hvh_20240227_20250819.txt

# load meteo data
df_knmi = pd.read_csv(knmi_data, skiprows = 46) 

# convert date to datetime-string
df_knmi["YYYYMMDD"] = pd.to_datetime(df_knmi["YYYYMMDD"], format='%Y%m%d')

# select variables of interest (windspeed and winddirection) and drop nan values
df_knmi = df_knmi[["YYYYMMDD", "DDVEC", "FHVEC", "RH"]].replace(r'^\s*$', np.nan, regex=True).dropna()

# convert variables to floats
df_knmi['FHVEC'] = df_knmi["FHVEC"].astype(np.float64)/10 # Vector mean windspeed (in m/s)
df_knmi['DDVEC'] = df_knmi["DDVEC"].astype(np.float64) # Vector mean wind direction in degrees (360=north; 90=east; 180=south; 270=west; 0=calm/variable)
df_knmi['RH'] = df_knmi["RH"].astype(np.float64)/10 # Daily precipitation amount (in mm)
df_knmi['RH'] = df_knmi['RH'].replace(-0.1, 0.05)

# set dates of interest
start_date = "20240607"
end_date = "20250617"
mask = (df_knmi["YYYYMMDD"] >= start_date) & (df_knmi["YYYYMMDD"] <= end_date)

# clip dataset on period
df_knmi_doi = df_knmi.loc[mask]

# clip on winspeeds above 8 m/s
df_knmi_doi_threshold = df_knmi_doi.loc[(df_knmi_doi["FHVEC"] >= 8)]

# measurement days
vlines = ["2024-06-07", "2024-07-17", "2024-09-17", "2024-10-09",
          "2024-11-15", "2025-02-14", "2025-05-14", "2025-06-17"]
vlines_dt = pd.to_datetime(vlines)

### plot
fontsize = 20

fig = plt.figure(figsize=(25, 12))

gs = GridSpec(nrows=3,
              ncols=2,
              width_ratios=[3, 1], 
              height_ratios=[1, 1, 1],
              wspace=0.075,
              hspace=0.1)

ax_ws = fig.add_subplot(gs[0, 0])
ax_wd = fig.add_subplot(gs[1, 0], sharex=ax_ws)
ax_pr = fig.add_subplot(gs[2, 0], sharex=ax_ws)

### (a) wind speed
ax_ws.plot(df_knmi_doi["YYYYMMDD"],
           df_knmi_doi["FHVEC"])
ax_ws.scatter(df_knmi_doi_threshold["YYYYMMDD"],
              df_knmi_doi_threshold["FHVEC"],
              color="red",
              s=20,
              zorder=3)
ax_ws.axhline(y=8,
              color="red",
              linestyle="--",
              linewidth=1,)
ax_ws.set_ylabel("Wind speed [m/s]", fontsize=fontsize)
ax_ws.tick_params(axis='both', labelsize=fontsize-2)

### (b) wind direction
ax_wd.scatter(df_knmi_doi_threshold["YYYYMMDD"],
              df_knmi_doi_threshold["DDVEC"],
              color="red",
              s=20,
              zorder=3)
ax_wd.set_ylabel("Wind direction [°]", fontsize=fontsize)
ax_wd.set_ylim(0, 360)
ax_wd.set_yticks([0, 90, 180, 270],) 
ax_wd.tick_params(axis='both', labelsize=fontsize-2)

### (c) rainfall
ax_pr.plot(df_knmi_doi["YYYYMMDD"],
           df_knmi_doi["RH"])
ax_pr.scatter(df_knmi_doi_threshold["YYYYMMDD"],
              df_knmi_doi_threshold["RH"],
              color="red",
              s=20,
              zorder=3)
ax_pr.set_ylabel("Rainfall [mm]", fontsize=fontsize)
ax_pr.set_xlabel("Date", fontsize=fontsize)
ax_pr.tick_params(axis='both', labelsize=fontsize-2)

### (d) wind rose
ax_wr = fig.add_subplot(gs[:, 1], projection="windrose")
ax_wr.bar(df_knmi_doi_threshold["DDVEC"], # wind direction
          df_knmi_doi_threshold["FHVEC"], # wind speed
          nsector = 24, # nr of direction bins
          bins = [8, 10, 12], # nr of 'speed' bins
          normed=False, 
          opening=0.8, 
          edgecolor='white',
          cmap = plt.cm.viridis)
ax_wr.legend(title="Wind speed [m/s]", loc="upper left", bbox_to_anchor=(-0.13, 0.04),
             fontsize=fontsize-2,        
             title_fontsize=fontsize)  
ax_wr.tick_params(labelsize=fontsize-2)

# Add panel letters
ax_ws.text(0.01, 0.97, '(a)', transform=ax_ws.transAxes,
           fontsize=fontsize+2, 
           va='top', ha='left')

ax_wd.text(0.01, 0.97, '(b)', transform=ax_wd.transAxes,
           fontsize=fontsize+2, 
           va='top', ha='left')

ax_pr.text(0.01, 0.97, '(c)', transform=ax_pr.transAxes,
           fontsize=fontsize+2, 
           va='top', ha='left')

ax_wr.text(-0.09, 1.03, '(d)', transform=ax_wr.transAxes,
           fontsize=fontsize+2, 
           va='top', ha='left')



# set xticks
ax_pr.set_xticks(vlines_dt)
ax_pr.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax_pr.get_xticklabels(), rotation=45, ha='right')
fig.autofmt_xdate()
ax_pr.tick_params(axis='x', labelrotation=45)

# vertical lines of measurement dates
for d in vlines_dt:
    ax_ws.axvline(d, color='grey', linestyle='--', linewidth=1, zorder = 1)
    ax_wd.axvline(d, color='grey', linestyle='--', linewidth=1, zorder = 1)
    ax_pr.axvline(d, color='grey', linestyle='--', linewidth=1, zorder = 1) 

plt.show()

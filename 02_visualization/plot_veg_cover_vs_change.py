#!/usr/bin/env python
'''
Script to visualise the vegetation cover vs the mean, standard deviation and coefficient of variation of the elevation change
'''
import os
import os.path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
print(plt.style.available)
plt.style.use('seaborn-v0_8')

df = pd.read_csv("/06_csv_parameters/overview.csv")

# convert date to datetime-string
df["epoch"] = pd.to_datetime(df["epoch"], format="%d/%m/%Y")
# compute number of days since previous epoch
df['day_diff'] = df['epoch'].diff().dt.days / 365.25


# import veggie and dz
directory = '/06_csv_parameters/vegcover_dzmean' 
df0 = pd.read_csv(rf"{directory}/vegcov_dz_0.csv")
df1 = pd.read_csv(rf"{directory}/vegcov_dz_1.csv")
df2 = pd.read_csv(rf"{directory}/vegcov_dz_2.csv")
df3 = pd.read_csv(rf"{directory}/vegcov_dz_3.csv")
df4 = pd.read_csv(rf"{directory}/vegcov_dz_4.csv")
df5 = pd.read_csv(rf"{directory}/vegcov_dz_5.csv")
df6 = pd.read_csv(rf"{directory}/vegcov_dz_6.csv")

# merge the dfs, where veg_cov is one column (equal in all) and dz_mean is a ddifferent column for each
df_veg_dz = df0[['veg_cov']].copy()
df_veg_dz['dz_mean_0'] = df0['dz_mean']
df_veg_dz['dz_mean_1'] = df1['dz_mean']
df_veg_dz['dz_mean_2'] = df2['dz_mean']
df_veg_dz['dz_mean_3'] = df3['dz_mean']
df_veg_dz['dz_mean_4'] = df4['dz_mean']
df_veg_dz['dz_mean_5'] = df5['dz_mean']
df_veg_dz['dz_mean_6'] = df6['dz_mean']

# change dz_mean to a rate of dz_mean per day using the epochs differences in days from df['epoch']
day_diffs = df['day_diff'].values[1:]
df_veg_dz['dz_mean_0'] = df_veg_dz['dz_mean_0'] / day_diffs[0]
df_veg_dz['dz_mean_1'] = df_veg_dz['dz_mean_1'] / day_diffs[1]
df_veg_dz['dz_mean_2'] = df_veg_dz['dz_mean_2'] / day_diffs[2]
df_veg_dz['dz_mean_3'] = df_veg_dz['dz_mean_3'] / day_diffs[3]
df_veg_dz['dz_mean_4'] = df_veg_dz['dz_mean_4'] / day_diffs[4]
df_veg_dz['dz_mean_5'] = df_veg_dz['dz_mean_5'] / day_diffs[5]
df_veg_dz['dz_mean_6'] = df_veg_dz['dz_mean_6'] / day_diffs[6]
# compute the stdev of dz_mean columns
df_veg_dz['dz_mean_std'] = df_veg_dz[['dz_mean_0', 'dz_mean_1', 'dz_mean_2', 'dz_mean_3', 'dz_mean_4', 'dz_mean_5', 'dz_mean_6']].std(axis=1)
df_veg_dz['dz_mean_mean'] = df_veg_dz[['dz_mean_0', 'dz_mean_1', 'dz_mean_2', 'dz_mean_3', 'dz_mean_4', 'dz_mean_5', 'dz_mean_6']].mean(axis=1)

# plot scatters
fig, axs = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
axs[0].scatter(df_veg_dz['dz_mean_mean'], df_veg_dz['veg_cov'], color='tab:blue', s=5)
axs[0].set_xlabel('Mean elevation change rate (m/year)')
axs[0].set_ylabel('Vegetation cover (%)') 
axs[0].set_title('(a)')
axs[0].set_xlim(-0.8, 0.8)

axs[1].set_title('(b)')
axs[1].set_xlim(0, 1.75)
axs[1].set_xlabel('Stdev. of elevation change rate (m/year)')
axs[1].scatter(df_veg_dz['dz_mean_std'], df_veg_dz['veg_cov'], color='tab:green', s=5)

axs[2].set_title('(c)')
axs[2].set_xlim(-15,15)
axs[2].set_xlabel('Coef. of variation of elevation change rate')
axs[2].scatter(df_veg_dz['dz_mean_std']/(df_veg_dz['dz_mean_mean']), df_veg_dz['veg_cov'], color='tab:orange', s=5)
plt.tight_layout()
plt.show()
plt.savefig(r"vegetation_cover_coef_variance_mean.png", dpi=300)



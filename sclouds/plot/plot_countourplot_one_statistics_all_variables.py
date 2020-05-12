""" Plotting routine used to plot subplots of spatially averages monthly means
and filtered by land sea and both.
"""
import numpy as np
import xarray as xr
import seaborn as sns
import glob
import os

from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)

from sclouds.helpers import (path_input, path_stats_results, VARIABLES,
                                UNITS, LONGNAME, STATISTICS, LONGNAME_STATISTICS)
from sclouds.io.utils import get_xarray_dataset_for_period
from sclouds.plot.helpers import (TEXT_WIDTH_IN, TEXT_HEIGHT_IN,
                                    path_python_figures, import_matplotlib,
                                    cmap_contour_plot, levels_contourplot,
                                    color_maps)
mat = import_matplotlib() #for mye
import matplotlib.pyplot as plt

n_rows = len(VARIABLES)
n_cols = 1
levels_contourplot = 100


for stat in STATISTICS: #['mean']:#STATISTICS:
    fig, axes =  plt.subplots(nrows = n_rows, ncols = n_cols, sharex=True, sharey=False)
    fig.set_size_inches(w = TEXT_WIDTH_IN, h = TEXT_HEIGHT_IN - 1 - 2)
    fig.suptitle(LONGNAME_STATISTICS[stat], fontsize = 16)
    for var, ax in zip(VARIABLES, axes):
        #if var != 'tcc':
        #print('Warning this duplicates the RH in plot for tcc')
        files = glob.glob(path_stats_results + '/*pixel*{}*all.nc'.format(var))
        if len(files) != 1:
            print(files)
        data = xr.open_dataset(files[0])

        vals = data[stat].values

        if var != 'tcc':
            vals   = np.flipud(vals)

        cntours = ax.contourf(vals, levels=levels_contourplot, cmap=color_maps[var])

        # Removes white lines
        for c in cntours.collections:
            c.set_edgecolor("face")

        fig.colorbar(cntours, ax=ax, label = '{} [{}]'.format(var, UNITS[var]))
        #a = sns.heatmap(vals, ax = ax, cbar = True, cmap = 'viridis', linewidths=0)
        ax.set_title(LONGNAME[var], fontsize = 14)
        ax.set_ylabel('Latitude')

        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.yaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))

        ax.set_yticklabels(labels = np.linspace(30, 50, 5))
        ax.set_xticklabels(labels = np.linspace(-20, 25, 10), rotation = 45)

    plt.xlabel('Longitude')
    plt.subplots_adjust(wspace = 0.2, hspace = 0.3, top=0.9, bottom=0.1, left = 0.14, right = .95)
    plt.savefig(path_python_figures + 'contourplot_all_variables_{}.pdf'.format(stat))
    print('Finished {}'.format(stat))

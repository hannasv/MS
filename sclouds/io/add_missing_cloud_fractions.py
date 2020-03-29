#!/usr/bin/env python
# coding: utf-8

# ## Calculate Cloud Fractions

# In[1]:

import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import xarray as xr

import glob
import xarray as xr
import numpy as np


# In[2]:


#data_dir = '/home/hanna/MS-suppl/files/'
data_dir = '/uio/hume/student-u89/hannasv/MS-suppl/'
path = '/uio/lagringshotell/geofag/projects/miphclac/hannasv/'
save_dir = '/uio/lagringshotell/geofag/projects/miphclac/hannasv/fractions_repo/'

data_monthly_repo = '/uio/lagringshotell/geofag/students/metos/'

import logging
LOG_FILENAME = 'example.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

logging.debug('This message should go to the log file')

def read_dlon_dlat(data_dir):
    """ Reading in the coordinate information."""

    nc_files = glob.glob(data_dir+'*small*.json')
    #print(nc_files[-1])
    with open(nc_files[-1]) as f:
        d =  json.load(f)

    d_phi      = d['dphi']
    d_theta    = d['dtheta']
    cell_areas = d['cell_area']
    lat_array  = d['lat']
    lon_array  = d['lon']
    return d_phi, d_theta, cell_areas, lat_array, lon_array

d_phi, d_theta, cell_areas, lat_array, lon_array = read_dlon_dlat(data_dir)

def clean_file(satfil):
    """Cleaning the raw files. Rewrinting it from 4 digit to binary."""
    if satfil.split('.')[-1] == 'grb':
        try:
            cloudMask = xr.open_dataset(satfil, engine = 'cfgrib')
        except EOFError as e:
            logging.debug(e)
            return None

        o = cloudMask['p260537'].values.reshape( (3712, 3712) )

        o[o>=3.0]=np.nan
        o[o==1.0]=0
        o[o==2.0]=1.0
    else:
        cloudMask = xr.open_dataset(satfil)
        o = cloudMask['cloudMask'].values.reshape( (3712, 3712) )
    return o

def area_grid_cell(c_lat, d_lat, d_lon):
    """ Computing the are of a pixel """
        R = 6371000  # in M
        # area er egentlig R**2
        area = R*(np.sin((c_lat + d_lat)*np.pi/180) - np.sin((c_lat - d_lat)*np.pi/180) )*(2*d_lon*np.pi/180) # R**2
        return np.abs(area)

def get_dict_with_all_keys():
    """ Merging all the subcoordinate information to one dictionary.
    Solved in this matter because of storage limitations on GitHub. """
    ex_fil = glob.glob(data_dir + '*ERA5*.json')
    merged_dict = {}

    for fil in ex_fil:
        with open(fil, 'r') as f:
            data_grid = json.load(f)
        merged_dict.update(data_grid)

    return merged_dict

data_dict = get_dict_with_all_keys()

def calc_fraction_one_cell(lat = '30.25', lon = '19.25', cmk = None, data = None):
    """Compute fraction in one cell. """
    if data:
        ## Improvements : This should read the files.
        ex = data[lat][lon]
        fraction = 0.0
        SAT_area = 0.0

        for key, item in ex.items():
            index = ex[key]['index']
            area  = ex[key]['area']

            if len(index) == len(area):
                fraction += np.nansum(np.array(area)*np.array(cmk[index]) )
                SAT_area += np.nansum(area)
            else:
                print('Returns nan for lat {}, lon {}'.format(lat, lon))
                #return np.nan, (lat, lon)

        return fraction/SAT_area, np.isnan(np.array(cmk[index])).sum()
    else:
        print('Please send data as a attribute.')
        return

def compute(satfil,
            lats = np.arange(30.0, 50.25, 0.25),
            lons = np.arange(-15.0, 25.25, 0.25)):
    """Regrid one time step/ one file. """
    o = clean_file(satfil)

    if o is not None:
        d_phi, d_theta, cell_areas, lat_array, lon_array = read_dlon_dlat(data_dir)
        clouds = o.reshape(-1)

        data_dict = get_dict_with_all_keys()

        GRID = np.zeros((len(lats), len(lons)) )
        GRID_NAN = np.zeros((len(lats), len(lons)) )

        for i,lat in enumerate(lats):
            for j, lon in enumerate(lons):
                fraction, nbr_nan = calc_fraction_one_cell(lat = str(lat),
                                                           lon = str(lon),
                                                           cmk = clouds,
                                                           data = data_dict)

                GRID[i][j] = fraction
                GRID_NAN[i][j] = nbr_nan

        return GRID, GRID_NAN
    else:
        return None, None

def timestamp(filename):
    """
    Returns the numpy datetime 64 [ns] for the current date.
    This is a bit hardcoded at the moment ....
    """
    splits = filename.split('-')
    ts = splits[5]
    year = ts[:4]
    month = ts[4:6]
    day = ts[6:8]
    hr = ts[8:10]
    minuts = ts[10:12]
    sek = ts[12:14]
    # TODO make sure all filenames have seconds
    return np.datetime64( year+"-"+month+"-"+day+"T"+hr ) # +":"+minuts+":"+sek

def make_folder_str(year, month):
    """ Generates the folder search str
    month : int
    year : int

    Returns : str
        year_month
    """

    month = "%2.2d" % month
    return "{}_{}".format(year, month)

def timestamp_str(filename):
    """
    Returns the numpy datetime 64 [ns] for the current date.
    This is a bit hardcoded at the moment ...
    """
    splits = filename.split('-')
    ts = splits[5]
    year = ts[:4]
    month = ts[4:6]
    day = ts[6:8]
    hr = ts[8:10]
    minuts = ts[10:12]
    sek = ts[12:14]
    return np.datetime64( year+"-"+month+"-"+day+"T"+hr+":00:00"+".000000").astype(str)

def get_missing_vals(folder):
    """ Returns missing timesteps in folder. """
    year, month = folder.split('_')
    year  = int(year)
    month = int(month)

    t = np.arange(datetime(year,month,1), datetime(year,month+1,1), timedelta(hours=1)).astype(str)
    folder = make_folder_str(month, year)
    files_in_folder = glob.glob(os.path.join(path, folder, '*grb'))
    times = [timestamp_str(fil) for fil in files_in_folder]
    a = times
    b = t
    c = [x for x in a if x not in b]+[x for x in b if x not in a]
    return c

def timestamp_to_file_search_str(timestamp):
    timestamp = timestamp.tostring()
    splits = [split.split('T') for split in timestamp.split(':')[0].split('-')]
    s = ''
    for a in np.concatenate(splits):
        s+=a
    return s

def removes_duplicates(year, month):
    folder = make_folder_str(year, month)
    #logging.debug( get_missing_vals(folder) ) # TODO

    files_in_folder = glob.glob(os.path.join(path, folder, '*grb'))
    times = [timestamp_str(fil) for fil in files_in_folder]

    if np.unique(times) != len(times):
        keeping = []
        missing = []
        for fil in files_in_folder:
            # if timestep is already there don't append
            search_for = timestamp_to_file_search_str(timestamp_str(fil))
            files =  glob.glob(os.path.join(path, folder, '*-{}*grb'.format(search_for)))
            if len(files) > 0:
                keeping.append(files[0]) # only keep the first one for multiple files of the same data
        return keeping
    else:
        return glob.glob(os.path.join(path, folder, '*.grb'))

def merge_ts_to_one_dataset(grb_files,
                            lat = np.arange(30.0, 50.25, 0.25),
                            lon = np.arange(-15.0, 25.25, 0.25)):
    """ grib_files : list of files. One month.  updated version of merge_ts_to_one_dataset """
    #data_grid = get_dict_with_all_keys()

    counter = 0
    for filename in grb_files:
        cloud_fraction, nans = compute(filename, lat, lon)
        if cloud_fraction is not None:
            # this becomes true if the grib file of the satelite images is corrupt.



            if counter == 0:
                # if the computation worked
                ds = xr.Dataset({'tcc': (['latitude', 'longitude'],   cloud_fraction),
                                 'nr_nans':(['latitude', 'longitude'], nans),
                                 #'nr_cells':(['latitude', 'longitude'], cnt_cells)
                                     },
                                 coords={'longitude': (['longitude'], lon),
                                         'latitude': (['latitude'], lat),
                                        })
                ts = timestamp(filename)
                ds['time'] = ts

                # Add time as a coordinate and dimension.
                ds = ds.assign_coords(time = ds.time)
                ds = ds.expand_dims(dim = 'time')
                counter += 1
                print('Finished nbr {}/{}'.format(counter, len(grb_files)))
            else:
                #clm, cnt_cells, cnt_nans = calc_all(filename, nc_file = nc_files[0])
                #cloud_fraction, nans = compute(filename, lat, lon)
                new_ds = xr.Dataset({'tcc': (['latitude', 'longitude'],  cloud_fraction),
                                     'nr_nans':(['latitude', 'longitude'], nans),
                                     #'nr_cells':(['latitude', 'longitude'], cnt_cells)
                                    },
                                      coords={'longitude': (['longitude'], lon),
                                              'latitude': (['latitude'], lat),
                                               })

                ts = timestamp(filename)
                new_ds['time'] = ts

                # Add time as a coordinate and dimension.
                new_ds = new_ds.assign_coords(time = new_ds.time)
                new_ds = new_ds.expand_dims(dim = 'time')

                try:
                    ds = ds.merge(new_ds)
                except xr.MergeError:
                    # Happens if MS1 and MS2 have taken a image at the same time
                    print("Filename not included {}".format(filename))

                counter += 1
                print('Finished nbr {}/{}'.format(counter, len(grb_files)))
        #print("completed {}/{} files".format(counter, len(grb_files)))
    return ds

def already_regridded(year, month):
    """  Checks if a month has been regridded.
    Returns:
         boolean
    """
    # TODO: Update path
    path = '/uio/lagringshotell/geofag/projects/miphclac/hannasv/fractions_repo/'
    #folder = make_folder_str(year = year, month = month)
    month = "%2.2d"%month # Skriver
    #key = "*-{}{}*.grb".format(year, month)
    full = os.path.join( path, '{}_{}.nc'.format(year, month) )
    return os.path.isfile(full)

def get_filename(year, month):
    month = "%2.2d" % month  # Skriver
    # key = "*-{}{}*.grb".format(year, month)
    return '{}_{}.nc'.format(year, month)

def get_year_month_from_filename(grib_file):
    """Returns the year and month of a given file."""
    year = None
    month = None



    return year, month


def add_missing_data_to_existing_nc_files(grb_files,
                                          lat = np.arange(30.0, 50.25, 0.25),
                                          lon = np.arange(-15.0, 25.25, 0.25)):
    """ grib_files : list of files. One month.  updated version of merge_ts_to_one_dataset

    TODO test this at metos. This should however tackle both cases when some files are regridded
    """
    data_grid = get_dict_with_all_keys()

    year, month = get_year_month_from_filename(grb_files[0])

    counter = 0
    for filename in grb_files:
        cloud_fraction, nans = compute(filename, lat, lon)
        if cloud_fraction is not None:
            # This becomes true if the grib file of the satelite images is corrupt.
            if counter == 0:
                # If the computation worked
                if already_regridded(year, month): # if the file is regridded 
                    ds = xr.open_dataset(os.path.join( data_monthly_repo, get_filename(year, month) ))
                    new_ds = xr.Dataset({'tcc': (['latitude', 'longitude'], cloud_fraction),
                                         'nr_nans': (['latitude', 'longitude'], nans),
                                         # 'nr_cells':(['latitude', 'longitude'], cnt_cells)
                                         },
                                        coords={'longitude': (['longitude'], lon),
                                                'latitude': (['latitude'], lat),
                                                })

                    ts = timestamp(filename)
                    new_ds['time'] = ts

                    # Add time as a coordinate and dimension.
                    new_ds = new_ds.assign_coords(time=new_ds.time)
                    new_ds = new_ds.expand_dims(dim='time')

                    try:
                        ds = ds.merge(new_ds)
                    except xr.MergeError:
                        # Happens if MS1 and MS2 have taken a image at the same time
                        print("Filename not included {}".format(filename))

                    counter += 1
                else: 
                    # If not regridded
                    ds = xr.Dataset({'tcc': (['latitude', 'longitude'],   cloud_fraction),
                                     'nr_nans':(['latitude', 'longitude'], nans),
                                     #'nr_cells':(['latitude', 'longitude'], cnt_cells)
                                         },
                                     coords={'longitude': (['longitude'], lon),
                                             'latitude': (['latitude'], lat),
                                            })
                    ts = timestamp(filename)
                    ds['time'] = ts
    
                    # Add time as a coordinate and dimension.
                    ds = ds.assign_coords(time = ds.time)
                    ds = ds.expand_dims(dim = 'time')
                    counter += 1
                    print('Finished nbr {}/{}'.format(counter, len(grb_files)))
            else:
                # adding the rest of
                new_ds = xr.Dataset({'tcc': (['latitude', 'longitude'],  cloud_fraction),
                                     'nr_nans':(['latitude', 'longitude'], nans),
                                     #'nr_cells':(['latitude', 'longitude'], cnt_cells)
                                    },
                                      coords={'longitude': (['longitude'], lon),
                                              'latitude': (['latitude'], lat),
                                               })

                ts = timestamp(filename)
                new_ds['time'] = ts

                # Add time as a coordinate and dimension.
                new_ds = new_ds.assign_coords(time = new_ds.time)
                new_ds = new_ds.expand_dims(dim = 'time')

                try:
                    ds = ds.merge(new_ds)
                except xr.MergeError:
                    # Happens if MS1 and MS2 have taken a image at the same time
                    print("Filename not included {}".format(filename))

                counter += 1
                print('Finished nbr {}/{}'.format(counter, len(grb_files)))
        #print("completed {}/{} files".format(counter, len(grb_files)))
    return ds


def compute_one_folder(subset, folder):
    import os
    ds = merge_ts_to_one_dataset(subset,
                                 lat =  np.arange(30.0, 50.25, 0.25) ,
                                 lon = np.arange(-15.0, 25.25, 0.25) )

    ds.to_netcdf(path = os.path.join(save_dir,'{}.nc'.format(folder)),
                 engine='netcdf4',
                 encoding ={'tcc': {'zlib': True, 'complevel': 9},
                           'nr_nans': {'zlib': True, 'complevel': 9} })

    return



def get_list_remainig_files():
    """
    REWRITE: tomorrow - Should check whats available in save repo.

    TODO: This is outdated.
    """
    print("Computes remaining files ...")
    search_str_finished = '*heilt*.nc'
    sat_dir = '/uio/lagringshotell/geofag/projects/miphclac/hannasv/'
    save_dir = '/uio/lagringshotell/geofag/students/metos/hannasv/satelite_data/'

    files = glob.glob(save_dir + search_str_finished)

    failed = []
    for i, fil in enumerate(files):
        if i == 0:
            ds = xr.open_dataset(fil)
        else:
            try:
                ds = ds.merge(xr.open_dataset(fil))
            except xr.MergeError:
                failed.append(fil)
            #print(i)
    sat_files = glob.glob(sat_dir + "*.grb")

    remaining_files = []
    for fil in sat_files:
        if not timestamp(fil) in ds.time.values:
            remaining_files.append(fil)

    return remaining_files

years = np.arange(2004, 2019)
months = np.arange(1, 13)

for y in years:
    for m in months:
        folder = make_folder_str(y, m)
        files_to_read = removes_duplicates(y, m)

        if len(files_to_read) > 0 and not already_regridded(y, m):
            print("Starts computation for folder : {}, containing {} files.".format(folder, len(files_to_read)))
            compute_one_folder(subset=files_to_read, folder=folder)
            #print(already_regridded(year = y, month = m))


if __name__ != '__main__':
    # looop over all month
    # Check if there is some available times for those files and regridd those.
    print('helllo to avoid errors')

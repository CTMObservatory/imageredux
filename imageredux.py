#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
# Pamela Lara, Moises Castillo
# All rights reserved.

from astropy import units as u
import numpy as np
import ccdproc
import glob
import os
from pathlib import Path

# This global var's will contain IN and OUT paths.
_OUT_DIR = ""
_IN_DIR = ""

# Create master dark
def do_dark_combine(dark_list):

    print("Combining darks...")

    # Median combine darks
    master_dark = ccdproc.combine(dark_list, method="median", unit="u.adu", clobber=True)

    # Write master dark to disk
    ccdproc.fits_ccddata_writer(master_dark, "master-dark.fit")

    return master_dark

# Create (non-normalized) master flat
def do_flat_combine(flat_list, master_dark):

    print("Combining flats...")

    # Median combine flats
    combined_flat = ccdproc.combine(flat_list, method="median", unit="u.adu", clobber=True)

    # Write combined flat to disk
    #ccdproc.fits_ccddata_writer(combined_flat, "average-flat.fit")

    print("Subtracting dark from flat...")

    # Subtract master dark from combined flat
    master_flat = ccdproc.subtract_dark(combined_flat, master_dark, data_exposure=combined_flat.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)

    # Write (non-normalized) master flat to disk
    ccdproc.fits_ccddata_writer(master_flat, "master-flat.fit")

    return master_flat

# Normalize master flat by median
def do_flat_normal(master_flat):

    print("Normalizing the masterflat...")

    # Normalize master flat by median division
    normalized_masterflat = master_flat / np.median(master_flat)

    # Convert numpy array to CCDData object
    normalized_masterflat = ccdproc.CCDData(normalized_masterflat, unit="u.adu")

    # Write (normalized) master flat to disk
    ccdproc.fits_ccddata_writer(normalized_masterflat, "master-flat.fit")

    return normalized_masterflat

# Image calibration
def do_calibrate(object_list, master_flat, master_dark):

    if not os.path.exists("cal_frames"):

        os.makedirs("cal_frames")

        cal_index = 1

        for item in object_list:

            # Convert frame into CCDData object
            object_frame = ccdproc.fits_ccddata_reader(item, unit="u.adu")

            print("Subtracting dark from object " + str(cal_index) + "...")

            # Subtract dark from object
            object_min_dark = ccdproc.subtract_dark(object_frame, master_dark, data_exposure=object_frame.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)

            # Write dark-subtracted object to disk
            #ccdproc.fits_ccddata_writer(object_min_dark, "obj-min-dark-"+str(cal_index)+".fit")

            print("Dividing object " + str(cal_index) + " by flat...")

            # Divide object by flat
            cal_object_frame = ccdproc.flat_correct(object_min_dark, master_flat)

            # Write calibrated object to disk
            ccdproc.fits_ccddata_writer(cal_object_frame, "cal_frames/cal-"+str(cal_index)+"-"+str(item))

            cal_index += 1

    else:

        print("<Error> Skipping redux: directory 'cal_frame' exists")


# Makes array of file paths in this directory and all subdirectories, recursively
# and filters by suffix
def do_file_list():

    file_array = np.asarray(sorted(Path(_IN_DIR).glob('**/*.*')))

    file_array_len = len(file_array)

    # Filters array for specified file suffix
    suffix_search = '.fit' # Examples: '.txt' '.py'
    filtered_list = [file_array[x].with_suffix(suffix_search) for x in range(file_array_len)]

def main():

    os.system('clear')
    print()
    print("// ImageRedux")
    print("// CGWA TDAG - Aug 2017")
    print()

    # Create lists
    bias_list = glob.glob(os.path.join(_IN_DIR, "bias", "*bias*.fit*"))
    dark_list = glob.glob(os.path.join(_IN_DIR, "dark", "*dark*.fit*"))
    flat_list = glob.glob(os.path.join(_IN_DIR, "flat", "*flat*.fit*"))

    # Create master calibration frames
    master_dark = do_dark_combine(dark_list)
    master_flat = do_flat_combine(flat_list, master_dark)

    obj_dirs = [f for f in os.listdir(_IN_DIR)

        if os.path.isdir(os.path.join(_IN_DIR, f))

           and f not in ['bias', 'dark', 'flat']]

    for obj in obj_dirs:

        # Calibrate object frames
        object_list = glob.glob(os.path.join(_IN_DIR, obj, "*.fit*"))
        #normalized_masterflat = do_flat_normal(master_flat)
        do_calibrate(object_list, master_flat, master_dark)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Arguments for imageredux')

    parser.add_argument(
        '-i', default='./',
        help='Path to root directory where FITS files are. Default is current dir.',
        metavar='DIR',
        dest='input_path',
        )

    parser.add_argument(
        '-o', default='./',
        help='Path where intermediate and final files will be saved. Default is current dir.',
        metavar='DIR',
        dest='output_path',
        )

    args = parser.parse_args()

    _OUT_DIR = args.output_path
    _IN_DIR = args.input_path

    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
# Pamela Lara, Moises Castillo
# All rights reserved.

from astropy import units as u
from astropy.io import fits
import numpy as np
import ccdproc
import glob
import os

# This global var's will contain IN and OUT paths.
_OUT_DIR = ""
_IN_DIR = ""

# Create master dark
def do_dark_combine(dark_list):

    print("Combining darks...")
    master_dark = ccdproc.combine(dark_list, method="median", unit="u.adu", clobber=True)
    ccdproc.fits_ccddata_writer(master_dark, "master-dark.fit")

    return master_dark

# Create master flat
def do_flat_combine(flat_list, master_dark):

    print("Combining flats...")
    combined_flat = ccdproc.combine(flat_list, method="median", unit="u.adu", clobber=True)
    #ccdproc.fits_ccddata_writer(combined_flat, "average-flat.fit")

    print("Subtracting dark from flat...")
    master_flat = ccdproc.subtract_dark(combined_flat, master_dark, data_exposure=combined_flat.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)
    ccdproc.fits_ccddata_writer(master_flat, "master-flat.fit")

    return master_flat

# Normalize master flat by median
def do_flat_normal(master_flat):

    print("Normalizing the masterflat...")

    # Convert CCDData object to numpy array
    master_flat = np.asarray(master_flat)

    # Calculate median of master flat
    masterflat_median = np.median(master_flat)
    print(masterflat_median)

    # Normalize master flat by median division
    normalized_masterflat = master_flat / masterflat_median

    # Convert numpy array to CCDData object
    normalized_masterflat = ccdproc.CCDData(normalized_masterflat, unit="u.adu")

    #ccdproc.fits_ccddata_writer(normalized_masterflat, "master-flat.fit")

    return normalized_masterflat

# Image calibration
def do_calibrate(object_list, master_flat, master_dark):

    if not os.path.exists("cal_frames"):
        os.makedirs("cal_frames")

        cal_index = 1

        for item in object_list:

            # Convert frame into CCD data object
            object_frame = ccdproc.fits_ccddata_reader(item, unit="u.adu")

            # Subtract dark from object
            print("Subtracting dark from object " + str(cal_index) + "...")
            object_min_dark = ccdproc.subtract_dark(object_frame, master_dark, data_exposure=object_frame.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)
            #ccdproc.fits_ccddata_writer(object_min_dark, "obj-min-dark-"+str(cal_index)+".fit")

            # Divide object by flat
            print("Dividing object " + str(cal_index) + " by flat...")
            cal_object_frame = ccdproc.flat_correct(object_min_dark, master_flat)
            ccdproc.fits_ccddata_writer(cal_object_frame, "cal_frames/cal-"+str(cal_index)+"-"+str(item))

            cal_index += 1

    else:
        print("No need to be redundant, silly!")


def main():

    # Create lists
    bias_list = glob.glob(os.path.join(_IN_DIR, "bias", "*bias*.fit*"))
    dark_list = glob.glob(os.path.join(_IN_DIR, "dark", "*dark*.fit*"))
    flat_list = glob.glob(os.path.join(_IN_DIR, "flat", "*flat*.fit*"))

    master_dark = do_dark_combine(dark_list)
    master_flat = do_flat_combine(flat_list, master_dark)

    obj_dirs = [f for f in os.listdir(_IN_DIR)
        if os.path.isdir(os.path.join(_IN_DIR, f))
           and f not in ['bias', 'dark', 'flat']]
    for obj in obj_dirs:
        object_list = glob.glob(os.path.join(_IN_DIR, obj, "*.fit*"))
        #normalized_masterflat = do_flat_normal(master_flat)
        do_calibrate(object_list, master_flat, master_dark)


if __name__ == '__main__':
    os.system('clear')
    print("======================================")
    print("// Welcome to TOROS ImageRedux module")
    print("// CGWA Time Domain Group (2017)")
    print("======================================")
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

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
    ccdproc.fits_ccddata_writer(combined_flat, "average-flat.fit")

    print("Subtracting dark from flat...")
    master_flat = ccdproc.subtract_dark(combined_flat, master_dark, data_exposure=combined_flat.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)
    ccdproc.fits_ccddata_writer(master_flat, "master-flat.fit")
    
    master_flat = do_flat_normal("master-flat.fit")

    return master_flat

# Normalizing Flat
def do_flat_normal(master_flat): # Normalization through median
    print("Normalizing the masterflat...")
    hdu_list = fits.open(master_flat) # bringing the master flat into an array to use numpy
    hdu_list.info()
    
    masterflat_data = hdu_list[0].data # The data is now stored as a 2-D numpy array.
    masterflat_median = np.median(masterflat_data) # Calculating the median of the master flat
    normalized_masterflat = masterflat_data/masterflat_median # normalazinf the master flat by dividing it by its median
    normalized_masterflat = ccdproc.CCDData(normalized_masterflat, unit=u.adu) #Convert np array to CCDData
    #normalized_masterflat = ccdproc.ccddata_writer(normalized_masterflat, "master-flat.fit") 
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
        ccdproc.fits_ccddata_writer(object_min_dark, "obj-min-dark-"+str(cal_index)+".fit")

        # Divide object by flat
        print("Dividing object " + str(cal_index) + " by flat...")
        cal_object_frame = ccdproc.flat_correct(object_min_dark, master_flat)
        ccdproc.fits_ccddata_writer(cal_object_frame, "cal_frames/cal-"+str(cal_index)+"-"+str(item))

        cal_index += 1

def main():

    # Initialize lists
    bias_list = []
    dark_list = []
    flat_list = []
    object_list = []
    bias_list = []

    # Append calibration and object frames to list
    for frame in glob.glob("*.fit"):

        if "bias" in frame:
            bias_list.append(frame)
        elif "dark" in frame:
            dark_list.append(frame)
        elif "flat" in frame:
            flat_list.append(frame)
        elif "bias" in frame:
        	bias_list.append(frame)
        else:
            object_list.append(frame)

    # Run commands here
    master_dark = do_dark_combine(dark_list)
    master_flat = do_flat_combine(flat_list, master_dark)
    do_calibrate(object_list, master_flat, master_dark)

if __name__ == '__main__':
    print("This program is autonomous. Beware.")
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

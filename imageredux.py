#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
imageredux
==========

Script to reduce images for LIGO counterpart searches.

Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
Pamela Lara, Moises Castillo

All rights reserved.
"""

from astropy import units as u
import numpy as np
import ccdproc
import glob
import os
from pathlib import Path
from astropy.table import Table

_IN_DIR = None
"The path to the images directory."
_OUT_DIR = None
"The path to the directory where new files will be saved."


def do_dark_combine(dark_list, master_frame_dir):
    """
    Create master dark by median-combining a list of dark images.

    Args:
        dark_list: a list of CCDData objects containing the individual dark frames

    Returns:
        a CCDData object containing the master dark
    """
    if not os.path.isfile(master_frame_dir+"/master-dark.fit"):

        log.write("<OUTPUT> Combining darks"+"\n")
        # Median combine darks
        master_dark = ccdproc.combine(dark_list, method="median", unit="u.adu", clobber=True)

        log.write("<OUTPUT> Writing master dark to disk"+"\n")
        # Write master dark to disk
        ccdproc.fits_ccddata_writer(master_dark, master_frame_dir+"/master-dark.fit")

    else:

        log.write("<OUTPUT> Skipping dark combine: assigning existing file 'master-dark.fit'"+"\n")
        # Read master dark from disk and assign to variable
        master_dark = ccdproc.fits_ccddata_reader(master_frame_dir+"/master-dark.fit")

    return master_dark


def do_flat_combine(flat_list, master_dark, master_frame_dir):
    """
    Create master flat.

    Args:
        flat_list: a list of CCDData objects containing the individual flat frames
        master_dark: a CCDData object containing the master dark
        master_frame_dir: a string identifying the output path for writing to disk

    Returns:
        a CCDData object containing the master flat.
    """
    if not os.path.isfile(master_frame_dir+"/master-flat.fit"):

        log.write("<OUTPUT> Combining flats"+"\n")
        # Median combine flats
        combined_flat = ccdproc.combine(flat_list, method="median", unit="u.adu", clobber=True)

        log.write("<OUTPUT> Subtracting dark from flat"+"\n")
        # Subtract master dark from combined flat
        master_flat = ccdproc.subtract_dark(combined_flat, master_dark, data_exposure=combined_flat.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)

        log.write("<OUTPUT> Writing master flat to disk"+"\n")
        # Write master flat to disk
        ccdproc.fits_ccddata_writer(master_flat, master_frame_dir+"/master-flat.fit")

    else:

        log.write("<OUTPUT> Skipping flat combine: assigning existing file 'master-flat.fit'"+"\n")
        # Read master flat from disk and assign to variable
        master_flat = ccdproc.fits_ccddata_reader(master_frame_dir+"/master-flat.fit")

    return master_flat


def do_calibrate(object_list, master_flat, master_dark, obj, cal_frame_dir):
    """
    Calibrate a list of images.

    Args:
        object_list: a list of CCDData objects containing the light frames to be calibrated
        master_flat: a CCDData object containing the master flat
        master_dark: a CCDData object containing the master dark
        cal_frame_dir: a string identifying the output path for writing to disk

    Returns:
        None
    """

    cal_dir = "cal_"+str(obj)

    if not os.path.exists(cal_dir):
        os.makedirs(cal_frame_dir+"/"+cal_dir)

        for item in object_list:

            frame = os.path.split(item)[1]

            log.write("<OUTPUT> Reading object " + str(frame)+"\n")
            # Read CCDData object
            object_frame = ccdproc.fits_ccddata_reader(item, unit="u.adu")

            log.write("<OUTPUT> Subtracting dark from " + str(frame)+"\n")
            # Subtract dark from object
            object_min_dark = ccdproc.subtract_dark(object_frame, master_dark, data_exposure=object_frame.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)

            log.write("<OUTPUT> Dividing " + str(frame) + " by flat"+"\n")
            # Divide object by flat
            cal_object_frame = ccdproc.flat_correct(object_min_dark, master_flat)

            log.write("<OUTPUT> Writing object " + str(frame) + " to disk"+"\n")
            # Write calibrated object to disk
            ccdproc.fits_ccddata_writer(cal_object_frame, cal_frame_dir+"/"+cal_dir+"/cal-"+str(frame))


def do_file_list():

    """Make array of file paths in this directory and all subdirectories, recursively
    and filter by suffix.
    """
    file_array = np.asarray(sorted(Path(_IN_DIR).glob('**/*.*')))

    file_array_len = len(file_array)

    # Filters array for specified file suffix
    suffix_search = '.fit' # Examples: '.txt' '.py'

    # There is an issue with the following line.
    #   appending .fit to ALL files!!
    filtered_list = [file_array[x].with_suffix(suffix_search) for x in range(file_array_len)]

    object_name = [filtered_list[x].parent.name for x in range(file_array_len)]

    file_name = [filtered_list[x].name for x in range(file_array_len)]

    observation_date = [filtered_list[x].parent.parent.name for x in range(file_array_len)]

    file_table = Table([observation_date, object_name, file_name, filtered_list], names=('OBS_Date','Object','Frame','Path'))

    obs_by_date = file_table.group_by('OBS_Date')

    return obs_by_date

def main():

    # Fancy header
    print("<STATUS> Starting image redux")

    # Create lists
    bias_list = glob.glob(os.path.join(_IN_DIR, "bias", "*bias*.fit*"))
    dark_list = glob.glob(os.path.join(_IN_DIR, "dark", "*dark*.fit*"))
    flat_list = glob.glob(os.path.join(_IN_DIR, "flat", "*flat*.fit*"))

    log.write("<OUTPUT> bias_list = " + str(bias_list)+"\n")
    log.write("<OUTPUT> dark_list = " + str(dark_list)+"\n")
    log.write("<OUTPUT> flat_list = " + str(flat_list)+"\n")

    # Create directory to save masters
    master_frame_dir = _OUT_DIR+"/master_frames"
    log.write("<OUTPUT> master_frame_dir = " + str(master_frame_dir)+"\n")
    if not os.path.exists(master_frame_dir):
        log.write("<OUTPUT> not os.path.exists(master_frame_dir) = " + str(not os.path.exists(master_frame_dir))+"\n")
        os.makedirs(master_frame_dir)

    # Create master calibration frames
    master_dark = do_dark_combine(dark_list, master_frame_dir)
    master_flat = do_flat_combine(flat_list, master_dark, master_frame_dir)

    # Create list of object directories
    obj_dirs = [f for f in os.listdir(_IN_DIR)
                if os.path.isdir(os.path.join(_IN_DIR, f)) and
                f not in ['bias', 'dark', 'flat']]

    obj_dirs.remove("master_frames")

    log.write("<OUTPUT> obj_dirs = " + str(obj_dirs)+"\n")
    log.write("<OUTPUT> " + "(Bool) dir 'master_frame_dir' exists > " + str(os.path.exists("master_frame_dir"))+"\n")

    # Create directory to save calibrated objects
    cal_frame_dir = _OUT_DIR+"/cal_frames"
    log.write("<OUTPUT> cal_frame_dir = " + str(cal_frame_dir)+"\n")
    if not os.path.exists(cal_frame_dir):
         log.write("<OUTPUT> not os.path.exists(cal_frame_dir) = " + str(not os.path.exists(cal_frame_dir))+"\n")
         os.makedirs(cal_frame_dir)

    # Calibrate object frames
    for obj in obj_dirs:
        log.write("<OUTPUT> obj = " + str(obj)+"\n")
        object_list = glob.glob(os.path.join(_IN_DIR, obj, "*.fit*"))
        log.write("<OUTPUT> object_list = " + str(object_list)+"\n")
        print("<STATUS> Running redux on " + str(object_list))
        do_calibrate(object_list, master_flat, master_dark, obj, cal_frame_dir)

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

    log = open("log.txt", "a")

    args = parser.parse_args()
    log.write("<OUTPUT> args = " + str(args)+"\n")

    _OUT_DIR = args.output_path
    _IN_DIR = args.input_path
    log.write("<OUTPUT> _OUT_DIR = " + str(_OUT_DIR)+"\n")
    log.write("<OUTPUT> _IN_DIR =ls " + str(_IN_DIR)+"\n")

    main()

    log.close()
    print("<STATUS> Image redux complete")
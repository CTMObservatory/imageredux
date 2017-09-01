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

__version__ = "1.0a1"

from astropy import units as u
import numpy as np
import ccdproc
import glob
import os
from pathlib import Path
from astropy.table import Table, Column

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
    out_filename = os.path.join(master_frame_dir, "master-dark.fit")
    if not os.path.isfile(out_filename):

        log.write("<OUTPUT> Combining darks\n")
        # Median combine darks
        master_dark = ccdproc.combine(dark_list, method="median", unit="u.adu", clobber=True)

        log.write("<OUTPUT> Writing master dark to disk\n")
        # Write master dark to disk
        ccdproc.fits_ccddata_writer(master_dark, out_filename)

    else:

        log.write("<OUTPUT> Skipping dark combine: assigning existing file 'master-dark.fit'\n")
        # Read master dark from disk and assign to variable
        master_dark = ccdproc.fits_ccddata_reader(out_filename)

    return master_dark, out_filename


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
    out_filename = os.path.join(master_frame_dir, "master-flat.fit")
    if not os.path.isfile(out_filename):

        log.write("<OUTPUT> Combining flats\n")
        # Median combine flats
        combined_flat = ccdproc.combine(flat_list, method="median", unit="u.adu")

        log.write("<OUTPUT> Subtracting dark from flat"+"\n")
        # Subtract master dark from combined flat
        master_flat = ccdproc.subtract_dark(combined_flat, master_dark, data_exposure=combined_flat.header["exposure"]*u.second, dark_exposure=master_dark.header["exposure"]*u.second, scale=True)

        log.write("<OUTPUT> Writing master flat to disk"+"\n")
        # Write master flat to disk
        ccdproc.fits_ccddata_writer(master_flat, out_filename)

    else:

        log.write("<OUTPUT> Skipping flat combine: assigning existing file 'master-flat.fit'"+"\n")
        # Read master flat from disk and assign to variable
        master_flat = ccdproc.fits_ccddata_reader(out_filename)

    return master_flat, out_filename


def do_calibrate(object_list, master_flat, master_dark, object_name, cal_frame_dir):
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

    cal_dir = "cal_{}".format(object_name)
    check_path = os.path.join(cal_frame_dir, cal_dir)

    if not os.path.exists(check_path):
        os.makedirs(check_path)

    # Calibration begins if directory cal_object exists and is empty
    if not os.listdir(check_path):
        for item in object_list:

            frame = os.path.split(item)[1]

            log.write("<OUTPUT> Reading object {}".format(frame))
            # Read CCDData object
            object_frame = ccdproc.fits_ccddata_reader(item, unit="u.adu")

            # Check if object frame is same size as master frames
            if not object_frame.shape == master_dark.shape:
                log.write("<STATUS> Skipping object calibration... Object frame is not same shape as Master frames\n")
                print("<STATUS> Skipping object calibration... Object frame is not same shape as Master frames")
                break
            else:
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

    """Make array of file paths in this directory and all subdirectories, recursively and filter by suffix.
    Assumes path:
        root_path/ObservationDate/objectFolder/objectFrames
    or
        root_path/ObservationDate/randomName/objectFolder/objectFrames
    """
    file_array = np.asarray(sorted(Path(_IN_DIR).glob('**/*.*')))

    file_array_len = len(file_array)

    # Filters array for specified file suffix
    suffix_search = '*.fit' # Examples: '.txt' '.py'

    # Filter list by suffix
    filtered_list = [file_array[x] for x in range(file_array_len) if file_array[x].match(suffix_search)]

    file_array_len = len(filtered_list)

    # Parse path to populate table
    object_name = [filtered_list[x].parent.name for x in range(file_array_len)]
    file_name = [filtered_list[x].name for x in range(file_array_len)]
    observation_date = [filtered_list[x].parent.parent.name if filtered_list[x].parent.parent.name.isdigit() else filtered_list[x].parent.parent.parent.name for x in range(file_array_len)]

    # Make list into Columns
    object_name = Column(object_name)
    file_name = Column(file_name)
    observation_date = Column(observation_date)

    # Populate Table
    file_table = Table([observation_date, object_name, file_name, filtered_list], names=('OBS_Date','Object','Frame','Path'))

    # Create groups by similar observation date
    obs_by_date = file_table.group_by('OBS_Date')

    return obs_by_date

def main():

    # Fancy header
    print("<STATUS> Starting image redux")

    nights_dirs = [os.path.join(_IN_DIR, anight)
                   for anight in os.listdir(_IN_DIR)
                   if os.path.isdir(os.path.join(_IN_DIR, anight))]

    for anight in nights_dirs:
        # I use this to create the output paths
        anight_base = os.path.basename(os.path.normpath(anight))
        # Create lists
        bias_list = glob.glob(os.path.join(anight, "bias", "*bias*.fit*"))
        dark_list = glob.glob(os.path.join(anight, "dark", "*dark*.fit*"))
        flat_list = glob.glob(os.path.join(anight, "flat", "*flat*.fit*"))

        log.write("<OUTPUT> bias_list = {}\n".format(bias_list))
        log.write("<OUTPUT> dark_list = {}\n".format(dark_list))
        log.write("<OUTPUT> flat_list = {}\n".format(flat_list))

        if dark_list and flat_list:
            # Create directory to save masters
            master_frame_dir = os.path.join(_OUT_DIR, anight_base, "master_frames")
            log.write("<OUTPUT> master_frame_dir = {}\n".format(master_frame_dir))
            if not os.path.exists(master_frame_dir):
                log.write("<OUTPUT> not os.path.exists(master_frame_dir) = " + str(not os.path.exists(master_frame_dir))+"\n")
                os.makedirs(master_frame_dir)

            # Create master calibration frames
            master_dark = do_dark_combine(dark_list, master_frame_dir)
            master_flat = do_flat_combine(flat_list, master_dark, master_frame_dir)

            # Create list of object directories
            obj_dirs = [f for f in os.listdir(anight)
                        if os.path.isdir(os.path.join(anight, f)) and
                        f not in ['bias', 'dark', 'flat']]

            log.write("<OUTPUT> obj_dirs = {}\n".format(obj_dirs))
            log.write("<OUTPUT> (Bool) dir 'master_frame_dir' exists > {}\n".format(os.path.exists("master_frame_dir")))

            # Create directory to save calibrated objects
            cal_frame_dir = os.path.join(_OUT_DIR, anight_base, "cal_frames")
            log.write("<OUTPUT> cal_frame_dir = {}\n".format(cal_frame_dir))
            if not os.path.exists(cal_frame_dir):
                 log.write("<OUTPUT> not os.path.exists(cal_frame_dir) = {}\n".format(not os.path.exists(cal_frame_dir)))
                 os.makedirs(cal_frame_dir)

            # Calibrate object frames
            for obj in obj_dirs:
                log.write("<OUTPUT> obj = {}\n".format(obj))
                object_list = glob.glob(os.path.join(anight, obj, "*.fit*"))
                log.write("<OUTPUT> object_list = {}\n".format(object_list))
                print("<STATUS> Running redux on {}".format(object_list))
                do_calibrate(object_list, master_flat, master_dark, obj, cal_frame_dir)
        else:
            log.write("<OUTPUT> Skipping directory: {}\n".format(anight))
            print("<STATUS> Skipping directory: {}".format(anight))

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Arguments for imageredux')

    parser.add_argument(
        '-i', default='.',
        help='Path to root directory where FITS files are. Default is current dir.',
        metavar='DIR',
        dest='input_path',
        )

    parser.add_argument(
        '-o', default='.',
        help='Path where intermediate and final files will be saved. Default is current dir.',
        metavar='DIR',
        dest='output_path',
        )

    args = parser.parse_args()
    _OUT_DIR = args.output_path
    _IN_DIR = args.input_path

    log = open(os.path.join(_OUT_DIR, "log.txt"), "a")
    log.write("<OUTPUT> args = " + str(args)+"\n")
    log.write("<OUTPUT> _OUT_DIR = " + str(_OUT_DIR)+"\n")
    log.write("<OUTPUT> _IN_DIR =ls " + str(_IN_DIR)+"\n")

    main()

    log.close()
    print("<STATUS> Image redux complete")

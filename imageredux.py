#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
imageredux - Script to reduce images for LIGO counterpart searches.

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
import logging


# create logger
logger = logging.getLogger(__name__)

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

        logger.info("Combining darks")
        # Median combine darks
        master_dark = ccdproc.combine(dark_list, method="median", unit="adu", clobber=True)

        logger.info("Writing master dark to disk")
        # Write master dark to disk
        ccdproc.fits_ccddata_writer(master_dark, out_filename)

    else:

        logger.warning("Skipping dark combine: assigning existing file 'master-dark.fit'")
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

        logger.info("Combining flats")
        # Median combine flats
        combined_flat = ccdproc.combine(flat_list, method="median", unit="adu")

        logger.info("Subtracting dark from flat")
        # Subtract master dark from combined flat
        master_flat = ccdproc.subtract_dark(
            combined_flat, master_dark,
            data_exposure=combined_flat.header["exposure"] * u.second,
            dark_exposure=master_dark.header["exposure"] * u.second,
            scale=True)

        logger.info("Writing master flat to disk")
        # Write master flat to disk
        ccdproc.fits_ccddata_writer(master_flat, out_filename)

    else:

        logger.warning("Skipping flat combine: assigning existing file 'master-flat.fit'")
        # Read master flat from disk and assign to variable
        master_flat = ccdproc.fits_ccddata_reader(out_filename)

    return master_flat, out_filename


def do_calibrate(object_list, master_flat, master_dark, object_name, cal_frame_dir, return_fits_objs=False):
    """
    Calibrate a list of images.

    Args:
        object_list: a list of CCDData objects containing the light frames to be calibrated
        master_flat: a CCDData object containing the master flat
        master_dark: a CCDData object containing the master dark
        cal_frame_dir: a string identifying the output path for writing to disk
        return_fits_obj=False: determine, if function should return list fits obj; set to False for memory saving

    Returns:
        A list of the calibrated CCDData objects (if return_fits_obj=True) and a list of the file paths where they were saved.
    """
    cal_dir = "cal_{}".format(object_name)
    check_path = os.path.join(cal_frame_dir, cal_dir)

    if not os.path.exists(check_path):
        os.makedirs(check_path)

    processed_frames, processed_fnames = [], []

    # Calibration begins if directory cal_object exists and is empty
    if not os.listdir(check_path):
        for item in object_list:

            frame = os.path.basename(item)

            logger.info("Reading object {}".format(frame))
            # Read CCDData object
            object_frame = ccdproc.fits_ccddata_reader(item, unit="adu")

            # Check if object frame is same size as master frames
            if not object_frame.shape == master_dark.shape:
                logger.warning("Skipping object calibration... Object frame is not same shape as Master frames")
                break
            else:
                logger.info("Subtracting dark from {}".format(frame))
                # Subtract dark from object
                object_min_dark = ccdproc.subtract_dark(
                    object_frame, master_dark,
                    data_exposure=object_frame.header["exposure"] * u.second,
                    dark_exposure=master_dark.header["exposure"] * u.second,
                    scale=True,
                    )

                logger.info("Dividing {} by flat".format(frame))
                # Divide object by flat
                cal_object_frame = ccdproc.flat_correct(object_min_dark, master_flat)

                logger.info("Writing object {} to disk".format(frame))
                # Write calibrated object to disk
                out_filename = os.path.join(check_path, "cal-{}".format(frame))
                ccdproc.fits_ccddata_writer(cal_object_frame, out_filename)
                if return_fits_objs:
                    processed_frames.append(cal_object_frame)
                processed_fnames.append(out_filename)


    # processed_frames is an empty list, if return_fits_obj=False
    # the true value should be used for the tests
    return processed_frames, processed_fnames


def do_file_list():
    """
    Make array of file paths in this directory and all subdirectories, recursively and filter by suffix.
   
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
    logger.info("Starting image redux")

    nights_dirs = [os.path.join(_IN_DIR, anight)
                   for anight in os.listdir(_IN_DIR)
                   if os.path.isdir(os.path.join(_IN_DIR, anight))]

    for anight in nights_dirs:
        # Create output paths
        anight_base = os.path.basename(os.path.normpath(anight))

        # Create lists
        bias_list = glob.glob(os.path.join(anight, "bias", "*[bB]ias*.fit*"))
        dark_list = glob.glob(os.path.join(anight, "dark", "*[dD]ark*.fit*"))
        flat_list = glob.glob(os.path.join(anight, "flat", "*[fF]lat*.fit*"))

        logger.debug("bias_list = {}".format(bias_list))
        logger.debug("dark_list = {}".format(dark_list))
        logger.debug("flat_list = {}".format(flat_list))

        if dark_list and flat_list:
            # Create directory to save masters
            master_frame_dir = os.path.join(_OUT_DIR, anight_base, "master_frames")
            logger.info("master_frame_dir = {}".format(master_frame_dir))
            if not os.path.exists(master_frame_dir):
                logger.info("not os.path.exists(master_frame_dir) = {}".format(not os.path.exists(master_frame_dir)))
                os.makedirs(master_frame_dir)

            # Create master calibration frames
            master_dark, __ = do_dark_combine(dark_list, master_frame_dir)
            master_flat, __ = do_flat_combine(flat_list, master_dark, master_frame_dir)

            # Create list of object directories
            obj_dirs = [f for f in os.listdir(anight)
                        if os.path.isdir(os.path.join(anight, f)) and
                        f not in ['bias', 'dark', 'flat']]

            logger.debug("obj_dirs = {}".format(obj_dirs))
            logger.debug("(Bool) dir 'master_frame_dir' exists > {}".format(os.path.exists("master_frame_dir")))

            # Create directory to save calibrated objects
            cal_frame_dir = os.path.join(_OUT_DIR, anight_base, "cal_frames")
            logger.info("cal_frame_dir = {}".format(cal_frame_dir))
            if not os.path.exists(cal_frame_dir):
                 logger.debug("not os.path.exists(cal_frame_dir) = {}".format(not os.path.exists(cal_frame_dir)))
                 os.makedirs(cal_frame_dir)

            # Calibrate object frames
            for obj in obj_dirs:
                logger.info("obj = {}".format(obj))
                object_list = glob.glob(os.path.join(anight, obj, "*.fit*"))
                logger.debug("object_list = {}".format(object_list))
                do_calibrate(object_list, master_flat, master_dark, obj, cal_frame_dir)
        else:
            logger.info("Skipping directory: {}".format(anight))


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


    logger.setLevel(logging.DEBUG)

    # create a file handler and set level to debug
    fh = logging.FileHandler(os.path.join(_OUT_DIR, "redux.log"), mode='w')
    fh.setLevel(logging.DEBUG)

    # create formatter and add it to the logger
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # create a console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    logger.debug("args = {}".format(args))
    logger.debug("_OUT_DIR = {}".format(_OUT_DIR))
    logger.debug("_IN_DIR =ls {}".format(_IN_DIR))

    main()

    logger.info("Image redux complete")

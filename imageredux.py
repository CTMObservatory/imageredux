#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
# Pamela Lara, Moises Castillo
# All rights reserved.

import ccdproc
from astropy import units as u
from os.path import exists

# Create master dark
def do_dark_combine(dark_list):

    print("Combining darks...")
    master_dark = ccdproc.combine(dark_list, output_file="master-dark.fit", method="median", unit="u.adu", clobber=True)
	
    return master_dark

# Create master flat
def do_flat_combine(flat_list):

    print("Combining flats...")
    master_flat = ccdproc.combine(flat_list, output_file="master-flat.fit", method="median", unit="u.adu", clobber=True)

    return master_flat

 # Subtract dark from flat
def do_dark_subtract(master_dark, master_flat):

    print("Subtracting dark from flat...")
    flat_min_dark = ccdproc.subtract_dark(master_flat, master_dark, data_exposure=master_flat.header['exposure']*u.second, dark_exposure=master_dark.header['exposure']*u.second, scale=True)
    ccdproc.fits_ccddata_writer(flat_min_dark, "flat-min-dark.fit")

    return flat_min_dark

# This Function takes a single image and reduces using dark and flat master.
def redux(image, masterDark, masterFlat):
    reduxFileName = image.replace(".fit","_redux.fit") # String of File Name

    # Check if file exists
    if exists(reduxFileName):
        print("Skipping reduction;", reduxFileName, 'already exists')
    else:
        reduxFile = ccdproc.CCDData.read(image,unit="adu") # Read file
        masterDark = ccdproc.CCDData.read(masterDark, unit="adu")
        masterFlat = ccdproc.CCDData.read(masterFlat, unit="adu")
        reduxFile = ccdproc.subtract_dark(reduxFile, masterDark, exposure_time='exptime', exposure_unit = u.second) # Subtract Dark
        reduxFile = ccdproc.flat_correct(reduxFile, masterFlat) # Divide by Flat
        # Write fits file
        reduxFile.write(reduxFileName)
    return reduxFileName

if __name__ == '__main__':
    redux('hatp27.fit','master_dark.fit','master_flat.fit')

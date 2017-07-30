#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
# Pamela Lara, Moises Castillo
# All rights reserved.
import ccdproc
from astropy import units as u
from os.path import exists

def examplefunction(arg1, arg2):
    return "Hello World!"

def doDarkComb (darklist):
	"This will combine darks to mke a darkmaster"
	darkmaster = ccdproc.combine(darklist, output_file="darkmaster.fits", method="median", unit=u.adu, clobber=True)
	return darkmaster

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
    print(examplefunction(2, 3))
    redux('hatp27.fit','master_dark.fit','master_flat.fit')

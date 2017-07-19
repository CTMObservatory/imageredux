#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
# Pamela Lara, Moises Castillo
# All rights reserved.
import ccdproc
from astropy import units as u

def examplefunction(arg1, arg2):
    return "Hello World!"

def doDarkComb (darklist):
	"This will combine darks to mke a darkmaster"
	darkmaster = ccdproc.combine(darklist, output_file="darkmaster.fits", method="median", unit=u.adu, clobber=True)
	return darkmaster

if __name__ == '__main__':
    print(examplefunction(2, 3))

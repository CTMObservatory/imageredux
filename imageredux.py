#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Martin Beroiz, Richard Camuccio, Juan Garcia,
# Pamela Lara, Moises Castillo
# All rights reserved.


def examplefunction(arg1, arg2):
    print("Hello World!")

def doDarkComb (darklist):
	"This will combine darks to mke a darkmaster"
	darkmaster = ccdproc.combine(darklist, output_file="darkmaster.fits", method="median", unit=u.adu)
	
	return 'darkmaster.fits'

if __name__ == '__main__':
    examplefunction(2, 3)

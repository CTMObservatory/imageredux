[![Build Status](https://travis-ci.org/toros-astro/imageredux.svg?branch=master)](https://travis-ci.org/toros-astro/imageredux)
[![codecov](https://codecov.io/gh/toros-astro/imageredux/branch/master/graph/badge.svg)](https://codecov.io/gh/toros-astro/imageredux)
# imageredux
Script to reduce images for LIGO counterpart searches.

Usage:

    $ python imageredux -i path/to/images -o path/to/output/dir

Type `python -h` for help on command line arguments.


The script will assume the following directory tree structure:

```
root_path
   |--- bias
   |    |--- *bias*.fits
   |    |--- ...
   |
   |--- dark
   |    |--- *dark*.fits
   |    |--- ...
   |
   |--- flat
   |    |--- *flat*.fits
   |    |--- ...
   |
   |--- object1
   |    |--- *.fits
   |    |--- ...
   |
   |--- object2
   |    |--- *.fits
   |    |--- ...
   |
   ...
```

Where `root_path` is the input dir for command line argument `-i`.
Intermediate files will be saved to a `calib_files` folder in the `-o` argument path.

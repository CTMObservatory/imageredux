import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import imageredux as redux
import unittest
from astropy.io import fits
import ccdproc
from numpy.random import normal


class TestCombinations(unittest.TestCase):
    def setUp(self):
        num_test_files = 3
        self.ccds = []
        self.nrows = 10
        self.ncols = 10
        for i in range(num_test_files):
            ccd = ccdproc.CCDData(
                normal(loc=100, scale=5, size=(self.nrows, self.ncols)),
                unit='adu',
                )
            ccd.header = {'exposure': 60.0}
            self.ccds.append(ccd)
        self.darkmaster_fname = None
        self.flatmaster_fname = None
        self.out_dir = "outputs"
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        redux.log = open(os.path.join(self.out_dir, "log.txt"), "w")

    def tearDown(self):
        redux.log.close()
        import shutil
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_do_dark_combine(self):
        darkmaster, dark_fname = redux.do_dark_combine(self.ccds, self.out_dir)
        self.darkmaster_fname = dark_fname
        # Test if darkmaster is correct type
        self.assertTrue(isinstance(darkmaster, ccdproc.CCDData))
        # Test if darkmaster shape is correct shape
        self.assertEqual(darkmaster.shape, (self.nrows, self.ncols))
        # Test if darkmaster file was saved
        self.assertTrue(os.path.exists(dark_fname))
        # Test if darkmaster file has correct shape
        self.assertEqual(fits.getdata(dark_fname).shape, (self.nrows, self.ncols))

    def test_do_flat_combine(self):
        dark_master = ccdproc.CCDData(
            normal(loc=100, scale=5, size=(self.nrows, self.ncols)),
            unit='adu',
            )
        dark_master.header = {'exposure': 60.0}
        flatmaster, flat_fname = redux.do_flat_combine(
            self.ccds, dark_master, self.out_dir,
            )
        self.flatmaster_fname = flat_fname
        # Test if flatmaster is correct type
        self.assertTrue(isinstance(flatmaster, ccdproc.CCDData))
        # Test if flatmaster shape is correct shape
        self.assertEqual(flatmaster.shape, (self.nrows, self.ncols))
        # Test if flatmaster file was saved
        self.assertTrue(os.path.exists(flat_fname))
        # Test if flatmaster file has correct shape
        self.assertEqual(fits.getdata(flat_fname).shape, (self.nrows, self.ncols))


class TestCalibrate(unittest.TestCase):
    def setUp(self):
        num_test_files = 3
        self.ccds = []
        self.nrows = 10
        self.ncols = 10
        self.out_dir = "outputs"
        self.in_dir = "inputs"
        self.obj_name = "ngc4993"
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        if not os.path.exists(self.in_dir):
            os.makedirs(self.in_dir)
        for i in range(num_test_files):
            ccd_hdu = fits.PrimaryHDU(
                data=normal(loc=100, scale=5, size=(self.nrows, self.ncols)),
                )
            ccd_hdu.header['EXPOSURE'] = 60.0
            fname = os.path.join(
                self.in_dir, "{}_{:02d}.fits".format(self.obj_name, i),
                )
            ccd_hdu.writeto(fname)
            self.ccds.append(fname)
        redux.log = open(os.path.join(self.out_dir, "log.txt"), "w")

    def tearDown(self):
        redux.log.close()
        import shutil
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)
        if os.path.exists(self.in_dir):
            shutil.rmtree(self.in_dir)

    def test_do_calibrate(self):
        dark_master = ccdproc.CCDData(
            normal(loc=100, scale=5, size=(self.nrows, self.ncols)),
            unit='adu',
            )
        dark_master.header = {'exposure': 60.0}
        flat_master = ccdproc.CCDData(
            normal(loc=100, scale=5, size=(self.nrows, self.ncols)),
            unit='adu',
            )
        flat_master.header = {'exposure': 60.0}
        cal_ccds, cal_fnames = redux.do_calibrate(
            self.ccds, flat_master, dark_master, self.obj_name, self.out_dir,
            )
        for acal in cal_ccds:
            # Test if it's correct type
            self.assertTrue(isinstance(acal, ccdproc.CCDData))
            # Test if its shape is correct
            self.assertEqual(acal.shape, (self.nrows, self.ncols))
        for afile in cal_fnames:
            # Test if file was saved
            self.assertTrue(os.path.exists(afile))
            # Test if file has correct shape
            self.assertEqual(fits.getdata(afile).shape, (self.nrows, self.ncols))


if __name__ == "__main__":
    unittest.main()

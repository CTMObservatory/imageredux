import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import imageredux as redux
import unittest
from astropy.io import fits
import ccdproc


class TestCombinations(unittest.TestCase):
    def setUp(self):
        from numpy.random import normal
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
        redux.log = open("log.txt", "w")
        self.darkmaster_fname = None
        self.flatmaster_fname = None
        self.out_dir = "outputs"
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    def tearDown(self):
        if self.darkmaster_fname and os.path.exists(self.darkmaster_fname):
            os.remove(self.darkmaster_fname)
        if self.flatmaster_fname and os.path.exists(self.flatmaster_fname):
            os.remove(self.flatmaster_fname)
        redux.log.close()
        if os.path.exists("log.txt"):
            os.remove("log.txt")
        if os.path.exists(self.out_dir):
            os.rmdir(self.out_dir)

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
        from numpy.random import normal
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


if __name__ == "__main__":
    unittest.main()

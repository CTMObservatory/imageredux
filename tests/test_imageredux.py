import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import imageredux
import unittest
from astropy.io import fits
import ccdproc


class TestDoDarkCombine(unittest.TestCase):
    def setUp(self):
        from numpy.random import normal
        num_test_dark_files = 3
        self.darks = []
        self.nrows = 10
        self.ncols = 10
        for i in range(num_test_dark_files):
            self.darks.append(
                ccdproc.CCDData(
                    normal(loc=100, scale=5, size=(self.nrows, self.ncols)),
                    unit='adu',
                    )
                )
        imageredux.log = open("log.txt", "w")
        self.darkmaster_fname = None

    def tearDown(self):
        if os.path.exists(self.darkmaster_fname):
            os.remove(self.darkmaster_fname)
        imageredux.log.close()
        if os.path.exists("log.txt"):
            os.remove("log.txt")

    def test_do_dark_combine(self):
        darkmaster, dark_fname = imageredux.do_dark_combine(self.darks, ".")
        self.darkmaster_fname = dark_fname
        # Test if darkmaster is correct type
        self.assertTrue(isinstance(darkmaster, ccdproc.CCDData))
        # Test if darkmaster shape is correct shape
        self.assertEqual(darkmaster.shape, (self.nrows, self.ncols))
        # Test if darkmaster file was saved
        self.assertTrue(os.path.exists(dark_fname))
        # Test if darkmaster file has correct shape
        self.assertEqual(fits.getdata(dark_fname).shape, (self.nrows, self.ncols))


class TestFlatCombine(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_do_flat_combine(self):
        pass


if __name__ == "__main__":
    unittest.main()

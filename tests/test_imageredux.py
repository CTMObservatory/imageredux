import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import imageredux
import unittest
from astropy.io import fits


class TestDarkComb(unittest.TestCase):
    def setUp(self):
        from numpy.random import normal
        num_test_dark_files = 3
        self.darkfilenames = []
        for i in range(num_test_dark_files):
            hdu = fits.PrimaryHDU(data=normal(loc=100, scale=5, size=(10, 10)))
            darkname = "dark_test_{:02d}.fits".format(i)
            self.darkfilenames.append(darkname)
            hdu.writeto(darkname)
        self.darkmaster_fname = None

    def tearDown(self):
        for afile in self.darkfilenames:
            os.remove(afile)
        if self.darkmaster_fname:
            os.remove(self.darkmaster_fname)

    def test_doDarkComb(self):
        self.darkmaster_fname = imageredux.doDarkComb(self.darkfilenames)
        self.assertTrue(os.path.exists(self.darkmaster_fname))

class TestRedux(unittest.TestCase):
    def setUp(self):
        from numpy.random import normal
        image_hdu = fits.PrimaryHDU(data=normal(loc=100, scale=5, size=(10, 10)))
        image_hdu.header['EXPTIME'] = 60.0
        self.image_name = "image.fits"
        image_hdu.writeto(self.image_name)

        dark_hdu = fits.PrimaryHDU(data=normal(loc=100, scale=5, size=(10, 10)))
        dark_hdu.header['EXPTIME'] = 60.0
        self.dark_name = "dark_master.fits"
        dark_hdu.writeto(self.dark_name)

        flat_hdu = fits.PrimaryHDU(data=normal(loc=100, scale=5, size=(10, 10)))
        self.flat_name = "flat_master.fits"
        flat_hdu.writeto(self.flat_name)

        self.redux_name = None

    def tearDown(self):
        os.remove(self.image_name)
        os.remove(self.dark_name)
        os.remove(self.flat_name)
        if self.redux_name:
            os.remove(self.redux_name)

    def test_redux(self):
        self.redux_name = imageredux.redux(self.image_name,
                                         self.dark_name,
                                         self.flat_name)
        self.assertTrue(os.path.exists(self.redux_name))

if __name__ == "__main__":
    unittest.main()

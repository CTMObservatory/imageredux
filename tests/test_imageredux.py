import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import imageredux
import unittest
from astropy.io import fits


class TestImageRedux(unittest.TestCase):
    def setUp(self):
        from numpy.random import normal
        num_test_dark_files = 3
        self.darkfilenames = []
        for i in range(num_test_dark_files):
            hdu = fits.PrimaryHDU(data=normal(loc=100, scale=5, size=(10, 10)))
            darkname = "dark_test_{:02d}.fits".format(i)
            self.darkfilenames.append(darkname)
            hdu.writeto(darkname)

    def tearDown(self):
        for afile in self.darkfilenames:
            os.remove(afile)

    def test_examplefunction(self):
        self.assertEqual(imageredux.examplefunction(1, 2), "Hello World!")

    def test_doDarkComb(self):
        darkmaster_fname = imageredux.doDarkComb(self.darkfilenames)
        self.assertTrue(os.path.exists(darkmaster_fname))


if __name__ == "__main__":
    unittest.main()

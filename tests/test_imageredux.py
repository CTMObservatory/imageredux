import unittest
import sys
import os

sys.path.append(os.path.abspath("."))
import imageredux


class TestImageRedux(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_examplefunction(self):
        self.assertEqual(imageredux.examplefunction(1, 2), "Hello World!")


if __name__ == "__main__":
    unittest.main()

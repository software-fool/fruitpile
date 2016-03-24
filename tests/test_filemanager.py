import unittest
import inspect
import os.path
import sys
from datetime import datetime

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from repo.filemanager import FileHandler, FileManager

class TestFileHandler(unittest.TestCase):

  def test_open_a_file_to_read(self):
    filename = "%s/data/example_file.txt" % (mydir)
    fh = FileHandler.create_file(filename, "r")
    data = fh.read()
    self.assertEquals(data, open(filename, "r").read())


if __name__ == "__main__":
  unittest.main()


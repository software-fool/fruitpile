# Copyright (c) 2016 Dominic Binks (software-fool on github)
# This file is part of Fruitpile.
#
# Fruitpile is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fruitpile is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fruitpile.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import inspect
import os.path
import sys
import io
from datetime import datetime

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from fruitpile.repo.filemanager import FileHandler, FileManager

class TestFileHandler(unittest.TestCase):

  def setUp(self):
    self.filename = "/tmp/test_filehandler.%d.txt" % (os.getpid())

  def tearDown(self):
    try:
      os.remove(self.filename)
    except OSError:
      pass

  def test_open_a_file_to_read(self):
    filename = "%s/data/example_file.txt" % (mydir)
    fh = FileHandler.create_file(filename, "r")
    data = fh.read()
    self.assertEquals(data, io.open(filename, "rb").read())

  def test_open_a_file_to_write(self):
    fh = FileHandler.create_file(self.filename, "w")
    contents = b"This is the files contents"
    fh.write(contents)
    fh.close()
    fob = io.open(self.filename, "rb")
    data = fob.read()
    self.assertEquals(contents, data)

  def test_chunked_writing(self):
    fh = FileHandler.create_file(self.filename, "w")
    chunk = b"This is the files contents"
    for i in range(5):
      fh.write(chunk)
    fh.close()
    fob = io.open(self.filename, "rb")
    data = fob.read()
    self.assertEquals(chunk*5, data)

  def test_chunked_reading(self):
    filename = "%s/data/example_file.txt" % (mydir)
    fh = FileHandler.create_file(filename, "r")
    data = fh.read(5)
    self.assertEquals(data, b"My na")

  def test_op_on_closed_file(self):
    with self.assertRaises(IOError):
      filename = "%s/data/example_file.txt" % (mydir)
      fh = FileHandler.create_file(filename, "r")
      fh.close()
      fh.read()

if __name__ == "__main__":
  unittest.main()


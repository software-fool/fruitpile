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

import os
import logging
import io

logger = logging.getLogger(__name__)

class FileHandler(object):

  def __init__(self, fob):
    self.fob = fob
    self.is_open = True

  def write(self, data):
    if not self.is_open:
      raise IOError("file not open")
    return self.fob.write(data)

  def close(self):
    self.fob.close()
    self.is_open = False

  def read(self, n=None):
    if not self.is_open:
      raise IOError("file not open")
    if n:
      data = self.fob.read(n)
    else:
      data = self.fob.read()
    return data

  @staticmethod
  def create_file(path, mode):
    return FileHandler(io.open(path, 'b'+mode))


class FileManager(object):
  def __init__(self, repopath):
    self.repopath = repopath

  def open(self, path, mode):
    dest = os.path.join(self.repopath, path)
    logger.debug("opening file %s with mode %s" % (path, mode))
    filedir = os.path.dirname(dest)
    if not os.path.isdir(filedir):
      os.makedirs(filedir, 0o700)
    fh = FileHandler.create_file(dest, mode)
    return fh




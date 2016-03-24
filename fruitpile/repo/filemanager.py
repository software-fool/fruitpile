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
    self.db = self.os.path(repopath, "repodb")

  def open(self, path, mode):
    logger.debug("opening file %s with mode %s")
    fh = FileHandler.create_file(os.path.join(self.repopath, path), mode)
    return fh




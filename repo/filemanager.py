import os
import logging

logger = logging.getLogger(__name__)

class FileHandler(object):

  def __init__(self, fob):
    self.fob = fob

  def write(self, data):
    return self.fob.write(data)

  def read(self, n=None):
    if n:
      data = self.fob.read(n)
    else:
      data = self.fob.read()
    return data

  @staticmethod
  def create_file(path, mode):
    return FileHandler(fob.open(path, mode))


class FileManager(object):
  def __init__(self, repopath):
    self.repopath = repopath
    self.db = self.os.path(repopath, "repodb")

  def open(self, path, mode):
    logger.debug("opening file %s with mode %s")
    fh = FileHandler.create_file(os.path.join(self.repopath, path), mode)
    return fh




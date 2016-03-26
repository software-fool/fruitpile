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

from .db.schema import *
from sqlalchemy.orm import sessionmaker
from importlib import import_module
from .fp_exc import *
import os
from datetime import datetime
from hashlib import sha1, sha256, sha512
from shutil import copyfileobj
import io
from .repo.filemanager import FileManager, FileHandler
import socket
import pwd

def _checksum_file(fob, hasher):
  m = hasher()
  while True:
    chunk = fob.read(128*1024)
    if chunk == "":
      break
    m.update(chunk)
  return m.hexdigest()

class Fruitpile(object):

  def __init__(self, path="store"):
    self.path=path
    self.dbpath = os.path.join(path,"fpl.db")

  def open(self):
    if not os.path.exists(self.dbpath):
      raise FPLConfiguration('fruitpile instance not found')
    self.lockpath = os.path.join(self.path, ".lock")
    self.hostname = socket.gethostname()
    self.pid = os.getpid()
    self.owner = os.getuid()
    self.owner_name = pwd.getpwuid(self.owner)[0]
    try:
      os.symlink("%s-%d-%d=%s" % (self.hostname, self.pid, self.owner, self.owner_name), self.lockpath)
    except OSError:
      raise FPLRepoInUse("%s path already in use %s" % (self.dbpath, os.readlink(self.lockpath)))
    self.engine = create_engine('sqlite:///%s' % (self.dbpath))
    Session = sessionmaker(bind=self.engine)
    self.session = Session()
    repos = self.session.query(Repo).all()
    if len(repos) != 1:
      raise FPLConfiguration('Only one repo handler supported')
    repo = repos[0]
    assert repo.repo_type == "FileManager"
    self.repo_data = repo
    self.repo = FileManager(self.repo_data.path)

  def add_new_fileset(self, **kwargs):
    fs = FileSet(name=kwargs.get("name"), repo=self.repo_data)
    self.session.add(fs)
    self.session.commit()
    return fs

  def list_filesets(self, **kwargs):
    fss = self.session.query(FileSet).all()
    return fss

  def add_file(self, **kwargs):
    srcfob = io.open(kwargs.get("source_file"), "rb")
    checksum = _checksum_file(srcfob, sha256)
    name = kwargs.get("name")
    path = kwargs.get("path")
    bf = BinFile(fileset_id=kwargs.get("fileset_id"),
                 name=name,
                 path=path,
                 version=kwargs.get("version"),
                 revision=kwargs.get("revision"),
                 primary=kwargs.get("primary"),
                 state=State(name="untested"),
                 create_date=datetime.now(),
                 update_date=datetime.now(),
                 source=kwargs.get("source"),
                 checksum=checksum)
    self.session.add(bf)
    snkfob = self.repo.open(os.path.join(path,name),"w")
    # we copy the file before commiting so that if the file copy fails
    # for some reason we should rollback the transaction and the database
    # is consistent with the file store
    srcfob.seek(0, 0)
    copyfileobj(srcfob, snkfob)
    self.session.commit()

  def list_files(self):
    bfs = self.session.query(BinFile).all()
    return bfs

  def init(self, **kwargs):
    if os.path.exists(self.path):
      raise FPLExists('cannot initialise the repo because the path already exists')
    if os.access(self.path, os.W_OK|os.R_OK|os.X_OK):
      raise FPLConfiguration('cannot access the target directory')
    os.mkdir(self.path)
    self.engine = create_engine('sqlite:///%s' % (self.dbpath))
    Base.metadata.create_all(bind=self.engine)
    Session = sessionmaker(bind=self.engine)
    self.session = Session()
    rp = Repo(name="default", path=self.path, repo_type="FileManager")
    self.session.add(rp)
    ss = []
    for sname in ["untested","testing","tested","approved","released","withdrawn"]:
      self.session.add(State(name=sname))
    self.session.commit()

  def close(self):
    self.repo.close()
    self.session.close()
    self.engine.dispose()
    os.remove(self.lockpath)
    self.lockpath = None

  def  __del__(self):
    # If we go out of scope and the object's being destroyed make sure
    # we remove the lock file.  Users should call close on the repo
    # before saying goodbye, but this should protect against cases
    # of unexpected termination
    if self.lockpath:
        os.remove(self.lockpath)

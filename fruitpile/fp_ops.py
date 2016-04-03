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
from sqlalchemy.exc import IntegrityError
from importlib import import_module
from .fp_exc import *
from .fp_perms import PermissionManager
from .fp_constants import *
from .fp_state import StateMachine
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
    if len(chunk) == 0:
      break
    m.update(chunk)
  return m.hexdigest()

class Fruitpile(object):

  def __init__(self, path="store"):
    self.path=path
    self.dbpath = os.path.join(path,"fpl.db")
    self.lockpath = None
    self.state_map = {}

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
    states = self.session.query(State).all()
    for state in states:
      self.state_map[state.name] = state.id
    self.perm_manager = PermissionManager(self.session)
    self.sm = StateMachine.create_state_machine(self.session)

  def init(self, **kwargs):
    if os.path.exists(self.path):
      raise FPLExists('cannot initialise the repo because the path already exists')
    if os.access(self.path, os.W_OK|os.R_OK|os.X_OK):
      raise FPLConfiguration('cannot access the target directory')
    os.mkdir(self.path)
    self.engine = create_engine('sqlite:///%s' % (self.dbpath))
    upgrade(self.engine, kwargs.get("uid"), kwargs.get("username"), self.path)
    Session = sessionmaker(bind=self.engine)
    self.session = Session()
    # Initialise the static data in the database
    self.sm = StateMachine.create_state_machine(self.session)

  def close(self):
    self.repo.close()
    self.session.close()
    self.engine.dispose()
    try:
      os.remove(self.lockpath)
    except OSError as exc:
      if exc[0] != 2:
        raise
    self.lockpath = None

  def  __del__(self):
    # If we go out of scope and the object's being destroyed make sure
    # we remove the lock file.  Users should call close on the repo
    # before saying goodbye, but this should protect against cases
    # of unexpected termination
    if self.lockpath:
        os.remove(self.lockpath)

  def add_new_fileset(self, **kwargs):
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.ADD_FILESET)
    fs = FileSet(name=kwargs.get("name"), version=kwargs.get("version"), revision=kwargs.get("revision"), repo=self.repo_data)
    self.session.add(fs)
    try:
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      raise FPLFileSetExists("file set %s already exists in store" % (kwargs.get("name")))
    return fs

  def list_filesets(self, **kwargs):
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.LIST_FILESETS)
    fss = self.session.query(FileSet).all()
    return fss

  def add_file(self, **kwargs):
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.ADD_FILE)
    source_file = kwargs.get("source_file")
    if not os.path.exists(source_file):
      raise FPLSourceFileNotFound("%s cannot be found" % (source_file))
    if not os.access(source_file, os.R_OK):
      raise FPLSourceFilePermissionDenied("%s cannot be read" % (source_file))
    srcfob = io.open(source_file, "rb")
    checksum = _checksum_file(srcfob, sha256)
    name = kwargs.get("name")
    path = kwargs.get("path")
    jot = datetime.now()
    bf = BinFile(fileset_id=kwargs.get("fileset_id"),
                 name=name,
                 path=path,
                 primary=kwargs.get("primary"),
                 state_id=self.state_map["untested"],
                 create_date=jot,
                 update_date=jot,
                 source=kwargs.get("source"),
                 checksum=checksum)
    self.session.add(bf)
    snkfob = self.repo.open(os.path.join(path,name),"w")
    # we copy the file before commiting so that if the file copy fails
    # for some reason we should rollback the transaction and the database
    # is consistent with the file store
    srcfob.seek(0, 0)
    copyfileobj(srcfob, snkfob)
    srcfob.close()
    snkfob.close()
    try:
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      raise FPLBinFileExists("binfile %s/%s in fileset (id=%d) already exists in store" % (name, path, kwargs.get("fileset_id")))
    return bf

  def transit_file(self, **kwargs):
    uid = kwargs.get("uid")
    file_id = kwargs.get("file_id")
    req_state = kwargs.get("req_state")
    if not self.sm.is_valid_state(req_state):
      raise FPLInvalidState("state %s is not a valid state" % (req_state))
    bf = self.session.query(BinFile).filter(BinFile.id == file_id).all()
    if len(bf) == 0:
      raise FPLBinFileNotExists("binfile with id=%d cannot be found" % (file_id))
    bf = bf[0]
    if not bf.primary:
      raise FPLInvalidTargetForStateChange("binfile with id=%d is an auxilliary file" % (file_id))
    new_state = self.sm.transit(uid, self.perm_manager, req_state, self)
    bf.state_id = self.sm.state_id
    bf.update_date = datetime.now()
    self.session.commit()
    return bf

  def list_files(self, **kwargs):
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.LIST_FILES)
    bfs = self.session.query(BinFile).all()
    return bfs

  def get_file(self, **kwargs):
    uid = kwargs.get("uid")
    file_id = kwargs.get("file_id")
    to_file = kwargs.get("to_file")
    self.perm_manager.check_permission(uid, Capability.GET_FILES)
    bfs = self.session.query(BinFile).filter(BinFile.id == file_id).all()
    if bfs == []:
      raise FPLBinFileNotExists("binfile with id=%d cannot be found" % (file_id))
    bf = bfs[0]
    if os.path.exists(to_file):
      raise FPLFileExists("Destination for get file exists, dest=%s" % (to_file))
    if not os.access(os.path.dirname(to_file), os.W_OK):
      raise FPLCannotWriteFile("Destination file directory not writeable %s" % (to_file))
    srcfob = self.repo.open(os.path.join(bf.path,bf.name),"r")
    snkfob = io.open(to_file, "wb")
    copyfileobj(srcfob, snkfob)
    srcfob.close()
    snkfob.close()
    return True

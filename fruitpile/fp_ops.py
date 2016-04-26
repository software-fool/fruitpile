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
    self.state_map = {}

  def open(self):
    if not os.path.exists(self.dbpath):
      raise FPLConfiguration('fruitpile instance not found')
    self.hostname = socket.gethostname()
    self.pid = os.getpid()
    self.owner = os.getuid()
    self.owner_name = pwd.getpwuid(self.owner)[0]
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

  def add_new_fileset(self, **kwargs):
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.ADD_FILESET)
    fs = FileSet(name=kwargs.get("name"), version=kwargs.get("version"), revision=kwargs.get("revision"), repo=self.repo_data)
    self.session.add(fs)
    try:
      self.session.commit()
      return fs
    except IntegrityError:
      self.session.rollback()
      raise FPLFileSetExists("file set %s already exists in store" % (kwargs.get("name")))

  def list_filesets(self, **kwargs):
    count = kwargs.get("count", -1)
    start_at = kwargs.get("start_at", 1)
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.LIST_FILESETS)
    q = self.session.query(FileSet).order_by(FileSet.id)
    if start_at != 1:
      q = q.offset(start_at)
    if count != -1:
      q = q.limit(count)
    fss = q.all()
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
    new_state = self.sm.transit(uid, self.perm_manager, bf.state.name, req_state, {"bf":bf,"obj":self})
    bf.state_id = self.sm.state_id
    bf.update_date = datetime.now()
    self.session.commit()
    return bf

  def list_files(self, **kwargs):
    count = kwargs.get("count", -1)
    start_at = kwargs.get("start_at", 1)
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.LIST_FILES)
    q = self.session.query(BinFile).order_by(BinFile.id)
    if start_at != 1:
      q = q.offset(start_at)
    if count != -1:
      q = q.limit(count)
    bfs = q.all()
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

  def tag_fileset(self, **kwargs):
    uid = kwargs.get("uid")
    fs = kwargs.get("fileset")
    tag = kwargs.get("tag")
    self.perm_manager.check_permission(uid, Capability.TAG_FILESET)
    tags = self.session.query(Tag).filter(Tag.tag == tag).all()
    if tags == []:
      tag = Tag(tag=tag)
      self.session.add(tag)
      self.session.commit()
    else:
      tag = tags[0]
      existing_tags = fs.tags(self.session)
      if tag.tag in existing_tags:
        return False
    tag_assoc = TagAssoc(tag_id=tag.id, fileset_id=fs.id)
    self.session.add(tag_assoc)
    self.session.commit()
    return True

  def add_fileset_property(self, **kwargs):
    uid = kwargs.get("uid")
    fileset = kwargs.get("fileset")
    name = kwargs.get("name")
    value = kwargs.get("value")
    update = kwargs.get("update", False)
    self.perm_manager.check_permission(uid, Capability.ADD_FILESET_PROPERTY)
    pas = self.session.query(PropAssoc).filter(PropAssoc.fileset_id == fileset.id).all()
    for pa in pas:
      prop = self.session.query(Property).filter(Property.id == pa.prop_id).one()
      if prop.name == name:
        if not update:
          raise FPLPropertyExists(name)
        self.perm_manager.check_permission(uid, Capability.UPDATE_FILESET_PROPERTY)
        prop.value = value
        self.session.commit()
        return True
    prop = Property(name=name, value=value)
    self.session.add(prop)
    self.session.commit()
    pa = PropAssoc(prop_id=prop.id, fileset_id=fileset.id)
    self.session.add(pa)
    self.session.commit()
    return True

  def get_fileset(self, **kwargs):
    uid = kwargs.get("uid")
    fileset_id = kwargs.get("fileset_id", None)
    name = kwargs.get("name", None)
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.LIST_FILESETS)
    if not name and not fileset_id:
      raise FPLNoFilesetSpecified
    q = self.session.query(FileSet)
    if name:
      q = q.filter(FileSet.name == name)
    if fileset_id:
      q = q.filter(FileSet.id == fileset_id)
    fss = q.all()
    return fss

  def tag_binfile(self, **kwargs):
    uid = kwargs.get("uid")
    bf = kwargs.get("binfile")
    tag = kwargs.get("tag")
    self.perm_manager.check_permission(uid, Capability.TAG_BINFILE)
    tags = self.session.query(Tag).filter(Tag.tag == tag).all()
    if tags == []:
      tag = Tag(tag=tag)
      self.session.add(tag)
      self.session.commit()
    else:
      tag = tags[0]
      existing_tags = bf.tags(self.session)
      if tag.tag in existing_tags:
        return False
    binfile_tag = BinFileTag(tag_id=tag.id, binfile_id=bf.id)
    self.session.add(binfile_tag)
    self.session.commit()
    return True

  def add_binfile_property(self, **kwargs):
    uid = kwargs.get("uid")
    binfile = kwargs.get("binfile")
    name = kwargs.get("name")
    value = kwargs.get("value")
    update = kwargs.get("update", False)
    self.perm_manager.check_permission(uid, Capability.ADD_BINFILE_PROPERTY)
    pas = self.session.query(BinFileProp).filter(BinFileProp.binfile_id == binfile.id).all()
    for pa in pas:
      prop = self.session.query(Property).filter(Property.id == pa.prop_id).one()
      if prop.name == name:
        if not update:
          raise FPLPropertyExists(name)
        self.perm_manager.check_permission(uid, Capability.UPDATE_BINFILE_PROPERTY)
        prop.value = value
        self.session.commit()
        return True
    prop = Property(name=name, value=value)
    self.session.add(prop)
    self.session.commit()
    pa = BinFileProp(prop_id=prop.id, binfile_id=binfile.id)
    self.session.add(pa)
    self.session.commit()
    return True

  def get_binfile(self, **kwargs):
    uid = kwargs.get("uid")
    binfile_id = kwargs.get("binfile_id", None)
    name = kwargs.get("name", None)
    self.perm_manager.check_permission(kwargs.get("uid"), Capability.LIST_FILES)
    if not name and not binfile_id:
      raise FPLNoBinfileSpecified
    q = self.session.query(BinFile)
    if name:
      q = q.filter(BinFile.name == name)
    if binfile_id:
      q = q.filter(BinFile.id == binfile_id)
    bfs = q.all()
    return bfs


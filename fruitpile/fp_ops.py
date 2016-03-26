from db.schema import *
from sqlalchemy.orm import sessionmaker
from importlib import import_module
from fp_exc import *
import os
from datetime import datetime
from hashlib import sha1, sha256, sha512
from shutil import copyfileobj
import io
from repo.filemanager import FileManager, FileHandler

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

  def get_filesets(self, **kwargs):
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
    

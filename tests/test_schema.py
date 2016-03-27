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
from datetime import datetime

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from fruitpile.db.schema import *
from sqlalchemy.orm import sessionmaker

def setUpDatabase():
  engine = create_engine('sqlite:///:memory:')
  Base.metadata.create_all(bind=engine)
  Session = sessionmaker(bind=engine)
  session = Session()
  return engine, session

class TestSchemaState(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_a_state(self):
    ss = self.session.query(State).all()
    self.assertEquals(len(ss), 0)    
    s = State(name="unverified")
    self.assertEquals(s.name, "unverified")
    self.session.add(s)
    self.session.commit()
    self.session.rollback()
    ss = self.session.query(State).all()
    self.assertEquals(len(ss), 1)
    self.assertEquals(ss[0], s)

  def test_create_multiple_states(self):
    state_names = ["unverified","in-testing","tested","approved","released"]
    s1s = []
    for i in state_names:
      s = State(name=i)
      self.session.add(s)
      s1s.append(s)
    self.session.commit()
    ss = self.session.query(State).all()
    self.assertEquals(len(ss), 5)
    for i in range(len(ss)):
        self.assertEquals(ss[i], s1s[i])

  def test_create_duplicate_state_should_fail(self):
    st1 = State(name="test_state")
    st2 = State(name="test_state")
    self.session.add_all([st1,st2])
    with self.assertRaises(IntegrityError):
      self.session.commit()
    self.session.rollback()

class TestSchemaRepo(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_a_repo(self):
    repos = self.session.query(Repo).all()
    self.assertEquals(len(repos), 0)
    repo = Repo(name="default", path="/export/fruitpile/repo", repo_type="FileManager")
    self.session.add(repo)
    self.session.commit()
    repos = self.session.query(Repo).all()
    self.assertEquals(len(repos), 1)
    self.assertEquals(repos[0], repo)

class TestSchemaFileSet(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()
  
  def tearDown(self):
    self.session.close()

  def test_create_a_fileset(self):
    fss = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 0)
    repo = Repo(name="default", path="/export/fruitpile/repo", repo_type="FileManager")
    fs = FileSet(name="test-1", repo=repo)
    self.session.add(fs)
    self.session.commit()
    fss = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 1)
    self.assertEquals(fss[0], fs)

  def test_create_multiple_filesets(self):
    fss = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 0)
    repo = Repo(name="default", path="/export/fruitpile/repo", repo_type="FileManager")
    fss = []
    for i in range(0,10):
      fs = FileSet(name="test-%d" % (i), repo=repo)
      self.session.add(fs)
      fss.append(fs)
    self.session.commit()
    fss2 = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 10)
    self.assertEquals(fss, fss2)


class TestSchemaBinFile(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_a_bin_file(self):
    bfs = self.session.query(BinFile).all()
    self.assertEquals(len(bfs), 0)
    repo = Repo(name="default", path="/export/fruitpile/repo", repo_type="FileManager")
    fs = FileSet(name="test-1", repo=repo)
    st = State(name="unverified")
    bf = BinFile(fileset=fs,
                 name="xx-1.4.tar.gz",
                 path="build-1/xx-1.4.tar.gz",
                 version="4",
                 revision="1234",
                 primary=True,
                 state=st,
                 create_date=datetime(2016,3,24),
                 update_date=datetime(2016,3,24),
                 source="buildbot",
                 checksum="12345")
    self.session.add(bf)
    self.session.commit()
    bfs = self.session.query(BinFile).all()
    self.assertEquals(len(bfs), 1)
    self.assertEquals(bfs[0], bf)

  def test_create_multiple_bin_files(self):
    bfs = self.session.query(BinFile).all()
    self.assertEquals(len(bfs), 0)
    repo = Repo(name="default", path="/export/fruitpile/repo", repo_type="FileManager")
    fs = FileSet(name="test-1", repo=repo)
    st = State(name="unverified")
    bfs = []
    targets = ["arm-cortex_m4","arm-cortex_a8","x86","x86_64","mip32","java","python"]
    for n in targets:
      bf = BinFile(fileset=fs,
                   name="xx-%s-1.4.tar.gz" % (n),
                   path="build-1/xx-%s-1.4.tar.gz" % (n),
                   version="4",
                   revision="1234",
                   primary=True,
                   state=st,
                   create_date=datetime(2016,2,12),
                   update_date=datetime(2016,2,12),
                   source="buildbot01",
                   checksum="12345-%s" % (n))
      bfs.append(bf)
      self.session.add(bf)
    self.session.commit()
    bfs1 = self.session.query(BinFile).all()
    self.assertEquals(len(bfs1), len(targets))
    self.assertEquals(bfs1, bfs)


class TestSchemaPermission(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_single_permission(self):
    perm = Permission(name="ADD_FILESET", desc="Grant permission to add a fileset")
    self.session.add(perm)
    self.session.commit()
    self.session.rollback()
    self.assertEquals(perm.name, "ADD_FILESET")
    self.assertEquals(perm.id, 1)
    perms = self.session.query(Permission).all()
    self.assertEquals(len(perms), 1)
    self.assertEquals(perms[0], perm)
    self.assertEquals(perms[0].name, "ADD_FILESET")
    self.assertEquals(perms[0].desc,"Grant permission to add a fileset")

  def test_create_multiple_permissions(self):
    perm_names = [("ADD_FILESET","Grant permission to add a fileset"),
                  ("ADD_FILES","Grant permission to add a file"),
                  ("LIST_FILESETS","Grant permission to list all filesets"),
                  ("LIST_FILES","Grant permission to list all files")]
    ps1 = []
    for name, desc in perm_names:
      ps1.append(Permission(name=name, desc=desc))
    self.session.add_all(ps1)
    self.session.commit()
    self.session.rollback()
    self.assertEquals(len(ps1), len(perm_names))
    ps2 = self.session.query(Permission).all()
    self.assertEquals(len(ps2), len(perm_names))
    self.assertEquals(ps1, ps2)

  def test_fail_to_create_duplicates(self):
    perm1 = Permission(name="ADD_FILESET", desc="Grant permission to add a fileset")
    self.session.add(perm1)
    perm2 = Permission(name="ADD_FILESET", desc="Some other permission with the same name")
    self.session.add(perm2)
    with self.assertRaises(IntegrityError):
      self.session.commit()
    self.session.rollback()


if __name__ == "__main__":
  unittest.main()

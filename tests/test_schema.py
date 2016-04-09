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
    self.assertEquals(str(s), "<State(unverified)>")
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

  def test_create_state_transitions(self):
    perm = Permission(name="A_PERMISSION", desc="A permission for testing")
    st1 = State(name="start")
    st2 = State(name="in-progress")
    st3 = State(name="in-review")
    st4 = State(name="approved")
    st5 = State(name="rejected")
    self.session.add_all([perm,st1,st2,st3,st4,st5])
    self.session.commit()
    trns1 = Transition(start_id=st1.id, end_id=st2.id, perm=perm)
    trns2 = Transition(start_id=st1.id, end_id=st5.id, perm=perm)
    self.session.add_all([trns1,trns2])
    self.session.commit()
    self.assertEquals(str(trns1), "<Transition(start=>in-progress)>")
    ts0 = self.session.query(Transition).all()
    self.assertEquals(len(ts0), 2)
    self.assertEquals(ts0[0].start_id, st1.id)
    self.assertEquals(ts0[0].end_id, st2.id)
    self.assertEquals(ts0[0].perm_id, perm.id)
    self.assertEquals(ts0[1].start_id, st1.id)
    self.assertEquals(ts0[1].end_id, st5.id)
    self.assertEquals(ts0[1].perm_id, perm.id)

  def test_create_state_transition_with_transition_function(self):
    st1 = State(name="begin")
    st2 = State(name="end")
    transfn = TransitionFunction(transfn="ensure_reviewed")
    perm = Permission(name="A_PERMISSION", desc="A permission for testing")
    self.session.add_all([st1,st2,transfn,perm])
    self.session.commit()
    trns1 = Transition(start_id=st1.id, end_id=st2.id, perm=perm, transfn_id=transfn.id)
    self.session.add(trns1)
    self.session.commit()
    ts = self.session.query(Transition).all()
    self.assertEquals(len(ts), 1)
    ts0 = ts[0]
    self.assertEquals(str(ts0), "<Transition(begin=>end with transfn=<TransitionFunction(ensure_reviewed)>([]))>")
    self.assertEquals(ts0.start_id, st1.id)
    self.assertEquals(ts0.end_id, st2.id)
    self.assertEquals(ts0.perm_id, perm.id)
    self.assertEquals(ts0.transfn_id, transfn.id)

  def test_create_state_transition_with_transition_function_and_data(self):
    st1 = State(name="begin")
    st2 = State(name="end")
    transfn = TransitionFunction(transfn="transition_function")
    perm = Permission(name="A_PERMISSION", desc="A permission for testing")
    self.session.add_all([st1,st2,transfn,perm])
    self.session.commit()
    trns1 = Transition(start_id=st1.id, end_id=st2.id, perm=perm, transfn_id=transfn.id)
    self.session.add(trns1)
    self.session.commit()
    trns_data = TransitionFunctionData(trans_id=trns1.id, data="THIS IS SOME DATA")
    self.session.add(trns_data)
    self.session.commit()
    transitions = self.session.query(Transition).all()
    self.assertEquals(len(transitions), 1)
    t0 = transitions[0]
    self.assertEquals(str(t0), "<Transition(begin=>end with transfn=<TransitionFunction(transition_function)>([<TransitionFunctionData(fn_id=1,data=THIS IS SOME DATA)>]))>")
    tdata = self.session.query(TransitionFunctionData).filter(TransitionFunctionData.trans_id==t0.id).all()
    self.assertEquals(len(tdata), 1)
    self.assertEquals(tdata[0].data, "THIS IS SOME DATA")


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
    fs = FileSet(name="test-1", version="3.1", revision="1234", repo=repo)
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
      fs = FileSet(name="test-%d" % (i), version="%s" % (i), revision="%s" % (i), repo=repo)
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
    fs = FileSet(name="test-1",
                 version="4",
                 revision="1234",
                 repo=repo)
    st = State(name="unverified")
    bf = BinFile(fileset=fs,
                 name="xx-1.4.tar.gz",
                 path="build-1/xx-1.4.tar.gz",
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
    self.assertEquals(str(bf), "<BinFile(name='xx-1.4.tar.gz', path='build-1/xx-1.4.tar.gz')>")

  def test_create_multiple_bin_files(self):
    bfs = self.session.query(BinFile).all()
    self.assertEquals(len(bfs), 0)
    repo = Repo(name="default", path="/export/fruitpile/repo", repo_type="FileManager")
    fs = FileSet(name="test-1",
                 version="4",
                 revision="1234",
                 repo=repo)
    st = State(name="unverified")
    bfs = []
    targets = ["arm-cortex_m4","arm-cortex_a8","x86","x86_64","mip32","java","python"]
    for n in targets:
      bf = BinFile(fileset=fs,
                   name="xx-%s-1.4.tar.gz" % (n),
                   path="build-1/xx-%s-1.4.tar.gz" % (n),
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

class TestSchemaUsers(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_user(self):
    perm = Permission(name="GOD", desc="God power to do everything")
    self.session.add(perm)
    self.session.commit()
    user = User(uid=1046, name="db")
    user_perms = UserPermission(user_id=1046, perm_id=perm.id)
    self.session.add_all([user,user_perms])
    self.session.commit()
    perms_for = self.session.query(UserPermission).all()
    self.assertEquals(len(perms_for), 1)
    perms_for_1046 = perms_for[0]
    self.assertEquals(perms_for_1046.user_id, 1046)
    self.assertEquals(perms_for_1046.user.name, "db")
    self.assertEquals(perms_for_1046.perm_id, perm.id)
    self.assertEquals(perms_for_1046.perm.name, "GOD")
    self.assertEquals(str(user), "<User(db=1046)>")
    self.assertEquals(str(user_perms), "<UserPermission(uid=1046,permid=1)>")

  def test_create_user_with_permissions_subset(self):
    perm_names = [("ADD_FILESET","Grant permission to add a fileset"),
                  ("ADD_FILES","Grant permission to add a file"),
                  ("LIST_FILESETS","Grant permission to list all filesets"),
                  ("LIST_FILES","Grant permission to list all files")]
    ps = []
    for name, desc in perm_names:
      ps.append(Permission(name=name, desc=desc))
    self.session.add_all(ps)
    self.session.commit()
    user = User(uid=1046, name="db")
    user_perms = [UserPermission(user_id=1046, perm_id=ps[2].id),
                  UserPermission(user_id=1046, perm_id=ps[3].id)]
    self.session.add_all([user]+user_perms)
    self.session.commit()
    users0 = self.session.query(User).all()
    user0 = users0[0]
    self.assertEquals(len(users0), 1)
    self.assertEquals(user0.uid, 1046)
    self.assertEquals(user0.user_perms[0].perm, ps[2])
    self.assertEquals(user0.user_perms[1].perm ,ps[3])
    self.assertNotIn(ps[0], user0.user_perms)
    self.assertNotIn(ps[1], user0.user_perms)

class TestMigrations(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_migration(self):
    mig = Migration(script="base_01")
    self.session.add(mig)
    self.session.commit()
    self.assertEquals(mig.script, "base_01")
    self.assertEquals(str(mig), "<Migration(id=1, script=base_01)>")

  def test_retrieve_migration(self):
    mig = Migration(script="base_level")
    self.session.add(mig)
    self.session.commit()
    self.assertEquals(mig.id, 1)
    records = self.session.query(Migration).all()
    self.assertEquals(len(records), 1)
    self.assertEquals(records[0], mig)

class TestPermission(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_permission(self):
    perm = Permission(name="OMNIPOTENCE", desc="An all powerful permission")
    self.session.add(perm)
    self.session.commit()
    self.assertEquals(perm.id, 1)
    self.assertEquals(str(perm), "<Permission(OMNIPOTENCE=1)>")


if __name__ == "__main__":
  unittest.main()

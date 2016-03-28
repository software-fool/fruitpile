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
from __future__ import print_function
import unittest
import io
import os
import sys
import sqlite3
import pprint

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from fruitpile import Fruitpile, FPLExists, FPLConfiguration, FPLRepoInUse, FPLFileSetExists, FPLBinFileExists, FPLSourceFileNotFound, FPLSourceFilePermissionDenied, FPLPermissionDenied
from fruitpile.db.schema import *
from fruitpile.fp_constants import Capability
from fruitpile.fp_state import StateMachine

# Destroys the entire tree of data (python equivalent of rm -rf)
def clear_tree(path):
  if os.path.exists(path) and os.path.isdir(path):
    for root, dirs, files in os.walk(path, topdown=False):
      for f in files:
        os.remove(os.path.join(root,f))
      for d in dirs:
        if os.path.exists(d):
          os.rmdir(d)
      os.rmdir(root)

class TestFruitpileInitOperations(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)

  def tearDown(self):
    clear_tree(self.store_path)

  def test_init_a_new_repo(self):
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    self.assertTrue(os.path.exists(self.store_path))
    dbpath = os.path.join(self.store_path, "fpl.db")
    self.assertTrue(os.path.exists(dbpath))
    conn = sqlite3.connect(dbpath)
    self.assertNotEquals(conn, None)
    curs = conn.execute("SELECT * FROM SQLITE_MASTER")
    rows = curs.fetchall()
    expected_tables = ["states",
                       "transfuncs",
                       "transitions",
                       "permissions",
                       "users",
                       "user_perms",
                       "repos",
                       "filesets",
                       "binfiles"]
    for r in rows:
      if r[0] == "table":
        self.assertTrue(r[1] in expected_tables)
    curs = conn.execute("SELECT * FROM repos")
    rows = curs.fetchall()
    self.assertEquals(len(rows), 1)
    # id, name, path, manager
    self.assertEquals(rows[0], (1,"default",self.store_path,"FileManager"))

  def test_init_a_new_repo_when_path_exists(self):
    with self.assertRaises(FPLExists):
      fob = io.open(self.store_path, "wb")
      fob.write(b"I am here\n")
      fob.close()
      fp = Fruitpile(self.store_path)
      fp.init(uid=1046, username="db")
    os.remove(self.store_path)

  def test_init_with_an_exist_repo_in_place(self):
    with self.assertRaises(FPLExists):
      fp1 = Fruitpile(self.store_path)
      fp1.init(uid=1046, username="db")
      fp2 = Fruitpile(self.store_path)
      fp2.init(uid=1046, username="db")


class TestFruitpileOpenOperations(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)

  def tearDown(self):
    clear_tree(self.store_path)

  def test_open_non_existent_repo(self):
    with self.assertRaises(FPLConfiguration):
      fp = Fruitpile(self.store_path)
      fp.open()

  def test_open_existing_repo(self):
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.assertNotEquals(fp.session, None)
    self.assertEquals(fp.repo.__class__.__name__, "FileManager")
    self.assertEquals(Capability.ADD_FILESET, 1)
    self.assertEquals(Capability.ADD_FILE, 2)
    self.assertEquals(Capability.LIST_FILESETS, 3)
    self.assertEquals(Capability.LIST_FILES, 4)
    self.assertEquals(Capability.BEGIN_TESTING, 5)
    self.assertEquals(Capability.WITHDRAW_ARTIFACT, 6)
    self.assertEquals(Capability.ARTIFACT_TESTED, 7)
    self.assertEquals(Capability.APPROVE_ARTIFACT, 8)
    self.assertEquals(Capability.RELEASE_ARTIFACT, 9)
    session = fp.session
    perms = session.query(UserPermission).filter(UserPermission.user_id==1046).all()
    self.assertEquals(len(perms), 9)

  def test_reopen_existing_repo(self):
    fp1 = Fruitpile(self.store_path)
    fp1.init(uid=1046, username="db")
    fp1.open()
    fp2 = Fruitpile(self.store_path)
    with self.assertRaises(FPLRepoInUse):
      fp2.open()
      self.assertEquals(fp1, fp2)

  def test_open_on_unreadable_permissions(self):
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    fp.close()
    os.chmod(self.store_path, 0o000)
    fp = Fruitpile(self.store_path)
    with self.assertRaises(FPLConfiguration):
      fp.open()
    os.chmod(self.store_path, 0o700)

class TestFruitpileAddFileSetOperations(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp

  def tearDown(self):
    self.fp.close()
    clear_tree(self.store_path)

  def test_list_filesets(self):
    filesets = self.fp.list_filesets(uid=1046)
    self.assertEquals(filesets, [])

  def test_add_new_fileset(self):
    fileset = self.fp.add_new_fileset(name="test-1", uid=1046)
    self.assertEquals(str(fileset), "<FileSet(test-1 in default)>")
    filesets = self.fp.list_filesets(uid=1046)
    self.assertEquals(len(filesets), 1)
    self.assertEquals(filesets[0], fileset)

  def test_add_duplicate_fileset(self):
    fs1 = self.fp.add_new_fileset(name="test-1", uid=1046)
    self.assertEquals(str(fs1), "<FileSet(test-1 in default)>")
    with self.assertRaises(FPLFileSetExists):
      fs2 = self.fp.add_new_fileset(name="test-1", uid=1046)

  def test_add_multiple_filesets(self):
    fss1 = []
    for i in range(10):
      fss1.append(self.fp.add_new_fileset(name="test-%d" % (i), uid=1046))
    fss2 = self.fp.list_filesets(uid=1046)
    self.assertEquals(fss1, fss2)



class TestFruitpileBinFileOperations(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp

  def tearDown(self):
    self.fp.close()
    clear_tree(self.store_path)

  def test_add_a_new_fileset_and_file(self):
    bfs = self.fp.list_files(uid=1046)
    self.assertEquals(bfs, [])
    fs =self.fp.add_new_fileset(name="test-1", uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        version="1",
        revision="123",
        primary=True,
        source="buildbot")
    bfs = self.fp.list_files(uid=1046)
    self.assertEquals(len(bfs), 1)
    self.assertEquals(bfs[0], bf)

  def test_add_multiple_files_to_fileset(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEquals(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1", uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bfs1 = []
    for i in range(10):
      bfs1.append(
          self.fp.add_file(
              uid=1046,
              source_file=filename,
              fileset_id=fs.id,
              name="requirements-%d.txt" % (i),
              path="deploy",
              version="1",
              revision="123",
              primary=True,
              source="buildbot")
      )
    self.assertEquals(len(bfs1), 10)
    bfs2 = self.fp.list_files(uid=1046)
    self.assertEquals(bfs1, bfs2)

  def test_add_multiple_files_to_multiple_filesets(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEquals(bfs0, [])
    fss = []
    for i in range(3):
      fss.append(self.fp.add_new_fileset(name="test-%d" % (i), uid=1046))
    bfs2 = []
    filename = "%s/data/example_file.txt" % (mydir)
    for j in range(12):
      bfs2.append(self.fp.add_file(
          uid=1046,
          source_file=filename,
          fileset_id = fss[j % 3].id,
          name="requirements-%d.txt" % (j),
          path="deploy",
          version="%d" % (j),
          revision="123",
          primary=True,
          source="buildbot")
              )
    self.assertEquals(len(bfs2), 12)
    bfs3 = self.fp.list_files(uid=1046)
    self.assertEquals(bfs2, bfs3)

  def test_add_same_file_and_path_twice_to_same_file_set(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEquals(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1", uid=1046)
    fs2 = self.fp.add_new_fileset(name="test-2", uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf1 = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id = fs.id,
        name="requirements.txt",
        path="deploy",
        version="1",
        revision="123",
        primary=True,
        source="buildbot")
    with self.assertRaises(FPLBinFileExists):
      bf2 = self.fp.add_file(
          uid=1046,
          source_file=filename,
          fileset_id = fs2.id,
          name="requirements.txt",
          path="deploy",
          version="1",
          revision="123",
          primary=True,
          source="buildbot")
    bfs1 = self.fp.list_files(uid=1046)
    self.assertEquals(len(bfs1), 1)
    self.assertEquals(bfs1[0], bf1)

  def test_add_same_name_to_same_file_set(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEquals(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1", uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf1 = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id = fs.id,
        name="requirements.txt",
        path="deploy",
        version="1",
        revision="123",
        primary=True,
        source="buildbot")
    with self.assertRaises(FPLBinFileExists):
      bf2 = self.fp.add_file(
          uid=1046,
          source_file = filename,
          fileset_id = fs.id,
          name ="requirements.txt",
          path="deploy1",
          version="1",
          revision="123",
          primary=True,
          source="buildbot")
    bfs1 = self.fp.list_files(uid=1046)
    self.assertEquals(len(bfs1), 1)
    self.assertEquals(bfs1[0], bf1)

  def test_add_missing_source_file(self):
    fs = self.fp.add_new_fileset(name="test-1", uid=1046)
    filename = "%s/data/example_file-1.txt" % (mydir)
    with self.assertRaises(FPLSourceFileNotFound):
      bf = self.fp.add_file(
          uid=1046,
          source_file=filename,
          fileset_id = fs.id,
          name="requirements.txt",
          path="deploy",
          version="1",
          revision="123",
          primary=True,
          source="buildbot")

  def test_add_unreadable_file(self):
    fs = self.fp.add_new_fileset(name="test-1", uid=1046)
    unreadable_file = "/tmp/_unreadable_%d" % (os.getpid())
    fob = io.open(unreadable_file, "wb")
    fob.close()
    os.chmod(unreadable_file, 0o000)
    with self.assertRaises(FPLSourceFilePermissionDenied):
      bf = self.fp.add_file(
          uid=1046,
          source_file=unreadable_file,
          fileset_id = fs.id,
          name="requirements.txt",
          path="deploy",
          version="1",
          revision="123",
          primary=True,
          source="buildbot")
    os.chmod(unreadable_file, 0o644)
    os.remove(unreadable_file)

  def test_add_fileset_without_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      fs = self.fp.add_new_fileset(name="test-1", uid=1047)

  def test_add_fileset_and_file_without_file_permission(self):
    session = self.fp.session
    user = User(uid=1047, name="test_user")
    perm1 = UserPermission(user_id=1047, perm_id=Capability.ADD_FILESET)
    perm2 = UserPermission(user_id=1047, perm_id=Capability.LIST_FILESETS)
    perm3 = UserPermission(user_id=1047, perm_id=Capability.LIST_FILES)
    session.add_all([user,perm1,perm2,perm3])
    session.commit()
    fs = self.fp.add_new_fileset(name="test-1", uid=1047)
    filename = "%s/data/example_file.txt" % (mydir)
    with self.assertRaises(FPLPermissionDenied):
      bf = self.fp.add_file(
        uid=1047,
        source_file=filename,
        fileset_id = fs.id,
        name="requirements.txt",
        path="deploy",
        version="1",
        revision="123",
        primary=True,
        source="buildbot")

def state_machine_callback_helper(uid, perm_man, old_state, new_state, obj):
  obj.called_back_uid = uid
  obj.called_back_perm_man = perm_man
  obj.called_back_old_state = old_state
  obj.called_back_new_state = new_state

class TestFruitpileStateMachine(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    self.called_back_uid = None
    self.called_back_perm_man = None
    self.called_back_old_state = None
    self.called_back_new_state = None

  def tearDown(self):
    self.fp.close()
    clear_tree(self.store_path)

  def test_create_state_machine(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    untested_state = self.fp.session.query(State).filter(State.name == "untested").first()
    self.assertEquals(sm.state, untested_state.name)
    self.assertEquals(len(sm._transitions), 6)
    untested_trans = sm._transitions[sm.state]
    self.assertEquals(len(untested_trans), 2)
    self.assertTrue("testing" in untested_trans)
    self.assertTrue("withdrawn" in untested_trans)
    self.assertTrue(untested_trans["testing"].capability, Capability.BEGIN_TESTING)
    self.assertEquals(sm.state_id, untested_state.id)

  def test_transition_from_one_state_to_another(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    sm.transit(1046, self.fp.perm_manager, "testing", self)
    self.assertEquals(sm.state, "testing")
    self.assertEquals(self.called_back_uid, None)
    self.assertEquals(self.called_back_perm_man, None)
    self.assertEquals(self.called_back_old_state, None)
    self.assertEquals(self.called_back_new_state, None)

  def test_transitions_through_all_states(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    init_state = "untested"
    for s in ["testing","tested","approved","released"]:
      new_state = sm.transit(1046, self.fp.perm_manager, s, self)
      self.assertEquals(sm.state, new_state)
    self.assertEquals(self.called_back_uid, None)
    self.assertEquals(self.called_back_perm_man, None)
    self.assertEquals(self.called_back_old_state, None)
    self.assertEquals(self.called_back_new_state, None)



if __name__ == "__main__":
  unittest.main()

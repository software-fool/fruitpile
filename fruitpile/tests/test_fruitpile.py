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
import sqlite3
from datetime import datetime, timedelta

from fruitpile import (
  Fruitpile,
  FPLExists,
  FPLConfiguration,
  FPLRepoInUse,
  FPLFileSetExists,
  FPLBinFileExists,
  FPLSourceFileNotFound,
  FPLSourceFilePermissionDenied,
  FPLPermissionDenied,
  FPLInvalidStateTransition,
  FPLInvalidState,
  FPLBinFileNotExists,
  FPLInvalidTargetForStateChange,
  FPLFileExists,
  FPLCannotTransitionState,
  FPLPropertyExists)
from fruitpile.db.schema import (
  State,
  BinFile,
  User,
  UserPermission,
  Tag,
  Property,
  PropAssoc,
  BinFileProp,
  downgrade)
from fruitpile.fp_constants import Capability
from fruitpile.fp_state import StateMachine


mydir = os.path.dirname(__file__)

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
    self.assertNotEqual(conn, None)
    curs = conn.execute("SELECT * FROM SQLITE_MASTER")
    rows = curs.fetchall()
    expected_tables = [
      "binfiles",
      "binfile_props",
      "binfile_tags",
      "comments",
      "filesets",
      "migrations",
      "permissions",
      "properties",
      "props_assocs",
      "repos",
      "states",
      "tags",
      "tags_assocs",
      "transfuncs",
      "transitions",
      "transfuncdata",
      "user_perms",
      "users"
    ]
    for r in rows:
      if r[0] == "table":
        self.assertTrue(r[1] in expected_tables)
    curs = conn.execute("SELECT * FROM repos")
    rows = curs.fetchall()
    self.assertEqual(len(rows), 1)
    # id, name, path, manager
    self.assertEqual(rows[0], (1,"default",self.store_path,"FileManager"))

  def test_init_a_new_repo_downgrade(self):
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    self.assertTrue(os.path.exists(self.store_path))
    downgrade(fp.engine)
    dbpath = os.path.join(self.store_path, "fpl.db")
    self.assertTrue(os.path.exists(dbpath))
    conn = sqlite3.connect(dbpath)
    self.assertNotEqual(conn, None)
    curs = conn.execute("SELECT * FROM SQLITE_MASTER")
    rows = curs.fetchall()
    self.assertEqual(rows, [])

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
    self.assertNotEqual(fp.session, None)
    self.assertEqual(fp.repo.__class__.__name__, "FileManager")
    self.assertEqual(Capability.ADD_FILESET, 1)
    self.assertEqual(Capability.ADD_FILE, 2)
    self.assertEqual(Capability.LIST_FILESETS, 3)
    self.assertEqual(Capability.LIST_FILES, 4)
    self.assertEqual(Capability.BEGIN_TESTING, 5)
    self.assertEqual(Capability.WITHDRAW_ARTIFACT, 6)
    self.assertEqual(Capability.ARTIFACT_TESTED, 7)
    self.assertEqual(Capability.APPROVE_ARTIFACT, 8)
    self.assertEqual(Capability.RELEASE_ARTIFACT, 9)
    self.assertEqual(Capability.GET_FILES, 10)
    self.assertEqual(Capability.TAG_FILESET, 11)
    self.assertEqual(Capability.ADD_FILESET_PROPERTY, 12)
    self.assertEqual(Capability.UPDATE_FILESET_PROPERTY, 13)
    self.assertEqual(Capability.TAG_BINFILE, 14)
    self.assertEqual(Capability.ADD_BINFILE_PROPERTY, 15)
    self.assertEqual(Capability.UPDATE_BINFILE_PROPERTY, 16)
    session = fp.session
    perms = session.query(UserPermission).filter(
      UserPermission.user_id==1046).all()
    self.assertEqual(len(perms), 16)

  def test_reopen_existing_repo(self):
    fp1 = Fruitpile(self.store_path)
    fp1.init(uid=1046, username="db")
    fp1.open()
    fp2 = Fruitpile(self.store_path)
    fp2.open()
    self.assertNotEqual(fp1, fp2)

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
    self.assertEqual(filesets, [])

  def _add_n_filesets(self, n):
    for i in range(1,n + 1):
      self.fp.add_new_fileset(uid=1046,
                              name="test-{}".format(i),
                              version="3.1",
                              revision="{}".format(1))

  def test_list_limit_filesets(self):
    self._add_n_filesets(10)
    filesets = self.fp.list_filesets(uid=1046, count=3)
    self.assertEqual(len(filesets), 3)
    for i in range(1,4):
      self.assertEqual(filesets[i - 1].name, "test-{}".format(i))

  def test_list_start_at_filesets(self):
    self._add_n_filesets(10)
    filesets = self.fp.list_filesets(uid=1046, start_at=7)
    self.assertEqual(len(filesets), 3)
    for i in range(3):
      self.assertEqual(filesets[i].name, "test-{}".format(i + 8))

  def test_list_start_at_limit_filesets(self):
    self._add_n_filesets(10)
    filesets = self.fp.list_filesets(uid=1046, count=3, start_at=4)
    self.assertEqual(len(filesets), 3)
    for i in range(3):
      self.assertEqual(filesets[i].name, "test-{}".format(i + 5))

  def test_add_new_fileset(self):
    fileset = self.fp.add_new_fileset(name="test-1",
                                      version="3.1",
                                      revision="1234",
                                      uid=1046)
    self.assertEqual(str(fileset), "<FileSet(test-1 in default)>")
    filesets = self.fp.list_filesets(uid=1046)
    self.assertEqual(len(filesets), 1)
    self.assertEqual(filesets[0], fileset)

  def test_add_duplicate_fileset(self):
    fs1 = self.fp.add_new_fileset(name="test-1",
                                  version="3.1",
                                  revision="1234",
                                  uid=1046)
    self.assertEqual(str(fs1), "<FileSet(test-1 in default)>")
    with self.assertRaises(FPLFileSetExists):
      self.fp.add_new_fileset(name="test-1",
                              version="3.1", revision="1234", uid=1046)

  def test_add_multiple_filesets(self):
    fss1 = []
    for i in range(10):
      fss1.append(self.fp.add_new_fileset(name="test-%d" % (i),
                                          version="0.1",
                                          revision="%s" % (i),
                                          uid=1046))
    fss2 = self.fp.list_filesets(uid=1046)
    self.assertEqual(fss1, fss2)


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
    self.assertEqual(bfs, [])
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    bfs = self.fp.list_files(uid=1046)
    self.assertEqual(len(bfs), 1)
    self.assertEqual(bfs[0], bf)
    self.assertLessEqual(datetime.now() - bf.create_date, timedelta(seconds=1))
    self.assertLessEqual(datetime.now() - bf.update_date, timedelta(seconds=1))

  def test_add_multiple_files_to_fileset(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
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
              primary=True,
              source="buildbot")
      )
    self.assertEqual(len(bfs1), 10)
    bfs2 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs1, bfs2)

  def test_add_multiple_files_to_fileset_with_auxilliaries(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
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
              primary=True if i == 0 else False,
              source="buildbot")
      )
    self.assertEqual(len(bfs1), 10)
    bfs2 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs1, bfs2)
    primaries = [x for x in filter(lambda x: x.primary, bfs2)]
    auxilliaries = [x for x in filter(lambda x: not x.primary, bfs2)]
    self.assertEqual(len(primaries), 1)
    self.assertEqual(len(auxilliaries), 9)
    self.assertEqual(primaries[0].id, 1)
    auxilliary_ids = sorted([auxilliary.id for auxilliary in auxilliaries])
    self.assertEqual(auxilliary_ids, [2,3,4,5,6,7,8,9,10])

  def test_add_multiple_files_to_multiple_filesets(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs0, [])
    fss = []
    for i in range(3):
      fss.append(self.fp.add_new_fileset(name="test-%d" % (i),
                                         version="%s" % (i),
                                         revision="%s" % (123 + i),
                                         uid=1046))
    bfs2 = []
    filename = "%s/data/example_file.txt" % (mydir)
    for j in range(12):
      bfs2.append(self.fp.add_file(
          uid=1046,
          source_file=filename,
          fileset_id=fss[j % 3].id,
          name="requirements-%d.txt" % (j),
          path="deploy",
          primary=True,
          source="buildbot")
      )
    self.assertEqual(len(bfs2), 12)
    bfs3 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs2, bfs3)

  def _add_n_filesets_m_files_each(self, n, m):
    for i in range(1, n + 1):
      self.fp.add_new_fileset(uid=1046,
                              name="test-{}".format(i),
                              version="3.1",
                              revision="{}".format(1))
    filename = "%s/data/example_file.txt" % (mydir)
    for i in range(1, m + 1):
      self.fp.add_file(uid=1046,
                       source_file=filename,
                       fileset_id=1,
                       name="artifact-%d.txt" % (i),
                       path="deploy",
                       primary=True,
                       source="buildbot")

  def test_list_files(self):
    self._add_n_filesets_m_files_each(1, 10)
    bfs = self.fp.list_files(uid=1046)
    self.assertEqual(len(bfs), 10)
    for i in range(10):
      self.assertEqual(bfs[i].name, "artifact-{}.txt".format(i + 1))

  def test_list_count_files(self):
    self._add_n_filesets_m_files_each(1, 10)
    bfs = self.fp.list_files(uid=1046, count=3)
    self.assertEqual(len(bfs), 3)
    for i in range(3):
      self.assertEqual(bfs[i].name, "artifact-{}.txt".format(i + 1))

  def test_list_start_at_files(self):
    self._add_n_filesets_m_files_each(1, 10)
    bfs = self.fp.list_files(uid=1046, start_at=7)
    self.assertEqual(len(bfs), 3)
    for i in range(3):
      self.assertEqual(bfs[i].name, "artifact-{}.txt".format(i + 8))

  def test_list_count_and_start_at_files(self):
    self._add_n_filesets_m_files_each(1, 10)
    bfs = self.fp.list_files(uid=1046, start_at=4, count=3)
    self.assertEqual(len(bfs), 3)
    for i in range(3):
      self.assertEqual(bfs[i].name, "artifact-{}.txt".format(i + 5))

  def test_add_same_file_and_path_twice_to_same_file_set(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    fs2 = self.fp.add_new_fileset(name="test-2",
                                  version="2",
                                  revision="124",
                                  uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf1 = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    with self.assertRaises(FPLBinFileExists):
      self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs2.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    bfs1 = self.fp.list_files(uid=1046)
    self.assertEqual(len(bfs1), 1)
    self.assertEqual(bfs1[0], bf1)

  def test_add_same_name_to_same_file_set(self):
    bfs0 = self.fp.list_files(uid=1046)
    self.assertEqual(bfs0, [])
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf1 = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    with self.assertRaises(FPLBinFileExists):
      self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy1",
        primary=True,
        source="buildbot")
    bfs1 = self.fp.list_files(uid=1046)
    self.assertEqual(len(bfs1), 1)
    self.assertEqual(bfs1[0], bf1)

  def test_add_missing_source_file(self):
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    filename = "%s/data/example_file-1.txt" % (mydir)
    with self.assertRaises(FPLSourceFileNotFound):
      self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")

  def test_add_unreadable_file(self):
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    unreadable_file = "/tmp/_unreadable_%d" % (os.getpid())
    fob = io.open(unreadable_file, "wb")
    fob.close()
    os.chmod(unreadable_file, 0o000)
    with self.assertRaises(FPLSourceFilePermissionDenied):
      self.fp.add_file(
        uid=1046,
        source_file=unreadable_file,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    os.chmod(unreadable_file, 0o644)
    os.remove(unreadable_file)

  def test_add_fileset_without_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      self.fp.add_new_fileset(name="test-1", uid=1047)

  def test_add_fileset_and_file_without_file_permission(self):
    session = self.fp.session
    user = User(uid=1047, name="test_user")
    perm1 = UserPermission(user_id=1047, perm_id=Capability.ADD_FILESET)
    perm2 = UserPermission(user_id=1047, perm_id=Capability.LIST_FILESETS)
    perm3 = UserPermission(user_id=1047, perm_id=Capability.LIST_FILES)
    session.add_all([user,perm1,perm2,perm3])
    session.commit()
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1047)
    filename = "%s/data/example_file.txt" % (mydir)
    with self.assertRaises(FPLPermissionDenied):
      self.fp.add_file(
        uid=1047,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
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
    untested_state = self.fp.session.query(State).filter(
      State.name == "untested").first()
    self.assertEqual(sm.state, untested_state.name)
    self.assertEqual(len(sm._transitions), 6)
    untested_trans = sm._transitions[sm.state]
    self.assertEqual(len(untested_trans), 2)
    self.assertTrue("testing" in untested_trans)
    self.assertTrue("withdrawn" in untested_trans)
    self.assertTrue(untested_trans["testing"].capability,
                    Capability.BEGIN_TESTING)
    self.assertEqual(sm.state_id, untested_state.id)

  def test_transition_from_one_state_to_another(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    sm.transit(1046, self.fp.perm_manager, "untested", "testing", {"obj":self})
    self.assertEqual(sm.state, "testing")
    self.assertEqual(self.called_back_uid, None)
    self.assertEqual(self.called_back_perm_man, None)
    self.assertEqual(self.called_back_old_state, None)
    self.assertEqual(self.called_back_new_state, None)

#  def test_transitions_through_all_states(self):
#    sm = StateMachine.create_state_machine(self.fp.session)
#    init_state = "untested"
#    for s in ["testing","tested","approved","released"]:
#      new_state = sm.transit(1046, self.fp.perm_manager, init_state, s, self)
#      self.assertEqual(sm.state, new_state)
#      init_state = new_state
#    self.assertEqual(self.called_back_uid, None)
#    self.assertEqual(self.called_back_perm_man, None)
#    self.assertEqual(self.called_back_old_state, None)
#    self.assertEqual(self.called_back_new_state, None)

  def test_illegal_transition_1(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    with self.assertRaises(FPLInvalidStateTransition):
      sm.transit(1046, self.fp.perm_manager,
                 "untested", "approved", self)

  def test_illegal_transition_2(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    new_state = sm.transit(1046, self.fp.perm_manager,
                           "untested", "testing", {"obj":self})
    with self.assertRaises(FPLInvalidStateTransition):
      sm.transit(1046, self.fp.perm_manager,
                 "testing", "approved", {"obj":self})

  def test_illegal_transition_3(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    new_state = sm.transit(1046, self.fp.perm_manager,
                           "untested", "testing", {"obj":self})
    with self.assertRaises(FPLInvalidStateTransition):
      sm.transit(1046, self.fp.perm_manager,
                 "testing", "untested", {"obj":self})

  def test_user_without_permission_to_transition_state(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    with self.assertRaises(FPLPermissionDenied):
      sm.transit(1047, self.fp.perm_manager,
                 "untested", "testing", {"obj":self})


class TestFruitpileStateTransitOperations(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.bf = bf
    self.fs = fs
    self.filename = filename
    self.assertEqual(self.bf.state.name, "untested")

  def tearDown(self):
    self.bf = None
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_create_file_and_transit_through_api(self):
    bf = self.fp.transit_file(uid=1046,
                              file_id=self.bf.id,
                              req_state="testing")
    self.assertEqual(bf.state.name, "testing")
    self.fp.session.rollback()
    bfs = self.fp.session.query(BinFile).all()
    self.assertEqual(len(bfs), 1)
    bf0 = bfs[0]
    self.assertEqual(bf0.state.name, "testing")
    self.assertNotEqual(bf0.update_date, bf0.create_date)

  def test_create_file_and_transit_through_api_invalid_state(self):
    with self.assertRaises(FPLInvalidStateTransition):
      self.fp.transit_file(uid=1046,
                           file_id=self.bf.id,
                           req_state="approved")
    self.assertEqual(self.bf.state_id, 1)
    self.assertEqual(self.bf.update_date, self.bf.create_date)

  def test_create_file_and_transit_to_unknown_state(self):
    with self.assertRaises(FPLInvalidState):
      self.fp.transit_file(uid=1046,
                           file_id=self.bf.id,
                           req_state="happy-birthday")
    self.assertEqual(self.bf.state_id, 1)
    self.assertEqual(self.bf.update_date, self.bf.create_date)

  def test_create_file_and_try_transit_without_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      self.fp.transit_file(uid=1047, file_id=self.bf.id, req_state="testing")
    self.assertEqual(self.bf.state_id, 1)
    self.assertEqual(self.bf.update_date, self.bf.create_date)

  def test_create_file_and_try_to_transit_unknown_file(self):
    with self.assertRaises(FPLBinFileNotExists):
      self.fp.transit_file(uid=1046,
                           file_id=self.bf.id + 1,
                           req_state="testing")
    self.assertEqual(self.bf.update_date, self.bf.create_date)

  def test_attempt_to_transit_an_auxilliary_file(self):
    bf = self.fp.add_file(
        uid=1046,
        source_file=self.filename,
        fileset_id=self.fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")
    with self.assertRaises(FPLInvalidTargetForStateChange):
      bf = self.fp.transit_file(uid=1046, file_id=bf.id, req_state="testing")
    self.assertEqual(self.bf.update_date, self.bf.create_date)

  def test_transit_file_without_accompanying_auxilliary_file(self):
    bf = self.fp.transit_file(uid=1046,
                              file_id=self.bf.id,
                              req_state="testing")
    self.assertEqual(bf.state.name, "testing")
    with self.assertRaises(FPLCannotTransitionState):
      bf = self.fp.transit_file(uid=1046,
                                file_id=self.bf.id, req_state="tested")

  def test_transit_file_with_accompanying_auxilliary_file(self):
    af = self.fp.add_file(
        uid=1046,
        source_file=self.filename,
        fileset_id=self.fs.id,
        name="test_report",
        path="deploy",
        primary=False,
        source="buildbot")
    bf = self.fp.transit_file(uid=1046,
                              file_id=self.bf.id,
                              req_state="testing")
    self.assertEqual(bf.state.name, "testing")
    bf = self.fp.transit_file(uid=1046, file_id=self.bf.id, req_state="tested")
    self.assertEqual(bf.state.name, "tested")


class TestFruitpileGetFileFromRepo(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    self.bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.aux = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")
    self.filename = filename

  def tearDown(self):
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_get_file_from_file_store(self):
    to_file = "/tmp/got_file.%d" % (os.getpid())
    self.fp.get_file(uid=1046, file_id=self.bf.id, to_file=to_file)
    orig_contents = io.open(self.filename, "rb").read()
    copy_contents = io.open(to_file, "rb").read()
    self.assertEqual(orig_contents, copy_contents)
    os.remove(to_file)

  def test_get_file_from_file_store_unknown_id(self):
    to_file = "/tmp/got_file.%d" % (os.getpid())
    with self.assertRaises(FPLBinFileNotExists):
      self.fp.get_file(uid=1046, file_id=self.aux.id + 1, to_file=to_file)

  def test_get_aux_file_from_store(self):
    to_file = "/tmp/got_file.%d" % (os.getpid())
    self.fp.get_file(uid=1046, file_id=self.aux.id, to_file=to_file)
    orig_contents = io.open(self.filename, "rb").read()
    copy_contents = io.open(to_file, "rb").read()
    self.assertEqual(orig_contents, copy_contents)
    os.remove(to_file)

  def test_try_get_file_over_existing_file(self):
    to_file = "/tmp/got_file.%d" % (os.getpid())
    self.fp.get_file(uid=1046, file_id=self.bf.id, to_file=to_file)
    with self.assertRaises(FPLFileExists):
      self.fp.get_file(uid=1046, file_id=self.aux.id, to_file=to_file)


class TestTransitionWithTransitionFunction(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    filename = "%s/data/example_file.txt" % (mydir)
    self.bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.aux = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")

  def tearDown(self):
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_check_file_with_file_name_exists(self):
    sm = StateMachine.create_state_machine(self.fp.session)
    new_state = sm.transit


class TestTags(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    self.fs = fs
    filename = "%s/data/example_file.txt" % (mydir)
    self.bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.aux = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")

  def tearDown(self):
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_create_new_tag(self):
    self.fp.tag_fileset(uid=1046, fileset=self.fs, tag="RC1")
    self.assertEqual(self.fs.tags(self.fp.session), ["RC1"])

  def test_create_new_tag_no_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      self.fp.tag_fileset(uid=1045, fileset=self.fs, tag="RC1")

  def test_create_reapply_same_tag(self):
    self.fp.tag_fileset(uid=1046, fileset=self.fs, tag="RC1")
    self.fp.tag_fileset(uid=1046, fileset=self.fs, tag="RC1")
    self.assertEqual(self.fs.tags(self.fp.session), ["RC1"])

  def test_add_multiple_tags(self):
    some_tags = ["RC1","RC2","RC3"]
    for t in some_tags:
      self.fp.tag_fileset(uid=1046, fileset=self.fs, tag=t)
    self.assertEqual(sorted(self.fs.tags(self.fp.session)), some_tags)

  def test_add_same_tag_to_multiple_filesets(self):
    tag = "RC1"
    fs = self.fp.add_new_fileset(name="test-2",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    self.fp.tag_fileset(uid=1046, fileset=self.fs, tag=tag)
    self.fp.tag_fileset(uid=1046, fileset=fs, tag=tag)
    tags = self.fp.session.query(Tag).all()
    self.assertEqual(len(tags), 1)


class TestProperty(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    self.fs = fs
    filename = "%s/data/example_file.txt" % (mydir)
    self.bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.aux = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")

  def tearDown(self):
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_add_new_property(self):
    self.fp.add_fileset_property(uid=1046,
                                 fileset=self.fs,
                                 name="TestDate",
                                 value="2015-10-31")
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})

  def test_add_new_property_no_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      self.fp.add_fileset_property(uid=1045, fileset=self.fs,
                                   name="TestDate", value="2015-10-31")

  def test_add_property_already_exists(self):
    self.fp.add_fileset_property(uid=1046, fileset=self.fs,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    with self.assertRaises(FPLPropertyExists):
      self.fp.add_fileset_property(uid=1046, fileset=self.fs,
                                   name="TestDate", value="2015-10-29")
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})

  def test_update_property(self):
    self.fp.add_fileset_property(uid=1046, fileset=self.fs,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    self.fp.add_fileset_property(uid=1046, fileset=self.fs,
                                 name="TestDate", value="2015-10-29",
                                 update=True)
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-29"})

  def test_update_property_permission_denied(self):
    self.fp.add_fileset_property(uid=1046, fileset=self.fs,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    with self.assertRaises(FPLPermissionDenied):
      self.fp.add_fileset_property(uid=1045, fileset=self.fs,
                                   name="TestDate", value="2015-10-29",
                                   update=True)

  def test_add_same_property_name_with_different_values_to_different_filesets(self):
    fs = self.fp.add_new_fileset(name="test-2",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    self.fp.add_fileset_property(uid=1046, fileset=self.fs,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.fs.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    self.fp.add_fileset_property(uid=1046, fileset=fs,
                                 name="TestDate", value="2015-10-29")
    self.assertEqual(fs.properties(self.fp.session), {"TestDate":"2015-10-29"})
    pas = self.fp.session.query(PropAssoc).all()
    self.assertEqual(len(pas), 2)
    props = self.fp.session.query(Property).all()
    self.assertEqual(len(props), 2)
    self.assertEqual(props[0].name, "TestDate")
    self.assertEqual(props[0].value, "2015-10-31")
    self.assertEqual(props[1].name, "TestDate")
    self.assertEqual(props[1].value, "2015-10-29")


class TestBinFileTags(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    self.fs = fs
    filename = "%s/data/example_file.txt" % (mydir)
    self.bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.aux = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")

  def tearDown(self):
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_create_new_binfile_tag(self):
    self.fp.tag_binfile(uid=1046, binfile=self.bf, tag="RC1")
    self.assertEqual(self.bf.tags(self.fp.session), ["RC1"])

  def test_create_new_binfile_tag_no_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      self.fp.tag_binfile(uid=1045, binfile=self.bf, tag="RC1")

  def test_create_reapply_same_tag_binfile(self):
    self.fp.tag_binfile(uid=1046, binfile=self.bf, tag="RC1")
    self.fp.tag_binfile(uid=1046, binfile=self.bf, tag="RC1")
    self.assertEqual(self.bf.tags(self.fp.session), ["RC1"])

  def test_add_multiple_tags_to_binfile(self):
    some_tags = ["RC1","RC2","RC3"]
    for t in some_tags:
      self.fp.tag_binfile(uid=1046, binfile=self.bf, tag=t)
    self.assertEqual(sorted(self.bf.tags(self.fp.session)), some_tags)

  def test_add_same_tag_to_multiple_binfiles(self):
    tag = "RC1"
    self.fp.tag_binfile(uid=1046, binfile=self.bf, tag=tag)
    self.fp.tag_binfile(uid=1046, binfile=self.aux, tag=tag)
    tags = self.fp.session.query(Tag).all()
    self.assertEqual(len(tags), 1)


class TestBinFileProperty(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)
    fp = Fruitpile(self.store_path)
    fp.init(uid=1046, username="db")
    fp.open()
    self.fp = fp
    fs = self.fp.add_new_fileset(name="test-1",
                                 version="1",
                                 revision="123",
                                 uid=1046)
    self.fs = fs
    filename = "%s/data/example_file.txt" % (mydir)
    self.bf = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="requirements.txt",
        path="deploy",
        primary=True,
        source="buildbot")
    self.aux = self.fp.add_file(
        uid=1046,
        source_file=filename,
        fileset_id=fs.id,
        name="coverage-report.txt",
        path="deploy",
        primary=False,
        source="buildbot")

  def tearDown(self):
    self.fp.close()
    self.fp = None
    clear_tree(self.store_path)

  def test_add_new_binfile_property(self):
    self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})

  def test_add_new_binfile_property_no_permission(self):
    with self.assertRaises(FPLPermissionDenied):
      self.fp.add_binfile_property(uid=1045, binfile=self.bf,
                                   name="TestDate", value="2015-10-31")

  def test_add_binfile_property_already_exists(self):
    self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    with self.assertRaises(FPLPropertyExists):
      self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                   name="TestDate", value="2015-10-29")
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})

  def test_update_binfile_property(self):
    self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                 name="TestDate", value="2015-10-29",
                                 update=True)
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-29"})

  def test_update_binfile_property_permission_denied(self):
    self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    with self.assertRaises(FPLPermissionDenied):
      self.fp.add_binfile_property(uid=1045, binfile=self.bf,
                                   name="TestDate", value="2015-10-29",
                                   update=True)

  def test_add_same_property_name_to_different_files(self):
    self.fp.add_binfile_property(uid=1046, binfile=self.bf,
                                 name="TestDate", value="2015-10-31")
    self.assertEqual(self.bf.properties(self.fp.session),
                     {"TestDate":"2015-10-31"})
    self.fp.add_binfile_property(uid=1046, binfile=self.aux,
                                 name="TestDate", value="2015-10-29")
    self.assertEqual(self.aux.properties(self.fp.session),
                     {"TestDate":"2015-10-29"})
    pas = self.fp.session.query(BinFileProp).all()
    self.assertEqual(len(pas), 2)
    props = self.fp.session.query(Property).all()
    self.assertEqual(len(props), 2)
    self.assertEqual(props[0].name, "TestDate")
    self.assertEqual(props[0].value, "2015-10-31")
    self.assertEqual(props[1].name, "TestDate")
    self.assertEqual(props[1].value, "2015-10-29")


if __name__ == "__main__":
  unittest.main()

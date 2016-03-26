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
import io
import os
import sys
import sqlite3

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from fruitpile import Fruitpile, FPLExists, FPLConfiguration, FPLRepoInUse, FPLFileSetExists
from fruitpile.db.schema import *

# Destroys the entire tree of data (python equivalent of rm -rf)
def clear_tree(path):
  if os.path.exists(path) and os.path.isdir(path):
    for root, dirs, files in os.walk(path):
      for f in files:
        os.remove(os.path.join(root,f))
    os.removedirs(path)

class TestFruitpileInitOperations(unittest.TestCase):

  def setUp(self):
    self.store_path = "/tmp/store%d" % (os.getpid())
    clear_tree(self.store_path)

  def tearDown(self):
    clear_tree(self.store_path)

  def test_init_a_new_repo(self):
    fp = Fruitpile(self.store_path)
    fp.init()
    self.assertTrue(os.path.exists(self.store_path))
    dbpath = os.path.join(self.store_path, "fpl.db")
    self.assertTrue(os.path.exists(dbpath))
    conn = sqlite3.connect(dbpath)
    self.assertNotEquals(conn, None)
    curs = conn.execute("SELECT * FROM SQLITE_MASTER")
    rows = curs.fetchall()
    expected_tables = ["states","repos","filesets","binfiles"]
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
      fp.init()
    os.remove(self.store_path)

  def test_init_with_an_exist_repo_in_place(self):
    with self.assertRaises(FPLExists):
      fp1 = Fruitpile(self.store_path)
      fp1.init()
      fp2 = Fruitpile(self.store_path)
      fp2.init()


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
    fp.init()
    fp.open()
    self.assertNotEquals(fp.session, None)
    self.assertEquals(fp.repo.__class__.__name__, "FileManager")

  def test_reopen_existing_repo(self):
    fp1 = Fruitpile(self.store_path)
    fp1.init()
    fp1.open()
    fp2 = Fruitpile(self.store_path)
    with self.assertRaises(FPLRepoInUse):
      fp2.open()
      self.assertEquals(fp1, fp2)

  def test_open_on_unreadable_permissions(self):
    fp = Fruitpile(self.store_path)
    fp.init()
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
    fp.init()
    fp.open()
    self.fp = fp

  def tearDown(self):
    self.fp.close()
    clear_tree(self.store_path)

  def test_list_filesets(self):
    filesets = self.fp.list_filesets()
    self.assertEquals(filesets, [])

  def test_add_new_fileset(self):
    fileset = self.fp.add_new_fileset(name="test-1")
    self.assertEquals(str(fileset), "<FileSet(test-1 in default)>")
    filesets = self.fp.list_filesets()
    self.assertEquals(len(filesets), 1)
    self.assertEquals(filesets[0], fileset)

  def test_add_duplicate_fileset(self):
    fs1 = self.fp.add_new_fileset(name="test-1")
    self.assertEquals(str(fs1), "<FileSet(test-1 in default)>")
    with self.assertRaises(FPLFileSetExists):
      fs2 = self.fp.add_new_fileset(name="test-1")

  def test_add_multiple_filesets(self):
    fss1 = []
    for i in range(10):
      fss1.append(self.fp.add_new_fileset(name="test-%d" % (i)))
    fss2 = self.fp.list_filesets()
    self.assertEquals(fss1, fss2)

if __name__ == "__main__":
  unittest.main()

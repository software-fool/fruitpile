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

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from fruitpile import Fruitpile, FPLExists, FPLConfiguration, FPLRepoInUse, FPLFileSetExists, FPLBinFileExists, FPLSourceFileNotFound, FPLSourceFilePermissionDenied
from fruitpile.fp_perms import *
from fruitpile.db.schema import *

def setUpDatabase():
  engine = create_engine('sqlite:///:memory:')
  Base.metadata.create_all(bind=engine)
  Session = sessionmaker(bind=engine)
  session = Session()
  return engine, session

class TestAllPermissions(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def build_permissions_table(self):
    for name,desc in [("ADD_FILESET","Grant permission to add a fileset"),
                      ("ADD_FILES","Grant permission to add a file"),
                      ("LIST_FILESETS","Grant permission to list all filesets"),
                      ("LIST_FILES","Grant permission to list all files")]:
      perm = Permission(name=name, desc=desc)
      self.session.add(perm)
    self.session.commit()
    all_perms = self.session.query(Permission).all()
    d = {}
    for perm in all_perms:
      d[perm.name] = perm.id
    perms = AllPermissions(d)
    self.assertEquals(perms.ADD_FILESET, 1)
    self.assertEquals(perms.ADD_FILES, 2)
    self.assertEquals(perms.LIST_FILESETS, 3)
    self.assertEquals(perms.LIST_FILES, 4)
    return perms

  def test_build_all_permissions_object(self):
    self.build_permissions_table()

  def test_all_permissions_access_unknown_permission(self):
    perms = self.build_permissions_table()
    with self.assertRaises(AttributeError):
      _ = perms.ARCHIVE_FILESET

if __name__ == "__main__":
  unittest.main()

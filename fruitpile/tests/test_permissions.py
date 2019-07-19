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
from fruitpile.fp_constants import Capability

def setUpDatabase():
  engine = create_engine('sqlite:///:memory:')
  Base.metadata.create_all(bind=engine)
  Session = sessionmaker(bind=engine)
  session = Session()
  return engine, session

def build_permissions_table(obj):
  for name,description in [("ADD_FILESET","Grant permission to add a fileset"),
                    ("ADD_FILES","Grant permission to add a file"),
                    ("LIST_FILESETS","Grant permission to list all filesets"),
                    ("LIST_FILES","Grant permission to list all files")]:
    perm = Permission(name=name, description=description)
    obj.session.add(perm)
  obj.session.commit()
  obj.assertEqual(Capability.ADD_FILESET, 1)
  obj.assertEqual(Capability.ADD_FILE, 2)
  obj.assertEqual(Capability.LIST_FILESETS, 3)
  obj.assertEqual(Capability.LIST_FILES, 4)


class TestCapabilities(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_build_all_permissions_object(self):
    build_permissions_table(self)

  def test_all_permissions_access_unknown_permission(self):
    build_permissions_table(self)
    with self.assertRaises(AttributeError):
      _ = Capability.ARCHIVE_FILESET


class TestPermissionManager(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_permission_manager(self):
    build_permissions_table(self)
    perm_man = PermissionManager(self.session)
    self.assertEqual(Capability.ADD_FILESET, 1)
    self.assertEqual(Capability.ADD_FILE, 2)
    self.assertEqual(Capability.LIST_FILESETS, 3)
    self.assertEqual(Capability.LIST_FILES, 4)

  def test_get_all_permissions_from_permission_manager(self):
    build_permissions_table(self)
    perm_man = PermissionManager(self.session)
    self.assertEqual(set(Capability.keys()),
                      set(["ADD_FILESET","ADD_FILE",
                           "LIST_FILESETS","LIST_FILES",
                           "APPROVE_ARTIFACT","ARTIFACT_TESTED",
                           "WITHDRAW_ARTIFACT","BEGIN_TESTING",
                           "RELEASE_ARTIFACT","GET_FILES",
                           "TAG_FILESET","ADD_FILESET_PROPERTY",
                           "UPDATE_FILESET_PROPERTY","TAG_BINFILE",
                           "ADD_BINFILE_PROPERTY","UPDATE_BINFILE_PROPERTY"]))

  def test_check_permission_with_uid_no_permissions(self):
    build_permissions_table(self)
    self.session.add(User(uid=1046,name="db"))
    self.session.commit()
    perm_man = PermissionManager(self.session)
    perms = self.session.query(UserPermission).filter(UserPermission.user_id==1046).all()
    perm_ids = [perm.id for perm in perms]
    self.assertEqual(perm_ids, [])
    with self.assertRaises(FPLPermissionDenied):
      perm_man.check_permission(Capability.LIST_FILESETS, set(perm_ids))

  def test_check_permission_with_uid_with_some_permissions(self):
    build_permissions_table(self)
    self.session.add(User(uid=1046,name="db"))
    self.session.add(UserPermission(user_id=1046,perm_id=2))
    self.session.add(UserPermission(user_id=1046,perm_id=3))
    self.session.commit()
    perm_man = PermissionManager(self.session)
    perm_man.check_permission(1046, Capability.LIST_FILESETS)
    self.assertTrue(True)
    with self.assertRaises(FPLPermissionDenied):
      perm_man.check_permission(1046, Capability.ADD_FILESET)



if __name__ == "__main__":
  unittest.main()

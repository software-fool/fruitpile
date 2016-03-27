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

def build_permissions_table(obj):
  for name,desc in [("ADD_FILESET","Grant permission to add a fileset"),
                    ("ADD_FILES","Grant permission to add a file"),
                    ("LIST_FILESETS","Grant permission to list all filesets"),
                    ("LIST_FILES","Grant permission to list all files")]:
    perm = Permission(name=name, desc=desc)
    obj.session.add(perm)
  obj.session.commit()
  AllPermissions.create(obj.session)
  obj.assertEquals(AllPermissions.ADD_FILESET, 1)
  obj.assertEquals(AllPermissions.ADD_FILES, 2)
  obj.assertEquals(AllPermissions.LIST_FILESETS, 3)
  obj.assertEquals(AllPermissions.LIST_FILES, 4)


class TestAllPermissions(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_build_all_permissions_object(self):
    build_permissions_table(self)

  def test_all_permissions_access_unknown_permission(self):
    build_permissions_table(self)
    with self.assertRaises(AttributeError):
      _ = AllPermissions.ARCHIVE_FILESET


class TestPermissionManager(unittest.TestCase):

  def setUp(self):
    self.engine, self.session = setUpDatabase()

  def tearDown(self):
    self.session.close()

  def test_create_permission_manager(self):
    build_permissions_table(self)
    perm_man = PermissionManager(self.session)
    self.assertEquals(AllPermissions.ADD_FILESET, 1)
    self.assertEquals(AllPermissions.ADD_FILES, 2)
    self.assertEquals(AllPermissions.LIST_FILESETS, 3)
    self.assertEquals(AllPermissions.LIST_FILES, 4)

  def test_get_all_permissions_from_permission_manager(self):
    build_permissions_table(self)
    perm_man = PermissionManager(self.session)
    self.assertEquals(set(AllPermissions.keys()),
                      set(["ADD_FILESET","ADD_FILES",
                           "LIST_FILESETS","LIST_FILES"]))

  def test_check_permission_with_uid_no_permissions(self):
    build_permissions_table(self)
    self.session.add(User(uid=1046,name="db"))
    self.session.commit()
    perm_man = PermissionManager(self.session)
    perms = self.session.query(UserPermission).filter(UserPermission.user_id==1046).all()
    perm_ids = [perm.id for perm in perms]
    self.assertEquals(perm_ids, [])
    with self.assertRaises(FPLPermissionDenied):
      perm_man.check_permission(AllPermissions.LIST_FILESETS, set(perm_ids))

  def test_check_permission_with_uid_with_some_permissions(self):
    build_permissions_table(self)
    self.session.add(User(uid=1046,name="db"))
    self.session.add(UserPermission(user_id=1046,perm_id=2))
    self.session.add(UserPermission(user_id=1046,perm_id=3))
    self.session.commit()
    perm_man = PermissionManager(self.session)
    user_perms = self.session.query(UserPermission).filter(UserPermission.user_id == 1046).all()
    perm_ids = [user_perm.perm_id for user_perm in user_perms]
    perm_man.check_permission(AllPermissions.LIST_FILESETS, set(perm_ids))
    self.assertTrue(True)
    with self.assertRaises(FPLPermissionDenied):
      perm_man.check_permission(AllPermissions.ADD_FILESET, set(perm_ids))



if __name__ == "__main__":
  unittest.main()

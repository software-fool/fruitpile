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

class Capability(object):
  __PERMS__ = {}

  def __init__(self, val, name, desc):
    self._val = val
    self._name = name
    self._desc = desc
    Capability.__PERMS__[name] = self
    Capability._add_item(name, val)

  @property
  def description(self):
    return self._desc

  @property
  def name(self):
    return self._name

  @property
  def ident(self):
    return self._val

  @classmethod
  def _add_item(cls, name, val):
    setattr(cls, name, val)

  @staticmethod
  def keys():
    # Return a copy to stop something accidentally (or intentionally)
    # fiddling with the permissions list
    return Capability.__PERMS__.keys()

  @staticmethod
  def get(name):
    return Capability.__PERMS__[name]

_CAPABILITIES = [
    (1, "ADD_FILESET", "Permission to create a new fileset"),
    (2, "ADD_FILE", "Permission to upload a new file to a fileset"),
    (3, "LIST_FILESETS", "Permission to list all the filesets"),
    (4, "LIST_FILES", "Permission to list all the files across all filesets"),
    (5, "BEGIN_TESTING", "Permission to transit an item to the testing state"),
    (6, "WITHDRAW_ARTIFACT", "Permission to withdraw and artifact"),
    (7, "ARTIFACT_TESTED", "Permission to mark testing as completed"),
    (8, "APPROVE_ARTIFACT", "Permission to mark artifact as approved"),
    (9, "RELEASE_ARTIFACT", "Permission to release artifact"),
    (10, "GET_FILES", "Permission to retrieve artifacts"),
    (11, "TAG_FILESET", "Permission to add tags to filesets")]

for perm_id, perm_name, perm_desc in _CAPABILITIES:
  Capability(perm_id, perm_name, perm_desc)

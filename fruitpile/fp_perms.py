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

from .db.schema import *
from .fp_exc import FPLPermissionDenied

class AllPermissions(object):
  d = {}

  @staticmethod
  def create(session):
    perms = session.query(Permission).all()
    for perm in perms:
      AllPermissions.add_item(perm.name, perm.id)

  @classmethod
  def add_item(cls, name, value):
    if not AllPermissions.d.has_key(name):
      AllPermissions.d[name] = value
      setattr(cls, name, value)

  @staticmethod
  def keys():
    return AllPermissions.d.keys()

class PermissionManager(object):

  def __init__(self, session):
    AllPermissions.create(session)

  def get_all_permissions(self):
    return self.perms.keys()

  def check_permission(self, permission, user_perms):
    # Sanity check that we got a set of user permissions through
    assert type(user_perms) == type(set())
    if permission not in user_perms:
      # The user doesn't have suitable permission to do this operation.
      # Raising an exception simplifies processing elsewhere since we
      # can allow the exception to propogate up through the stack until
      # we need to report it to the user.
      raise FPLPermissionDenied("user does not have permission %s" % (permission))

  

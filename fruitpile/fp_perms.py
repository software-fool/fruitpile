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

class AllPermissions(dict):
  def __getattr__(self, name):
    if name in self:
      return self[name]
    raise AttributeError

class PermissionManager(object):

  def __init__(self, session):
    perms = session.query(Permission).all()
    d = {}
    for perm in perms:
      d[perm.name] = perm.id
    self.perms = AllPermissions(d)

  def get_all_permissions(self):
    return self.perms.keys()

  def check_permission(self, permission, user_perms):
    # Sanity check that we got a set of user permissions through
    assert type(user_perms) == type(set())
    if permission not in user_perms:
      raise FPLPermissionDenied("user does not have permission %s" % (permission))
    
  def get_perm_id(self, name):
    return self.perms[name]

  

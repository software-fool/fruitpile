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
from .fp_constants import Capability


class PermissionManager(object):

  def __init__(self, session):
    self.session = session

  def check_permission(self, uid, permission):
    perms = self.session.query(UserPermission).filter(UserPermission.user_id == uid).all()
    user_perms = set([perm.perm_id for perm in perms])
    # Sanity check that we got a set of user permissions through
    assert type(user_perms) == type(set())
    if permission not in user_perms:
      # The user doesn't have suitable permission to do this operation.
      # Raising an exception simplifies processing elsewhere since we
      # can allow the exception to propogate up through the stack until
      # we need to report it to the user.
      raise FPLPermissionDenied("user does not have permission %s" % (permission))

  

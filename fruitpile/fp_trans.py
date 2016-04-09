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
from .fp_constants import Capability
from .fp_exc import FPLCannotTransitionState, FPLInvalidStateTransition, FPLUnknownState, FPLPermissionDenied

def check_auxilliary_file_in_fileset(uid, perm_man, old_state, new_state, d):
  bf = d["bf"]
  target_names = set([dt.data[5:] for dt in d["data"]])
  fs_id = bf.fileset_id
  # perm manager carries the session, so we'll borrow it here
  bfs = perm_man.session.query(BinFile).filter(BinFile.fileset_id==fs_id).filter(BinFile.primary==False).all()
  for bf0 in bfs:
    for t0 in target_names:
      if bf0.name.endswith(t0):
        target_names.discard(bf0.name)
        break
  if target_names != set([]):
    raise FPLCannotTransitionState("Transition disallowed by check auxilliary file in fileset")
  return


  
  

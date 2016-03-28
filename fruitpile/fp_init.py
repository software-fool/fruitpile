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
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from .fp_exc import *
from .fp_constants import *

def init_data(session, uid, username, path):
  rp = Repo(name="default", path=path, repo_type="FileManager")
  session.add(rp)
  state_dict = {}
  for sname in ["untested","testing","tested","approved","released","withdrawn"]:
    state = State(name=sname)
    session.add(state)
  session.commit()
  for s in session.query(State).all():
    state_dict[s.name] = s
  for transition in [("untested","testing",None,Capability.BEGIN_TESTING),
                     ("untested","withdrawn",None,Capability.WITHDRAW_ARTIFACT),
                     ("testing","tested",None,Capability.ARTIFACT_TESTED),
                     ("testing","withdrawn",None,Capability.WITHDRAW_ARTIFACT),
                     ("tested","approved",None,Capability.APPROVE_ARTIFACT),
                     ("tested","withdrawn",None,Capability.WITHDRAW_ARTIFACT),
                     ("approved","released",None,Capability.RELEASE_ARTIFACT),
                     ("approved","withdrawn",None,Capability.WITHDRAW_ARTIFACT)]:
    start_id = state_dict[transition[0]].id
    end_id= state_dict[transition[1]].id
    session.add(Transition(start_id=start_id,
                           end_id=end_id,
                           transfn_id=transition[2],
                           perm_id=transition[3]))
  session.add(User(uid=uid, name=username))
  for name in Capability.keys():
    cap = Capability.get(name)
    session.add(Permission(id=cap.ident, name=cap.name, desc=cap.description))
    session.add(UserPermission(user_id=uid, perm_id=cap.ident)) 
  session.commit()


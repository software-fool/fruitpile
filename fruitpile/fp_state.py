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
from collections import namedtuple
import fp_trans
import inspect

StateTransition = namedtuple("StateTransition", ["new_state","capability","transfn","data"])

TRANS_FN = {}
for name, fn in inspect.getmembers(fp_trans, inspect.isfunction):
  if name[:6] == "check_":
    TRANS_FN[name] = fn

class StateMachine(object):
  def __init__(self):
    self._state = None
    self._state_dict = {}
    self._transitions = {}

  @property
  def state(self):
    return self._state

  @property
  def state_id(self):
    return self._state_dict[self._state].id

  def is_valid_state(self, state):
    return state in self._state_dict

  def transit(self, uid, perm_man, old_state, new_state, external_data):
    try:
      valid_trans = self._transitions[old_state]
    except KeyError:
      raise FPLUnknownState("An unknown state: %s" % (self._state))
    try:
      trans_control = valid_trans[new_state]
    except KeyError:
      raise FPLInvalidStateTransition("Invalid state transition from %s to %s" % (self._state, new_state))
    perm_man.check_permission(uid, trans_control.capability)
    try:
      if trans_control.transfn is not None:
        d = {"data":trans_control.data}
        d.update(external_data)
        trans_control.transfn(uid, perm_man, old_state, new_state, d)
    except Exception as exc:
      if isinstance(exc, FPLPermissionDenied):
        raise exc
      raise FPLCannotTransitionState("Transit state function for %s->%s rejected state transition" % (self._state, new_state), exc)
    self._state = new_state
    return new_state

  @staticmethod
  def create_state_machine(session):
    states = session.query(State).all()
    state_names = [state.name for state in states]
    sm = StateMachine()
    for nm in state_names:
      sm._transitions[nm] = {}
    for s in states:
      sm._state_dict[s.name] = s
    start_states = state_names[:]
    transitions = session.query(Transition).all()
    for t in transitions:
      # For each transition add the state transition to the
      # transition map for this start state
      if t.transfn_id is not None:
        trnsfn = TRANS_FN[t.transfn.transfn]
      else:
        trnsfn = lambda a,b,c,d,e: None
      sm._transitions[t.start.name][t.end.name] = \
                StateTransition(new_state=t.end.name,
                                capability=t.perm_id,
                                transfn=trnsfn,
                                data=t.transfuncdata)
      try:
        del start_states[start_states.index(t.end.name)]
      except ValueError:
        # state was already removed from the list
        pass
    assert len(start_states) == 1
    # We currently only support the notion of a single start state
    # which is identified by a state which you cannot arrive at.
    # This will break if you have a state such as "open" which can
    # be returned to (hence the assert above).  In this case the
    # simple solution is to create a "new" state which transitions
    # to "open" and have "open" being the state you can return to,
    # until the system is configured to handle this case.  In all
    # circumstances there must be at least one starting state.
    # While multiple start states do make sense in some scenarios
    # this system doesn't appear to need such functionality.
    sm._state = session.query(State).filter(State.name == start_states[0]).first().name
    return sm

  

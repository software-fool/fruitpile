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

from fruitpile import (
  FPLInvalidStateTransition,
  FPLPermissionDenied,
  FPLUnknownState,
  FPLCannotTransitionState,
  FPLSourceFilePermissionDenied)
from fruitpile.fp_state import StateMachine, StateTransition


class DummyPermManager(object):
  def __init__(self, allow):
    self.allow = allow

  def check_permission(self, uid, capability):
    if not self.allow:
      raise FPLPermissionDenied


def transition_function(uid, pm, old_state, new_state, d):
  obj = d["obj"]
  obj.called_back_uid = uid
  obj.called_back_pm = pm
  obj.called_back_old_state = old_state
  obj.called_back_new_state = new_state
  obj.called_back_data = d["data"]
  if obj.refuse_callback:
    raise obj.refuse_callback


class TestStateMachine(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def build_simple_state_machine(self, fn):
    sm = StateMachine()
    sm._state = "start"
    sm._transitions["start"] = {
      "end": StateTransition(new_state="end",
                             capability="OMNIPOTENCE",
                             transfn=fn,data=["name=This is some data"])}
    return sm

  def test_empty_state_machine(self):
    sm = StateMachine()
    self.assertEqual(sm.state, None)
    with self.assertRaises(FPLUnknownState):
      sm.transit(1000, None, "start", "new_state", {"obj":self})

  def test_simple_state_machine(self):
    sm = self.build_simple_state_machine(lambda a,b,c,d,e: None)
    self.assertEqual(sm.state, "start")
    pm = DummyPermManager(True)
    new_state = sm.transit(100, pm, "start", "end", {"obj":self})
    self.assertEqual(new_state, "end")

  def test_simple_state_machine_permission_denied_transition(self):
    sm = self.build_simple_state_machine(lambda a,b,c,d,e: None)
    self.assertEqual(sm.state, "start")
    pm = DummyPermManager(False)
    with self.assertRaises(FPLPermissionDenied):
      sm.transit(100, pm, "start", "end", {"obj":self})

  def test_simple_state_machine_with_callback(self):
    sm = self.build_simple_state_machine(transition_function)
    self.assertEqual(sm.state, "start")
    pm = DummyPermManager(True)
    self.refuse_callback = None
    new_state = sm.transit(100, pm, "start", "end", {"obj":self})
    self.assertEqual(new_state, "end")
    self.assertEqual(self.called_back_uid, 100)
    self.assertEqual(self.called_back_pm, pm)
    self.assertEqual(self.called_back_old_state, "start")
    self.assertEqual(self.called_back_new_state, "end")
    self.assertEqual(self.called_back_data, ["name=This is some data"])

  def test_simple_state_machine_with_callback_disallowed_general_error(self):
    sm = self.build_simple_state_machine(transition_function)
    self.assertEqual(sm.state, "start")
    pm = DummyPermManager(True)
    self.refuse_callback = KeyError("TEST")
    new_state = None
    with self.assertRaises(FPLCannotTransitionState):
      new_state = sm.transit(100, pm, "start", "end", {"obj":self})
    self.assertEqual(new_state, None)
    self.assertEqual(self.called_back_uid, 100)
    self.assertEqual(self.called_back_pm, pm)
    self.assertEqual(self.called_back_old_state, "start")
    self.assertEqual(self.called_back_new_state, "end")
    self.assertEqual(self.called_back_data, ["name=This is some data"])

  def test_simple_state_machine_with_callback_disallowed_source_file_permission_denied(self):
    sm = self.build_simple_state_machine(transition_function)
    self.assertEqual(sm.state, "start")
    pm = DummyPermManager(True)
    self.refuse_callback = FPLSourceFilePermissionDenied("TEST")
    new_state = None
    with self.assertRaises(FPLCannotTransitionState) as exc:
      new_state = sm.transit(100, pm, "start", "end", {"obj":self})
    self.assertTrue(isinstance(exc.exception.exc,
                               FPLSourceFilePermissionDenied))
    self.assertEqual(new_state, None)
    self.assertEqual(self.called_back_uid, 100)
    self.assertEqual(self.called_back_pm, pm)
    self.assertEqual(self.called_back_old_state, "start")
    self.assertEqual(self.called_back_new_state, "end")
    self.assertEqual(self.called_back_data, ["name=This is some data"])

  def test_simple_state_machine_with_callback_disallowed_permission_denied_passthrough(self):
    sm = self.build_simple_state_machine(transition_function)
    self.assertEqual(sm.state, "start")
    pm = DummyPermManager(True)
    self.refuse_callback = FPLPermissionDenied("TEST")
    new_state = None
    with self.assertRaises(FPLPermissionDenied):
      new_state = sm.transit(100, pm, "start", "end", {"obj":self})
    self.assertEqual(new_state, None)
    self.assertEqual(self.called_back_uid, 100)
    self.assertEqual(self.called_back_pm, pm)
    self.assertEqual(self.called_back_old_state, "start")
    self.assertEqual(self.called_back_new_state, "end")
    self.assertEqual(self.called_back_data, ["name=This is some data"])


if __name__ == "__main__":
  unittest.main()

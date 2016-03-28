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

class FruitpileError(Exception):
  pass

class FPLConfiguration(FruitpileError):
  pass

class FPLExists(FruitpileError):
  pass

class FPLRepoInUse(FruitpileError):
  pass

class FPLFileSetExists(FruitpileError):
  pass

class FPLBinFileExists(FruitpileError):
  pass

class FPLSourceFileNotFound(FruitpileError):
  pass

class FPLSourceFilePermissionDenied(FruitpileError):
  pass

class FPLPermissionDenied(FruitpileError):
  pass

class FPLInvalidStateTransition(FruitpileError):
  pass

class FPLUnknownState(FruitpileError):
  pass

class FPLCannotTransitionState(FruitpileError):
  def __init__(self, msg, exc):
    self.msg = msg
    self.exc = exc

class FPLInvalidState(FruitpileError):
  pass

class FPLBinFileNotExists(FruitpileError):
  pass

class FPLInvalidTargetForStateChange(FruitpileError):
  pass

class FPLFileExists(FruitpileError):
  pass

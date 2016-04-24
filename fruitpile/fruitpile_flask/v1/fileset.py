# -*- mode: python -*-
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
from flask_restful import reqparse, fields, marshal_with
from ..api_utils import FruitpileResource
from ...fp_ops import Fruitpile
import os


class FruitpileFileset(FruitpileResource):
  def __init__(self, **kwargs):
    self.fp = Fruitpile(kwargs["fppath"])
    self.fp.open()
    super(FruitpileFilesets,self).__init__()

  def get(self, id):
    pass

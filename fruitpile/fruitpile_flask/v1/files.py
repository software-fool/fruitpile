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
from flask_restful import reqparse
from ..api_utils import FruitpileResource
from ...fp_ops import Fruitpile
import os

class FruitpileFiles(FruitpileResource):
  def __init__(self, **kwargs):
    self.fp = Fruitpile(kwargs["fppath"])
    self.fp.open()
    super(FruitpileFiles,self).__init__()

  def get(self):
    parser = reqparse.RequestParser()
    parser.add_argument('count', type=int, help='number of files to return in one block')
    parser.add_argument('start_at', type=int, help='position to start at')
    args = parser.parse_args()
    bfs = self.fp.list_files(uid=os.getuid(), count=args["count"], start_at=args["start_at"])
    bfss = [{"fileset_id":bf.fileset_id,
             "fileset": bf.fileset.name,
             "name":bf.name,
             "primary":bf.primary,
             "state": bf.state.name,
             "create_date":str(bf.create_date),
             "update_date":str(bf.update_date),
             "source": bf.source} for bf in bfs]
    return bfss

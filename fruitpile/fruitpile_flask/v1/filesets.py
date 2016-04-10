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
from flask_restful import Resource, reqparse
from ...fp_ops import Fruitpile
import os

class FruitpileFilesets(Resource):
  def __init__(self, **kwargs):
    self.fp = Fruitpile(kwargs["fppath"])
    self.fp.open()

  def get(self):
    parser = reqparse.RequestParser()
    parser.add_argument('count', type=int, help='number of files to return in one block')
    parser.add_argument('start_at', type=int, help='position to start at')
    args = parser.parse_args()
    fss = self.fp.list_filesets(uid=os.getuid(), count=args["count"], start_at=args["start_at"])
    fsss = [{"fileset_id":fs.id,
             "name":fs.name,
             "version":fs.version,
             "revision":fs.revision,
             "repo":fs.repo.name} for fs in fss]
    return fsss

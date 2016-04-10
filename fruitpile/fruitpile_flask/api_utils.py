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
from flask import jsonify, abort, make_response
from flask_restful import Resource
from flask.ext.httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
  if username == "fruitpile":
    return "Fru1tpi13R"
  return None

@auth.error_handler
def unauthorized():
  # return 403 instead of 401 to prevent browsers from displaying the
  # default auth dialog
  return make_response(jsonify({"message":"Unauthorized access"}), 403)


# Base class for all Fruitpile REST endpoints to allow things like
# authentication to be done reliably across the API.
class FruitpileResource(Resource):
  decorators = [auth.login_required]

  def __init__(self):
    super(FruitpileResource, self).__init__()

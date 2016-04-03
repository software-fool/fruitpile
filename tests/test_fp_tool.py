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
from __future__ import unicode_literals
import unittest
import io
import os
import sys
import sqlite3
import pprint
from datetime import datetime, timedelta
from argparse import Namespace
from io import StringIO

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
parentdir = os.path.dirname(mydir)
sys.path.extend([parentdir])

from fruitpile.fp_tool import *

from test_fruitpile import clear_tree

class TestFPToolInit(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())

  def tearDown(self):
    clear_tree(self.path)

  def test_init_a_repo(self):
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    self.assertTrue(os.path.exists(self.path))
    conn = sqlite3.connect(os.path.join(self.path,"fpl.db"))
    curs = conn.execute("SELECT * FROM SQLITE_MASTER")
    rows = curs.fetchall()
    self.assertEquals(len(rows), 20)
    curs = conn.execute("select * from repos")
    rows = curs.fetchall()
    self.assertEquals(len(rows), 1)
    self.assertEquals(rows[0][1], "default")

class TestFPToolFileSetOps(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)

  def tearDown(self):
    clear_tree(self.path)

  def check_output(self, ns, expected):
    fob = StringIO()
    fp_list_filesets(ns, fob=fob)
    op = fob.getvalue()
    words = op.split()
    self.assertEquals(words, expected)

  def test_list_filesets(self):
    ns = Namespace(path=self.path)
    self.check_output(ns, [])

  def test_add_fileset(self):
    ns = Namespace(path=self.path, version="3.1", revision="1234", name="test-1")
    fp_add_filesets(ns)
    ns = Namespace(path=self.path)
    self.check_output(ns, ["default","1","3.1","1234","test-1"])

  def test_add_multiple_filesets(self):
    words = []
    for i in range(3):
      vers = "3.%d" % (i)
      revn = "123%d" % (i)
      name = "test-%d" % (i)
      ns = Namespace(path=self.path, version=vers, revision=revn, name=name)
      fp_add_filesets(ns)
      words.extend(["default","%d" % (i+1), vers, revn, name])
    ns = Namespace(path=self.path)
    self.check_output(ns, words)

  def test_add_repeated_fileset(self):
    ns = Namespace(path=self.path, version="3.1", revision="1234", name="test-1")
    fob = StringIO()
    fp_add_filesets(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    fob = StringIO()
    fp_add_filesets(ns, fob=fob)
    output = fob.getvalue()
    words = output.split()
    self.assertEquals(words, ["Fileset","'test-1'","already","exists"])

class TestFPToolFileOps(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    ns = Namespace(path=self.path, version="3.1", revision="1", name="build-1")
    fob = StringIO()
    fp_add_filesets(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, version="3.1", revision="2", name="build-2")
    fob = StringIO()
    fp_add_filesets(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, version="3.1", revision="3", name="build-3")
    fob = StringIO()
    fp_add_filesets(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")    

  def tearDown(self):
    clear_tree(self.path)

  def check_output(self, ns, expected):
    fob = StringIO()
    fp_list_files(ns, fob=fob)
    op = fob.getvalue()
    words = op.split()
    self.assertEquals(words, expected)

  def test_list_all_files_when_none_added(self):
    ns = Namespace(path=self.path, long=False)
    self.check_output(ns, [])

  def test_add_single_file_in_repo(self):
    ns = Namespace(path=self.path, 
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="builds",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False)
    self.check_output(ns, ["1","1","untested","P", "builds/requirements.txt"])

  def test_add_file_to_non_existent_fileset(self):
    ns = Namespace(path=self.path, 
                   fileset="build-71",
                   name="requirements.txt",
                   repopath="builds",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    output = fob.getvalue()
    words = output.split()
    self.assertEquals(words, ["Failed","to","add","file,","fileset","'build-71'","not","found"])

  def test_add_file_to_different_filesets(self):
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="build-1",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-2",
                   name="requirements.txt",
                   repopath="build-2",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False)
    self.check_output(ns, ["1","1","untested","P","build-1/requirements.txt",
                           "2","2","untested","P","build-2/requirements.txt"])

  def test_add_file_long_list(self):
    tmp_path = "/tmp/sample_file%d.txt" % (os.getpid())
    tmp_fob = io.open(tmp_path, "wb")
    tmp_fob.write(b"This is some text")
    tmp_fob.close()
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="build-1",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=True)
    self.check_output(ns, ["1/1","build-1/requirements.txt","untested","cksum:","2263d8dd95ccfe1ad45d732c6eaaf59b3345e6647331605cb15aae52002dff75","--"])

  def test_add_two_files_two_filesets_long_list(self):
    tmp_path = "/tmp/sample_file%d.txt" % (os.getpid())
    tmp_fob = io.open(tmp_path, "wb")
    tmp_fob.write(b"This is some text")
    tmp_fob.close()
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="build-1",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-2",
                   name="requirements.txt",
                   repopath="build-2",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=True)
    self.check_output(ns, ["1/1","build-1/requirements.txt","untested","cksum:","2263d8dd95ccfe1ad45d732c6eaaf59b3345e6647331605cb15aae52002dff75","--",
                           "2/2","build-2/requirements.txt","untested","cksum:","2263d8dd95ccfe1ad45d732c6eaaf59b3345e6647331605cb15aae52002dff75","--"])

  def test_add_two_files_to_single_fileset_long_list(self):
    tmp_path = "/tmp/sample_file%d.txt" % (os.getpid())
    tmp_fob = io.open(tmp_path, "wb")
    tmp_fob.write(b"This is some text")
    tmp_fob.close()
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="build-1",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements1.txt",
                   repopath="build-1",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=True)
    self.check_output(ns, ["1/1","build-1/requirements.txt","untested","cksum:","2263d8dd95ccfe1ad45d732c6eaaf59b3345e6647331605cb15aae52002dff75","--",
                           "1/2","build-1/requirements1.txt","untested","cksum:","2263d8dd95ccfe1ad45d732c6eaaf59b3345e6647331605cb15aae52002dff75","--"])

  def test_add_single_auxilliary_file_in_repo(self):
    ns = Namespace(path=self.path, 
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="builds",
                   auxilliary=True,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, fob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False)
    self.check_output(ns, ["1","1","untested","A", "builds/requirements.txt"])



if __name__ == "__main__":
  unittest.main()
    
  
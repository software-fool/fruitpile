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

  def _check_repo(self):
    self.assertTrue(os.path.exists(self.path))
    conn = sqlite3.connect(os.path.join(self.path,"fpl.db"))
    curs = conn.execute("SELECT * FROM SQLITE_MASTER")
    rows = curs.fetchall()
    self.assertEquals(len(rows), 33)
    curs = conn.execute("select * from repos")
    rows = curs.fetchall()
    self.assertEquals(len(rows), 1)
    self.assertEquals(rows[0][1], "default")

  def test_init_a_repo(self):
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    self._check_repo()

  def test_init_a_repo_from_cli(self):
    fp_tool_main([self.path,"init"])
    self._check_repo()


class TestFPToolFileSetOps(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)

  def tearDown(self):
    clear_tree(self.path)

  def check_output(self, ns, expected):
    fob = StringIO()
    fp_list_filesets(ns, outfob=fob)
    op = fob.getvalue()
    words = op.split()
    self.assertEquals(words, expected)

  def test_list_filesets(self):
    ns = Namespace(path=self.path, count=-1, start_at=1, tags=False, properties=False)
    self.check_output(ns, [])

  def test_list_filesets_from_cli(self):
    fob = StringIO()
    oldout, olderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = fob, fob
    fp_tool_main([self.path,"lsfs"])
    sys.stdout, sys.stderr = oldout, olderr
    self.assertEquals(fob.getvalue(), "")

  def test_add_fileset(self):
    ns = Namespace(path=self.path, version="3.1", revision="1234", name="test-1")
    fp_add_filesets(ns)
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
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
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
    self.check_output(ns, words)

  def test_add_repeated_fileset(self):
    ns = Namespace(path=self.path, version="3.1", revision="1234", name="test-1")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
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
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, version="3.1", revision="2", name="build-2")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, version="3.1", revision="3", name="build-3")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")    

  def tearDown(self):
    clear_tree(self.path)

  def check_output(self, ns, expected):
    fob = StringIO()
    fp_list_files(ns, outfob=fob)
    op = fob.getvalue()
    words = op.split()
    self.assertEquals(words, expected)

  def test_list_all_files_when_none_added(self):
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1)
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
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
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
    fp_add_file(ns, errfob=fob)
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
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-2",
                   name="requirements.txt",
                   repopath="build-2",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
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
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=True, count=-1, start_at=1, tags=False, properties=False)
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
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-2",
                   name="requirements.txt",
                   repopath="build-2",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=True, count=-1, start_at=1, tags=False, properties=False)
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
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements1.txt",
                   repopath="build-1",
                   auxilliary=False,
                   origin="buildbot",
                   source_file=tmp_path)
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=True, count=-1, start_at=1, tags=False, properties=False)
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
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
    self.check_output(ns, ["1","1","untested","A", "builds/requirements.txt"])


class TestFPToolTransitOperations(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    ns = Namespace(path=self.path, version="3.1", revision="1", name="build-1")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, 
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="builds",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, 
                   fileset="build-1",
                   name="requirements-2.txt",
                   repopath="builds",
                   auxilliary=True,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="test_report",
                   repopath="builds",
                   auxilliary=True,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")

  def tearDown(self):
    clear_tree(self.path)

  def test_transit_file_to_testing(self):
    ns = Namespace(path=self.path, id=1, state="testing")
    fob = StringIO()
    fp_transit_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    fob = StringIO()
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
    fp_list_files(ns, outfob=fob)
    txt = fob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["1","1","testing","P","builds/requirements.txt",
                              "1","2","untested","A","builds/requirements-2.txt",
                              "1","3","untested","A","builds/test_report"])

  def test_transit_auxilliary_file(self):
    ns = Namespace(path=self.path, id=2, state="testing")
    fob = StringIO()
    outfob = StringIO()
    fp_transit_file(ns, errfob=fob, outfob=outfob)
    txt = fob.getvalue()
    self.assertEquals(txt, "attempted to change state on an auxilliary file\n")
    self.assertEquals(outfob.getvalue(), "")

  def test_transit_incorrect_state(self):
    ns = Namespace(path=self.path, id=1, state="released")
    fob = StringIO()
    fp_transit_file(ns, errfob=fob)
    txt = fob.getvalue()
    self.assertEquals(txt, "the transition to state 'released' for file id 1 is not permitted\n")

  def test_transit_unknown_state(self):
    ns = Namespace(path=self.path, id=1, state="jelly")
    fob = StringIO()
    fp_transit_file(ns, errfob=fob)
    txt = fob.getvalue()
    self.assertEquals(txt, "requested state 'jelly' is not recognised\n")

  def test_transit_unknown_file(self):
    ns = Namespace(path=self.path, id=5, state="testing")
    fob = StringIO()
    fp_transit_file(ns, errfob=fob)
    txt = fob.getvalue()
    self.assertEquals(txt, "file id 5 cannot be found\n")

  def test_transit_file_through_all_states(self):
    for state in ["testing","tested","approved","released"]:
      ns = Namespace(path=self.path, id=1, state=state)
      fob = StringIO()
      fp_transit_file(ns, outfob=fob)
      self.assertEquals(fob.getvalue(), "")
      fob = StringIO()
      ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
      fp_list_files(ns, outfob=fob)
      txt = fob.getvalue()
      words = txt.split()
      self.assertEquals(words, ["1","1",state,"P","builds/requirements.txt",
                                "1","2","untested","A","builds/requirements-2.txt",
                              "1","3","untested","A","builds/test_report"])

  def _withdraw(self):
    ns = Namespace(path=self.path, id=1, state="withdrawn")
    outfob = StringIO()
    errfob = StringIO()
    fp_transit_file(ns, outfob=outfob, errfob=errfob)
    return outfob, errfob

  def _check_withdrawn(self):
    fob, _ = self._withdraw()
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, long=False, count=-1, start_at=1, tags=False, properties=False)
    fp_list_files(ns, outfob=fob)
    txt = fob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["1","1","withdrawn","P","builds/requirements.txt",
                              "1","2","untested","A","builds/requirements-2.txt",
                              "1","3","untested","A","builds/test_report"])

  def test_transit_file_untested_to_withdrawn(self):
    self._check_withdrawn()

  def test_transit_file_testing_to_withdrawn(self):
    ns = Namespace(path=self.path, id=1, state="testing")
    fp_transit_file(ns)
    self._check_withdrawn()

  def test_transit_file_tested_to_withdrawn(self):
    for s in ["testing","tested"]:
      ns = Namespace(path=self.path, id=1, state=s)
      fp_transit_file(ns)
    self._check_withdrawn()

  def test_transit_file_approved_to_withdrawn(self):
    for s in ["testing","tested","approved"]:
      ns = Namespace(path=self.path, id=1, state=s)
      fp_transit_file(ns)
    self._check_withdrawn()

  def _check_fails_withdrawn(self):
    outfob, errfob = self._withdraw()
    self.assertEquals(errfob.getvalue(), "the transition to state 'withdrawn' for file id 1 is not permitted\n")

  def test_cant_tranit_from_released_to_withdrawn(self):
    for s in ["testing","tested","approved","released"]:
      ns = Namespace(path=self.path, id=1, state=s)
      fp_transit_file(ns)
    self._check_fails_withdrawn()

class TestFPToolGetFileOperations(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    ns = Namespace(path=self.path, version="3.1", revision="1", name="build-1")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="builds",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements-2.txt",
                   repopath="builds",
                   auxilliary=True,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    self.dest_path = "/tmp/tmp_file.{}".format(os.getpid())

  def tearDown(self):
    clear_tree(self.path)
    try:
      os.remove(self.dest_path)
    except:
      pass

  def test_get_a_copy_of_a_file(self):
    ns = Namespace(path=self.path, id=1, to_file=self.dest_path)
    outfob = StringIO()
    errfob = StringIO()
    fp_get_file(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(outfob.getvalue(), "")
    self.assertEquals(errfob.getvalue(), "")
    obytes = io.open(self.dest_path, "rb").read()
    nbytes = io.open("requirements.txt", "rb").read()
    self.assertEquals(obytes, nbytes)

  def test_get_a_copy_of_auxilliary_file(self):
    ns = Namespace(path=self.path, id=2, to_file=self.dest_path)
    outfob = StringIO()
    errfob = StringIO()
    fp_get_file(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(outfob.getvalue(), "")
    self.assertEquals(errfob.getvalue(), "")
    obytes = io.open(self.dest_path, "rb").read()
    nbytes = io.open("requirements.txt", "rb").read()
    self.assertEquals(obytes, nbytes)
      
  def test_try_to_get_non_existent_file(self):
    ns = Namespace(path=self.path, id=5, to_file=self.dest_path)
    outfob = StringIO()
    errfob = StringIO()
    fp_get_file(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(outfob.getvalue(), "")
    self.assertEquals(errfob.getvalue(), "the file with id 5 cannot be found\n")

  def test_try_to_overwrite_file_with_get_file(self):
    io.open(self.dest_path, "wb").close()
    ns = Namespace(path=self.path, id=1, to_file=self.dest_path)
    outfob = StringIO()
    errfob = StringIO()
    fp_get_file(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(outfob.getvalue(), "")
    self.assertEquals(errfob.getvalue(), "the target file '{}' already exists, not overwriting\n".format(self.dest_path))

  def test_try_to_write_to_not_permitted_location(self):
    new_path = "/root/cannot_write_here"
    ns = Namespace(path=self.path, id=1, to_file=new_path)
    outfob = StringIO()
    errfob = StringIO()
    fp_get_file(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(outfob.getvalue(), "")
    self.assertEquals(errfob.getvalue(), "the target file '{}' cannot be written to\n".format(new_path))


class TestFPToolTagFileSetOperations(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    ns = Namespace(path=self.path, version="3.1", revision="1", name="build-1")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, version="3.1", revision="2", name="build-2")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    self.dest_path = "/tmp/tmp_file.{}".format(os.getpid())

  def tearDown(self):
    clear_tree(self.path)
    try:
      os.remove(self.dest_path)
    except:
      pass

  def test_tag_fileset_by_id(self):
    ns = Namespace(path=self.path, id=1, tag="RC1")
    fob = StringIO()
    fp_add_fileset_tags(ns, outfob=fob, errfob=fob)
    self.assertEquals(fob.getvalue(), "")
    outfob = StringIO()
    ns = Namespace(path=self.path, tags=True, count=-1, start_at=1, properties=False)
    errfob = StringIO()
    fp_list_filesets(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(errfob.getvalue(), "")
    txt = outfob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["default","1","3.1","1","build-1",
                              "RC1",
                              "default","2","3.1","2","build-2"])

  def test_tag_fileset_by_id_multiple_tags(self):
    for tag in ["RC1","RC2","RC3"]:
      ns = Namespace(path=self.path, id=1, tag=tag)
      fob = StringIO()
      fp_add_fileset_tags(ns, outfob=fob, errfob=fob)
      self.assertEquals(fob.getvalue(), "")
    outfob = StringIO()
    ns = Namespace(path=self.path, tags=True, count=-1, start_at=1, properties=False)
    errfob = StringIO()
    fp_list_filesets(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(errfob.getvalue(), "")
    txt = outfob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["default","1","3.1","1","build-1",
                              "RC1,RC2,RC3",
                              "default","2","3.1","2","build-2"])

  def test_tag_multiple_filesets_with_same_tag(self):
    for fs_id in [1,2]:
      ns = Namespace(path=self.path, id=fs_id, tag="RC1")
      fob = StringIO()
      fp_add_fileset_tags(ns, outfob=fob, errfob=fob)
      self.assertEquals(fob.getvalue(), "")
    outfob = StringIO()
    ns = Namespace(path=self.path, tags=True, count=-1, start_at=1, properties=False)
    errfob = StringIO()
    fp_list_filesets(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(errfob.getvalue(), "")
    txt = outfob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["default","1","3.1","1","build-1",
                              "RC1",
                              "default","2","3.1","2","build-2",
                              "RC1"])

class TestFPAddFileSetPropertyOperations(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    ns = Namespace(path=self.path, version="3.1", revision="1", name="build-1")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, version="3.1", revision="2", name="build-2")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.dest_path = "/tmp/tmp_file.{}".format(os.getpid())

  def tearDown(self):
    clear_tree(self.path)
    try:
      os.remove(self.dest_path)
    except:
      pass

  def test_add_property_by_id(self):
    ns = Namespace(path=self.path, id=1, name="TestDate", value="2015-10-31", update=False)
    fob = StringIO()
    fp_add_fileset_props(ns, outfob=fob, errfob=fob)
    self.assertEquals(fob.getvalue(), "")
    outfob = StringIO()
    ns = Namespace(path=self.path, tags=False, count=-1, start_at=1, properties=True)
    errfob = StringIO()
    fp_list_filesets(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(errfob.getvalue(), "")
    txt = outfob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["default","1","3.1","1","build-1",
                              "TestDate=2015-10-31",
                              "default","2","3.1","2","build-2"])

  def test_add_property_already_exists(self):
    ns = Namespace(path=self.path, id=1, name="TestDate", value="2015-10-31", update=False)
    fob = StringIO()
    fp_add_fileset_props(ns, outfob=fob, errfob=fob)
    self.assertEquals(fob.getvalue(), "")
    errfob = StringIO()
    fp_add_fileset_props(ns, outfob=fob, errfob=errfob)
    self.assertEquals(fob.getvalue(), "")
    txt = errfob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["Fileset","id","1","already","has","property","TestDate"])

  def test_add_property_and_update(self):
    ns = Namespace(path=self.path, id=1, name="TestDate", value="2015-10-31", update=False)
    fob = StringIO()
    fp_add_fileset_props(ns, outfob=fob, errfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path, id=1, name="TestDate", value="2015-10-29", update=True)
    fp_add_fileset_props(ns, outfob=fob, errfob=fob)
    self.assertEquals(fob.getvalue(), "")
    errfob = StringIO()
    ns = Namespace(path=self.path, tags=False, count=-1, start_at=1, properties=True)
    fp_list_filesets(ns, outfob=fob, errfob=errfob)
    self.assertEquals(errfob.getvalue(), "")
    txt = fob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["default","1","3.1","1","build-1",
                              "TestDate=2015-10-29",
                              "default","2","3.1","2","build-2"])


class TestFPToolTagBinFileOperations(unittest.TestCase):

  def setUp(self):
    self.path = "/tmp/fptool.%d" % (os.getpid())
    ns = Namespace(path=self.path)
    fp_init_repo(ns)
    ns = Namespace(path=self.path, version="3.1", revision="1", name="build-1")
    fob = StringIO()
    fp_add_filesets(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements.txt",
                   repopath="builds",
                   auxilliary=False,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    ns = Namespace(path=self.path,
                   fileset="build-1",
                   name="requirements-2.txt",
                   repopath="builds",
                   auxilliary=True,
                   origin="buildbot",
                   source_file="requirements.txt")
    fob = StringIO()
    fp_add_file(ns, outfob=fob)
    self.assertEquals(fob.getvalue(), "")
    self.dest_path = "/tmp/tmp_file.{}".format(os.getpid())

  def tearDown(self):
    clear_tree(self.path)
    try:
      os.remove(self.dest_path)
    except:
      pass

  def test_tag_a_binfile_by_id(self):
    ns = Namespace(path=self.path, id=1, tag="RC1")
    fob = StringIO()
    fp_add_binfile_tags(ns, outfob=fob, errfob=fob)
    self.assertEquals(fob.getvalue(), "")
    outfob = StringIO()
    ns = Namespace(path=self.path, tags=True, count=-1, start_at=1, properties=False, long=False)
    errfob = StringIO()
    fp_list_files(ns, outfob=outfob, errfob=errfob)
    self.assertEquals(errfob.getvalue(), "")
    txt = outfob.getvalue()
    words = txt.split()
    self.assertEquals(words, ["1","1","untested","P","builds/requirements.txt",
                              "RC1",
                              "1","2","untested","A","builds/requirements-2.txt"])

if __name__ == "__main__":
  unittest.main()

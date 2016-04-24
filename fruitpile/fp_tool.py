#!/usr/bin/env python
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
from __future__ import unicode_literals
from fruitpile import Fruitpile, FPLInvalidState, FPLBinFileNotExists, FPLInvalidTargetForStateChange, FPLInvalidStateTransition, FPLFileSetExists, FPLFileExists, FPLCannotWriteFile, FPLPropertyExists
from argparse import ArgumentParser
import pwd
import os
import sys
from jinja2 import Template

def fp_init_repo(ns):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.init(uid=owner, username=pwd.getpwuid(owner)[0])
  fp.open()
  fp.close()

def fp_list_filesets(ns, outfob=sys.stdout, errfob=sys.stderr):
  template = Template('{{ " %-10s %10s %8s %8s %-39s"|format(item.repo.name, item.id,item.version,item.revision,item.name) }}')
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  fss = fp.list_filesets(uid=owner, count=ns.count, start_at=ns.start_at)
  for fs in fss:
    print(template.render(item=fs), file=outfob)
    if ns.tags:
      print("  "+",".join(fs.tags(fp.session)), file=outfob)
    if ns.properties:
      for pk,pv in fs.properties(fp.session).items():
        print("  {}={}".format(pk, pv), file=outfob)
  fp.close()

def fp_add_filesets(ns, outfob=sys.stdout, errfob=sys.stderr):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  try:
    fss = fp.add_new_fileset(uid=owner,
                             version=ns.version,
                             revision=ns.revision,
                             name=ns.name)
  except FPLFileSetExists as e:
    print("Fileset '{0}' already exists".format(str(ns.name)), file=outfob)
  fp.close()

def fp_add_fileset_tags(ns, outfob=sys.stdout, errfob=sys.stderr):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  fss = fp.get_fileset(uid=owner, fileset_id=ns.id)
  if fss == []:
    print("Fileset id {0} not found".format(ns.id), file=errfob)
    return 1
  fp.tag_fileset(uid=owner, fileset=fss[0], tag=ns.tag)

def fp_add_fileset_props(ns, outfob=sys.stdout, errfob=sys.stderr):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  fss = fp.get_fileset(uid=owner, fileset_id=ns.id)
  if fss == []:
    print("Fileset id {0} not found".format(ns.id), file=errfob)
    return 1
  try:
    fp.add_fileset_property(uid=owner, fileset=fss[0], name=ns.name, value=ns.value, update=ns.update)
  except FPLPropertyExists:
    print("Fileset 1 already has property {}".format(ns.name), file=errfob)
  

def fp_add_file(ns, outfob=sys.stdout, errfob=sys.stderr):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  fss = fp.list_filesets(uid=owner)
  bf = None
  for fs in fss:
    if fs.name == ns.fileset:
      bf = fp.add_file(uid=owner,
                       fileset_id=fs.id,
                       name=ns.name,
                       path=ns.repopath,
                       primary=(not ns.auxilliary),
                       source=ns.origin,
                       source_file=ns.source_file)
      break
  if not bf:
    print("Failed to add file, fileset '{0}' not found".format(str(ns.fileset)), file=errfob)
  fp.close()

def fp_list_files(ns, outfob=sys.stdout, errfob=sys.stdout):
  if ns.long:
    template = Template("""{{ "%10d/%-10d"|format(item.fileset_id,item.id) }} {{ "%s/%s"|format(item.path,item.name)}}
{{ item.state.name }} {{ "auxilliary" if not item.primary }}
cksum: {{ item.checksum }}
--""")
  else:
    template = Template("""{{ "%6d %10d"|format(item.fileset_id,item.id) }} {{ "%10s"|format(item.state.name) }} {{ "A" if not item.primary }}{{ "P" if item.primary }} {{ "%s/%s"|format(item.path,item.name)}}""")
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  bfs = fp.list_files(uid=owner, count=ns.count, start_at=ns.start_at)
  for bf in bfs:
    print(template.render(item=bf), file=outfob)
  fp.close()

def fp_transit_file(ns, outfob=sys.stdout, errfob=sys.stderr):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  try:
    bf = fp.transit_file(uid=owner, file_id=ns.id, req_state=ns.state)
  except FPLInvalidState as e:
    print("requested state '{0}' is not recognised".format(ns.state), file=errfob)
  except FPLBinFileNotExists as e:
    print("file id {0} cannot be found".format(ns.id), file=errfob)
  except FPLInvalidTargetForStateChange as e:
    print("attempted to change state on an auxilliary file", file=errfob)
  except FPLInvalidStateTransition as e:
    print("the transition to state '{0}' for file id {1} is not permitted".format(ns.state, ns.id), file=errfob)
  fp.close()

def fp_get_file(ns, outfob=sys.stdout, errfob=sys.stderr):
  fp = Fruitpile(ns.path)
  owner = os.getuid()
  fp.open()
  try:
    found = fp.get_file(uid=owner,
                        file_id=ns.id,
                        to_file=ns.to_file)
  except FPLBinFileNotExists as e:
    print("the file with id {} cannot be found".format(ns.id), file=errfob)
  except FPLFileExists as e:
    print("the target file '{}' already exists, not overwriting".format(ns.to_file), file=errfob)
  except FPLCannotWriteFile as e:
    print("the target file '{}' cannot be written to".format(ns.to_file), file=errfob)
  fp.close()
    
def fp_serve_repo(ns):
  print("SERVE: %s" % (ns))

def fp_tool_main(args):
  parser = ArgumentParser(prog="fp_tool", description="Fruitpile command line tool")
  parser.add_argument("path", help="Path to Fruitpile store")
  subparsers = parser.add_subparsers(help="sub-command help")

  # init
  parser_init = subparsers.add_parser("init", help="Help for the init command")
  parser_init.set_defaults(func=fp_init_repo)

  # list filesets
  parser_list_fss = subparsers.add_parser("lsfs", help="List filesets in store")
  parser_list_fss.add_argument("-c", "--count", metavar="COUNT", default=-1, help="Limit results to COUNT")
  parser_list_fss.add_argument("-s", "--start-at", metavar="START_AT", default=1, help="Start returning results from START_AT item")
  parser_list_fss.add_argument("-t", "--tags", action='store_true', default=False, help="Report tags associated with each fileset")
  parser_list_fss.add_argument("-p", "--properties", action='store_true', default=False, help="Report properties associated with each fileset")

  parser_list_fss.set_defaults(func=fp_list_filesets)

  # add fileset
  parser_add_fss = subparsers.add_parser("addfs", help="Add a new fileset in store")
  parser_add_fss.add_argument("name", help="Fileset name to add")
  parser_add_fss.add_argument("-V","--version", required=True, default="0",
                               help="Version of the file being added")
  parser_add_fss.add_argument("-r","--revision", required=True, default="1",
                               help="Revision of the file being added")

  parser_add_fss.set_defaults(func=fp_add_filesets)

  # add file
  parser_add_file = subparsers.add_parser("add", help="Add a new file in a filset")
  parser_add_file.add_argument("-f","--fileset", required=True,
                               help="Name of the fileset to add this file")
  parser_add_file.add_argument("-a","--auxilliary", action='store_true',
                               help="Indicates that this file is a auxilliary file")
  parser_add_file.add_argument("-s","--source_file", required=True,
                               help="File to add to the store")
  parser_add_file.add_argument("-o","--origin", required=True,
                               help="Origin of this file")
  parser_add_file.add_argument("-n","--name", required=True,
                               help="Name of file in repo")
  parser_add_file.add_argument("-p", "--repopath", required=True,
                               help="Path to the file in the repo fileset")
  parser_add_file.set_defaults(func=fp_add_file)

  # list files
  parser_list_files = subparsers.add_parser("ls", help="List files in the repo")
  parser_list_files.add_argument("-l", "--long", action='store_true', default=False,
                                 help="Give a longer list of file information")
  parser_list_files.add_argument("-c", "--count", metavar="COUNT", default=-1, help="Limit results to COUNT")
  parser_list_files.add_argument("-s", "--start-at", metavar="START_AT", default=1, help="Start returning results from START_AT item")
  parser_list_files.set_defaults(func=fp_list_files)

  # transit file
  parser_transit_file = subparsers.add_parser("transit", help="transit file state in repo")
  parser_transit_file.add_argument("-i","--id", type=int, required=True, help="File id of the file to be transitted")
  parser_transit_file.add_argument("-s","--state", required=True, help="New state of the item")
  parser_transit_file.set_defaults(func=fp_transit_file)

  # get a file
  parser_get_file = subparsers.add_parser("get", help="retrieve a file from the repo")
  parser_get_file.add_argument("-i","--id", type=int, required=True, help="File id of the file to be retrieved from the repo")
  parser_get_file.add_argument("-t","--to-file", required=True, help="Name of the file to copy the contents to")
  parser_get_file.set_defaults(func=fp_get_file)

  # tag a fileset
  parser_tag_fileset = subparsers.add_parser("tagfs", help="tag a fileset")
  parser_tag_fileset.add_argument("-i", "--id", type=int, required=True, help="Fileset id to add the tag to")
  parser_tag_fileset.add_argument("-t", "--tag", required=True, help="Tag to add to the fileset")
  parser_tag_fileset.set_defaults(func=fp_add_fileset_tags)

  # add property to fileset
  parser_add_fs_prop = subparsers.add_parser("fsprop", help="add or update a property")
  parser_add_fs_prop.add_argument("-i", "--id", type=int, required=True, help="Fileset id to add the property to")
  parser_add_fs_prop.add_argument("-n", "--name", required=True, help="Property name to be added")
  parser_add_fs_prop.add_argument("-v", "--value", required=True, help="Value of property to be added")
  parser_add_fs_prop.add_argument("-u", "--update", action='store_true', help="Update the property if it already exists")
  parser_add_fs_prop.set_defaults(func=fp_add_fileset_props)

  # server
  parser_serve = subparsers.add_parser("serve", help="Help for the serve command")
  parser_serve.set_defaults(func=fp_serve_repo)
  
  ns = parser.parse_args(args)
  ns.func(ns)
  
  
if __name__ == "__main__":
  fp_tool_main(sys.argv[1:])

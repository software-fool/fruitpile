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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class State(Base):
  __tablename__ = 'states'

  # The state id
  id = Column(Integer, primary_key=True)
  # The state name
  name = Column(String(20), nullable=False)
  
  def __repr__(self):
    return "<State(%s)>" % (self.name)

class Repo(Base):
  __tablename__ = 'repos'

  # The repo id primary key
  id = Column(Integer, primary_key=True)
  # The repo name
  name = Column(String(60), nullable=False)
  path = Column(String, nullable=False)
  repo_type = Column(String)
  filesets = relationship("FileSet")

class FileSet(Base):
  __tablename__ = 'filesets'

  id = Column(Integer, primary_key=True)
  name = Column(String, nullable=False)
  binfiles = relationship("BinFile")
  repo_id = Column(Integer, ForeignKey('repos.id'), nullable=False)
  repo = relationship("Repo", back_populates="filesets")

  def __repr__(self):
    return "<FileSet(%s in %s)>" % (self.name, self.repo.name)


class BinFile(Base):
  __tablename__ = 'binfiles'

  id = Column(Integer, primary_key=True)
  # The fileset this file belongs to
  fileset_id = Column(Integer, ForeignKey('filesets.id'), nullable=False)
  fileset = relationship("FileSet", back_populates="binfiles")

  # The name is the basename of the object - what's called
  name = Column(String, nullable=False)
  # The path to the file in the repository
  path = Column(String, nullable=False)
  # Version of the file - for example buildbot build number
  version = Column(String, nullable=False)
  # Revision of the file - i.e. the tip commit id, tag etc.
  revision = Column(String, nullable=False)
  # Whether the file is a primary file type or an auxilliary file
  primary = Column(Boolean, nullable=False)
  # The state of the file (references the state table to allow state flexibility)
  state_id = Column(Integer, ForeignKey('states.id'), nullable=False)
  state = relationship("State")
  # When the entry was first added
  create_date = Column(DateTime, nullable=False)
  # When the file was last updated
  update_date = Column(DateTime, nullable=False)
  # Where did the file come from (normally a hostname - or server)
  source = Column(String, nullable=False)
  # The file's checksum, with a suitable leading string which indicates
  # what type of checksum has been used (SHA1, SHA256, SHA512)
  checksum = Column(String, nullable=False)
  # ztype indicates whether the repository has used compression to store
  # the file and if so, what type.  If the file is already in a compressed
  # form then it won't be recompressed (typically used for text documents
  ztype = Column(String)
  
  
  def __repr__(self):
    return "<BinFile(name='%s', path='%s')>" % (self.name, self.path)

  def write(data):
    fob = open(self.path, "wb")
    fob.write(data)



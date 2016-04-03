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
from sqlalchemy.schema import UniqueConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from ..fp_constants import *

Base = declarative_base()

class Migration(Base):
  __tablename__ = 'migrations'

  id = Column(Integer, primary_key=True)
  script = Column(String(255), unique=True, nullable=False)

  def __repr__(self):
    return "<Migration(id=%d, script=%s)>" % (self.id, self.script)

class State(Base):
  __tablename__ = 'states'

  # The state id
  id = Column(Integer, primary_key=True)
  # The state name
  name = Column(String(20), unique=True, nullable=False)
  
  def __repr__(self):
    return "<State(%s)>" % (self.name)

class TransitionFunction(Base):
  __tablename__ = 'transfuncs'

  id = Column(Integer, primary_key=True, nullable=False)
  transfn = Column(String, unique=True, nullable=False)
  transitions = relationship('Transition')

  def __repr__(self):
    return "<TransitionFunction(%s)>" % (self.transfn)
  
class Transition(Base):
  __tablename__ = 'transitions'
  __table_args__ = (
    PrimaryKeyConstraint('start_id','end_id'),
    CheckConstraint('start_id != end_id')
  )

  start_id = Column(Integer, ForeignKey('states.id'), nullable=False)
  end_id = Column(Integer, ForeignKey('states.id'), nullable=False)
  start = relationship('State', primaryjoin="State.id==Transition.start_id", foreign_keys=[start_id])
  end = relationship('State', primaryjoin="State.id==Transition.end_id", foreign_keys=[end_id])
  transfn_id = Column(Integer, ForeignKey('transfuncs.id'))
  transfn = relationship('TransitionFunction', back_populates='transitions')
  perm_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
  perm = relationship('Permission', back_populates='transitions')

  def __repr__(self):
    if self.transfn and self.transfn != "":
      transfn_str = "with transfn=%s" % (self.transfn)
    else:
      transfn_str = ""
    return "<Transition(%s=>%s%s>" % (self.start.name,self.end.name, transfn_str)

class Permission(Base):
  __tablename__ = 'permissions'

  id = Column(Integer, primary_key=True)
  user_perms = relationship('UserPermission')
  name = Column(String(20), unique=True, nullable=False)
  desc = Column(String, nullable=False)
  transitions = relationship('Transition')

  def __repr__(self):
    return "<Permission(%s=%d)>" % (self.name, self.id)

class User(Base):
  __tablename__ = 'users'

  uid = Column(Integer, primary_key=True)
  user_perms = relationship('UserPermission')
  name = Column(String(20), unique=True, nullable=False)

  def __repr__(self):
    return "<User(%s=%d)>" % (self.name, self.id)

class UserPermission(Base):
  __tablename__ = 'user_perms'
  __table_args__ = (
    PrimaryKeyConstraint('user_id','perm_id'),
  )

  user_id = Column(Integer, ForeignKey('users.uid'), nullable=False)
  user = relationship('User', back_populates='user_perms')
  perm_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
  perm = relationship('Permission', back_populates='user_perms')


  def __repr__(self):
    return "<UserPermission(uid=%d,permid=%d)>" % (self.user_id, self.perm_id)

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
  name = Column(String, unique=True, nullable=False)
  binfiles = relationship("BinFile")
  repo_id = Column(Integer, ForeignKey('repos.id'), nullable=False)
  repo = relationship("Repo", back_populates="filesets")
  # Version of the fileset - for example buildbot build number
  version = Column(String, nullable=False)
  # Revision of the fileset - i.e. the tip commit id, tag etc.
  revision = Column(String, nullable=False)

  def __repr__(self):
    return "<FileSet(%s in %s)>" % (self.name, self.repo.name)


class BinFile(Base):
  __tablename__ = 'binfiles'
  __table_args__ = (
    UniqueConstraint('name', 'path'),
    UniqueConstraint('fileset_id', 'name')
  )

  id = Column(Integer, primary_key=True)
  # The fileset this file belongs to
  fileset_id = Column(Integer, ForeignKey('filesets.id'), nullable=False)
  fileset = relationship("FileSet", back_populates="binfiles")

  # The name is the basename of the object - what's called
  name = Column(String, nullable=False)
  # The path to the file in the repository
  path = Column(String, nullable=False)
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

def upgrade(engine, uid, username, path):
  Base.metadata.create_all(bind=engine)
  Session = sessionmaker(bind=engine)
  session = Session()
  rp = Repo(name="default", path=path, repo_type="FileManager")
  session.add(rp)
  session.add(User(uid=uid, name=username))
  for name in Capability.keys():
    cap = Capability.get(name)
    session.add(Permission(id=cap.ident, name=cap.name, desc=cap.description))
    session.add(UserPermission(user_id=uid, perm_id=cap.ident)) 
  state_dict = {}
  for sname in ["untested","testing","tested","approved","released","withdrawn"]:
    state = State(name=sname)
    session.add(state)
  session.commit()
  for s in session.query(State).all():
    state_dict[s.name] = s
  for transition in [("untested","testing",None,Capability.BEGIN_TESTING),
                     ("untested","withdrawn",None,Capability.WITHDRAW_ARTIFACT),
                     ("testing","tested",None,Capability.ARTIFACT_TESTED),
                     ("testing","withdrawn",None,Capability.WITHDRAW_ARTIFACT),
                     ("tested","approved",None,Capability.APPROVE_ARTIFACT),
                     ("tested","withdrawn",None,Capability.WITHDRAW_ARTIFACT),
                     ("approved","released",None,Capability.RELEASE_ARTIFACT),
                     ("approved","withdrawn",None,Capability.WITHDRAW_ARTIFACT)]:
    start_id = state_dict[transition[0]].id
    end_id= state_dict[transition[1]].id
    session.add(Transition(start_id=start_id,
                           end_id=end_id,
                           transfn_id=transition[2],
                           perm_id=transition[3]))
  mig = Migration(id=1, script=__name__)
  session.add(mig)
  session.commit()
  session.close()
 
def downgrade(engine):
  Base.metadata.drop_all(bind=engine)


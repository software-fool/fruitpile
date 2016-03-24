import unittest
import inspect
import os.path
import sys

mydir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
sys.path.append(os.path.dirname(mydir))

from db.schema import *
from sqlalchemy.orm import sessionmaker

class TestState(unittest.TestCase):

  def setUp(self):
    self.engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=self.engine)
    Session = sessionmaker(bind=self.engine)
    self.session = Session()

  def tearDown(self):
    self.session.close()

  def test_create_a_state(self):
    ss = self.session.query(State).all()
    self.assertEquals(len(ss), 0)    
    s = State(name="unverified")
    self.assertEquals(s.name, "unverified")
    self.session.add(s)
    self.session.commit()
    self.session.rollback()
    ss = self.session.query(State).all()
    self.assertEquals(len(ss), 1)
    self.assertEquals(ss[0], s)

  def test_create_multiple_states(self):
    state_names = ["unverified","in-testing","tested","approved","released"]
    s1s = []
    for i in state_names:
      s = State(name=i)
      self.session.add(s)
      s1s.append(s)
    self.session.commit()
    ss = self.session.query(State).all()
    self.assertEquals(len(ss), 5)
    for i in range(len(ss)):
        self.assertEquals(ss[i], s1s[i])


class TestFileSet(unittest.TestCase):

  def setUp(self):
    self.engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=self.engine)
    Session = sessionmaker(bind=self.engine)
    self.session = Session()
  
  def tearDown(self):
    self.session.close()

  def test_create_a_fileset(self):
    fss = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 0)
    fs = FileSet(name="test-1")
    self.session.add(fs)
    self.session.commit()
    fss = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 1)
    self.assertEquals(fss[0], fs)

  def test_create_multiple_filesets(self):
    fss = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 0)
    fss = []
    for i in range(0,10):
      fs = FileSet(name="test-%d" % (i))
      self.session.add(fs)
      fss.append(fs)
    self.session.commit()
    fss2 = self.session.query(FileSet).all()
    self.assertEquals(len(fss), 10)
    self.assertEquals(fss, fss2)



if __name__ == "__main__":
  unittest.main()

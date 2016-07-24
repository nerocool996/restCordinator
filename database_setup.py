import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

import psycopg2
import urlparse

Base = declarative_base()
##Config Ends##
class User(Base):
	__tablename__='user'
	name = Column(String(40),nullable=False)
	id = Column(Integer,primary_key = True)
	picture = Column(String(200))
	email = Column(String(100),nullable=False)
	pollItems = relationship("Going",cascade="all, delete-orphan")

class  Going(Base):
	__tablename__= 'going'
	name = Column(String(80),nullable= False)
	id = Column(Integer, primary_key = True)
 	rest_id = Column(Integer)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	@property
	def serialize(self):
		return {
		'name' : self.name,
		'id' : self.id,
		}


##END OF FILE##
engine = create_engine('sqlite:///goingOut.db')

Base.metadata.create_all(engine)

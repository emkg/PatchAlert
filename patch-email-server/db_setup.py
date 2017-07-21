import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    isAdmin = Column(Integer) # 0 or 1


class Alert(Base):
    __tablename__ = 'alert'

    servers = Column(String(500), nullable=False)
    date = Column(String(10), nullable=False)
    startTime = Column(String(7), nullable=False)
    endTime = Column(String(7), nullable=False)
    createdBy = relationship(User)
    approvedBy = relationship(User)
    isApproved = Column(Integer) # 0 or 1
    isExpired = Column(Integer) # 0 or 1
    approvedBy_id = Column(Integer, ForeignKey('user.id'))
    createdBy_id = Column(Integer, ForeignKey('user.id'))
    id = Column(Integer, primary_key = True)

    @property
    def serialize(self):
        # returns object data in easily serializable form-data
        return {
            'servers': self.servers,
            'date': self.date,
            'startTime': self.startTime,
            'endTime': self.endTime,
            'createdBy': self.createdBy,
            'approvedBy': self.approvedBy,
            'isApproved': self.isApproved,
            'id': self.id,
            'createdBy_id': self.createdBy_id,
            'approvedBy_id': self.approvedBy_id,
        }

class Request(Base):
    __tablename__ = 'request'

    server = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    reason = Column(String(250), nullable = False)
    altDate = Column(String(7), nullable=False)
    altTime = Column(String(7), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    alert = relationship(Alert)
    alert_id = Column(Integer, ForeignKey('alert.id'))

    @property
    def serialize(self):
        # returns object data in easily serializable form-data
        return {
            'server': self.server,
            'reason': self.reason,
            'altDate': self.altDate,
            'altTime': self.altTime,
            'user': self.user,
            'user_id': self.user_id,
            'alert': self.alert,
            'alert_id': self.alert_id,
            'id': self.id,
        }

####### insert at end of file ######

engine = create_engine(
'sqlite:///patchalerts.db')

Base.metadata.create_all(engine)

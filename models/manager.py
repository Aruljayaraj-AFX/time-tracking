from sqlalchemy import Column, String,DateTime, func,JSON
from sqlalchemy.ext.declarative import declarative_base

Manager_Base = declarative_base()

class Musers(Manager_Base):
    __tablename__='Manager'

    Manager_id = Column(String, primary_key=True,nullable=False)
    Managername = Column(String,nullable=False)
    email = Column(String,unique=True,nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())  
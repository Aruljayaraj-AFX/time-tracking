from sqlalchemy import Column, String,DateTime, func,JSON
from sqlalchemy.ext.declarative import declarative_base

user_Base = declarative_base()

class users(user_Base):
    __tablename__='users'

    user_id = Column(String, primary_key=True,nullable=False)
    username = Column(String,nullable=False)
    email = Column(String,unique=True,nullable=False)
    password = Column(String, nullable=False)
    project_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())  
from sqlalchemy import Column, String, Integer, DateTime, func, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Projects(Base):
    __tablename__ = 'UPDATE_PROJECTS'

    sno = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    date= Column(DateTime, nullable=False)
    project_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    work_description = Column(String, nullable=False)
    hour_contribution = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())

from sqlalchemy import Column, String,DateTime, func,JSON
from sqlalchemy.ext.declarative import declarative_base

project_Base = declarative_base()

class project(project_Base):
    __tablename__='projects'

    project_id = Column(String, primary_key=True,nullable=False)
    projectname = Column(String,nullable=False)
    project_description = Column(String, nullable=True)
    project_members = Column(JSON,nullable=False)
    hour_contribution = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())  
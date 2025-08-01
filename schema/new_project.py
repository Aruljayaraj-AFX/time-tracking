from pydantic import BaseModel

class new_project(BaseModel):
    project_name: str
    project_description: str
    project_members: list[str]
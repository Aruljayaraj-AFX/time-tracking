from pydantic import BaseModel

class new_report(BaseModel):
    Startdate: str
    Enddate: str
    member_name: list[str]
    project_names: list[str]
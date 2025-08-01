from pydantic import BaseModel

class dailyupdate(BaseModel):
    date: str
    projectid: str
    userid: str
    workdescription: str
    hours: float
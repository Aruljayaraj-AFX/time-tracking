from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schema.user import LoginRequest
from schema.daily import dailyupdate
from database.db import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.user_dashboard import u_login,c_Authorization,otp,check_otp,update_password,update_hours,hours_getdata,fetch_data_by_date
from models.user_data import users
from models.projects import project

user_router = APIRouter()

@user_router.post("/user_login")
async def user_login(check:LoginRequest,db: Session = Depends(get_db)):
    u_log = await u_login(check.email, check.password, db)
    return u_log

@user_router.get("/u_security_checku/")
async def read(token: object = Depends(c_Authorization())):
    return token 

@user_router.get("/otp/")
async def otp_route(response: dict = Depends(otp())):
    return response


@user_router.get("/otp_v/")
async def otp_route(otp:str,otptoken:str,db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    result=await check_otp(otp, otptoken, db, token)
    return result

@user_router.put("/update_password/")
async def update_password_route(new_password: str, db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    response = await update_password(new_password, db, token)
    return response

@user_router.get("/get-projectsu/")
async def get_projects(db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    projects = db.query(project).all()
    project_list = [proj.projectname for proj in projects]
    return {"projects": project_list}

@user_router.get("/userid/")
async def get_userid(db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    user = db.query(users).filter(users.email == token["sub"]).first()
    if user:
        return {"user_id": user.user_id}
    else:
        return {"error": "User not found"}
    
@user_router.get("/projectid/")
async def get_projectid(projectname: str, db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    project_obj = db.query(project).filter(project.projectname == projectname).first()
    if project_obj:
        return {"project_id": project_obj.project_id}
    else:
        return {"error": "Project not found"}

@user_router.post("/UPDATE_hours/")
async def update_hours_route(new:dailyupdate, db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    result = await update_hours(new , db, token)
    return result

@user_router.get("/hour_details")
async def hours_data(db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    result=hours_getdata(db,token)
    return result

@user_router.get("/get_user_projects")
async def get_user_projects(project_id: str, db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    email = token["sub"]
    user = db.query(users).filter(users.email == email).first()
    project = db.query(project).filter(project.project_id == project_id).first()
    username = user.username
    project_members = project.project_members
    for i in range(len(project_members)):
        if project_members[i] == username:
            index = i
            de=project.hour_contribution[index] 
    return {
        "project_name": project.projectname,
        "project_description": project.project_description,
        "hour_contribution": de
    }

@user_router.get("/date_fetch")
async def date_fetch(date:str, db: Session = Depends(get_db), token: dict = Depends(c_Authorization())):
    result = await fetch_data_by_date(date, db, token)
    return result
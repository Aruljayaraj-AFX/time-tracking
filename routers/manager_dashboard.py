from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.db import get_db
from services.manager_dashboard import login, user_Authorization,change_password, create_user_logic, new_pro,check_d_data
from models.user_data import users
from fastapi.encoders import jsonable_encoder
from schema.new_project import new_project
from schema.report import new_report
from models.projects import project
from schema.user import LoginRequest
from fastapi import Query
from datetime import datetime, timedelta
from typing import List
from collections import defaultdict
from models.daily_update import Projects

router = APIRouter()

@router.post("/login")
async def login_route(logd: LoginRequest, db: Session = Depends(get_db)):
    return await login(logd.email, logd.password, db)

@router.get("/security_check/")
async def read(token: object = Depends(user_Authorization())):
    return token 

@router.put("/change_password/")
async def change_password_route(new_password: str,db: Session = Depends(get_db),token: dict = Depends(user_Authorization())):
    response = await change_password(new_password, db, token)
    return response

@router.post("/new_user")
async def create_user(name:str, email: str, password: str, db: Session = Depends(get_db),token: dict = Depends(user_Authorization())):
    response = await create_user_logic(name, email, password, db, token)
    return response

@router.get("/user_details")
async def get_user(db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    user_objs = db.query(users).all()
    username_list = [user.username for user in user_objs]
    email_list = [user.email for user in user_objs]
    project_ids_list = []
    for user in user_objs:
        if user.project_ids is not None:
            project_ids_list.append(user.project_ids)
        else:
            project_ids_list.append("No projects assigned")
    return {
        "usernames": username_list,
        "emails": email_list,
        "project_ids": project_ids_list
    }

@router.get("/username_list")
async def get_user(db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    user_objs = db.query(users).all()
    username_list = [user.username for user in user_objs]
    return username_list

@router.get("/particular_user")
async def get_particular_user(username: str, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    user = db.query(users).filter(users.username == username).first()
    if not user.project_ids:
        project_d = "No projects assigned to this user"
    else:
        project_d={}
        for i in user.project_ids:
            project_dj = db.query(project).filter(project.project_id == i).first()
            user_pro=[u for u in project_dj.project_members]
            exist_time=[u for u in project_dj.hour_contribution]
            for i in range(len(user_pro)):
                if user_pro[i] == username:
                    index=i
            project_d[project_dj.projectname] = {
                "project_id": project_dj.project_id,
                "project_name": project_dj.projectname,
                "project_description": project_dj.project_description,
                "hour_contribution": exist_time[index]
            }
    return {
        "username": user.username,
        "email": user.email,
        "project_ids": project_d
    }

            

@router.post("/new_projects")
async def get_new_projects(new: new_project, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    pro = await new_pro(new,db)  
    return pro

@router.get("/add-member-for-project")
async def get_member_pro(pro_name:str,db:Session=Depends(get_db),token:dict=Depends(user_Authorization())):
    user_objs = db.query(users).all()
    username_list = [user.username for user in user_objs]
    pro_m=db.query(project).filter(project.projectname==pro_name).first()
    member_usernames = [member for member in pro_m.project_members]
    non_members = [uname for uname in username_list if uname not in member_usernames]
    return non_members

@router.put("/add-new-member-on-pro")
async def add_new_member(pro_name: str,member: list[str],db: Session = Depends(get_db),token: dict = Depends(user_Authorization())):
    pro_obj = db.query(project).filter(project.projectname == pro_name).first()
    existing_usernames = [u for u in pro_obj.project_members]
    exist_time=[u for u in pro_obj.hour_contribution]
    for username in member:
        if username not in existing_usernames:
            existing_usernames.append(username)
            exist_time.append(0)
    pro_obj.project_members = existing_usernames
    pro_obj.hour_contribution = exist_time
    db.commit()
    return {"message": "Members added successfully"}

@router.put("/remove-member-from-pro")
async def remove_member_from_pro(pro_name: str,membername: str,db: Session = Depends(get_db),token: dict = Depends(user_Authorization())):
    pro_obj = db.query(project).filter(project.projectname == pro_name).first()
    if not pro_obj:
        return {"message": "Project not found"}
    user_pro=[u for u in pro_obj.project_members]
    if membername not in pro_obj.project_members:
        return {"message": "User is not a member of this project"}
    for i in range(len(user_pro)):
        if user_pro[i] == membername:
            index=i
    final=user_pro.pop(index)
    exist_time=[u for u in pro_obj.hour_contribution]
    exist_time.pop(index)
    pro_obj.hour_contribution = exist_time
    pro_obj.project_members = user_pro
    db.commit()
    return {
        "message": f"User '{membername}' removed successfully",
        "remaining_members": [u for u in pro_obj.project_members]
    }

@router.get("/get-projects")
async def get_projects(db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    projects = db.query(project).all()
    project_de={}
    t_hour=0
    for i in projects:
        project_de[i.projectname]=i.hour_contribution
    for j in project_de:
        for i in project_de[j]:
            t_hour+=i
    project_de["overall_hours"] = t_hour
    project_de["project_count"] = len(projects)
    return project_de

@router.get("/get-project-details")
async def get_project_details(pro_name: str, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    project_obj = db.query(project).filter(project.projectname == pro_name).first()
    if not project_obj:
        return {"message": "Project not found"}
    t_hour=0
    for i in project_obj.hour_contribution:
        t_hour+=i
    project_details = {
        "project_id": project_obj.project_id,
        "project_name": project_obj.projectname,
        "project_description": project_obj.project_description,
        "project_members": project_obj.project_members,
        "hour_contribution": t_hour,
        "created_at": project_obj.created_at
    }
    return project_details

@router.get("/get-projects-by-id")
async def get_projects_by_id(project_name: str, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    project_obj = db.query(project).filter(project.projectname == project_name).first()
    pro_id= project_obj.project_id
    result = check_d_data(pro_id, db)
    return result

@router.get("/get-projectid")
async def get_project_id(pro_ids: List[str] = Query(...),  db: Session = Depends(get_db),token: dict = Depends(user_Authorization())):
    project_names = []
    for pro_id in pro_ids:
        project_obj = db.query(project).filter(project.project_id == pro_id).first()
        if project_obj:
            project_names.append(project_obj.projectname)
    return {"project_names": project_names}

@router.post("/get-reports")
async def get_reports(report: new_report, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    start_date_str = report.Startdate
    end_date_str = report.Enddate
    start_date = datetime.strptime(start_date_str, "%d-%m-%Y").date()
    end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date()
    all_dates = [(start_date + timedelta(days=i)).strftime("%d-%m-%Y")for i in range((end_date - start_date).days + 1)]
    member_names = report.member_name
    project_names = report.project_names
    eachmember_name = {}
    eachmember_id = {}
    report_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    total_hours = 0
    user_total_hours = defaultdict(int)       
    project_total_hours = defaultdict(int)    
    for name in member_names:
        user = db.query(users).filter(users.username == name).first()
        if not user:
            continue
        user_id = user.user_id
        project_ids = []
        valid_project_names = []
        for pname in project_names:
            proj = db.query(project).filter(project.projectname == pname).first()
            if proj and name in proj.project_members:
                project_ids.append(proj.project_id)
                valid_project_names.append(proj.projectname)
        eachmember_name[name] = valid_project_names
        eachmember_id[user_id] = project_ids
        for pid in project_ids:
            for date_str in all_dates:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
                result = db.query(Projects).filter(
                    Projects.user_id == user_id,
                    Projects.project_id == pid,
                    Projects.date == date_obj
                ).first()
                if result:
                    hour = result.hour_contribution
                    report_data[user_id][pid][date_str] = {
                        "work_description": result.work_description,
                        "hour_contribution": hour,
                        "project_id": result.project_id,
                        "user_id": result.user_id,
                        "date": result.date.strftime("%d-%m-%Y"),
                        "created_at": result.created_at.strftime("%d-%m-%Y %H:%M:%S"),
                    }
                    total_hours += hour
                    user_total_hours[user_id] += hour
                    project_total_hours[pid] += hour
    active_members = 0
    project_active_count = 0
    for user_id, projects_dict in report_data.items():
        user_has_data = False
        for pid, dates_dict in projects_dict.items():
            if dates_dict:
                project_active_count += 1
                if not user_has_data:
                    active_members += 1
                    user_has_data = True
    return {
        "status": "success",
        "data": {
            "startdate": start_date_str,
            "enddate": end_date_str,
            "alldates": all_dates,
            "eachmember_name": eachmember_name,
            "eachmember_id": eachmember_id,
            "report": report_data,
            "member_active": active_members,
            "project_active": project_active_count,
            "total_hours": total_hours,
            "user_total_hours": dict(user_total_hours),         
            "project_total_hours": dict(project_total_hours)    
        }
    }

@router.get("/pro_details")
async def get_pro_details(db:Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    projects = db.query(project).all()
    project_details = []
    for proj in projects:
        total_hours = sum(proj.hour_contribution)
        project_details.append({
            "project_name": proj.projectname,
            "hour_contribution": total_hours,
            "created_at": proj.created_at
        })
    return {"projects": project_details}

@router.get("/today_sub")
async def get_today_submissions(db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    today = datetime.now().date()
    submissions = db.query(Projects).filter(Projects.date == today).all()
    len_submissions = len(submissions)
    return {
        "today_submissions": len_submissions,
        }

from passlib.context import CryptContext
from models.manager import Musers
from models.user_data import users
from models.daily_update import Projects
from models.projects import project
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from database.db import get_db
import uuid
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified
from datetime import date

SECRET_KEY = "your_super_secret_key"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
ACCESS_otpEXPIRE_MINUTES = 1

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def u_login(email: str, password: str, db: Session):
    try:
        user = db.query(users).filter(users.email == email).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        
        is_valid = pwd_context.verify(password, user.password)
        if is_valid:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            payload = {
                "sub": user.email,
                "exp": expire
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return {"status": "success", "message": "Login successful", "token": token}
        else:
            return {"status": "error", "message": "Invalid password"}

    except Exception as e:
        return {"status": "error", "message": f"Login failed: {str(e)}"}


class c_Authorization(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(c_Authorization, self).__init__(auto_error=auto_error)
    async def __call__(self, request: Request,db: Session = Depends(get_db)):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code")
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            if "sub" not in payload:
                raise HTTPException(status_code=403, detail="Invalid token payload")
            token = payload["sub"]
            man_user = db.query(users).filter(users.email == token).first()
            if man_user is None:
                raise HTTPException(status_code=403, detail="User not found")
            return payload  
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

class otp:
    def __call__(self, db: Session = Depends(get_db),token: dict = Depends(c_Authorization())):
        email = token["sub"] 
        sender_email = "aruljayarajj826@gmail.com"
        sender_password = "mjlw hpey ydex otlj"
        otp = str(random.randint(100000, 999999))
        subject = "Your OTP for Password Reset"
        body = (
            f"Dear user,\n\n"
            f"Your One-Time Password (OTP) for resetting your password is: {otp}\n\n"
            f"Please use this OTP to verify your request. It is valid for a limited time.\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"Thanks,\nTeam CodeWork"
        )
        if sender_password is None:
            raise HTTPException(status_code=500, detail="Email password is not set.")
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
            server.quit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_otpEXPIRE_MINUTES)
        payload = {
                "sub": otp,
                "exp": expire
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"message": "OTP email sent successfully", "secret": token}

async def check_otp(otp: str, otptoken: str, db: Session, token: dict):
    try:
        payload = jwt.decode(otptoken, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] != otp:
            raise HTTPException(status_code=403, detail="Invalid OTP")
        return {"status": "success", "message": "OTP verified successfully"}
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired OTP token")
    except Exception as e:
        return {"status": "error", "message": f"OTP verification failed: {str(e)}"}
    
async def update_password(new_password: str, db: Session, token: dict):
    try:
        email = token["sub"] 
        user = db.query(users).filter(users.email == email).first()
        user.password = pwd_context.hash(new_password)
        db.commit()
        return {"status": "success", "message": "Password updated successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Password update failed: {str(e)}"}
    
async def update_hours(new, db: Session, token: dict):
    try:
        email = token["sub"]
        new_up = Projects(
            date=new.date,
            project_id=new.projectid,
            user_id=new.userid,
            work_description=new.workdescription,
            hour_contribution=new.hours
        )
        db.add(new_up)
        user = db.query(users).filter(users.user_id == new.userid).first()
        username = user.username
        project_obj = db.query(project).filter(project.project_id == new.projectid).first()
        project_members = project_obj.project_members
        hour_contributions = project_obj.hour_contribution
        if username in project_members:
            index = project_members.index(username)
            hour_contributions[index] += new.hours
            flag_modified(project_obj, "hour_contribution")  
        else:
            return {
                "status": "error",
                "message": "User is not a member of the project"
            }
        db.commit()
        db.refresh(new_up)
        return {
            "status": "success",
            "message": "Hours updated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update hours: {str(e)}"
        }


def hours_getdata(db: Session, token: dict):
    email = token["sub"]
    user = db.query(users).filter(users.email == email).first()
    userid = user.user_id
    username = user.username
    project_list = user.project_ids

    total_hours = 0
    week_hours = 0
    today = date.today()
    last_7_dates = [(today - timedelta(days=i)) for i in range(7)]
    daily_logs = db.query(Projects).filter(Projects.date == today, Projects.user_id == userid).all()
    daily_contribution = sum(p.hour_contribution for p in daily_logs)
    for i in last_7_dates:
        weekly_logs = db.query(Projects).filter(Projects.date == i, Projects.user_id == userid).all()
        for log in weekly_logs:
            week_hours += log.hour_contribution
    detailed_projects = []
    for pid in project_list:
        project_obj = db.query(project).filter(project.project_id == pid).first()
        if project_obj:
            try:
                index = project_obj.project_members.index(username)
                user_contribution = project_obj.hour_contribution[index]
            except ValueError:
                user_contribution = 0
            detailed_projects.append({
                "project_id": pid,
                "project_name": project_obj.projectname,
                "project_description": project_obj.project_description,
                "hour_contribution": user_contribution
            })
            total_hours += user_contribution
    return {
        "user_id": userid,
        "total_hours": total_hours,
        "active_projects": len(project_list),
        "daily_contribution": daily_contribution,
        "weekly_hours": week_hours,
        "projects": detailed_projects
    }

async def fetch_data_by_date(date: str, db: Session, token: dict):
    try:
        email = token["sub"]
        user = db.query(users).filter(users.email == email).first()
        user_id = user.user_id
        daily_logs = db.query(Projects).filter(Projects.date == date, Projects.user_id == user_id).all()
        
        if not daily_logs:
            return {"status": "error", "message": "No data found for the specified date"}
        
        contributions = []
        for log in daily_logs:
            pro_name=db.query(project).filter(project.project_id == log.project_id).first()
            pron=pro_name.projectname
            contributions.append({
                "project_name": pron,
                "work_description": log.work_description,
                "hour_contribution": log.hour_contribution
            })
        return {
            "status": "success",
            "date": date,
            "contributions": contributions
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch data: {str(e)}"}
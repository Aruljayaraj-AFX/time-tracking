from passlib.context import CryptContext
from models.manager import Musers
from models.user_data import users
from models.projects import project
from models.daily_update import Projects
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from database.db import get_db
import uuid
from datetime import date

SECRET_KEY = "your_super_secret_key"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def login(email: str, password: str, db: Session):
    try:
        user = db.query(Musers).filter(Musers.email == email).first()
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

class user_Authorization(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(user_Authorization, self).__init__(auto_error=auto_error)
    async def __call__(self, request: Request,db: Session = Depends(get_db)):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code")
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            if "sub" not in payload:
                raise HTTPException(status_code=403, detail="Invalid token payload")
            token = payload["sub"]
            man_user = db.query(Musers).filter(Musers.email == token).first()
            if man_user is None:
                raise HTTPException(status_code=403, detail="User not found")
            return payload  
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        
async def change_password(new_password: str, db: Session, token: dict):
    try:
        email = token["sub"] 
        user = db.query(Musers).filter(Musers.email == email).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        user.password = pwd_context.hash(new_password)
        db.commit()
        return {"status": "success", "message": "Password changed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Password change failed: {str(e)}"}
    
async def create_user_logic(name: str, email: str, password: str, db: Session, token: dict):
    try:
        decoded_token = token  
        if not decoded_token or "sub" not in decoded_token:
            raise HTTPException(status_code=403, detail="Unauthorized action")
        existing_user = db.query(users).filter(users.email == email).first()
        if existing_user:
            return {"status": "error", "message": "User already exists"}
        hashed_password = pwd_context.hash(password)
        new_user = users(
            user_id="CW" + str(uuid.uuid4()),  
            username=name, 
            email=email,
            password=hashed_password,
            project_ids = ""
        )
        db.add(new_user)
        db.commit()
        return {"status": "success", "message": "User created successfully"}
    except Exception as e:
        return {"status": "error", "message": f"User creation failed: {str(e)}"}
    
async def new_pro(new, db: Session):
    try:
        project_id = "PR" + str(uuid.uuid4())  
        hour_contribution = [0 for member in new.project_members]
        new_project_data = project(
            project_id=project_id,
            projectname=new.project_name,
            project_description=new.project_description,
            project_members=new.project_members,
            hour_contribution=hour_contribution,
            created_at=datetime.utcnow()
        )
        db.add(new_project_data)
        for member in new.project_members:
            user = db.query(users).filter(users.username == member).first()
            user.project_ids = user.project_ids + [project_id] if user.project_ids else [project_id]
            db.add(user)
        db.commit()
        db.refresh(new_project_data)
        return {"status": "success", "message": "Project created successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Project creation failed: {str(e)}"}
    

def check_d_data(project_id: str, db: Session):
    try:
        today = date.today()
        daily_data = db.query(Projects).filter(
            Projects.date == today,
            Projects.project_id == project_id
        ).all()
        if not daily_data:
            return {"status": "error", "message": "No data found for today"}
        project_details = []
        user_ids = set()
        for data in daily_data:
            project_details.append({
                "date": data.date,
                "project_id": data.project_id,
                "user_id": data.user_id,
                "work_description": data.work_description,
                "hour_contribution": data.hour_contribution
            })
            user_ids.add(data.user_id)
        last_7_dates = [today - timedelta(days=i) for i in range(7)]
        project_data = []
        for d in last_7_dates:
            records = db.query(Projects).filter(
                Projects.date == d,
                Projects.project_id == project_id
            ).all()
            for entry in records:
                user_obj = db.query(users).filter(users.user_id == entry.user_id).first()
                project_obj = db.query(project).filter(project.project_id == entry.project_id).first()
                if user_obj and project_obj:
                    project_data.append({
                        "date": entry.date,
                        "username": user_obj.username,
                        "project_name": project_obj.projectname,
                        "work_description": entry.work_description,
                        "hour_contribution": entry.hour_contribution
                    })
        return {
            "status": "success",
            "message": "Data fetched successfully",
            "project_details_count": len(project_details),
            "unique_users": len(user_ids),
            "project_data": project_data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch data: {str(e)}"
        }

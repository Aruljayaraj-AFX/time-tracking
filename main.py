from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uvicorn
from routers.manager_dashboard import router
from routers.user_dashboard import user_router
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/codework/employee-time-tracking/v1", tags=["manager_dashboard"])
app.include_router(user_router, prefix="/codework/employee-time-tracking/v1", tags=["user_dashboard"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
from  sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_URL= "postgresql://hello_0bri_user:F4Ost504KNuIyjQgbvoK37AimV7EC2Mw@dpg-d266t36uk2gs73bkfck0-a.oregon-postgres.render.com/hello_0bri"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
session=SessionLocal(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
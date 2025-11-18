# backend/app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, select
from .models import User
from sqlmodel import create_engine

security = HTTPBasic()
engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as s:
        yield s

def basic_auth(credentials: HTTPBasicCredentials = Depends(security), session: Session = Depends(get_session)):
    username = credentials.username
    password = credentials.password
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if not user or user.password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

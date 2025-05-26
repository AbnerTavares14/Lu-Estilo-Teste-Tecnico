from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from app.db.connection import session
from sqlalchemy.orm import Session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

def get_db_session():
    try:
        db = session()
        yield db
    finally:
        db.close()
    

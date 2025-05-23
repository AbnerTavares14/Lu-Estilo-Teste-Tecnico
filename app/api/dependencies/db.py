from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from app.db.connection import session
from sqlalchemy.orm import Session
from app.api.dependencies.auth import UserManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

def get_db_session():
    try:
        db = session()
        yield db
    finally:
        db.close()
    
def token_verifier(
    db: Session = Depends(get_db_session),
    token = Depends(oauth2_scheme)
):
    um = UserManager(db)
    um.verify_token(access_token=token)
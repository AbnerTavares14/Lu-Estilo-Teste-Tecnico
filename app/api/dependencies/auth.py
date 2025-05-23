from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db_session
from app.services.auth import AuthService
from app.models.domain.user import UserModel
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_auth_service(db: Session = Depends(get_db_session)):
    return AuthService(db)

async def get_current_user(token: str = Depends(oauth2_scheme), auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.verify_token(token)

async def restrict_to_role(role: str, user: UserModel = Depends(get_current_user)):
    if user.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user
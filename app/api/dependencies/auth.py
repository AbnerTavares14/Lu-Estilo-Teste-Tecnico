from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db_session
from app.services.auth import AuthService
from app.db.repositories.auth import AuthRepository
from app.models.domain.user import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_user_repository(db: Session = Depends(get_db_session)):
    return AuthRepository(db)

def get_auth_service(auth_repo: AuthRepository = Depends(get_user_repository)):
    return AuthService(auth_repo)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    auth_service: AuthService = Depends(get_auth_service)
) -> UserModel:
    try:
        user = auth_service.verify_token(token) 
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException as e: 
        raise e 
    except Exception: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def restrict_to_role(role: str, user: UserModel = Depends(get_current_user)):
    if user.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user
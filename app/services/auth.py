from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.models.domain.user import UserModel
from app.models.schemas.user import UserCreate, UserLogin
from app.db.repositories.auth import AuthRepository

crypt_context = CryptContext(schemes=["sha256_crypt"])

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    def create_user(self, user: UserCreate):
        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=crypt_context.hash(user.password),
            role=user.role
        )
        return self.auth_repo.create_user(user_model)

    def authenticate_user(self, user: UserLogin, expires_in: int = 3600, refresh_expires_in: int = 7 * 24 * 3600):
        user_on_db = self.auth_repo.get_user_by_username(user.username)
        if user_on_db is None or not crypt_context.verify(user.password, user_on_db.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        payload = {"sub": user_on_db.username, "exp": exp, "type": "access"}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

        refresh_exp = datetime.now(timezone.utc) + timedelta(seconds=refresh_expires_in)
        refresh_token = str(uuid.uuid4())
        self.auth_repo.create_refresh_token(user_on_db.id, refresh_token, refresh_exp)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in, 
            "refresh_token": refresh_token,
            "refresh_expires_in": refresh_expires_in  
        }

    def verify_token(self, access_token: str):
        try:
            data = jwt.decode(access_token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
            if data.get("type") != "access":
                raise JWTError("Invalid token type")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

        user_on_db = self.auth_repo.get_user_by_username(data['sub'])
        if user_on_db is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
        return user_on_db

    def refresh_access_token(self, refresh_token: str, access_expires_in: int = 3600):
        token_model = self.auth_repo.get_refresh_token(refresh_token)
        if token_model is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        expires_at = token_model.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            self.auth_repo.delete_refresh_token(refresh_token)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        user_on_db = self.auth_repo.get_user_by_id(token_model.user_id)
        if user_on_db is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        access_exp = datetime.now(timezone.utc) + timedelta(seconds=access_expires_in)
        access_payload = {"sub": user_on_db.username, "exp": access_exp, "type": "access"}
        access_token = jwt.encode(access_payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

        self.auth_repo.delete_refresh_token(refresh_token)
        refresh_expires_in = 7 * 24 * 3600  
        refresh_exp = datetime.now(timezone.utc) + timedelta(seconds=refresh_expires_in)
        new_refresh_token = str(uuid.uuid4())
        self.auth_repo.create_refresh_token(user_on_db.id, new_refresh_token, refresh_exp)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_expires_in,  
            "refresh_token": new_refresh_token,
            "refresh_expires_in": refresh_expires_in  
        }
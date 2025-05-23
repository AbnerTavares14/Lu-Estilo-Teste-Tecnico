from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.models.schemas.user import UserCreate, UserLogin
from app.models.domain.user import UserModel
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()
crypt_context = CryptContext(schemes=["sha256_crypt"])
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

class UserManager:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int):
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def create_user(self, user: UserCreate):
        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=crypt_context.hash(user.password),
            role="user"
        )
        try:
            self.db.add(user_model)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        

    def authenticate_user(self, user: UserLogin, expires_in: int = 3600):
        user_on_db = self.db.query(UserModel).filter_by(username=user.username).first()
        if user_on_db is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not crypt_context.verify(user.password, user_on_db.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        payload = {
            "sub": user.username,
            "exp": exp
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": exp.isoformat()
        }
    
    def verify_token(self, access_token: str):
        try:
            data = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

        user_on_db = self.db.query(UserModel).filter_by(username=data['sub']).first()
        if user_on_db is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

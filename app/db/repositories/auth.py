from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.domain.user import UserModel
from app.models.domain.refresh_token import RefreshTokenModel
from passlib.context import CryptContext

crypt_context = CryptContext(schemes=["sha256_crypt"])

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_user_by_username(self, username: str):
        return self.db.query(UserModel).filter(UserModel.username == username).first()

    def create_user(self, username: str, email: str, password: str, role: str = "user"):
        user_model = UserModel(
            username=username,
            email=email,
            password_hash=crypt_context.hash(password),
            role=role
        )
        try:
            self.db.add(user_model)
            self.db.commit()
            return user_model
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    def create_refresh_token(self, user_id: int, token: str, expires_at):
        refresh_token = RefreshTokenModel(user_id=user_id, token=token, expires_at=expires_at)
        self.db.add(refresh_token)
        self.db.commit()
        return refresh_token

    def get_refresh_token(self, token: str):
        return self.db.query(RefreshTokenModel).filter_by(token=token).first()

    def delete_refresh_token(self, token: str):
        token_model = self.get_refresh_token(token)
        if token_model:
            self.db.delete(token_model)
            self.db.commit()
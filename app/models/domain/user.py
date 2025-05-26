from app.db.base import Base
from sqlalchemy import Column, Integer, String, Enum
from app.models.enum.user import UserRoleEnum

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRoleEnum, name="user_role_enum", create_type=False), 
                  nullable=False, 
                  default=UserRoleEnum.USER)
from app.db.base import Base
from sqlalchemy import Column, Integer, String

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    cpf = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True, unique=True, index=True)

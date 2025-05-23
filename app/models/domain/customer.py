# app/models/domain/customer.py
from app.db.base import Base
from sqlalchemy import Column, Integer, String

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    cpf = Column(String, unique=True, nullable=False, index=True)
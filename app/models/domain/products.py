from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, nullable=False, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=False)
    price = Column(Integer, index=True, nullable=False)
    bar_code = Column(String, index=True, nullable=False)
    section = Column(String, index=True, nullable=False)
    initial_stock = Column(Integer, index=True, nullable=False)
    validation_date = Column(DateTime, index=True, nullable=False)
    images = Column(String, index=True, nullable=False)


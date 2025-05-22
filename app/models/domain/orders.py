from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY
from sqlalchemy.sql import func
from app.db.base import Base

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, nullable=False, autoincrement=True)
    customer_id = Column(Integer, index=True, nullable=False)
    product_id = Column(Integer, index=True, nullable=False)
    products = Column(ARRAY(Integer), nullable=False)  # Store product IDs as an array of integers
    quantity = Column(Integer, nullable=False)
    status = Column(String, index=True, nullable=False)

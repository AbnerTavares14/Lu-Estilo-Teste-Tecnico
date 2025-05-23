from app.db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

class OrderProduct(Base):
    __tablename__ = "order_products"
    order_id = Column(Integer, ForeignKey("orders.id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity = Column(Integer, nullable=False)
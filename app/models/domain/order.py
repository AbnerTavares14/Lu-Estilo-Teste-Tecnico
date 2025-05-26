from app.db.base import Base
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float, CheckConstraint
from sqlalchemy.dialects.postgresql import ENUM as SAEnum 
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.enum.order import OrderStatus

OrderStatusEnum = SAEnum(
    OrderStatus,
    name="order_status",
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
    native_enum=True,
    create_type=False
)

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(OrderStatusEnum, nullable=False, default=OrderStatus.PENDING.value)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    total_amount = Column(Float, nullable=False, default=0.0)

    customer = relationship("CustomerModel")
    order_products = relationship("OrderProduct", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="check_total_amount_non_negative"),
    )

class OrderProduct(Base):
    __tablename__ = "order_products"
    order_id = Column(Integer, ForeignKey("orders.id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("OrderModel", back_populates="order_products")
    product = relationship("ProductModel")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_unit_price_non_negative"),
    )
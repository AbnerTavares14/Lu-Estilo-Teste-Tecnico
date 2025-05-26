from app.db.base import Base 
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from typing import List 

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False) 
    barcode = Column(String, unique=True, nullable=False, index=True)
    section = Column(String, nullable=False)
    stock = Column(Integer, nullable=False) 
    expiry_date = Column(Date, nullable=True) 
    images = relationship("ProductImageModel", back_populates="product", cascade="all, delete-orphan")

class ProductImageModel(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product = relationship("ProductModel", back_populates="images")

    def __repr__(self):
        return f"<ProductImageModel(id={self.id}, url='{self.url[:30]}...', product_id={self.product_id})>"
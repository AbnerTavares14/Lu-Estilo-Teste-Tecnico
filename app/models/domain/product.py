from app.db.base import Base
from sqlalchemy import Column, Integer, String, Float, Date

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    barcode = Column(String, unique=True, nullable=False, index=True)
    section = Column(String, nullable=False)
    stock = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=True)
    image_url = Column(String, nullable=True)
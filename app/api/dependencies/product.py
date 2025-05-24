from fastapi import Depends
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db_session
from app.services.products import ProductService
from app.db.repositories.products import ProductRepository

def get_product_repository(db: Session = Depends(get_db_session)):
    return ProductRepository(db)

def get_product_service(product_repo = Depends(get_product_repository)):
    return ProductService(product_repo)
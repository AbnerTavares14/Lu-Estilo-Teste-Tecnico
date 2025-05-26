from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db_session
from app.db.repositories.products import ProductRepository
from app.services.products import ProductService

def get_product_repository(db: Annotated[Session, Depends(get_db_session)]) -> ProductRepository:
    return ProductRepository(db)

def get_product_service(
    product_repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> ProductService:
    return ProductService(product_repository)
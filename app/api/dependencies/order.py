from fastapi import Depends
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db_session
from app.services.order import OrderService
from app.db.repositories.orders import OrderRepository
from app.db.repositories.products import ProductRepository
from app.db.repositories.customers import CustomerRepository

def get_order_repository(db: Session = Depends(get_db_session)):
    return OrderRepository(db)

def get_product_repository(db: Session = Depends(get_db_session)):
    return ProductRepository(db)

def get_customer_repository(db: Session = Depends(get_db_session)):
    return CustomerRepository(db)

def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository)
):
    return OrderService(order_repo, product_repo, customer_repo)
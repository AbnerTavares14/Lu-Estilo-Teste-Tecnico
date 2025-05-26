from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db_session
from app.api.dependencies.product import get_product_service 
from app.api.dependencies.customer import get_customer_repository
from app.services.products import ProductService

from app.db.repositories.orders import OrderRepository
from app.db.repositories.customers import CustomerRepository 
from app.services.order import OrderService
from app.services.whatsapp_service import WhatsappService
from app.api.dependencies.whatsapp import get_whatsapp_service

def get_order_repository(db: Annotated[Session, Depends(get_db_session)]) -> OrderRepository:
    return OrderRepository(db)

def get_order_service(
    order_repository: Annotated[OrderRepository, Depends(get_order_repository)],
    product_service: Annotated[ProductService, Depends(get_product_service)], 
    customer_repository: Annotated[CustomerRepository, Depends(get_customer_repository)], 
    whatsapp_service: Annotated[WhatsappService, Depends(get_whatsapp_service)] = None
) -> OrderService:
    return OrderService(order_repository, product_service, customer_repository, whatsapp_service)
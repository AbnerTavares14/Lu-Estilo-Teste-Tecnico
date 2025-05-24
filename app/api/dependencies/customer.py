from fastapi import Depends
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db_session
from app.services.customer import CustomerService
from app.db.repositories.customers import CustomerRepository


def get_customer_repository(db: Session = Depends(get_db_session)):
    return CustomerRepository(db)

def get_customer_service(customer_repo: CustomerRepository = Depends(get_customer_repository)):
    return CustomerService(customer_repo)
from typing import List
from sqlalchemy.orm import Session
from app.models.domain.customer import CustomerModel

class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_customers(self, order_by: str = None, skip: int = 0, limit: int = 100) -> List[CustomerModel]:
        query = self.db.query(CustomerModel)
        if order_by:
            query = query.order_by(getattr(CustomerModel, order_by))
        query = query.offset(skip).limit(limit)
        return query.all()

    def get_customer_by_id(self, id: int) -> CustomerModel:
        return self.db.query(CustomerModel).filter(CustomerModel.id == id).first()

    def get_customer_by_email(self, email: str) -> CustomerModel:
        return self.db.query(CustomerModel).filter(CustomerModel.email == email).first()

    def get_customer_by_cpf(self, cpf: str) -> CustomerModel:
        return self.db.query(CustomerModel).filter(CustomerModel.cpf == cpf).first()

    def create_customer(self, customer: CustomerModel) -> CustomerModel:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update_customer(self, customer: CustomerModel) -> CustomerModel:
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete_customer(self, id: int) -> None:
        customer = self.get_customer_by_id(id)
        if customer:
            self.db.delete(customer)
            self.db.commit()
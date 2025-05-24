from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.domain.customer import CustomerModel
from app.models.schemas.customer import CustomerResponse

class CustomerRepository:
    def __init__(self, db: Session): 
        self.db = db

    def get_customer_by_id(self, customer_id: int):
        return self.db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    
    def get_customers(self, order_by:str, skip: int = 0, limit: int = 100):
        if order_by == "name":
            customers = self.db.query(CustomerModel).offset(skip).limit(limit).order_by(CustomerModel.name).all()
        elif order_by == "email":
            customers = self.db.query(CustomerModel).offset(skip).limit(limit).order_by(CustomerModel.email).all()
        else:
            customers = self.db.query(CustomerModel).offset(skip).limit(limit).all()
        
        return [CustomerResponse.model_validate(customer) for customer in customers]

    def get_customer_by_email(self, email: str):
        return self.db.query(CustomerModel).filter(CustomerModel.email == email).first()

    def get_customer_by_cpf(self, cpf: str):
        return self.db.query(CustomerModel).filter(CustomerModel.cpf == cpf).first()
    
    def get_customer_by_name(self, name: str):
        return self.db.query(CustomerModel).filter(CustomerModel.name == name).first()

    def create_customer(self, name: str, email: str, cpf: str):
        customer_model = CustomerModel(
            name=name,
            email=email,
            cpf=cpf
        ) 
        try:
            self.db.add(customer_model)
            self.db.commit()
            return customer_model
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer already exists")
        
    def update_customer(self, customer_model: CustomerModel, name: str, email: str, cpf: str):
        customer_model.name = name
        customer_model.email = email
        customer_model.cpf = cpf
        self.db.commit()
        return customer_model

    def delete_customer(self, customer_model: CustomerModel):
        self.db.delete(customer_model)
        self.db.commit()
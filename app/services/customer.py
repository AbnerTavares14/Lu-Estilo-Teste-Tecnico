from app.db.repositories.customers import CustomerRepository
from fastapi import HTTPException, status
from app.models.schemas.customer import CustomerSchema

class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    def get_customer_by_id(self, customer_id: int):
        return self.customer_repository.get_customer_by_id(customer_id) 

    def get_customers(self, order_by: str, skip: int = 0, limit: int = 100):
        return self.customer_repository.get_customers(order_by, skip, limit)
    
    def create_customer(self, customer: CustomerSchema):
        email_already_registered = self.customer_repository.get_customer_by_email(customer.email)
        
        if email_already_registered is not None:
            print(email_already_registered.email)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        
        cpf_already_registered = self.customer_repository.get_customer_by_cpf(customer.cpf)
        
        if cpf_already_registered is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF already registered")
        return self.customer_repository.create_customer(
            name=customer.name,
            email=customer.email,
            cpf=customer.cpf
        )

    def update_customer(self, id: int, customer_with_update: CustomerSchema):
        customer_model = self.customer_repository.get_customer_by_id(id)
        if customer_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        email_already_registered = self.customer_repository.get_customer_by_email(customer_with_update.email)
        if email_already_registered is not None and email_already_registered.id != id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        
        cpf_already_registered = self.customer_repository.get_customer_by_cpf(customer_with_update.cpf)
        if cpf_already_registered is not None and cpf_already_registered.id != id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF already registered")
        

        return self.customer_repository.update_customer(
            customer_model, 
            customer_with_update.name, 
            customer_with_update.email, 
            customer_with_update.cpf
        )

    def delete_customer(self, id: int):
        customer = self.customer_repository.get_customer_by_id(id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return self.customer_repository.delete_customer(customer)
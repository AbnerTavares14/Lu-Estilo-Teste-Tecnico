from app.db.repositories.customers import CustomerRepository
from app.models.domain.customer import CustomerModel
from app.models.schemas.customer import CustomerSchema
from sqlalchemy.orm import Session

class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    def get_customers(self, order_by: str = None, skip: int = 0, limit: int = 100):
        return self.customer_repository.get_customers(order_by, skip, limit)

    def get_customer_by_id(self, id: int):
        return self.customer_repository.get_customer_by_id(id)

    def get_customer_by_email(self, email: str):
        return self.customer_repository.get_customer_by_email(email)

    def get_customer_by_cpf(self, cpf: str):
        return self.customer_repository.get_customer_by_cpf(cpf)

    def create_customer(self, client: CustomerSchema):
        customer = CustomerModel(
            name=client.name,
            email=client.email,
            cpf=client.cpf
        )
        return self.customer_repository.create_customer(customer)

    def update_customer(self, id: int, client: CustomerSchema):
        existing_client = self.customer_repository.get_customer_by_id(id)
        existing_client.name = client.name
        existing_client.email = client.email
        existing_client.cpf = client.cpf
        return self.customer_repository.update_customer(existing_client)

    def delete_customer(self, id: int):
        self.customer_repository.delete_customer(id)
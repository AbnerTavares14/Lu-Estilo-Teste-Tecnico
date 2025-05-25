from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.services.customer import CustomerService
from app.api.dependencies.customer import get_customer_service
from app.api.dependencies.auth import get_current_user
from app.models.schemas.customer import CustomerSchema, CustomerResponse

customer_route = APIRouter(prefix="/clients", tags=["Clients"], dependencies=[Depends(get_current_user)])

@customer_route.get("/", response_model=List[CustomerResponse])
def get_clients(
    order_by: str = None,
    skip: int = 0,
    limit: int = 100,
    customer_service: CustomerService = Depends(get_customer_service)
):
    clients = customer_service.get_customers(order_by=order_by, skip=skip, limit=limit)
    return [CustomerResponse.model_validate(client) for client in clients]

@customer_route.get("/{id}", response_model=CustomerResponse)
def get_client_by_id(
    id: int,
    customer_service: CustomerService = Depends(get_customer_service)
):
    client = customer_service.get_customer_by_id(id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerResponse.model_validate(client)

@customer_route.post("/", status_code=status.HTTP_201_CREATED)
def create_client(
    client: CustomerSchema,
    customer_service: CustomerService = Depends(get_customer_service)
):
    existing_email = customer_service.get_customer_by_email(client.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    existing_cpf = customer_service.get_customer_by_cpf(client.cpf)
    if existing_cpf:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF already registered")
    customer_service.create_customer(client)
    return {"message": "success"}

@customer_route.put("/{id}", response_model=CustomerResponse)
def update_client(
    id: int,
    client: CustomerSchema,
    customer_service: CustomerService = Depends(get_customer_service)
):
    existing_client = customer_service.get_customer_by_id(id)
    if not existing_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    existing_email = customer_service.get_customer_by_email(client.email)
    if existing_email and existing_email.id != id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    existing_cpf = customer_service.get_customer_by_cpf(client.cpf)
    if existing_cpf and existing_cpf.id != id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF already registered")
    updated_client = customer_service.update_customer(id, client)
    return CustomerResponse.model_validate(updated_client)

@customer_route.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    id: int,
    customer_service: CustomerService = Depends(get_customer_service)
):
    client = customer_service.get_customer_by_id(id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    customer_service.delete_customer(id)
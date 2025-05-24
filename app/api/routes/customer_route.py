from fastapi import APIRouter, Depends, Response, status
from starlette.responses import JSONResponse
from app.api.dependencies.customer import get_customer_service
from app.api.dependencies.auth import get_current_user
from app.services.customer import CustomerService
from typing import Optional
from app.models.schemas.customer import CustomerSchema
from fastapi.encoders import jsonable_encoder
from app.models.schemas.customer import CustomerResponse

customer_route = APIRouter(prefix="/clients", tags=["clients"], dependencies=[Depends(get_current_user)])

@customer_route.get("/")
def get_clients(
    limit: int = 10,
    skip: int = 0,
    customer_service: CustomerService = Depends(get_customer_service),
    order_by: Optional[str] = None,
):
    clients = customer_service.get_customers(order_by=order_by, skip=skip, limit=limit)
    return JSONResponse(
        content=jsonable_encoder(clients),
        status_code=status.HTTP_200_OK
    )


@customer_route.get("/{id}")
def get_client_by_id(
    id: int,
    customer_service: CustomerService = Depends(get_customer_service)
):
    client = CustomerResponse.model_validate(customer_service.get_customer_by_id(id))

    return JSONResponse(
        content=jsonable_encoder(client),
        status_code=status.HTTP_200_OK
    )

@customer_route.post("/")
def create_client(
    customer: CustomerSchema,
    customer_service: CustomerService = Depends(get_customer_service)
):
    customer_service.create_customer(customer)

    return JSONResponse(
        content={"message": "success"},
        status_code=status.HTTP_201_CREATED
    )

@customer_route.put("/{id}")
def update_client(
    id: int,
    customer: CustomerSchema,
    customer_service: CustomerService = Depends(get_customer_service)
):
    client = customer_service.update_customer(id=id, customer_with_update=customer)
    client = CustomerResponse.model_validate(client)

    return JSONResponse(
        content=jsonable_encoder(client),
        status_code=status.HTTP_200_OK
    )

@customer_route.delete("/{id}")
def delete_client(
    id: int,
    customer_service: CustomerService = Depends(get_customer_service)
):
    customer_service.delete_customer(id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
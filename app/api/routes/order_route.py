from fastapi import APIRouter, Depends, Response, status
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.order import get_order_service
from app.services.order import OrderService
from app.models.schemas.order import OrderCreate
from typing import Optional

order_route = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)])

@order_route.post("/")
def create_order(
    order: OrderCreate,
    order_service: OrderService = Depends(get_order_service)
):
    order_created = order_service.create_order(order)

    return JSONResponse(
        content=jsonable_encoder(order_created),
        status_code=status.HTTP_201_CREATED
)

@order_route.get("/")
def get_orders(
    limit: int = 10,
    skip: int = 0,
    order_service: OrderService = Depends(get_order_service),
    customer_id: Optional[int] = None,
    status_order: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    order_by: Optional[str] = "order_date",
    order_direction: Optional[str] = "desc",
):
    orders = order_service.get_orders(
        skip=skip, 
        limit=limit, 
        customer_id=customer_id,
        status=status_order,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        order_direction=order_direction
    )

    return JSONResponse(
        content=jsonable_encoder(orders),
        status_code=status.HTTP_200_OK
)

@order_route.get("/{id}")
def get_order_by_id(
    id: int,
    order_service: OrderService = Depends(get_order_service)
):
    order = order_service.get_order_by_id(id)

    return JSONResponse(
        content=jsonable_encoder(order),
        status_code=status.HTTP_200_OK
)
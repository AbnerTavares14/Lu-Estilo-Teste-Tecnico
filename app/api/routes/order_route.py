from fastapi import APIRouter, Depends, Response, status, Query
from typing import List, Optional
from datetime import date as PyDate 

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.order import get_order_service 
from app.services.order import OrderService
from app.models.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate

order_route = APIRouter(
    prefix="/orders",
    tags=["Orders"], 
    dependencies=[Depends(get_current_user)] 
)

@order_route.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_new_order( 
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service)
):
    order_model = order_service.create_order(order_data)
    return order_model 

@order_route.get("/", response_model=List[OrderResponse])
def list_orders( 
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    customer_id: Optional[int] = Query(None, ge=1),
    status_filter: Optional[str] = Query(None, alias="status"), 
    start_date: Optional[str] = Query(None, description="Format YYYY-MM-DD"), 
    end_date: Optional[str] = Query(None, description="Format YYYY-MM-DD"),   
    order_by: Optional[str] = Query("created_at", description="Field to order by, e.g., 'created_at', 'total_amount'"),
    order_direction: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    product_section: Optional[str] = Query(None, alias="section"), 
    order_service: OrderService = Depends(get_order_service)
):
    order_models = order_service.get_orders(
        skip=skip, limit=limit, customer_id=customer_id, status_filter=status_filter,
        start_date_str=start_date, end_date_str=end_date, 
        order_by_field=order_by, order_direction=order_direction, product_section=product_section
    )
    return order_models

@order_route.get("/{order_id}", response_model=OrderResponse) 
def retrieve_order( 
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
):
    order_model = order_service.get_order_by_id(order_id)
    return order_model

@order_route.put("/{order_id}", response_model=OrderResponse) 
def update_existing_order( 
    order_id: int,
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service)
):
    order_model = order_service.update_order(order_id, order_data)
    return order_model

@order_route.patch("/{order_id}/status", response_model=OrderResponse) 
def update_order_status_only( 
    order_id: int,
    status_update_data: OrderStatusUpdate,
    order_service: OrderService = Depends(get_order_service)
):
    order_model = order_service.update_order_status(order_id, status_update_data)
    return order_model

@order_route.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT) 
def remove_order( 
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
):
    order_service.delete_order(order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
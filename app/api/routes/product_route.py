from fastapi import APIRouter, Depends, Response, status
from typing import List, Optional

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.product import get_product_service
from app.api.dependencies.permissions import require_admin
from app.services.products import ProductService
from app.models.schemas.product import ProductSchema, ProductResponse

product_route = APIRouter(
    prefix="/products",
    tags=["Products"], 
    dependencies=[Depends(get_current_user)]
)

@product_route.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 10,
    section: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available: Optional[bool] = None,
    product_service: ProductService = Depends(get_product_service),
):
    product_models = product_service.get_products(
        skip=skip, limit=limit, section=section,
        min_price=min_price, max_price=max_price, available=available
    )
    return product_models

@product_route.get("/{product_id}", response_model=ProductResponse)
def retrieve_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    product_model = product_service.get_product_by_id(product_id)
    return product_model

@product_route.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_new_product(
    product_data: ProductSchema, 
    product_service: ProductService = Depends(get_product_service)
):
    created_product_model = product_service.create_product(product_data)
    return created_product_model

@product_route.put("/{product_id}", response_model=ProductResponse, dependencies=[Depends(require_admin)])
def update_existing_product(
    product_id: int,
    product_update_data: ProductSchema,
    product_service: ProductService = Depends(get_product_service)
):
    updated_product_model = product_service.update_product(
        product_id=product_id,
        product_update_data=product_update_data
    )
    return updated_product_model 

@product_route.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def remove_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    product_service.delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
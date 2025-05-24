from fastapi import APIRouter, Depends, Response, status
from starlette.responses import JSONResponse
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.product import get_product_service
from app.services.products import ProductService
from typing import Optional
from app.models.schemas.product import ProductSchema
from fastapi.encoders import jsonable_encoder
from app.models.schemas.product import ProductResponse


product_route = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(get_current_user)])

@product_route.get("/")
def get_products(
    limit: int = 10,
    skip: int = 0,
    product_service: ProductService = Depends(get_product_service),
    section: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available: Optional[bool] = None,
):
    products = product_service.get_products(
        skip=skip, 
        limit=limit, 
        section=section,
        min_price=min_price,
        max_price=max_price,
        available=available
    )
    
    return JSONResponse(
        content=jsonable_encoder(products),
        status_code=status.HTTP_200_OK
    )


@product_route.get("/{id}")
def get_product_by_id(
    id: int,
    product_service: ProductService = Depends(get_product_service)
):
    product = ProductResponse.model_validate(product_service.get_product_by_id(id))

    return JSONResponse(
        content=jsonable_encoder(product),
        status_code=status.HTTP_200_OK
    )

@product_route.post("/")
def create_product(
    product: ProductSchema,
    product_service: ProductService = Depends(get_product_service)
):
    product_service.create_product(product)

    return JSONResponse(
        content={"message": "success"},
        status_code=status.HTTP_201_CREATED
    )

@product_route.put("/{id}")
def update_product(
    id: int,
    product: ProductSchema,
    product_service: ProductService = Depends(get_product_service)
):
    product = product_service.update_product(id=id, product_with_update=product)
    product = ProductResponse.model_validate(product)

    return JSONResponse(
        content=jsonable_encoder(product),
        status_code=status.HTTP_200_OK
    )

@product_route.delete("/{id}")
def delete_product(
    id: int,
    product_service: ProductService = Depends(get_product_service)
):
    product_service.delete_product(id)

    return JSONResponse(
        content={"message": "success"},
        status_code=status.HTTP_200_OK
    )
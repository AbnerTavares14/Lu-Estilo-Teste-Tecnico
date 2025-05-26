from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.db.repositories.products import ProductRepository
from app.models.domain.product import ProductModel
from app.models.schemas.product import ProductSchema

class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def get_product_by_id(self, product_id: int) -> ProductModel:
        product = self.product_repository.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        section: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        available: Optional[bool] = None,
    ) -> List[ProductModel]:
        return self.product_repository.get_products(
            skip=skip,
            limit=limit,
            section=section,
            min_price=min_price,
            max_price=max_price,
            available=available
        )

    def create_product(self, product_create_data: ProductSchema) -> ProductModel:
        barcode_already_registered = self.product_repository.get_product_by_barcode(
            product_create_data.barcode
        )

        if barcode_already_registered:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Barcode already registered"
            )
        
        try:
            return self.product_repository.create_product(product_create_data)
        except IntegrityError: 
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Barcode already registered (DB integrity)"
            )


    def update_product(self, product_id: int, product_update_data: ProductSchema) -> ProductModel:
        product_to_update = self.get_product_by_id(product_id) 

        if product_update_data.barcode != product_to_update.barcode:
            barcode_already_registered = self.product_repository.get_product_by_barcode(product_update_data.barcode)
            if barcode_already_registered: 
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Barcode already registered for another product"
                )
        try:
            return self.product_repository.update_product(product_to_update, product_update_data)
        except IntegrityError: 
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Update failed due to data conflict (e.g., barcode already exists for another product - DB integrity)"
            )


    def update_product_stock(self, product_id: int, quantity_change: int, increase: bool = False) -> ProductModel:
        product = self.get_product_by_id(product_id) 
        if not increase: 
            if quantity_change < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity to decrease must be non-negative")
            if product.stock < quantity_change:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
            new_stock_level = product.stock - quantity_change
        else: 
            if quantity_change < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity to increase must be non-negative")
            new_stock_level = product.stock + quantity_change
        
        return self.product_repository.update_stock(product, new_stock_level)

    def delete_product(self, product_id: int) -> None:
        product_to_delete = self.get_product_by_id(product_id)
        self.product_repository.delete_product(product_to_delete)
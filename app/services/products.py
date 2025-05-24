from typing import List, Optional
from app.db.repositories.products import ProductRepository
from fastapi import HTTPException, status
from app.models.schemas.product import ProductSchema, ProductResponse


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def get_product_by_id(self, product_id: int):
        return self.product_repository.get_product_by_id(product_id)
    
    def get_products(
            self, 
            skip: int = 0, 
            limit: int = 100, 
            section: Optional[str] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            available: Optional[bool] = None,
    ) -> List[ProductResponse]:
        return self.product_repository.get_products(
            skip=skip, 
            limit=limit, 
            section=section,
            min_price=min_price,
            max_price=max_price,
            available=available
        )
        
    def create_product(self, product: ProductSchema) -> ProductResponse:
        barcode_already_registered = self.product_repository.get_product_by_barcode(product.barcode)
        
        if barcode_already_registered is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already registered")
        
        return self.product_repository.create_product(product)
    
    def update_product(self, id: int, product_with_update: ProductSchema) -> ProductResponse:
        product_model = self.product_repository.get_product_by_id(id)
        if product_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        barcode_already_registered = self.product_repository.get_product_by_barcode(product_with_update.barcode)
        if barcode_already_registered is not None and barcode_already_registered.id != id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already registered")
        
        return self.product_repository.update_product(id, product_with_update)
    
    def delete_product(self, id: int):
        product = self.product_repository.get_product_by_id(id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return self.product_repository.delete_product(product)
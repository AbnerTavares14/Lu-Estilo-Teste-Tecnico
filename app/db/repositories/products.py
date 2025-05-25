from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.domain.product import ProductModel
from app.models.schemas.product import ProductSchema, ProductResponse

class ProductRepository:
    def __init__(self, db: Session): 
        self.db = db

    def get_product_by_id(self, product_id: int) -> ProductResponse:
        return self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
    
    def get_product_by_barcode(self, barcode: str) -> ProductResponse:
        return self.db.query(ProductModel).filter(ProductModel.barcode == barcode).first()
    
    def get_products(
            self, 
            skip: int, 
            limit: int, 
            section: Optional[str] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            available: Optional[bool] = None,
    ) -> List[ProductResponse]:
        
        query = self.db.query(ProductModel)

        if section:
            query = query.filter(ProductModel.section == section)

        if min_price is not None:
            query = query.filter(ProductModel.price >= min_price)
        
        if max_price is not None:
            query = query.filter(ProductModel.price <= max_price)
        
        if available is not None:
            if available:
                query = query.filter(ProductModel.stock > 0)
            else:
                query = query.filter(ProductModel.stock == 0)
        
        products = query.offset(skip).limit(limit).all()
        return [ProductResponse.model_validate(product) for product in products]
    
    def create_product(self, product: ProductSchema) -> ProductResponse:
        try:
            db_product = ProductModel(**product.model_dump())
            self.db.add(db_product)
            self.db.commit()
            self.db.refresh(db_product)
            return ProductResponse.model_validate(db_product)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this barcode already exists."
            )
        
    
    def update_product(self, product_id: int, product: ProductSchema) -> ProductResponse:
        db_product = self.get_product_by_id(product_id)

        for key, value in product.model_dump().items():
            setattr(db_product, key, value)
        
        self.db.commit()
        self.db.refresh(db_product)
        return ProductResponse.model_validate(db_product)
    

    def update_stock(self, product: ProductModel) -> ProductResponse:
        db_product = self.get_product_by_id(product.id)
        db_product.stock = product.stock
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete_product(self, product: ProductModel) -> None:
        self.db.delete(product)
        self.db.commit()
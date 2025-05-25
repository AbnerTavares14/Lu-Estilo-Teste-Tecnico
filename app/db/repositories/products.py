from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.domain.product import ProductModel
from app.models.schemas.product import ProductSchema 

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_product_by_id(self, product_id: int) -> Optional[ProductModel]:
        return self.db.query(ProductModel).filter(ProductModel.id == product_id).first()

    def get_product_by_barcode(self, barcode: str) -> Optional[ProductModel]:
        return self.db.query(ProductModel).filter(ProductModel.barcode == barcode).first()

    def get_products(
        self,
        skip: int,
        limit: int,
        section: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        available: Optional[bool] = None,
    ) -> List[ProductModel]:

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
        
        products = query.order_by(ProductModel.id).offset(skip).limit(limit).all() 
        return products

    def create_product(self, product_data: ProductSchema) -> ProductModel:
        db_product = ProductModel(**product_data.model_dump())
        try:
            self.db.add(db_product)
            self.db.commit()
            self.db.refresh(db_product)
            return db_product
        except IntegrityError:
            self.db.rollback()
            raise 

    def update_product(
        self,
        db_product: ProductModel,
        product_update_data: ProductSchema 
    ) -> ProductModel:
        
        update_data_dict = product_update_data.model_dump(exclude_unset=True)
        for key, value in update_data_dict.items():
            setattr(db_product, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(db_product)
            return db_product
        except IntegrityError: 
            self.db.rollback()
            raise 

    def update_stock(self, product_to_update: ProductModel, new_stock_level: int) -> ProductModel:
        product_to_update.stock = new_stock_level
        self.db.commit()
        self.db.refresh(product_to_update)
        return product_to_update

    def delete_product(self, product_to_delete: ProductModel) -> None:
        self.db.delete(product_to_delete)
        self.db.commit()
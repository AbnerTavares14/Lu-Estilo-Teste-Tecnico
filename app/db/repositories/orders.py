from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date as PyDate, timedelta 

from app.models.domain.order import OrderModel, OrderProduct
from app.models.domain.product import ProductModel


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order_model_data: OrderModel, order_product_models_data: List[OrderProduct]) -> OrderModel:
        try:
            self.db.add(order_model_data)
            self.db.flush()  

            for op_model in order_product_models_data:
                op_model.order_id = order_model_data.id 
            
            self.db.add_all(order_product_models_data)
            self.db.commit()
            self.db.refresh(order_model_data) 

            # mas se for, esta é a forma.
            # return self.get_order_by_id_internal(order_model_data.id) # Chama um método interno para recarregar com selectinload
            return order_model_data # Retorna o objeto já com ID e persistido. Relações podem ser carregadas por lazy/explicitamente.
        except IntegrityError:
            self.db.rollback()
            raise 

    def get_order_by_id_internal(self, order_id: int, load_relations: bool = True) -> Optional[OrderModel]:
        query = self.db.query(OrderModel)
        if load_relations:
            query = query.options(
                selectinload(OrderModel.customer), 
                selectinload(OrderModel.order_products).selectinload(OrderProduct.product)
            )
        return query.filter(OrderModel.id == order_id).first()

    def get_order_by_id(self, order_id: int) -> Optional[OrderModel]:
        return self.get_order_by_id_internal(order_id, load_relations=True)


    def get_orders(
        self,
        limit: int = 100,
        skip: int = 0,
        customer_id: Optional[int] = None,
        status_filter: Optional[str] = None, 
        start_date: Optional[PyDate] = None, 
        end_date: Optional[PyDate] = None,
        order_by_field: str = "created_at", 
        order_direction: str = "desc",
        product_section: Optional[str] = None 
    ) -> List[OrderModel]:
        query = self.db.query(OrderModel).options(
            selectinload(OrderModel.customer),
            selectinload(OrderModel.order_products).selectinload(OrderProduct.product)
        )

        if customer_id is not None:
            query = query.filter(OrderModel.customer_id == customer_id)
        if status_filter is not None:
            query = query.filter(OrderModel.status == status_filter)
        if start_date is not None:
            query = query.filter(OrderModel.created_at >= start_date)
        if end_date is not None:
            query = query.filter(OrderModel.created_at < (end_date + timedelta(days=1)))
        if product_section is not None:
            query = query.join(OrderModel.order_products).join(OrderProduct.product).filter(ProductModel.section == product_section).distinct()


        # Order by
        order_column = getattr(OrderModel, order_by_field, OrderModel.created_at)
        if order_direction == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())

        orders = query.offset(skip).limit(limit).all()
        return orders
    
    def update_order_status(self, order_to_update: OrderModel, new_status: str) -> OrderModel:
        order_to_update.status = new_status
        self.db.commit()
        self.db.refresh(order_to_update)
        return order_to_update
    
    def update_order(
        self, 
        order_to_update: OrderModel, 
        new_customer_id: int,
        new_status: str,
        new_total_amount: float,
        new_order_products: List[OrderProduct]
        ) -> OrderModel:
        try:
            order_to_update.customer_id = new_customer_id
            order_to_update.status = new_status
            order_to_update.total_amount = new_total_amount

            for op in list(order_to_update.order_products): 
                self.db.delete(op)
            self.db.flush() 

            order_to_update.order_products = new_order_products 
            for op_model in new_order_products:
                op_model.order_id = order_to_update.id 

            self.db.commit()
            self.db.refresh(order_to_update) 

            return self.get_order_by_id_internal(order_to_update.id, load_relations=True)
        except IntegrityError:
            self.db.rollback()
            raise

    def delete_order(self, order_to_delete: OrderModel) -> None:
        self.db.delete(order_to_delete)
        self.db.commit()
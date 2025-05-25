from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, logger, status
from app.models.domain.order import OrderModel, OrderProduct
from app.models.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from typing import List, Dict

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order: OrderCreate, total_amount: float, order_items: List[Dict]) -> OrderResponse:
        try:
            db_order = OrderModel(
                customer_id=order.customer_id,
                status=order.status,
                total_amount=total_amount
            )
            self.db.add(db_order)
            self.db.flush() 

            order_products = [
                OrderProduct(
                    order_id=db_order.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"]
                )
                for item in order_items
            ]
            self.db.add_all(order_products)
            self.db.commit()

            db_order = self.db.query(OrderModel).options(
                selectinload(OrderModel.order_products).selectinload(OrderProduct.product)
            ).filter(OrderModel.id == db_order.id).first()

            return OrderResponse.model_validate(db_order)
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Failed to create order: {str(e.orig)}"
            )

    def get_order_by_id(self, order_id: int) -> OrderResponse:
        order = self.db.query(OrderModel).options(
            selectinload(OrderModel.order_products).selectinload(OrderProduct.product)
        ).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return OrderResponse.model_validate(order)

    def get_orders(
        self,
        limit: int = 100,
        skip: int = 0,
        customer_id: int = None,
        status: str = None,
        start_date: str = None,
        end_date: str = None,
        order_by: str = "created_at",
        order_direction: str = "desc",
        section: str = None
    ) -> List[OrderResponse]:
        print(status)
        query = self.db.query(OrderModel).options(
            selectinload(OrderModel.order_products).selectinload(OrderProduct.product)
        )

        if customer_id is not None:
            query = query.filter(OrderModel.customer_id == customer_id)

        if status is not None:
            query = query.filter(OrderModel.status == status)

        if start_date is not None:
            query = query.filter(OrderModel.created_at >= start_date)

        if end_date is not None:
            query = query.filter(OrderModel.created_at <= end_date)

        if section is not None:
            query = query.filter(OrderModel.section == section)

        if order_by == "created_at":
            if order_direction == "asc":
                query = query.order_by(OrderModel.created_at.asc())
            else:
                query = query.order_by(OrderModel.created_at.desc())

        orders = query.offset(skip).limit(limit).all()
        return [OrderResponse.model_validate(order) for order in orders]
    
    def update_order_status(self, order_id: int, status: OrderStatusUpdate) -> OrderResponse:
        order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        order.status = status.status
        self.db.commit()
        self.db.refresh(order)
        
        return OrderResponse.model_validate(order)
    
    def update_order(self, order_id: int, total_amount: float, order_items: List[Dict], order_data: OrderCreate) -> OrderResponse:
        try:
            order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            order.customer_id = order_data.customer_id
            order.status = order_data.status
            order.total_amount = total_amount

            order.order_products = [
                OrderProduct(
                    order_id=order.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"]
                )
                for item in order_items
            ]

            self.db.commit()
            self.db.refresh(order)

            order = self.db.query(OrderModel).options(
                selectinload(OrderModel.order_products).selectinload(OrderProduct.product)
            ).filter(OrderModel.id == order_id).first()


            return OrderResponse.model_validate(order)
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Failed to update order: {str(e.orig)}"
            )

    def delete_order(self, order_id: int) -> None:
        order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        self.db.delete(order)
        self.db.commit()
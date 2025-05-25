from typing import List
from fastapi import HTTPException, status as http_status
from app.db.repositories.orders import OrderRepository
from app.db.repositories.products import ProductRepository
from app.db.repositories.customers import CustomerRepository
from app.models.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate

class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        customer_repository: CustomerRepository
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.customer_repository = customer_repository

    def create_order(self, order: OrderCreate) -> OrderResponse:
        customer = self.customer_repository.get_customer_by_id(order.customer_id)
        if not customer:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        total_amount = 0.0
        order_items = []
        for item in order.products:
            product = self.product_repository.get_product_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item.product_id} not found"
                )
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product ID {item.product_id}"
                )
            
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": product.price
            })
            total_amount += product.price * item.quantity

            product.stock -= item.quantity
            self.product_repository.update_stock(product)


        db_order = self.order_repository.create_order(order, total_amount, order_items)

        db_order.customer_name = customer.name if customer else None
        return db_order

    def get_order_by_id(self, order_id: int) -> OrderResponse:
        order = self.order_repository.get_order_by_id(order_id)
        customer = self.customer_repository.get_customer_by_id(order.customer_id)
        if not order:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        order.customer_name = customer.name if customer else None
        return order 
    

    def get_orders(
        self,
        limit: int = 100,
        skip: int = 0,
        customer_id: int = None,
        status: str = None,
        start_date: str = None,
        end_date: str = None,
        order_by: str = "order_date",
        order_direction: str = "desc",
        section: str = None
        
    ) -> List[OrderResponse]:
        if status is not None:
            valid_statuses = ["pending", "processing", "completed", "canceled"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Status must be one of {valid_statuses}"
                )
        orders = self.order_repository.get_orders(
            limit=limit,
            skip=skip,
            customer_id=customer_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            order_by=order_by,
            order_direction=order_direction,
            section=section
        )
        for order in orders:
            customer = self.customer_repository.get_customer_by_id(order.customer_id)
            order.customer_name = customer.name if customer else None
        return orders
    
    def update_order(self, order_id: int, order: OrderCreate) -> OrderResponse:
        existing_order = self.order_repository.get_order_by_id(order_id)
        if not existing_order:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        customer = self.customer_repository.get_customer_by_id(order.customer_id)
        if not customer:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        for product_response in existing_order.products:
            product = self.product_repository.get_product_by_id(product_response.product.id)
            if product:
                product.stock += product_response.quantity
                self.product_repository.update_stock(product)

        total_amount = 0.0
        order_items = []
        for item in order.products:
            product = self.product_repository.get_product_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item.product_id} not found"
                )
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product ID {item.product_id}"
                )
            total_amount += product.price * item.quantity
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": product.price
            })
            product.stock -= item.quantity
            self.product_repository.update_stock(product)

        db_order = self.order_repository.update_order(order_id, total_amount, order_items, order_data=order)

        db_order.customer_name = customer.name
        return db_order
    
    def delete_order(self, order_id: int) -> None:
        existing_order = self.order_repository.get_order_by_id(order_id)
        if not existing_order:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        self.order_repository.delete_order(order_id)

        for item in existing_order.products:
            product = self.product_repository.get_product_by_id(item.product.id)
            if product:
                product.stock += item.quantity
                self.product_repository.update_stock(product)

    
    def update_order_status(self, order_id: int, status: OrderStatusUpdate) -> OrderResponse:
        existing_order = self.order_repository.get_order_by_id(order_id)
        if not existing_order:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        updated_order = self.order_repository.update_order_status(order_id, status)
        return updated_order
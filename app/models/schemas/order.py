from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import List, Optional
from app.models.schemas.product import ProductResponse

class OrderProductCreate(BaseModel):
    product_id: int
    quantity: int

    @field_validator('product_id')
    def validate_product_id(cls, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Product ID must be a positive integer")
        return value

    @field_validator('quantity')
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError("Quantity must be positive")
        return value

class OrderCreate(BaseModel):
    customer_id: int
    status: str = "pending"
    products: List[OrderProductCreate]

    @field_validator('customer_id')
    def validate_customer_id(cls, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Customer ID must be a positive integer")
        return value

    @field_validator('status')
    def validate_status(cls, value):
        valid_statuses = ["pending", "processing", "completed", "canceled"]
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return value

    @field_validator('products')
    def validate_products(cls, value):
        if not value:
            raise ValueError("At least one product must be included in the order")
        return value

class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator('status')
    def validate_status(cls, value):
        valid_statuses = ["pending", "processing", "completed", "canceled"]
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return value


class OrderProductResponse(BaseModel):
    product: ProductResponse
    quantity: int

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    status: str
    total_amount: float
    products: List[OrderProductResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def map_order_products_to_products(cls, data):
        if isinstance(data, dict) and 'order_products' in data:
            data['products'] = [
                {'product': op['product'], 'quantity': op['quantity']}
                for op in data['order_products']
            ]
            del data['order_products']
        elif hasattr(data, 'order_products'):
            data.products = [
                OrderProductResponse(product=op.product, quantity=op.quantity)
                for op in data.order_products
            ]
        return data

    class Config:
        from_attributes = True
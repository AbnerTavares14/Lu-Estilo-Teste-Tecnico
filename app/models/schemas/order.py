from typing import List
from pydantic import BaseModel, Field, field_validator

class OrderSchema(BaseModel):
    customer_id: int = Field(..., description="The unique identifier for the user.")
    product_id: List[int] = Field(..., description="The unique identifier for the product.")
    quantity: int = Field(..., gt=0, description="The quantity of the product.")
    order_date: str = Field(..., description="The date of the order.")
    status: str = Field(..., description="The status of the order.") 

    @field_validator('order_date')
    def validate_order_date(cls, value):
        if not value.isalnum():
            raise ValueError("Order date must be alphanumeric.")
        return value

    @field_validator('status')
    def validate_status(cls, value):
        if not value.isalnum():
            raise ValueError("Status must be alphanumeric.")
        return value

    @field_validator('customer_id')
    def validate_customer_id(cls, value):
        if not isinstance(value, int):
            raise ValueError("Customer ID must be an integer.")
        return value

    @field_validator('product_id')
    def validate_product_id(cls, value):
        if not isinstance(value, int):
            raise ValueError("Product ID must be an integer.")
        return value

    @field_validator('quantity')
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return value
    
class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    product_id: List[int]
    product_description: str
    status: str
    total_price: float
    quantity: int
    created_at: str

    class Config:
        from_attributes = True

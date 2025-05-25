from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import List, Optional
from app.models.schemas.product import ProductResponse
from enum import Enum as PyEnum

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
    product: ProductResponse  # O produto em si
    quantity: int             # A quantidade deste produto no pedido
    unit_price: float         # O preço unitário do produto no momento do pedido

    model_config = ConfigDict(from_attributes=True)

    # Adicionar um model_validator para popular unit_price do OrderProduct
    @model_validator(mode='before')
    @classmethod
    def populate_unit_price_from_orm(cls, data):
        if hasattr(data, 'unit_price') and hasattr(data, 'product') and hasattr(data, 'quantity'):
             # 'data' aqui é uma instância de OrderProduct (ORM)
            return {
                'product': data.product, # Será convertido para ProductResponse
                'quantity': data.quantity,
                'unit_price': data.unit_price # Preço unitário do OrderProduct
            }
        return data


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None # Nome do cliente, populado pelo serviço
    status: str
    total_amount: float
    products: List[OrderProductResponse] # Lista dos produtos no pedido
    created_at: datetime
    updated_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def prepare_data_from_orm(cls, data):
        # Se 'data' é um objeto ORM (OrderModel)
        if hasattr(data, 'order_products') and hasattr(data, 'customer'):
            prepared_data = {
                'id': data.id,
                'customer_id': data.customer_id,
                'customer_name': data.customer.name if data.customer else None,
                'status': data.status.value if isinstance(data.status, PyEnum) else data.status, # Garante que o valor do Enum seja usado
                'total_amount': data.total_amount,
                'products': data.order_products, # Passa a lista de OrderProduct (ORM)
                'created_at': data.created_at,
                'updated_at': data.updated_at
            }
            return prepared_data
        # Se 'data' já for um dict (ex: vindo de um jsonable_encoder anterior)
        elif isinstance(data, dict) and 'order_products' in data:
            data['products'] = data.pop('order_products')
            if 'customer' in data and isinstance(data['customer'], dict):
                 data['customer_name'] = data['customer'].get('name')
            # Garantir que o status seja o valor string
            if 'status' in data and hasattr(data['status'], 'value'): # se for um enum
                data['status'] = data['status'].value
        return data

    model_config = ConfigDict(from_attributes=True)
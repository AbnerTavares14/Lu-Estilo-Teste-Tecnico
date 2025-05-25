from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProductSchema(BaseModel):
    description: str = Field(..., min_length=1, max_length=255, description="The description of the product.")
    price: float = Field(..., gt=0, description="The price of the product.")
    barcode: str = Field(..., min_length=1, max_length=255, description="The barcode of the product.")
    section: str = Field(..., min_length=1, max_length=255, description="The section of the product.")
    stock: int = Field(..., gt=0, description="The stock of the product.")
    expiry_date: Optional[date] = None
    image_url: str = Field(..., description="The image URL of the product.")
    
    @field_validator('price')
    def validate_price(cls, value):
        if value <= 0:
            raise ValueError("Price must be greater than 0.")
        return value

    @field_validator('barcode')
    def validate_barcode(cls, value):
        if not value.isalnum():
            raise ValueError("Barcode must be alphanumeric.")
        return value
    
    @field_validator('section')
    def validate_section(cls, value):
        if not value.isalnum():
            raise ValueError("Section must be alphanumeric.")
        return value
    
    @field_validator('stock')
    def validate_stock(cls, value):
        if value <= 0:
            raise ValueError("Stock must be greater than 0.")
        return value
    
    @field_validator('expiry_date', mode='before')
    def validate_expiry_date(cls, value):
        if value is None:
            return value
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("Expiry date must be a valid date in ISO format (YYYY-MM-DD).")
        raise ValueError("Expiry date must be a valid date string or None.")

    @field_validator('image_url')
    def validate_image_url(cls, value):
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError("Image URL must start with 'http://' or 'https://'.")
        return value
    

class ProductResponse(BaseModel):
    id: int
    description: str
    price: float
    barcode: str
    section: str
    stock: int
    expiry_date: Optional[date]
    image_url: str

    model_config = ConfigDict(from_attributes=True)
from datetime import date
from typing import Optional, List # Adicionar List
from pydantic import BaseModel, ConfigDict, Field, field_validator, HttpUrl 

class ProductImageSchema(BaseModel): 
    id: int
    url: HttpUrl 

    model_config = ConfigDict(from_attributes=True)

class ProductSchema(BaseModel): 
    description: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0) 
    barcode: str = Field(..., min_length=1, max_length=255)
    section: str = Field(..., min_length=1, max_length=255)
    stock: int = Field(..., ge=0) 
    expiry_date: Optional[date] = None
    image_urls: List[HttpUrl] = Field(default_factory=list, description="List of image URLs for the product.")


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
        if not value.replace(" ", "").isalnum(): 
             raise ValueError("Section must contain only alphanumeric characters and spaces.")
        return value.strip()
    
    @field_validator('stock')
    def validate_stock(cls, value):
        if value < 0: 
            raise ValueError("Stock must be greater than or equal to 0.")
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

    @field_validator('image_urls', mode='before') 
    def validate_image_urls(cls, value):
        if not isinstance(value, list):
            raise ValueError("image_urls must be a list.")
        return value
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Calça Jeans Slim Fit",
                "price": 189.90,
                "barcode": "7899876543210",
                "section": "Jeans",
                "stock": 75,
                "expiry_date": None, 
                "image_urls": [
                    "https://example.com/images/calca_jeans_frente.jpg",
                    "https://example.com/images/calca_jeans_detalhe.jpg"
                ]
            }
        }
    )

class ProductResponse(BaseModel): 
    id: int
    description: str
    price: float
    barcode: str
    section: str
    stock: int
    expiry_date: Optional[date]
    images: List[ProductImageSchema] = [] 

    model_config = ConfigDict(from_attributes=True)
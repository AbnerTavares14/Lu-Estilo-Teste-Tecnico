from pydantic import BaseModel, Field, field_validator

class Product(BaseModel):
    description: str = Field(..., min_length=1, max_length=255, description="The description of the product.")
    price: float = Field(..., gt=0, description="The price of the product.")
    barcode: str = Field(..., min_length=1, max_length=255, description="The barcode of the product.")
    section: str = Field(..., min_length=1, max_length=255, description="The section of the product.")
    stock: int = Field(..., gt=0, description="The stock of the product.")
    expiry_date: str = Field(..., description="The expiry date of the product.")
    image_url: str = Field(..., description="The image URL of the product.")

    @field_validator('description')
    def validate_description(cls, value):
        if not value.replace(" ", "").isalpha():
            raise ValueError("Description must contain only alphabetic characters and spaces.")
        if len(value) < 10:
            raise ValueError("Description must be at least 10 characters long.")
        return value
    
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
    
    @field_validator('expiry_date')
    def validate_expiry_date(cls, value):
        if not value.isalnum():
            raise ValueError("Expiry date must be alphanumeric.")
        return value

    @field_validator('image_url')
    def validate_image_url(cls, value):
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError("Image URL must start with 'http://' or 'https://'.")
        return value
from pydantic import BaseModel, Field, field_validator

class Customer(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The name of the customer.")
    email: str = Field(..., min_length=1, max_length=100, description="The email of the customer.")
    cpf: str = Field(..., min_length=1, max_length=15, description="The CPF of the customer.")

    @field_validator('name')
    def validate_name(cls, value):
        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only alphabetic characters and spaces.")
        return value
    
    @field_validator('email')
    def validate_email(cls, value):
        if not value.endswith('@example.com'):
            raise ValueError("Email must be from the domain 'example.com'.")
        return value
    
    @field_validator('cpf')
    def validate_cpf(cls, value):
        if not value.isdigit():
            raise ValueError("CPF must contain only digits.")
        if len(value) != 11:
            raise ValueError("CPF must be 11 digits long.")
        return value
    
    
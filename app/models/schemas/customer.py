from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
import re

class CustomerSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The name of the customer.")
    email: EmailStr = Field(..., min_length=1, max_length=100, description="The email of the customer.")
    cpf: str = Field(..., min_length=1, max_length=15, description="The CPF of the customer.")

    @field_validator('name')
    def validate_name(cls, value):
        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only alphabetic characters and spaces.")
        return value
    
    @field_validator('cpf')
    def validate_cpf(cls, value):
        cpf_cleaned = re.sub(r'\D', '', value)

        if not cpf_cleaned.isdigit():
            raise ValueError("CPF must contain only digits.")
        
        if len(cpf_cleaned) != 11:
            raise ValueError("CPF must be 11 digits long.")
        
        if len(set(cpf_cleaned)) == 1:
            raise ValueError("Invalid CPF: all digits are the same.")

        def calculate_verifier_digit(digits, factor):
            sum_digit = 0
            for i in range(len(digits)):
                sum_digit += int(digits[i]) * (factor - i)
            remainder = sum_digit % 11
            return 0 if remainder < 2 else 11 - remainder

        first_nine_digits = cpf_cleaned[:9]
        first_verifier_digit = calculate_verifier_digit(first_nine_digits, 10)

        if int(cpf_cleaned[9]) != first_verifier_digit:
            raise ValueError("Invalid CPF: first check digit is incorrect.")

        first_ten_digits = cpf_cleaned[:10]
        second_verifier_digit = calculate_verifier_digit(first_ten_digits, 11)

        if int(cpf_cleaned[10]) != second_verifier_digit:
            raise ValueError("Invalid CPF: second check digit is incorrect.")
            
        return cpf_cleaned 

class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    cpf: str

    model_config = ConfigDict(from_attributes=True)
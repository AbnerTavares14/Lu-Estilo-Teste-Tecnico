from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
import re

class CustomerSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The name of the customer.")
    email: EmailStr = Field(..., min_length=1, max_length=100, description="The email of the customer.")
    cpf: str = Field(..., min_length=1, max_length=15, description="The CPF of the customer.")
    phone_number: Optional[str] = Field(None, description="Customer phone number (ex: +5511999998888)") 

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
    
    @field_validator('phone_number')
    def validate_and_clean_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None 

        if value.startswith('+'):
            cleaned_number = '+' + re.sub(r'\D', '', value[1:])
        else:
            cleaned_number = re.sub(r'\D', '', value)

        if cleaned_number.startswith('+'):
            if not re.fullmatch(r"^\+[1-9]\d{9,14}$", cleaned_number): 
                raise ValueError("Invalid international phone number. Expected E.164 (e.g., +5511999998888).")
            return cleaned_number
        else: 
            if re.fullmatch(r"^\d{10,11}$", cleaned_number): # Número local brasileiro (10 ou 11 dígitos)
                normalized_br_number = "+55" + cleaned_number # Adiciona +55
                # Revalida após adicionar +55 para garantir que está no formato E.164 esperado
                if not re.fullmatch(r"^\+55\d{10,11}$", normalized_br_number): # Ex: +5511987654321
                    raise ValueError("Invalid Brazilian phone number after E.164 normalization.")
                return normalized_br_number
            else:
                raise ValueError("Invalid phone number. Use local (10-11 digits) or E.164 format (+XXXXXXXXXXX).")
            
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Maria Oliveira",
                "email": "maria.oliveira@example.com",
                "cpf": "444.151.740-86", 
                "phone_number": "+5521912345678"
            }
        }
    )
    
class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    cpf: str
    phone_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
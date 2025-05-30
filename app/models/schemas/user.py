from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="The username of the user.")
    email: EmailStr = Field(..., description="The email address of the user.")
    password: str = Field(..., min_length=8, max_length=128, description="The password of the user.")
    role: str = "USER"

    @field_validator('username')
    def validate_username(cls, value):
        if not value.isalnum():
            raise ValueError("Username must be alphanumeric.")
        return value
    
    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter.")
        if not any(char in "!@#$%^&*()-_+=<>?{}[]|:;\"'`~" for char in value):
            raise ValueError("Password must contain at least one special character.")
        return value
    
    @field_validator('role')
    def validate_role(cls, value):
        valid_roles = ["USER", "ADMIN"]
        if value not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}.")
        return value

    model_config = ConfigDict(
            from_attributes=True,
            json_schema_extra={
                "example": {
                    "username": "joaosilva",
                    "email": "joao.silva@example.com",
                    "password": "Password123!",
                    "role": "USER" 
                }
            }
        ) 

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="The username of the user.")
    password: str = Field(..., min_length=8, max_length=128, description="The password of the user.")
   
    @field_validator('username')
    def validate_username(cls, value):
        if not value.isalnum():
            raise ValueError("Username must be alphanumeric.")
        return value

    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return value
    
    model_config = ConfigDict(
            from_attributes=True,
            json_schema_extra={
                "example": {
                    "username": "joaosilva",
                    "password": "Password123!"
                }
            }
        )

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token to renew the access token.")

    model_config = ConfigDict(
            from_attributes=True,
            json_schema_extra={
                "example": {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2FvX3NpbHZhIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE2NzgwMzY4MDB9.xxxxxxxxxxxx"
                }
            }
        )
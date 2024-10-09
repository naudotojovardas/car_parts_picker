# Pydantic Models
from pydantic import BaseModel, EmailStr
from pydantic import field_validator

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserModel(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str

class UserInDB(UserModel):
    hashed_password: str

class UserCreate(BaseModel):
    email: str
    password: str
    confirm_password: str

    @field_validator('email')
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email. Must contain '@'.")
        return v

    @field_validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError("Passwords do not match.")
        return v

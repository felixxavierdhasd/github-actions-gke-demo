from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(OrderBase):
    pass


class OrderResponse(OrderBase):
    id: int
    user_id: int
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

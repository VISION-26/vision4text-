from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    ADMIN = "Admin"
    RESEARCHER = "Researcher"
    OPERATOR = "Operator"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: Optional[Role] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str

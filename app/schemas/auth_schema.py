from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=200)
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"


class RefreshRequest(BaseModel):
    refreshToken: str


class RefreshResponse(BaseModel):
    accessToken: str
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str


class MeResponse(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr


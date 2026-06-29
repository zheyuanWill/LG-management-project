"""
Authentication Schemas
"""
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserBrief"


class UserBrief(BaseModel):
    """Brief user info in token response"""
    id: int
    username: str
    real_name: Optional[str] = None
    role: str
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


# Update forward references
TokenResponse.model_rebuild()

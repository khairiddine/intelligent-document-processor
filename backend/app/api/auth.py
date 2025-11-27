"""
Authentication API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import UserRegister, UserLogin, Token
from app.services.auth import register_user, login_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    - **email**: User email address
    - **password**: User password (minimum 8 characters)
    - **full_name**: Optional full name
    """
    return await register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with email and password
    
    Returns JWT access token
    """
    return await login_user(
        email=credentials.email,
        password=credentials.password
    )

@router.get("/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user information from JWT token
    """
    token = credentials.credentials
    return await get_current_user(token)

@router.post("/logout")
async def logout():
    """
    Logout (client should discard token)
    """
    return {"message": "Successfully logged out"}

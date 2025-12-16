"""Authentication utilities for Game Service."""
import os
from typing import Optional
from fastapi import Header, HTTPException, status
import httpx


AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify JWT token with Auth Service.
    
    Args:
        authorization: Bearer token from request header
        
    Returns:
        dict: Decoded token payload with user info
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                params={"token": token},
                timeout=5.0
            )
            
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Get current authenticated user.
    Use this as a dependency in protected routes.
    
    Example:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user["sub"]}
    """
    return await verify_token(authorization)


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Get current user if token is provided, otherwise return None.
    Use for optional authentication.
    """
    if not authorization:
        return None
    
    try:
        return await verify_token(authorization)
    except HTTPException:
        return None

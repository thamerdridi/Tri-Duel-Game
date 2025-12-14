import os
from typing import Optional

import httpx
from fastapi import Header, HTTPException, status


AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
GAME_SERVICE_SUBJECT = os.getenv("GAME_SERVICE_SUBJECT", "game_service")


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
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

    token = authorization.split(" ", 1)[1]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                params={"token": token},
                timeout=5.0
            )

        if response.status_code == 200:
            return response.json()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )


async def require_game_service_jwt(authorization: Optional[str] = Header(None)) -> dict:
    payload = await verify_token(authorization)
    if payload.get("sub") != GAME_SERVICE_SUBJECT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return payload


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    return await verify_token(authorization)


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None

    try:
        return await verify_token(authorization)
    except HTTPException:
        return None

"""
Authentication Client - HTTP client for Auth Service communication.

Handles all communication with the authentication service including
token verification and user validation.
"""
import httpx
import logging
import os
from typing import Optional
from fastapi import HTTPException, status, Header

from game_app.configs.client_config import (
    AUTH_SERVICE_URL,
    AUTH_TIMEOUT,
    AUTH_ENDPOINTS,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE,
    CA_BUNDLE_PATH,
)

logger = logging.getLogger(__name__)


class AuthClient:
    """
    Client for Auth Service communication.

    Provides methods to verify tokens and validate users.
    Implements retry logic and proper error handling.
    """

    def __init__(self):
        self.base_url = AUTH_SERVICE_URL
        self.timeout = AUTH_TIMEOUT
        # Determine verify parameter for httpx (either path to CA bundle or True)
        if os.path.exists(CA_BUNDLE_PATH):
            self.verify = CA_BUNDLE_PATH
            logger.debug(f"Using CA bundle at {CA_BUNDLE_PATH} for TLS verification")
        else:
            self.verify = True
            logger.debug("No CA bundle found, using system default CA store for TLS verification")

    async def verify_token(self, token: str) -> dict:
        """
        Verify JWT token with Auth Service.

        Args:
            token: JWT token string (without "Bearer " prefix)

        Returns:
            dict: Decoded token payload with user info

        Raises:
            HTTPException: If token is invalid, expired, or service unavailable
        """
        endpoint = f"{self.base_url}{AUTH_ENDPOINTS['validate']}"

        logger.debug(f"🔐 Verifying token with auth service: {endpoint}")

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify) as client:
                    response = await client.get(
                        endpoint,
                        params={"token": token}
                    )

                if response.status_code == 200:
                    logger.debug("✅ Token verified successfully")
                    return response.json()
                elif response.status_code == 401:
                    logger.warning("❌ Invalid or expired token")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token"
                    )
                else:
                    logger.error(f"❌ Auth service returned status {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token verification failed"
                    )

            except httpx.TimeoutException:
                logger.warning(f"⏱️ Auth service timeout (attempt {attempt}/{MAX_RETRY_ATTEMPTS})")
                if attempt == MAX_RETRY_ATTEMPTS:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Auth service timeout"
                    )

            except httpx.RequestError as e:
                logger.warning(f"🔌 Auth service connection error (attempt {attempt}/{MAX_RETRY_ATTEMPTS}): {e}")
                if attempt == MAX_RETRY_ATTEMPTS:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Auth service unavailable"
                    )

            # Exponential backoff
            if attempt < MAX_RETRY_ATTEMPTS:
                import asyncio
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        # Should never reach here due to raises above, but just in case
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable after retries"
        )


# Global client instance
auth_client = AuthClient()


# ============================================================
# FASTAPI DEPENDENCIES (for backward compatibility)
# ============================================================

async def verify_token_dependency(authorization: Optional[str] = None) -> dict:
    """
    FastAPI dependency for token verification.

    Use with Header(...) in your routes.
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
    return await auth_client.verify_token(token)


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Get current authenticated user.
    Use this as a dependency in protected routes.

    Example:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user["sub"]}
    """
    return await verify_token_dependency(authorization)


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Get current user if token is provided, otherwise return None.
    Use for optional authentication.
    """
    if not authorization:
        return None

    try:
        return await verify_token_dependency(authorization)
    except HTTPException:
        return None

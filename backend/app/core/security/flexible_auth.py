"""
Dependencia de autenticación flexible que acepta JWT o URL firmada
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request

from app.core.security.signed_url_auth import verify_signed_url_headers
from app.domains.autenticacion.dependencies import get_current_user_optional
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


async def require_auth_or_signed_url(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Optional[User]:
    """
    Dependencia que requiere autenticación JWT O URL firmada válida

    Returns:
        User object if JWT auth, None if signed URL auth
    """
    # Log headers for debugging
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug("Looking for signed URL headers: X-Signed-Data and X-Signed-Signature")

    # Check for signed URL headers
    signed_url_data = await verify_signed_url_headers(request)
    logger.debug(f"Signed URL data result: {signed_url_data}")

    # If we have valid signed URL, allow access
    if signed_url_data:
        logger.info("✅ Access granted via signed URL")
        return None  # Return None to indicate signed URL auth

    # Check JWT auth
    logger.debug(f"Current user from JWT: {current_user}")

    # Otherwise, require JWT authentication
    if not current_user:
        logger.warning("❌ Access denied: No valid authentication (neither JWT nor signed URL)")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide JWT token or valid signed URL"
        )

    logger.info(f"✅ Access granted via JWT for user: {current_user.email}")
    return current_user


# Create the dependency
RequireAuthOrSignedUrl = Depends(require_auth_or_signed_url)

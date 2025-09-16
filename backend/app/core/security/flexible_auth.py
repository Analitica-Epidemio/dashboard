"""
Dependencia de autenticación flexible que acepta JWT o URL firmada
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request
from app.domains.autenticacion.dependencies import get_current_user_optional
from app.core.security.signed_url_auth import verify_signed_url_headers
from app.domains.autenticacion.models import User


async def RequireAuthOrSignedUrl():
    """
    Dependencia que requiere autenticación JWT O URL firmada válida

    Returns:
        User object if JWT auth, None if signed URL auth
    """
    async def dependency(
        request: Request,
        current_user: Optional[User] = Depends(get_current_user_optional)
    ) -> Optional[User]:
        # Check for signed URL headers
        signed_url_data = await verify_signed_url_headers(request)

        # If we have valid signed URL, allow access
        if signed_url_data:
            return None  # Return None to indicate signed URL auth

        # Otherwise, require JWT authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Provide JWT token or valid signed URL"
            )

        return current_user

    return Depends(dependency)
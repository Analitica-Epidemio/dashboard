"""
List users endpoint
"""

from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.domains.auth.schemas import UserResponse
from app.domains.auth.dependencies import require_superadmin
from app.domains.auth.models import User


async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_async_session)
) -> List[UserResponse]:
    """
    List all users (Superadmin only)

    - **skip**: Number of users to skip
    - **limit**: Maximum number of users to return
    """
    from sqlalchemy import select
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return users
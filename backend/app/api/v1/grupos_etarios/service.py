
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
from app.domains.dashboard.age_groups_config import GrupoEdad

from .schemas import ConfiguracionRangosCreate, ConfiguracionRangosOut


async def list_configs(
    session: AsyncSession = Depends(get_async_session),
) -> list[ConfiguracionRangosOut]:
    result = await session.execute(select(GrupoEdad))
    rows = result.scalars().all()
    return [ConfiguracionRangosOut.model_validate(r) for r in rows]


async def create_config(
    payload: ConfiguracionRangosCreate,
    session: AsyncSession = Depends(get_async_session),
) -> ConfiguracionRangosOut:
    new = GrupoEdad(**payload.model_dump())
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return ConfiguracionRangosOut.model_validate(new)


async def delete_config(
    config_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> bool | None:
    result = await session.get(GrupoEdad, config_id)
    if not result:
        return None
    await session.delete(result)
    await session.commit()
    return True

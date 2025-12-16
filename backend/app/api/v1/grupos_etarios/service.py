from sqlmodel import select
from app.core.database import get_async_session
from app.domains.dashboard.age_groups_config import GrupoEdad
from .schemas import (
    ConfiguracionRangosCreate,
)

def list_configs():
    session = get_async_session()
    data = session.exec(select(List[GrupoEdad])).all()
    return data

def create_config(payload: ConfiguracionRangosCreate):
    session = get_async_session()
    new = List[GrupoEdad].from_orm(payload)
    session.add(new)
    session.commit()
    session.refresh(new)
    return new

def delete_config(config_id: int):
    session = get_async_session()
    obj = session.get(List[GrupoEdad], config_id)
    if not obj:
        return None
    session.delete(obj)
    session.commit()
    return True

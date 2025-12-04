from sqlmodel import select
from backend.app.db.session import get_session
from .models import ConfiguracionRangos
from .schemas import (
    ConfiguracionRangosCreate,
)

def list_configs():
    session = get_session()
    data = session.exec(select(ConfiguracionRangos)).all()
    return data

def create_config(payload: ConfiguracionRangosCreate):
    session = get_session()
    new = ConfiguracionRangos.from_orm(payload)
    session.add(new)
    session.commit()
    session.refresh(new)
    return new

def delete_config(config_id: int):
    session = get_session()
    obj = session.get(ConfiguracionRangos, config_id)
    if not obj:
        return None
    session.delete(obj)
    session.commit()
    return True

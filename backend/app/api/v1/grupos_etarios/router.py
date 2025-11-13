from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.domains.grupos_etarios.gruposetarios_models import ConfiguracionRangos
from app.core.database import get_async_session
from app.core.query_builders import EventoQueryBuilder
from .schemas import 

router = APIRouter(prefix="/gruposetarios", tags=["GruposEtarios"])
    

# Registrar endpoints de listado
@router.post("/", response_model=ConfiguracionRangosOut)
def crear_rangoetario(config: ConfiguracionRangosCreate, db: Session = Depends(get_db)):
    nueva = ConfiguracionRangos(**config.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/", response_model=list[ConfiguracionRangosOut])
def listar_rangoaetarios(db: Session = Depends(get_db)):
    return db.query(ConfiguracionRangos).all()

@router.get("/{config_id}", response_model=ConfiguracionRangosOut)
def obtener_rangoetario(config_id: int, db: Session = Depends(get_db)):
    config = db.query(ConfiguracionRangos).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config

@router.delete("/{config_id}", status_code=204)
def eliminar_rangoetario(config_id: int, db: Session = Depends(get_db)):
    config = db.query(ConfiguracionRangos).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    db.delete(config)
    db.commit()
    return None

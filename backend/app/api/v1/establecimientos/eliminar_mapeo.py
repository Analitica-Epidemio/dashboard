"""Endpoint para eliminar un mapeo existente."""

from fastapi import Depends, HTTPException, Path
from sqlmodel import Session

from app.core.database import get_session
from app.domains.territorio.establecimientos_models import Establecimiento


async def eliminar_mapeo_snvs_ign(
    id_establecimiento_snvs: int = Path(..., description="ID del establecimiento SNVS"),
    session: Session = Depends(get_session),
) -> dict:
    """
    Elimina un mapeo existente (desvincular).

    Remueve el código REFES, coordenadas y metadata del mapeo del establecimiento SNVS.
    """
    # Obtener establecimiento SNVS
    estab_snvs = session.get(Establecimiento, id_establecimiento_snvs)
    if not estab_snvs or estab_snvs.source != "SNVS":
        raise HTTPException(
            status_code=404,
            detail=f"Establecimiento SNVS con ID {id_establecimiento_snvs} no encontrado",
        )

    # Verificar que tenga mapeo
    if not estab_snvs.codigo_refes:
        raise HTTPException(
            status_code=400,
            detail="El establecimiento SNVS no tiene un mapeo para eliminar",
        )

    codigo_refes_eliminado = estab_snvs.codigo_refes

    # Remover mapeo
    estab_snvs.codigo_refes = None
    # Opcionalmente remover coordenadas (o mantenerlas si son propias)
    # estab_snvs.latitud = None
    # estab_snvs.longitud = None

    # Limpiar metadata de mapeo
    estab_snvs.mapeo_score = None
    estab_snvs.mapeo_similitud_nombre = None
    estab_snvs.mapeo_confianza = None
    estab_snvs.mapeo_razon = None
    estab_snvs.mapeo_es_manual = None
    estab_snvs.mapeo_validado = None

    session.add(estab_snvs)
    session.commit()
    session.refresh(estab_snvs)

    return {
        "message": "Mapeo eliminado exitosamente",
        "establecimiento_snvs_id": estab_snvs.id,
        "codigo_snvs": estab_snvs.codigo_snvs,
        "codigo_refes_eliminado": codigo_refes_eliminado,
    }

"""Endpoint para actualizar un mapeo existente."""

from fastapi import Depends, HTTPException, Path
from sqlmodel import Session

from app.core.database import get_session
from app.domains.territorio.establecimientos_models import Establecimiento

from .mapeo_schemas import ActualizarMapeoRequest
from .suggestions_service import (
    calcular_score_match,
    calcular_similitud_nombre,
    determinar_confianza,
    generar_razon_match,
)


async def actualizar_mapeo_snvs_ign(
    request: ActualizarMapeoRequest,
    id_establecimiento_snvs: int = Path(..., description="ID del establecimiento SNVS"),
    session: Session = Depends(get_session),
) -> dict:
    """Actualiza un mapeo existente apuntando a un nuevo establecimiento IGN."""
    # Obtener establecimiento SNVS
    estab_snvs = session.get(Establecimiento, id_establecimiento_snvs)
    if not estab_snvs or estab_snvs.source != "SNVS":
        raise HTTPException(
            status_code=404,
            detail=f"Establecimiento SNVS con ID {id_establecimiento_snvs} no encontrado"
        )

    # Verificar que tenga mapeo
    if not estab_snvs.codigo_refes:
        raise HTTPException(
            status_code=400,
            detail="El establecimiento SNVS no tiene un mapeo existente. Use POST para crear uno."
        )

    # Obtener nuevo establecimiento IGN
    estab_ign_nuevo = session.get(Establecimiento, request.id_establecimiento_ign_nuevo)
    if not estab_ign_nuevo or estab_ign_nuevo.source != "IGN":
        raise HTTPException(
            status_code=404,
            detail=f"Establecimiento IGN con ID {request.id_establecimiento_ign_nuevo} no encontrado"
        )

    codigo_refes_anterior = estab_snvs.codigo_refes

    # Calcular nueva metadata
    similitud_nombre = calcular_similitud_nombre(
        estab_snvs.nombre or "",
        estab_ign_nuevo.nombre or ""
    )

    provincia_match = False
    departamento_match = False
    localidad_match = False

    if estab_snvs.id_localidad_indec and estab_ign_nuevo.id_localidad_indec:
        localidad_match = (estab_snvs.id_localidad_indec == estab_ign_nuevo.id_localidad_indec)

    score = calcular_score_match(
        similitud_nombre,
        provincia_match,
        departamento_match,
        localidad_match
    )

    confianza = determinar_confianza(score, similitud_nombre)

    razon = request.razon or generar_razon_match(
        similitud_nombre,
        provincia_match,
        departamento_match,
        localidad_match
    )

    # Actualizar datos del SNVS
    estab_snvs.codigo_refes = estab_ign_nuevo.codigo_refes
    estab_snvs.latitud = estab_ign_nuevo.latitud
    estab_snvs.longitud = estab_ign_nuevo.longitud
    estab_snvs.id_localidad_indec = estab_ign_nuevo.id_localidad_indec

    # Actualizar metadata del mapeo
    estab_snvs.mapeo_score = score
    estab_snvs.mapeo_similitud_nombre = similitud_nombre
    estab_snvs.mapeo_confianza = confianza
    estab_snvs.mapeo_razon = razon
    estab_snvs.mapeo_es_manual = True
    estab_snvs.mapeo_validado = True

    session.add(estab_snvs)
    session.commit()
    session.refresh(estab_snvs)

    return {
        "message": "Mapeo actualizado exitosamente",
        "establecimiento_snvs_id": estab_snvs.id,
        "codigo_snvs": estab_snvs.codigo_snvs,
        "codigo_refes_anterior": codigo_refes_anterior,
        "codigo_refes_nuevo": estab_snvs.codigo_refes,
        "similitud_nombre": similitud_nombre,
        "score": score,
        "confianza": confianza,
    }

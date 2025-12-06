"""Endpoint para crear mapeo SNVS → IGN."""

from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.domains.territorio.establecimientos_models import Establecimiento

from .mapeo_schemas import CrearMapeoRequest
from .suggestions_service import (
    calcular_score_match,
    calcular_similitud_nombre,
    determinar_confianza,
    generar_razon_match,
)


async def crear_mapeo_snvs_ign(
    request: CrearMapeoRequest,
    session: Session = Depends(get_session),
) -> dict:
    """
    Crea un mapeo manual entre un establecimiento SNVS y uno IGN.

    Copia los datos geográficos del establecimiento IGN al SNVS y registra
    metadata del mapeo.
    """
    # Obtener establecimiento SNVS
    estab_snvs = session.get(Establecimiento, request.id_establecimiento_snvs)
    if not estab_snvs or estab_snvs.source != "SNVS":
        raise HTTPException(
            status_code=404,
            detail=f"Establecimiento SNVS con ID {request.id_establecimiento_snvs} no encontrado",
        )

    # Obtener establecimiento IGN
    estab_ign = session.get(Establecimiento, request.id_establecimiento_ign)
    if not estab_ign or estab_ign.source != "IGN":
        raise HTTPException(
            status_code=404,
            detail=f"Establecimiento IGN con ID {request.id_establecimiento_ign} no encontrado",
        )

    # Verificar si ya tiene mapeo
    if estab_snvs.codigo_refes:
        raise HTTPException(
            status_code=400,
            detail=f"El establecimiento SNVS ya tiene un mapeo a REFES {estab_snvs.codigo_refes}. Use PUT para actualizar.",
        )

    # Calcular metadata del mapeo
    similitud_nombre = calcular_similitud_nombre(
        estab_snvs.nombre or "", estab_ign.nombre or ""
    )

    # Para mapeos manuales, consideramos los datos geográficos del SNVS
    # (que pueden no existir, por eso son opcionales)
    provincia_match = False
    departamento_match = False
    localidad_match = False

    # Si ambos tienen localidad, verificar match geográfico
    if estab_snvs.id_localidad_indec and estab_ign.id_localidad_indec:
        localidad_match = estab_snvs.id_localidad_indec == estab_ign.id_localidad_indec

    score = calcular_score_match(
        similitud_nombre, provincia_match, departamento_match, localidad_match
    )

    confianza = determinar_confianza(score, similitud_nombre)

    razon = request.razon or generar_razon_match(
        similitud_nombre, provincia_match, departamento_match, localidad_match
    )

    # Copiar datos del IGN al SNVS
    estab_snvs.codigo_refes = estab_ign.codigo_refes
    estab_snvs.latitud = estab_ign.latitud
    estab_snvs.longitud = estab_ign.longitud
    estab_snvs.id_localidad_indec = estab_ign.id_localidad_indec

    # Registrar metadata del mapeo
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
        "message": "Mapeo creado exitosamente",
        "establecimiento_snvs_id": estab_snvs.id,
        "codigo_snvs": estab_snvs.codigo_snvs,
        "codigo_refes": estab_snvs.codigo_refes,
        "similitud_nombre": similitud_nombre,
        "score": score,
        "confianza": confianza,
    }

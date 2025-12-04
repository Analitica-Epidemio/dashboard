"""
Endpoint para obtener detalle de casos de un domicilio específico.

Usado cuando el usuario hace click en un punto del mapa para ver
todos los casos/eventos asociados a ese domicilio.
"""

from datetime import date
from typing import List, Optional

from fastapi import Depends, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlmodel import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.eventos_epidemiologicos.eventos.models import (
    Evento,
    EventoGrupoEno,
    GrupoEno,
    TipoEno,
)
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.territorio.geografia_models import (
    Departamento,
    Domicilio,
    Localidad,
    Provincia,
)


class CasoDetalle(BaseModel):
    """Detalle de un caso/evento en el domicilio"""

    id_evento: int = Field(..., description="ID del evento")
    fecha_evento: Optional[date] = Field(None, description="Fecha del evento")
    tipo_evento_nombre: Optional[str] = Field(
        None, description="Nombre del tipo de evento"
    )
    grupo_evento_nombre: Optional[str] = Field(
        None, description="Nombre del grupo de evento"
    )
    clasificacion_manual: Optional[str] = Field(
        None, description="Clasificación manual"
    )
    estado: Optional[str] = Field(None, description="Estado del caso")

    # Datos del ciudadano
    codigo_ciudadano: int = Field(..., description="Código del ciudadano")
    dni: Optional[str] = Field(None, description="DNI del ciudadano")
    nombre_completo: Optional[str] = Field(None, description="Nombre completo")
    edad: Optional[int] = Field(
        None, description="Edad del ciudadano al momento del evento"
    )
    sexo: Optional[str] = Field(None, description="Sexo del ciudadano")


class DomicilioDetalleResponse(BaseModel):
    """Respuesta con detalle completo del domicilio y sus casos"""

    # Datos del domicilio
    id_domicilio: int = Field(..., description="ID del domicilio")
    direccion: str = Field(..., description="Dirección completa")
    latitud: float = Field(..., description="Latitud")
    longitud: float = Field(..., description="Longitud")

    # Datos geográficos
    localidad_nombre: str = Field(..., description="Nombre de la localidad")
    departamento_nombre: Optional[str] = Field(
        None, description="Nombre del departamento"
    )
    provincia_nombre: str = Field(..., description="Nombre de la provincia")

    # Casos
    total_casos: int = Field(..., description="Total de casos en este domicilio")
    casos: List[CasoDetalle] = Field(default_factory=list, description="Lista de casos")

    # Resumen por tipo
    casos_por_tipo: dict = Field(
        default_factory=dict, description="Conteo de casos por tipo de evento"
    )


async def get_domicilio_detalle(
    id_domicilio: int = Path(..., description="ID del domicilio"),
    fecha_desde: Optional[date] = Query(
        None, description="Filtrar casos desde esta fecha"
    ),
    fecha_hasta: Optional[date] = Query(
        None, description="Filtrar casos hasta esta fecha"
    ),
    session: Session = Depends(get_session),
) -> SuccessResponse[DomicilioDetalleResponse]:
    """
    Obtiene detalle completo de un domicilio con todos sus casos.

    Útil para mostrar en un dialog/modal cuando el usuario hace click
    en un punto del mapa.
    """

    # Verificar que el domicilio existe y obtener sus datos geográficos
    domicilio_stmt = (
        select(
            Domicilio,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.nombre.label("departamento_nombre"),
            Provincia.nombre.label("provincia_nombre"),
        )
        .join(Localidad, Domicilio.id_localidad_indec == Localidad.id_localidad_indec)
        .join(
            Departamento,
            Localidad.id_departamento_indec == Departamento.id_departamento_indec,
        )
        .join(
            Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec
        )
        .where(Domicilio.id == id_domicilio)
    )
    domicilio_result = session.exec(domicilio_stmt).first()

    if not domicilio_result:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Domicilio no encontrado")

    domicilio = domicilio_result[0]
    localidad_nombre = domicilio_result.localidad_nombre
    departamento_nombre = domicilio_result.departamento_nombre
    provincia_nombre = domicilio_result.provincia_nombre

    # Obtener eventos del domicilio con tipo y grupo
    query = (
        select(
            Evento.id,
            Evento.fecha_minima_evento,
            Evento.fecha_nacimiento,
            Evento.clasificacion_manual,
            Evento.clasificacion_estrategia,
            Ciudadano.codigo_ciudadano,
            Ciudadano.numero_documento,
            Ciudadano.nombre,
            Ciudadano.apellido,
            Ciudadano.sexo_biologico,
            TipoEno.nombre.label("tipo_nombre"),
            GrupoEno.nombre.label("grupo_nombre"),
        )
        .select_from(Evento)
        .join(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
        .outerjoin(TipoEno, Evento.id_tipo_eno == TipoEno.id)
        .outerjoin(EventoGrupoEno, Evento.id == EventoGrupoEno.id_evento)
        .outerjoin(GrupoEno, EventoGrupoEno.id_grupo_eno == GrupoEno.id)
        .where(Evento.id_domicilio == id_domicilio)
    )

    # Aplicar filtros temporales
    if fecha_desde is not None:
        query = query.where(Evento.fecha_minima_evento >= fecha_desde)
    if fecha_hasta is not None:
        query = query.where(Evento.fecha_minima_evento <= fecha_hasta)

    # Ordenar por fecha más reciente primero
    query = query.order_by(Evento.fecha_minima_evento.desc())

    results = session.exec(query).all()

    # Construir lista de casos
    casos: List[CasoDetalle] = []
    casos_por_tipo = {}

    for row in results:
        # Calcular edad al momento del evento
        edad = None
        if row.fecha_nacimiento and row.fecha_minima_evento:
            edad = (row.fecha_minima_evento - row.fecha_nacimiento).days // 365

        # Construir nombre completo
        nombre_completo = None
        if row.nombre or row.apellido:
            partes = []
            if row.apellido:
                partes.append(row.apellido)
            if row.nombre:
                partes.append(row.nombre)
            nombre_completo = ", ".join(partes) if partes else None

        caso = CasoDetalle(
            id_evento=row.id,
            fecha_evento=row.fecha_minima_evento,
            tipo_evento_nombre=row.tipo_nombre,
            grupo_evento_nombre=row.grupo_nombre,
            clasificacion_manual=row.clasificacion_manual,
            estado=row.clasificacion_estrategia,
            codigo_ciudadano=row.codigo_ciudadano,
            dni=str(row.numero_documento) if row.numero_documento else None,
            nombre_completo=nombre_completo,
            edad=edad,
            sexo=row.sexo_biologico.value if row.sexo_biologico else None,
        )
        casos.append(caso)

        # Contar por tipo
        tipo_key = row.tipo_nombre or row.clasificacion_manual or "Sin clasificar"
        casos_por_tipo[tipo_key] = casos_por_tipo.get(tipo_key, 0) + 1

    # Construir dirección
    partes_direccion = []
    if domicilio.calle:
        direccion = domicilio.calle
        if domicilio.numero:
            direccion += f" {domicilio.numero}"
        partes_direccion.append(direccion)

    if partes_direccion:
        direccion_completa = f"{partes_direccion[0]}, {localidad_nombre}"
    else:
        direccion_completa = localidad_nombre

    response_data = DomicilioDetalleResponse(
        id_domicilio=id_domicilio,
        direccion=direccion_completa,
        latitud=float(domicilio.latitud) if domicilio.latitud else 0.0,
        longitud=float(domicilio.longitud) if domicilio.longitud else 0.0,
        localidad_nombre=localidad_nombre,
        departamento_nombre=departamento_nombre,
        provincia_nombre=provincia_nombre,
        total_casos=len(casos),
        casos=casos,
        casos_por_tipo=casos_por_tipo,
    )

    return SuccessResponse(data=response_data)

"""
Endpoint para obtener estadísticas resumen del dashboard
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.eventos.models import Evento, GrupoEno, TipoEno
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.territorio.geografia_models import Provincia, Departamento, Localidad

logger = logging.getLogger(__name__)


class EventoStats(BaseModel):
    """Estadísticas de eventos más típicos"""
    tipo_eno: str
    codigo_tipo: Optional[str]
    total: int
    clasificaciones: Dict[str, int]


class GrupoStats(BaseModel):
    """Estadísticas de grupos más típicos"""
    grupo_eno: str
    codigo_grupo: Optional[str]
    total: int
    tipos: List[Dict[str, Any]]


class PiramidePoblacional(BaseModel):
    """Datos para pirámide poblacional"""
    age: str
    sex: str
    value: int


class TerritorioAfectado(BaseModel):
    """Provincia/Departamento/Localidad afectada"""
    nivel: str  # "provincia", "departamento", "localidad"
    nombre: str
    codigo_indec: Optional[int]
    total_eventos: int
    hijos: Optional[List[Dict[str, Any]]] = None


class TablaResumen(BaseModel):
    """Tabla resumen con datos clave"""
    total_eventos: int
    total_confirmados: int
    total_sospechosos: int
    total_negativos: int
    total_personas_afectadas: int
    fecha_primer_evento: Optional[date]
    fecha_ultimo_evento: Optional[date]


class DashboardResumenResponse(BaseModel):
    """Response del dashboard resumen"""
    tabla_resumen: TablaResumen
    eventos_mas_tipicos: List[EventoStats]
    grupos_mas_tipicos: List[GrupoStats]
    piramide_poblacional: List[PiramidePoblacional]
    territorios_afectados: List[TerritorioAfectado]


async def get_dashboard_resumen(
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    grupo_id: Optional[int] = Query(None, description="Filtrar por grupo ENO"),
    tipo_eno_id: Optional[int] = Query(None, description="Filtrar por tipo ENO"),
    clasificacion: Optional[str] = Query(None, description="Filtrar por clasificación"),
    provincia_id: Optional[int] = Query(None, description="Filtrar por provincia INDEC"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[DashboardResumenResponse]:
    """
    Obtiene estadísticas resumen del dashboard:
    - Tabla resumen con totales
    - Eventos más típicos
    - Grupos más típicos
    - Pirámide poblacional
    - Territorios afectados (jerárquico)
    """

    # Construir filtros base
    filtros = []
    if fecha_desde:
        filtros.append(Evento.fecha_minima_evento >= fecha_desde)
    if fecha_hasta:
        filtros.append(Evento.fecha_minima_evento <= fecha_hasta)
    if tipo_eno_id:
        filtros.append(Evento.id_tipo_eno == tipo_eno_id)
    if clasificacion:
        filtros.append(Evento.clasificacion_estrategia == clasificacion)

    # Filtro adicional para grupo (many-to-many)
    if grupo_id:
        from app.domains.eventos_epidemiologicos.eventos.models import EventoGrupoEno
        filtros.append(
            Evento.id.in_(
                select(EventoGrupoEno.id_evento).where(EventoGrupoEno.id_grupo_eno == grupo_id)
            )
        )

    # 1. TABLA RESUMEN
    query_total = select(func.count(Evento.id)).where(and_(*filtros) if filtros else True)
    total_eventos = (await db.execute(query_total)).scalar_one()

    query_confirmados = select(func.count(Evento.id)).where(
        and_(
            Evento.clasificacion_estrategia == "CONFIRMADOS",
            *(filtros if filtros else [])
        )
    )
    total_confirmados = (await db.execute(query_confirmados)).scalar_one()

    query_sospechosos = select(func.count(Evento.id)).where(
        and_(
            Evento.clasificacion_estrategia == "SOSPECHOSOS",
            *(filtros if filtros else [])
        )
    )
    total_sospechosos = (await db.execute(query_sospechosos)).scalar_one()

    query_negativos = select(func.count(Evento.id)).where(
        and_(
            Evento.clasificacion_estrategia == "NEGATIVOS",
            *(filtros if filtros else [])
        )
    )
    total_negativos = (await db.execute(query_negativos)).scalar_one()

    # Total personas afectadas (ciudadanos únicos)
    query_personas = select(func.count(func.distinct(Evento.codigo_ciudadano))).where(
        and_(
            Evento.codigo_ciudadano.isnot(None),
            *(filtros if filtros else [])
        )
    )
    total_personas = (await db.execute(query_personas)).scalar_one()

    # Fechas primer y último evento
    query_fechas = select(
        func.min(Evento.fecha_minima_evento),
        func.max(Evento.fecha_minima_evento)
    ).where(and_(*filtros) if filtros else True)
    fechas_result = (await db.execute(query_fechas)).one()
    fecha_primer_evento = fechas_result[0]
    fecha_ultimo_evento = fechas_result[1]

    tabla_resumen = TablaResumen(
        total_eventos=total_eventos,
        total_confirmados=total_confirmados,
        total_sospechosos=total_sospechosos,
        total_negativos=total_negativos,
        total_personas_afectadas=total_personas,
        fecha_primer_evento=fecha_primer_evento,
        fecha_ultimo_evento=fecha_ultimo_evento
    )

    # 2. EVENTOS MÁS TÍPICOS (Top 10 tipos de eventos)
    query_eventos = (
        select(
            TipoEno.nombre,
            TipoEno.codigo,
            func.count(Evento.id).label("total"),
            Evento.clasificacion_estrategia
        )
        .join(TipoEno, Evento.id_tipo_eno == TipoEno.id)
        .where(and_(*filtros) if filtros else True)
        .group_by(TipoEno.nombre, TipoEno.codigo, Evento.clasificacion_estrategia)
        .order_by(func.count(Evento.id).desc())
        .limit(100)  # Límite amplio para agrupar después
    )
    eventos_result = (await db.execute(query_eventos)).all()

    # Agrupar por tipo de evento
    eventos_dict: Dict[str, EventoStats] = {}
    for tipo_nombre, tipo_codigo, total, clasificacion in eventos_result:
        if tipo_nombre not in eventos_dict:
            eventos_dict[tipo_nombre] = EventoStats(
                tipo_eno=tipo_nombre,
                codigo_tipo=tipo_codigo,
                total=0,
                clasificaciones={}
            )
        eventos_dict[tipo_nombre].total += total
        if clasificacion:
            eventos_dict[tipo_nombre].clasificaciones[clasificacion] = (
                eventos_dict[tipo_nombre].clasificaciones.get(clasificacion, 0) + total
            )

    eventos_mas_tipicos = sorted(
        eventos_dict.values(),
        key=lambda x: x.total,
        reverse=True
    )[:10]

    # 3. GRUPOS MÁS TÍPICOS - Ahora usando la tabla de unión evento_grupo_eno
    from app.domains.eventos_epidemiologicos.eventos.models import EventoGrupoEno

    query_grupos = (
        select(
            GrupoEno.nombre,
            GrupoEno.codigo,
            TipoEno.nombre.label("tipo_nombre"),
            func.count(Evento.id).label("total")
        )
        .join(EventoGrupoEno, Evento.id == EventoGrupoEno.id_evento)
        .join(GrupoEno, EventoGrupoEno.id_grupo_eno == GrupoEno.id)
        .join(TipoEno, Evento.id_tipo_eno == TipoEno.id)
        .where(and_(*filtros) if filtros else True)
        .group_by(GrupoEno.nombre, GrupoEno.codigo, TipoEno.nombre)
        .order_by(func.count(Evento.id).desc())
    )
    grupos_result = (await db.execute(query_grupos)).all()

    # Agrupar por grupo
    grupos_dict: Dict[str, GrupoStats] = {}
    for grupo_nombre, grupo_codigo, tipo_nombre, total in grupos_result:
        if grupo_nombre not in grupos_dict:
            grupos_dict[grupo_nombre] = GrupoStats(
                grupo_eno=grupo_nombre,
                codigo_grupo=grupo_codigo,
                total=0,
                tipos=[]
            )
        grupos_dict[grupo_nombre].total += total
        grupos_dict[grupo_nombre].tipos.append({
            "tipo": tipo_nombre,
            "total": total
        })

    grupos_mas_tipicos = sorted(
        grupos_dict.values(),
        key=lambda x: x.total,
        reverse=True
    )[:10]

    # 4. PIRÁMIDE POBLACIONAL (grupos de edad y sexo)
    # Primero obtener eventos con ciudadanos
    query_piramide = (
        select(
            Evento.edad_anos_al_momento_apertura,
            Ciudadano.sexo_biologico
        )
        .join(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
        .where(
            and_(
                Evento.codigo_ciudadano.isnot(None),
                Evento.edad_anos_al_momento_apertura.isnot(None),
                Ciudadano.sexo_biologico.isnot(None),
                *(filtros if filtros else [])
            )
        )
    )
    piramide_result = (await db.execute(query_piramide)).all()

    # Agrupar por rangos de edad y sexo
    age_groups = {
        "0-4": (0, 4), "5-9": (5, 9), "10-14": (10, 14), "15-19": (15, 19),
        "20-24": (20, 24), "25-29": (25, 29), "30-34": (30, 34), "35-39": (35, 39),
        "40-44": (40, 44), "45-49": (45, 49), "50-54": (50, 54), "55-59": (55, 59),
        "60-64": (60, 64), "65-69": (65, 69), "70-74": (70, 74), "75-79": (75, 79),
        "80+": (80, 150)
    }

    piramide_data: Dict[tuple, int] = {}
    for edad, sexo in piramide_result:
        # Determinar grupo de edad
        age_group = None
        for group_name, (min_age, max_age) in age_groups.items():
            if min_age <= edad <= max_age:
                age_group = group_name
                break

        if age_group and sexo in ["M", "F"]:
            key = (age_group, sexo)
            piramide_data[key] = piramide_data.get(key, 0) + 1

    piramide_poblacional = [
        PiramidePoblacional(age=age, sex=sex, value=count)
        for (age, sex), count in piramide_data.items()
    ]

    # 5. TERRITORIOS AFECTADOS (solo provincias por ahora, jerárquico después)
    # Necesitamos hacer join con establecimientos para obtener la provincia
    from app.domains.territorio.establecimientos_models import Establecimiento

    query_territorios = (
        select(
            Provincia.nombre,
            Provincia.id_provincia_indec,
            func.count(Evento.id).label("total")
        )
        .join(
            Establecimiento,
            Evento.id_establecimiento_notificacion == Establecimiento.id
        )
        .join(
            Localidad,
            Establecimiento.id_localidad_indec == Localidad.id_localidad_indec
        )
        .join(
            Departamento,
            Localidad.id_departamento == Departamento.id
        )
        .join(
            Provincia,
            Departamento.id_provincia_indec == Provincia.id_provincia_indec
        )
        .where(and_(*filtros) if filtros else True)
        .group_by(Provincia.nombre, Provincia.id_provincia_indec)
        .order_by(func.count(Evento.id).desc())
    )
    territorios_result = (await db.execute(query_territorios)).all()

    territorios_afectados = [
        TerritorioAfectado(
            nivel="provincia",
            nombre=nombre,
            codigo_indec=codigo_indec,
            total_eventos=total,
            hijos=None  # Por ahora sin jerarquía, se puede expandir después
        )
        for nombre, codigo_indec, total in territorios_result
    ]

    response = DashboardResumenResponse(
        tabla_resumen=tabla_resumen,
        eventos_mas_tipicos=eventos_mas_tipicos,
        grupos_mas_tipicos=grupos_mas_tipicos,
        piramide_poblacional=piramide_poblacional,
        territorios_afectados=territorios_afectados
    )

    return SuccessResponse(data=response)

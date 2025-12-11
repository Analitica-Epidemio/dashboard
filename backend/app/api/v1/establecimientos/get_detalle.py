"""
Endpoint para obtener detalle de eventos y personas relacionadas con un establecimiento.

Usado cuando el usuario hace click en un establecimiento del mapa para ver
todos los eventos/personas asociados según el tipo de relación (clínica, diagnóstico, muestra, etc.).
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import Depends, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlmodel import Session, col

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia
from app.domains.vigilancia_nominal.models.atencion import (
    DiagnosticoCasoEpidemiologico,
    TratamientoCasoEpidemiologico,
)
from app.domains.vigilancia_nominal.models.caso import (
    CasoEpidemiologico,
    CasoGrupoEnfermedad,
)
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    GrupoDeEnfermedades,
)
from app.domains.vigilancia_nominal.models.salud import MuestraCasoEpidemiologico
from app.domains.vigilancia_nominal.models.sujetos import Ciudadano


class PersonaRelacionada(BaseModel):
    """Detalle de una persona relacionada al establecimiento"""

    # Datos del ciudadano
    codigo_ciudadano: int = Field(..., description="Código del ciudadano")
    dni: Optional[str] = Field(None, description="DNI del ciudadano")
    nombre_completo: Optional[str] = Field(None, description="Nombre completo")
    edad: Optional[int] = Field(
        None, description="Edad del ciudadano al momento del evento"
    )
    sexo: Optional[str] = Field(None, description="Sexo del ciudadano")

    # Datos del evento
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

    # Tipo de relación con el establecimiento
    tipo_relacion: str = Field(
        ...,
        description="Tipo de relación: consulta, notificacion, carga, muestra, diagnostico",
    )


class EstablecimientoDetalleResponse(BaseModel):
    """Respuesta con detalle completo del establecimiento y sus relaciones"""

    # Datos del establecimiento
    id_establecimiento: int = Field(..., description="ID del establecimiento")
    nombre: str = Field(..., description="Nombre del establecimiento")
    codigo_refes: Optional[str] = Field(None, description="Código REFES")
    codigo_snvs: Optional[str] = Field(None, description="Código SNVS")
    latitud: float = Field(..., description="Latitud")
    longitud: float = Field(..., description="Longitud")

    # Datos geográficos
    localidad_nombre: Optional[str] = Field(None, description="Nombre de la localidad")
    departamento_nombre: Optional[str] = Field(
        None, description="Nombre del departamento"
    )
    provincia_nombre: Optional[str] = Field(None, description="Nombre de la provincia")

    # Personas y eventos relacionados
    total_personas: int = Field(..., description="Total de personas relacionadas")
    personas: List[PersonaRelacionada] = Field(
        default_factory=list, description="Lista de personas relacionadas"
    )

    # Resumen por tipo de relación
    relaciones_por_tipo: dict = Field(
        default_factory=dict, description="Conteo de relaciones por tipo"
    )

    # Resumen por tipo de evento
    eventos_por_tipo: dict = Field(
        default_factory=dict, description="Conteo de eventos por tipo"
    )


async def get_establecimiento_detalle(
    id_establecimiento: int = Path(..., description="ID del establecimiento"),
    fecha_desde: Optional[date] = Query(
        None, description="Filtrar eventos desde esta fecha"
    ),
    fecha_hasta: Optional[date] = Query(
        None, description="Filtrar eventos hasta esta fecha"
    ),
    session: Session = Depends(get_session),
) -> SuccessResponse[EstablecimientoDetalleResponse]:
    """
    Obtiene detalle completo de un establecimiento con todas las personas/eventos relacionados.

    El establecimiento puede estar relacionado con eventos de las siguientes maneras:
    - Consulta: Lugar donde se realizó la primera consulta clínica (id_establecimiento_consulta)
    - Notificación: Establecimiento que notificó/reportó el caso (id_establecimiento_notificacion)
    - Carga: Establecimiento donde se cargó el caso en el sistema (id_establecimiento_carga)
    - Muestra: Lugar donde se tomó la muestra (MuestraCasoEpidemiologico.id_establecimiento_muestra)
    - Diagnóstico: Lugar donde se realizó el diagnóstico (DiagnosticoCasoEpidemiologico.id_establecimiento_diagnostico)

    Útil para mostrar en un dialog/modal cuando el usuario hace click en un establecimiento del mapa.
    """

    # Verificar que el establecimiento existe y obtener sus datos geográficos
    estab_stmt = (
        select(
            Establecimiento,
            col(Localidad.nombre).label("localidad_nombre"),
            col(Departamento.nombre).label("departamento_nombre"),
            col(Provincia.nombre).label("provincia_nombre"),
        )
        .outerjoin(
            Localidad,
            col(Establecimiento.id_localidad_indec)
            == col(Localidad.id_localidad_indec),
        )
        .outerjoin(
            Departamento,
            col(Localidad.id_departamento_indec)
            == col(Departamento.id_departamento_indec),
        )
        .outerjoin(
            Provincia,
            col(Departamento.id_provincia_indec) == col(Provincia.id_provincia_indec),
        )
        .where(col(Establecimiento.id) == id_establecimiento)
    )
    estab_result = session.exec(estab_stmt).first()

    if not estab_result:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Establecimiento no encontrado")

    establecimiento = estab_result[0]
    localidad_nombre = estab_result.localidad_nombre
    departamento_nombre = estab_result.departamento_nombre
    provincia_nombre = estab_result.provincia_nombre

    # ===== PASO 1: CasoEpidemiologicos con relación directa (consulta, notificación, carga) =====
    query_eventos = (
        select(
            col(CasoEpidemiologico.id).label("id_evento"),
            col(CasoEpidemiologico.fecha_minima_caso),
            col(CasoEpidemiologico.fecha_nacimiento),
            col(CasoEpidemiologico.clasificacion_manual),
            col(CasoEpidemiologico.clasificacion_estrategia),
            col(CasoEpidemiologico.id_establecimiento_consulta),
            col(CasoEpidemiologico.id_establecimiento_notificacion),
            col(CasoEpidemiologico.id_establecimiento_carga),
            col(Ciudadano.codigo_ciudadano),
            col(Ciudadano.numero_documento),
            col(Ciudadano.nombre),
            col(Ciudadano.apellido),
            col(Ciudadano.sexo_biologico),
            col(Enfermedad.nombre).label("tipo_nombre"),
            col(GrupoDeEnfermedades.nombre).label("grupo_nombre"),
        )
        .select_from(CasoEpidemiologico)
        .join(
            Ciudadano,
            col(CasoEpidemiologico.codigo_ciudadano) == col(Ciudadano.codigo_ciudadano),
        )
        .outerjoin(
            Enfermedad, col(CasoEpidemiologico.id_enfermedad) == col(Enfermedad.id)
        )
        .outerjoin(
            CasoGrupoEnfermedad,
            col(CasoEpidemiologico.id) == col(CasoGrupoEnfermedad.id_caso),
        )
        .outerjoin(
            GrupoDeEnfermedades,
            col(CasoGrupoEnfermedad.id_grupo) == col(GrupoDeEnfermedades.id),
        )
        .where(
            or_(
                col(CasoEpidemiologico.id_establecimiento_consulta)
                == id_establecimiento,
                col(CasoEpidemiologico.id_establecimiento_notificacion)
                == id_establecimiento,
                col(CasoEpidemiologico.id_establecimiento_carga) == id_establecimiento,
            )
        )
    )

    # Aplicar filtros temporales
    if fecha_desde is not None:
        query_eventos = query_eventos.where(
            col(CasoEpidemiologico.fecha_minima_caso) >= fecha_desde
        )
    if fecha_hasta is not None:
        query_eventos = query_eventos.where(
            col(CasoEpidemiologico.fecha_minima_caso) <= fecha_hasta
        )

    results_eventos = session.execute(query_eventos).all()

    # ===== PASO 2: Muestras tomadas en este establecimiento =====
    query_muestras = (
        select(
            col(CasoEpidemiologico.id).label("id_evento"),
            col(CasoEpidemiologico.fecha_minima_caso),
            col(CasoEpidemiologico.fecha_nacimiento),
            col(CasoEpidemiologico.clasificacion_manual),
            col(CasoEpidemiologico.clasificacion_estrategia),
            col(Ciudadano.codigo_ciudadano),
            col(Ciudadano.numero_documento),
            col(Ciudadano.nombre),
            col(Ciudadano.apellido),
            col(Ciudadano.sexo_biologico),
            col(Enfermedad.nombre).label("tipo_nombre"),
            col(GrupoDeEnfermedades.nombre).label("grupo_nombre"),
        )
        .select_from(MuestraCasoEpidemiologico)
        .join(
            CasoEpidemiologico,
            col(MuestraCasoEpidemiologico.id_caso) == col(CasoEpidemiologico.id),
        )
        .join(
            Ciudadano,
            col(CasoEpidemiologico.codigo_ciudadano) == col(Ciudadano.codigo_ciudadano),
        )
        .outerjoin(
            Enfermedad, col(CasoEpidemiologico.id_enfermedad) == col(Enfermedad.id)
        )
        .outerjoin(
            CasoGrupoEnfermedad,
            col(CasoEpidemiologico.id) == col(CasoGrupoEnfermedad.id_caso),
        )
        .outerjoin(
            GrupoDeEnfermedades,
            col(CasoGrupoEnfermedad.id_grupo) == col(GrupoDeEnfermedades.id),
        )
        .where(col(MuestraCasoEpidemiologico.id_establecimiento) == id_establecimiento)
    )

    if fecha_desde is not None:
        query_muestras = query_muestras.where(
            col(CasoEpidemiologico.fecha_minima_caso) >= fecha_desde
        )
    if fecha_hasta is not None:
        query_muestras = query_muestras.where(
            col(CasoEpidemiologico.fecha_minima_caso) <= fecha_hasta
        )

    results_muestras = session.execute(query_muestras).all()

    # ===== PASO 3: Diagnósticos realizados en este establecimiento =====
    query_diagnosticos = (
        select(
            col(CasoEpidemiologico.id).label("id_evento"),
            col(CasoEpidemiologico.fecha_minima_caso),
            col(CasoEpidemiologico.fecha_nacimiento),
            col(CasoEpidemiologico.clasificacion_manual),
            col(CasoEpidemiologico.clasificacion_estrategia),
            col(Ciudadano.codigo_ciudadano),
            col(Ciudadano.numero_documento),
            col(Ciudadano.nombre),
            col(Ciudadano.apellido),
            col(Ciudadano.sexo_biologico),
            col(Enfermedad.nombre).label("tipo_nombre"),
            col(GrupoDeEnfermedades.nombre).label("grupo_nombre"),
        )
        .select_from(DiagnosticoCasoEpidemiologico)
        .join(
            CasoEpidemiologico,
            col(DiagnosticoCasoEpidemiologico.id_caso) == col(CasoEpidemiologico.id),
        )
        .join(
            Ciudadano,
            col(CasoEpidemiologico.codigo_ciudadano) == col(Ciudadano.codigo_ciudadano),
        )
        .outerjoin(
            Enfermedad, col(CasoEpidemiologico.id_enfermedad) == col(Enfermedad.id)
        )
        .outerjoin(
            CasoGrupoEnfermedad,
            col(CasoEpidemiologico.id) == col(CasoGrupoEnfermedad.id_caso),
        )
        .outerjoin(
            GrupoDeEnfermedades,
            col(CasoGrupoEnfermedad.id_grupo) == col(GrupoDeEnfermedades.id),
        )
        .where(
            col(DiagnosticoCasoEpidemiologico.id_establecimiento_diagnostico)
            == id_establecimiento
        )
    )

    if fecha_desde is not None:
        query_diagnosticos = query_diagnosticos.where(
            col(CasoEpidemiologico.fecha_minima_caso) >= fecha_desde
        )
    if fecha_hasta is not None:
        query_diagnosticos = query_diagnosticos.where(
            col(CasoEpidemiologico.fecha_minima_caso) <= fecha_hasta
        )

    results_diagnosticos = session.execute(query_diagnosticos).all()

    # ===== PASO 4: Tratamientos dados en este establecimiento =====
    query_tratamientos = (
        select(
            col(CasoEpidemiologico.id).label("id_evento"),
            col(CasoEpidemiologico.fecha_minima_caso),
            col(CasoEpidemiologico.fecha_nacimiento),
            col(CasoEpidemiologico.clasificacion_manual),
            col(CasoEpidemiologico.clasificacion_estrategia),
            col(Ciudadano.codigo_ciudadano),
            col(Ciudadano.numero_documento),
            col(Ciudadano.nombre),
            col(Ciudadano.apellido),
            col(Ciudadano.sexo_biologico),
            col(Enfermedad.nombre).label("tipo_nombre"),
            col(GrupoDeEnfermedades.nombre).label("grupo_nombre"),
        )
        .select_from(TratamientoCasoEpidemiologico)
        .join(
            CasoEpidemiologico,
            col(TratamientoCasoEpidemiologico.id_caso) == col(CasoEpidemiologico.id),
        )
        .join(
            Ciudadano,
            col(CasoEpidemiologico.codigo_ciudadano) == col(Ciudadano.codigo_ciudadano),
        )
        .outerjoin(
            Enfermedad, col(CasoEpidemiologico.id_enfermedad) == col(Enfermedad.id)
        )
        .outerjoin(
            CasoGrupoEnfermedad,
            col(CasoEpidemiologico.id) == col(CasoGrupoEnfermedad.id_caso),
        )
        .outerjoin(
            GrupoDeEnfermedades,
            col(CasoGrupoEnfermedad.id_grupo) == col(GrupoDeEnfermedades.id),
        )
        .where(
            col(TratamientoCasoEpidemiologico.id_establecimiento_tratamiento)
            == id_establecimiento
        )
    )

    if fecha_desde is not None:
        query_tratamientos = query_tratamientos.where(
            col(CasoEpidemiologico.fecha_minima_caso) >= fecha_desde
        )
    if fecha_hasta is not None:
        query_tratamientos = query_tratamientos.where(
            col(CasoEpidemiologico.fecha_minima_caso) <= fecha_hasta
        )

    results_tratamientos = session.execute(query_tratamientos).all()

    # ===== PROCESAR TODOS LOS RESULTADOS =====
    personas_dict = {}
    relaciones_por_tipo = {}
    eventos_por_tipo = {}

    # Procesar eventos directos (consulta, notificación, carga)
    for row in results_eventos:
        # Calcular edad al momento del evento
        edad = None
        if row.fecha_nacimiento and row.fecha_minima_caso:
            edad = (row.fecha_minima_caso - row.fecha_nacimiento).days // 365

        # Construir nombre completo
        nombre_completo = None
        if row.nombre or row.apellido:
            partes = []
            if row.apellido:
                partes.append(row.apellido)
            if row.nombre:
                partes.append(row.nombre)
            nombre_completo = ", ".join(partes) if partes else None

        # Determinar tipos de relación para este evento
        tipos_relacion = []
        if row.id_establecimiento_consulta == id_establecimiento:
            tipos_relacion.append("consulta")
        if row.id_establecimiento_notificacion == id_establecimiento:
            tipos_relacion.append("notificacion")
        if row.id_establecimiento_carga == id_establecimiento:
            tipos_relacion.append("carga")

        # Crear una entrada por cada tipo de relación
        for tipo_rel in tipos_relacion:
            # Usar una clave única: codigo_ciudadano + id_evento + tipo_relacion
            key = f"{row.codigo_ciudadano}_{row.id_evento}_{tipo_rel}"

            if key not in personas_dict:
                persona = PersonaRelacionada(
                    id_evento=row.id_evento,
                    fecha_evento=row.fecha_minima_caso,
                    tipo_evento_nombre=row.tipo_nombre,
                    grupo_evento_nombre=row.grupo_nombre,
                    clasificacion_manual=row.clasificacion_manual,
                    estado=row.clasificacion_estrategia,
                    codigo_ciudadano=row.codigo_ciudadano,
                    dni=str(row.numero_documento) if row.numero_documento else None,
                    nombre_completo=nombre_completo,
                    edad=edad,
                    sexo=row.sexo_biologico.value if row.sexo_biologico else None,
                    tipo_relacion=tipo_rel,
                )
                personas_dict[key] = persona

                # Contar por tipo de relación
                relaciones_por_tipo[tipo_rel] = relaciones_por_tipo.get(tipo_rel, 0) + 1

        # Contar por tipo de evento
        tipo_key = row.tipo_nombre or row.clasificacion_manual or "Sin clasificar"
        eventos_por_tipo[tipo_key] = eventos_por_tipo.get(tipo_key, 0) + 1

    # Helper function para procesar resultados comunes (muestras, diagnósticos, tratamientos)
    def procesar_resultado_comun(row: Any, tipo_relacion: str) -> None:
        """Procesa un resultado y agrega la persona al diccionario"""
        edad = None
        if row.fecha_nacimiento and row.fecha_minima_caso:
            edad = (row.fecha_minima_caso - row.fecha_nacimiento).days // 365

        nombre_completo = None
        if row.nombre or row.apellido:
            partes = []
            if row.apellido:
                partes.append(row.apellido)
            if row.nombre:
                partes.append(row.nombre)
            nombre_completo = ", ".join(partes) if partes else None

        # Clave única
        key = f"{row.codigo_ciudadano}_{row.id_evento}_{tipo_relacion}"

        if key not in personas_dict:
            persona = PersonaRelacionada(
                id_evento=row.id_evento,
                fecha_evento=row.fecha_minima_caso,
                tipo_evento_nombre=row.tipo_nombre,
                grupo_evento_nombre=row.grupo_nombre,
                clasificacion_manual=row.clasificacion_manual,
                estado=row.clasificacion_estrategia,
                codigo_ciudadano=row.codigo_ciudadano,
                dni=str(row.numero_documento) if row.numero_documento else None,
                nombre_completo=nombre_completo,
                edad=edad,
                sexo=row.sexo_biologico.value if row.sexo_biologico else None,
                tipo_relacion=tipo_relacion,
            )
            personas_dict[key] = persona
            relaciones_por_tipo[tipo_relacion] = (
                relaciones_por_tipo.get(tipo_relacion, 0) + 1
            )

        # Contar por tipo de evento
        tipo_key = row.tipo_nombre or row.clasificacion_manual or "Sin clasificar"
        eventos_por_tipo[tipo_key] = eventos_por_tipo.get(tipo_key, 0) + 1

    # Procesar muestras
    for row in results_muestras:
        procesar_resultado_comun(row, "muestra")

    # Procesar diagnósticos
    for row in results_diagnosticos:
        procesar_resultado_comun(row, "diagnostico")

    # Procesar tratamientos
    for row in results_tratamientos:
        procesar_resultado_comun(row, "tratamiento")

    # Convertir dict a lista
    personas = list(personas_dict.values())

    response_data = EstablecimientoDetalleResponse(
        id_establecimiento=id_establecimiento,
        nombre=establecimiento.nombre,
        codigo_refes=establecimiento.codigo_refes,
        codigo_snvs=establecimiento.codigo_snvs,
        latitud=float(establecimiento.latitud) if establecimiento.latitud else 0.0,
        longitud=float(establecimiento.longitud) if establecimiento.longitud else 0.0,
        localidad_nombre=localidad_nombre,
        departamento_nombre=departamento_nombre,
        provincia_nombre=provincia_nombre,
        total_personas=len(personas),
        personas=personas,
        relaciones_por_tipo=relaciones_por_tipo,
        eventos_por_tipo=eventos_por_tipo,
    )

    return SuccessResponse(data=response_data)

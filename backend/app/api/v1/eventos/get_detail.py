"""
Get evento detail endpoint
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.atencion_medica.salud_models import MuestraEvento
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.clasificacion.models import TipoClasificacion
from app.domains.eventos_epidemiologicos.eventos.models import (
    DetalleEventoSintomas,
    Evento,
)
from app.domains.sujetos_epidemiologicos.animales_models import Animal
from app.domains.sujetos_epidemiologicos.ciudadanos_models import (
    Ciudadano,
)
from app.domains.territorio.geografia_models import Domicilio


class CiudadanoInfo(BaseModel):
    """Información del ciudadano"""

    codigo: int = Field(..., description="Código del ciudadano")
    nombre: str = Field(..., description="Nombre")
    apellido: str = Field(..., description="Apellido")
    documento: Optional[str] = Field(None, description="Número de documento")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    sexo: Optional[str] = Field(None, description="Sexo")
    provincia: Optional[str] = Field(None, description="Provincia de residencia")
    localidad: Optional[str] = Field(None, description="Localidad de residencia")
    calle: Optional[str] = Field(None, description="Calle del domicilio")
    numero: Optional[str] = Field(None, description="Número del domicilio")
    barrio: Optional[str] = Field(None, description="Barrio popular")
    telefono: Optional[str] = Field(None, description="Teléfono de contacto")
    es_embarazada: Optional[bool] = Field(None, description="Si está embarazada")
    cobertura_social: Optional[str] = Field(None, description="Cobertura social u obra social")
    ocupacion_laboral: Optional[str] = Field(None, description="Ocupación laboral")


class AnimalInfo(BaseModel):
    """Información del animal"""

    id: int = Field(..., description="ID del animal")
    identificacion: Optional[str] = Field(None, description="Identificación del animal")
    especie: Optional[str] = Field(None, description="Especie")
    raza: Optional[str] = Field(None, description="Raza")
    provincia: Optional[str] = Field(None, description="Provincia")
    localidad: Optional[str] = Field(None, description="Localidad")


class SintomaInfo(BaseModel):
    """Información de síntoma"""

    id: int = Field(..., description="ID del síntoma")
    nombre: Optional[str] = Field(None, description="Nombre del síntoma")
    fecha_inicio: Optional[date] = Field(None, description="Fecha de inicio del síntoma")
    semana_epidemiologica: Optional[int] = Field(None, description="Semana epidemiológica de aparición")
    anio_epidemiologico: Optional[int] = Field(None, description="Año epidemiológico")


class EstudioInfo(BaseModel):
    """Información de estudio realizado sobre una muestra"""

    id: int = Field(..., description="ID del estudio")
    determinacion: Optional[str] = Field(None, description="Determinación realizada")
    tecnica: Optional[str] = Field(None, description="Técnica utilizada")
    resultado: Optional[str] = Field(None, description="Resultado del estudio")
    fecha_estudio: Optional[date] = Field(None, description="Fecha del estudio")
    fecha_recepcion: Optional[date] = Field(None, description="Fecha de recepción")


class MuestraInfo(BaseModel):
    """Información de muestra con sus estudios"""

    id: int = Field(..., description="ID de la muestra")
    tipo: Optional[str] = Field(None, description="Tipo de muestra")
    fecha_toma_muestra: Optional[date] = Field(None, description="Fecha de toma")
    establecimiento: Optional[str] = Field(None, description="Establecimiento donde se tomó")
    semana_epidemiologica: Optional[int] = Field(None, description="Semana epidemiológica")
    anio_epidemiologico: Optional[int] = Field(None, description="Año epidemiológico")
    valor: Optional[str] = Field(None, description="Valor del resultado general")
    estudios: List[EstudioInfo] = Field(default_factory=list, description="Estudios realizados sobre esta muestra")


class DiagnosticoInfo(BaseModel):
    """Información de diagnóstico"""

    id: int = Field(..., description="ID del diagnóstico")
    diagnostico: Optional[str] = Field(None, description="Diagnóstico")
    fecha: Optional[date] = Field(None, description="Fecha del diagnóstico")
    es_principal: Optional[bool] = Field(
        None, description="Si es diagnóstico principal"
    )


class EstablecimientoInfo(BaseModel):
    """Información de establecimiento"""

    id: int = Field(..., description="ID del establecimiento")
    nombre: Optional[str] = Field(None, description="Nombre del establecimiento")
    tipo: Optional[str] = Field(None, description="Tipo de establecimiento")
    provincia: Optional[str] = Field(None, description="Provincia")
    localidad: Optional[str] = Field(None, description="Localidad")


class TratamientoInfo(BaseModel):
    """Información de tratamiento"""

    id: int = Field(..., description="ID del tratamiento")
    descripcion: Optional[str] = Field(None, description="Descripción del tratamiento")
    establecimiento: Optional[str] = Field(None, description="Establecimiento de tratamiento")
    fecha_inicio: Optional[date] = Field(None, description="Fecha de inicio")
    fecha_fin: Optional[date] = Field(None, description="Fecha de fin")
    resultado: Optional[str] = Field(None, description="Resultado del tratamiento")
    recibio_tratamiento: Optional[bool] = Field(
        None, description="Si recibió tratamiento"
    )


class InternacionInfo(BaseModel):
    """Información de internación"""

    id: int = Field(..., description="ID de la internación")
    fecha_internacion: Optional[date] = Field(None, description="Fecha de internación")
    fecha_alta: Optional[date] = Field(None, description="Fecha de alta")
    requirio_uci: Optional[bool] = Field(None, description="Si requirió UCI")


class InvestigacionInfo(BaseModel):
    """Información de investigación epidemiológica"""

    id: int = Field(..., description="ID de la investigación")
    es_usuario_centinela: Optional[bool] = Field(
        None, description="Si es usuario centinela"
    )
    es_evento_centinela: Optional[bool] = Field(
        None, description="Si es evento centinela"
    )
    participo_usuario_centinela: Optional[bool] = Field(
        None, description="Si participó usuario centinela"
    )
    id_usuario_centinela_participante: Optional[int] = Field(
        None, description="ID del usuario centinela que participó"
    )
    id_usuario_registro: Optional[int] = Field(
        None, description="ID del usuario que registró"
    )
    id_snvs_evento: Optional[int] = Field(
        None, description="ID SNVS del evento"
    )
    es_investigacion_terreno: Optional[bool] = Field(
        None, description="Si fue investigación de terreno"
    )
    fecha_investigacion: Optional[date] = Field(
        None, description="Fecha de investigación"
    )
    tipo_lugar_investigacion: Optional[str] = Field(
        None, description="Tipo y lugar de investigación"
    )
    origen_financiamiento: Optional[str] = Field(
        None, description="Origen del financiamiento"
    )


class ContactoInfo(BaseModel):
    """Información de contactos"""

    id: int = Field(..., description="ID del registro de contactos")
    contacto_caso_confirmado: Optional[bool] = Field(
        None, description="Contacto con caso confirmado"
    )
    contacto_caso_sospechoso: Optional[bool] = Field(
        None, description="Contacto con caso sospechoso"
    )
    contactos_menores_un_ano: Optional[int] = Field(
        None, description="Contactos menores de 1 año"
    )
    contactos_vacunados: Optional[int] = Field(None, description="Contactos vacunados")
    contactos_embarazadas: Optional[int] = Field(
        None, description="Contactos embarazadas"
    )


class AmbitoConcurrenciaInfo(BaseModel):
    """Información de ámbito de concurrencia"""

    id: int = Field(..., description="ID del ámbito")
    nombre_lugar: Optional[str] = Field(None, description="Nombre del lugar")
    tipo_lugar: Optional[str] = Field(None, description="Tipo de lugar")
    localidad: Optional[str] = Field(None, description="Localidad del ámbito")
    fecha_ocurrencia: Optional[date] = Field(None, description="Fecha de ocurrencia")
    frecuencia_concurrencia: Optional[str] = Field(
        None, description="Frecuencia de concurrencia"
    )


class AntecedenteInfo(BaseModel):
    """Información de antecedente epidemiológico"""

    id: int = Field(..., description="ID del antecedente")
    descripcion: Optional[str] = Field(None, description="Descripción del antecedente")
    fecha_antecedente: Optional[date] = Field(None, description="Fecha del antecedente")


class VacunaInfo(BaseModel):
    """Información de vacuna"""

    id: int = Field(..., description="ID de la vacuna")
    nombre_vacuna: Optional[str] = Field(None, description="Nombre de la vacuna")
    fecha_ultima_dosis: Optional[date] = Field(
        None, description="Fecha de última dosis"
    )
    dosis_total: Optional[int] = Field(None, description="Total de dosis")


class DomicilioGeograficoInfo(BaseModel):
    """Información geográfica del domicilio al momento del evento"""

    latitud: Optional[Decimal] = Field(None, description="Latitud del domicilio")
    longitud: Optional[Decimal] = Field(None, description="Longitud del domicilio")
    calle: Optional[str] = Field(None, description="Calle del domicilio")
    numero: Optional[str] = Field(None, description="Número del domicilio")
    localidad: Optional[str] = Field(None, description="Localidad del domicilio")
    departamento: Optional[str] = Field(None, description="Departamento del domicilio")
    provincia: Optional[str] = Field(None, description="Provincia del domicilio")


class EventoDetailResponse(BaseModel):
    """Respuesta detallada de un evento (EVENT-CENTERED)"""

    # Datos básicos del evento
    id: int = Field(..., description="ID del evento")
    id_evento_caso: int = Field(..., description="ID del caso")
    tipo_eno_id: int = Field(..., description="ID del tipo ENO")
    tipo_eno_nombre: Optional[str] = Field(None, description="Nombre del tipo ENO")
    tipo_eno_descripcion: Optional[str] = Field(
        None, description="Descripción del tipo ENO"
    )
    enfermedad: Optional[str] = Field(None, description="Enfermedad relacionada")

    # Fechas importantes
    fecha_minima_evento: date = Field(..., description="Fecha mínima del evento")
    fecha_inicio_sintomas: Optional[date] = Field(
        None, description="Fecha de inicio de síntomas"
    )
    fecha_apertura_caso: Optional[date] = Field(
        None, description="Fecha de apertura del caso"
    )
    fecha_primera_consulta: Optional[date] = Field(
        None, description="Fecha de primera consulta"
    )
    fecha_notificacion: Optional[date] = Field(
        None, description="Fecha de notificación"
    )
    fecha_diagnostico: Optional[date] = Field(None, description="Fecha de diagnóstico")
    fecha_investigacion: Optional[date] = Field(
        None, description="Fecha de investigación"
    )

    # Semanas epidemiológicas
    semana_epidemiologica_apertura: Optional[int] = Field(
        None, description="Semana epidemiológica de apertura"
    )
    anio_epidemiologico_apertura: Optional[int] = Field(
        None, description="Año epidemiológico de apertura"
    )
    semana_epidemiologica_sintomas: Optional[int] = Field(
        None, description="Semana epidemiológica de síntomas"
    )

    # Clasificación del evento
    clasificacion_estrategia: Optional[TipoClasificacion] = Field(
        None, description="Clasificación estratégica del evento"
    )
    confidence_score: Optional[float] = Field(None, description="Score de confianza")
    metadata_clasificacion: Optional[Dict[str, Any]] = Field(
        None, description="Metadata de clasificación"
    )
    metadata_extraida: Optional[Dict[str, Any]] = Field(
        None, description="Metadata extraída"
    )

    # Trazabilidad de clasificación
    id_estrategia_aplicada: Optional[int] = Field(
        None, description="ID de la estrategia que se aplicó para clasificar"
    )
    estrategia_nombre: Optional[str] = Field(
        None, description="Nombre de la estrategia aplicada"
    )
    trazabilidad_clasificacion: Optional[Dict[str, Any]] = Field(
        None, description="Trazabilidad completa: reglas evaluadas, condiciones cumplidas, razón de clasificación"
    )

    # Sujeto del evento
    tipo_sujeto: str = Field(..., description="Tipo de sujeto")
    ciudadano: Optional[CiudadanoInfo] = Field(
        None, description="Información del ciudadano"
    )
    animal: Optional[AnimalInfo] = Field(None, description="Información del animal")

    # Información geográfica del domicilio (snapshot del momento del evento)
    domicilio_geografico: Optional[DomicilioGeograficoInfo] = Field(
        None, description="Snapshot geográfico del domicilio al momento del evento"
    )

    # Establecimientos relacionados
    establecimiento_consulta: Optional[EstablecimientoInfo] = Field(
        None, description="Establecimiento de consulta"
    )
    establecimiento_notificacion: Optional[EstablecimientoInfo] = Field(
        None, description="Establecimiento que notificó"
    )
    establecimiento_carga: Optional[EstablecimientoInfo] = Field(
        None, description="Establecimiento de carga"
    )

    # Estados y flags
    es_caso_sintomatico: Optional[bool] = Field(None, description="Si es sintomático")
    requiere_revision_especie: Optional[bool] = Field(
        None, description="Si requiere revisión"
    )

    # Observaciones y datos originales
    observaciones_texto: Optional[str] = Field(None, description="Observaciones")
    id_origen: Optional[str] = Field(None, description="ID del sistema origen")
    datos_originales_csv: Optional[Dict[str, Any]] = Field(
        None, description="Datos originales del CSV"
    )

    # TODAS las relaciones del evento (EVENT-CENTERED)
    sintomas: List[SintomaInfo] = Field(
        default_factory=list, description="Síntomas del evento"
    )
    muestras: List[MuestraInfo] = Field(
        default_factory=list, description="Muestras del evento"
    )
    diagnosticos: List[DiagnosticoInfo] = Field(
        default_factory=list, description="Diagnósticos del evento"
    )
    tratamientos: List[TratamientoInfo] = Field(
        default_factory=list, description="Tratamientos del evento"
    )
    internaciones: List[InternacionInfo] = Field(
        default_factory=list, description="Internaciones del evento"
    )
    investigaciones: List[InvestigacionInfo] = Field(
        default_factory=list, description="Investigaciones del evento"
    )
    contactos: List[ContactoInfo] = Field(
        default_factory=list, description="Contactos del evento"
    )
    ambitos_concurrencia: List[AmbitoConcurrenciaInfo] = Field(
        default_factory=list, description="Ámbitos de concurrencia"
    )
    antecedentes: List[AntecedenteInfo] = Field(
        default_factory=list, description="Antecedentes epidemiológicos"
    )
    vacunas: List[VacunaInfo] = Field(
        default_factory=list, description="Vacunas relacionadas"
    )

    # Timestamps
    created_at: Optional[Any] = Field(None, description="Fecha de creación")
    updated_at: Optional[Any] = Field(None, description="Fecha de actualización")

    # Conteos
    total_sintomas: int = Field(0, description="Total de síntomas")
    total_muestras: int = Field(0, description="Total de muestras")
    total_diagnosticos: int = Field(0, description="Total de diagnósticos")
    total_tratamientos: int = Field(0, description="Total de tratamientos")
    total_internaciones: int = Field(0, description="Total de internaciones")
    total_investigaciones: int = Field(0, description="Total de investigaciones")

    model_config = ConfigDict(from_attributes=True)


logger = logging.getLogger(__name__)


async def get_evento_detail(
    evento_id: int,
    include_relations: bool = Query(True, description="Incluir datos relacionados"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[EventoDetailResponse]:
    """
    Obtiene el detalle completo de un evento.

    **Incluye:**
    - Datos completos del evento
    - Información del ciudadano o animal
    - Síntomas, muestras, diagnósticos
    - Metadata de clasificación
    - Timeline de eventos
    """

    logger.info(
        f"🔍 Obteniendo detalle de evento {evento_id} para usuario {current_user.email}"
    )

    try:
        # Query con TODAS las relaciones necesarias (EVENT-CENTERED)
        query = select(Evento).where(Evento.id == evento_id)

        if include_relations:
            query = query.options(
                selectinload(Evento.tipo_eno),
                selectinload(Evento.estrategia_aplicada),
                # Sujetos del evento
                selectinload(Evento.ciudadano).selectinload(Ciudadano.datos),
                selectinload(Evento.animal).selectinload(Animal.localidad),
                # Datos geográficos del evento (normalized domicilio)
                selectinload(Evento.domicilio).selectinload(Domicilio.localidad),
                # Establecimientos del evento
                selectinload(Evento.establecimiento_consulta),
                selectinload(Evento.establecimiento_notificacion),
                selectinload(Evento.establecimiento_carga),
                # Salud y diagnósticos del evento
                selectinload(Evento.sintomas).selectinload(
                    DetalleEventoSintomas.sintoma
                ),
                selectinload(Evento.muestras).selectinload(MuestraEvento.muestra),
                selectinload(Evento.muestras).selectinload(MuestraEvento.establecimiento),
                selectinload(Evento.muestras).selectinload(MuestraEvento.estudios),
                selectinload(Evento.diagnosticos),
                selectinload(Evento.tratamientos),
                selectinload(Evento.internaciones),
                # Investigación epidemiológica del evento
                selectinload(Evento.investigaciones),
                selectinload(Evento.contactos),
                selectinload(Evento.ambitos_concurrencia),
                selectinload(Evento.antecedentes),
                # Prevención del evento
                selectinload(Evento.vacunas),
            )

        result = await db.execute(query)
        evento = result.scalar_one_or_none()

        if not evento:
            logger.warning(f"❌ Evento {evento_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evento {evento_id} no encontrado",
            )

        # Preparar respuesta detallada (EVENT-CENTERED)
        response = EventoDetailResponse(
            # Datos básicos del evento
            id=evento.id,
            id_evento_caso=evento.id_evento_caso,
            tipo_eno_id=evento.id_tipo_eno,
            tipo_eno_nombre=evento.tipo_eno.nombre if evento.tipo_eno else None,
            tipo_eno_descripcion=(
                evento.tipo_eno.descripcion if evento.tipo_eno else None
            ),
            enfermedad=getattr(evento, "enfermedad", None),
            # Fechas importantes del evento
            fecha_minima_evento=evento.fecha_minima_evento,
            fecha_inicio_sintomas=evento.fecha_inicio_sintomas,
            fecha_apertura_caso=evento.fecha_apertura_caso,
            fecha_primera_consulta=evento.fecha_primera_consulta,
            fecha_notificacion=getattr(evento, "fecha_notificacion", None),
            fecha_diagnostico=getattr(evento, "fecha_diagnostico", None),
            fecha_investigacion=getattr(evento, "fecha_investigacion", None),
            # Semanas epidemiológicas
            semana_epidemiologica_apertura=evento.semana_epidemiologica_apertura,
            anio_epidemiologico_apertura=evento.anio_epidemiologico_apertura,
            semana_epidemiologica_sintomas=evento.semana_epidemiologica_sintomas,
            # Clasificación del evento
            clasificacion_estrategia=evento.clasificacion_estrategia,
            confidence_score=evento.confidence_score,
            metadata_clasificacion=evento.metadata_clasificacion,
            metadata_extraida=evento.metadata_extraida,
            # Trazabilidad de clasificación
            id_estrategia_aplicada=evento.id_estrategia_aplicada,
            estrategia_nombre=evento.estrategia_aplicada.name if evento.estrategia_aplicada else None,
            trazabilidad_clasificacion=evento.trazabilidad_clasificacion,
            # Tipo de sujeto
            tipo_sujeto=(
                "humano"
                if evento.ciudadano
                else "animal" if evento.animal else "desconocido"
            ),
            # Estados del evento
            es_caso_sintomatico=evento.es_caso_sintomatico,
            requiere_revision_especie=evento.requiere_revision_especie,
            # Observaciones y datos originales
            observaciones_texto=evento.observaciones_texto,
            id_origen=evento.id_origen,
            datos_originales_csv=evento.datos_originales_csv,
            # Timestamps
            created_at=evento.created_at,
            updated_at=evento.updated_at,
            # Conteos iniciales
            total_sintomas=len(evento.sintomas or []),
            total_muestras=len(evento.muestras or []),
            total_diagnosticos=len(evento.diagnosticos or []),
            total_tratamientos=len(evento.tratamientos or []),
            total_internaciones=len(evento.internaciones or []),
            total_investigaciones=len(evento.investigaciones or []),
        )

        # Agregar datos del sujeto
        if evento.ciudadano:
            # Get location and address from evento's domicilio (not ciudadano's)
            provincia_nombre = None
            localidad_nombre = None
            calle_domicilio = None
            numero_domicilio = None
            barrio_popular = None
            if evento.domicilio:
                calle_domicilio = evento.domicilio.calle
                numero_domicilio = evento.domicilio.numero
                # Note: barrio_popular might not exist in Domicilio model
                barrio_popular = getattr(evento.domicilio, 'barrio_popular', None)
                if evento.domicilio.localidad:
                    localidad_nombre = evento.domicilio.localidad.nombre

            # Get contact info and additional data from first datos record
            telefono = None
            es_embarazada = None
            cobertura_social = None
            ocupacion_laboral = None
            if evento.ciudadano.datos:
                primer_datos = evento.ciudadano.datos[0]
                telefono = primer_datos.informacion_contacto
                es_embarazada = getattr(primer_datos, "es_embarazada", None)
                cobertura_social = getattr(primer_datos, "cobertura_social_obra_social", None)
                ocupacion_laboral = getattr(primer_datos, "ocupacion_laboral", None)

            response.ciudadano = CiudadanoInfo(
                codigo=evento.ciudadano.codigo_ciudadano,
                nombre=evento.ciudadano.nombre,
                apellido=evento.ciudadano.apellido,
                documento=(
                    str(evento.ciudadano.numero_documento)
                    if evento.ciudadano.numero_documento
                    else None
                ),
                fecha_nacimiento=evento.ciudadano.fecha_nacimiento,
                sexo=evento.ciudadano.sexo_biologico,
                provincia=provincia_nombre,
                localidad=localidad_nombre,
                calle=calle_domicilio,
                numero=numero_domicilio,
                barrio=barrio_popular,
                telefono=telefono,
                es_embarazada=es_embarazada,
                cobertura_social=cobertura_social,
                ocupacion_laboral=ocupacion_laboral,
            )

        if evento.animal:
            response.animal = AnimalInfo(
                id=evento.animal.id,
                identificacion=evento.animal.identificacion,
                especie=evento.animal.especie,
                raza=evento.animal.raza,
                provincia=evento.animal.provincia,
                localidad=evento.animal.localidad,
            )

        # Agregar establecimientos del evento
        if evento.establecimiento_consulta:
            response.establecimiento_consulta = EstablecimientoInfo(
                id=evento.establecimiento_consulta.id,
                nombre=evento.establecimiento_consulta.nombre,
                tipo=getattr(evento.establecimiento_consulta, "tipo", None),
                provincia=getattr(evento.establecimiento_consulta, "provincia", None),
                localidad=getattr(evento.establecimiento_consulta, "localidad", None),
            )

        if evento.establecimiento_notificacion:
            response.establecimiento_notificacion = EstablecimientoInfo(
                id=evento.establecimiento_notificacion.id,
                nombre=evento.establecimiento_notificacion.nombre,
                tipo=getattr(evento.establecimiento_notificacion, "tipo", None),
                provincia=getattr(
                    evento.establecimiento_notificacion, "provincia", None
                ),
                localidad=getattr(
                    evento.establecimiento_notificacion, "localidad", None
                ),
            )

        if evento.establecimiento_carga:
            response.establecimiento_carga = EstablecimientoInfo(
                id=evento.establecimiento_carga.id,
                nombre=evento.establecimiento_carga.nombre,
                tipo=getattr(evento.establecimiento_carga, "tipo", None),
                provincia=getattr(evento.establecimiento_carga, "provincia", None),
                localidad=getattr(evento.establecimiento_carga, "localidad", None),
            )

        # Agregar datos geográficos del domicilio (normalized, inmutable)
        if evento.domicilio:
            localidad_nombre = None
            departamento_nombre = None
            provincia_nombre = None

            if evento.domicilio.localidad:
                localidad_nombre = evento.domicilio.localidad.nombre

            response.domicilio_geografico = DomicilioGeograficoInfo(
                latitud=evento.domicilio.latitud,
                longitud=evento.domicilio.longitud,
                calle=evento.domicilio.calle,
                numero=evento.domicilio.numero,
                localidad=localidad_nombre,
                departamento=departamento_nombre,
                provincia=provincia_nombre,
            )

        # Agregar TODAS las relaciones del evento si se solicitaron (EVENT-CENTERED)
        if include_relations:
            # Síntomas del evento
            response.sintomas = [
                SintomaInfo(
                    id=s.id,
                    nombre=(
                        s.sintoma.signo_sintoma
                        if hasattr(s, "sintoma") and s.sintoma
                        else None
                    ),
                    fecha_inicio=s.fecha_inicio_sintoma,
                    semana_epidemiologica=s.semana_epidemiologica_aparicion_sintoma,
                    anio_epidemiologico=s.anio_epidemiologico_sintoma,
                )
                for s in (evento.sintomas or [])
            ]

            # Muestras del evento con sus estudios anidados
            response.muestras = [
                MuestraInfo(
                    id=m.id,
                    tipo=m.muestra.descripcion if m.muestra else None,
                    fecha_toma_muestra=m.fecha_toma_muestra,
                    establecimiento=m.establecimiento.nombre if m.establecimiento else None,
                    semana_epidemiologica=m.semana_epidemiologica_muestra,
                    anio_epidemiologico=m.anio_epidemiologico_muestra,
                    valor=m.valor,
                    estudios=[
                        EstudioInfo(
                            id=est.id,
                            determinacion=est.determinacion,
                            tecnica=est.tecnica,
                            resultado=est.resultado,
                            fecha_estudio=est.fecha_estudio,
                            fecha_recepcion=est.fecha_recepcion,
                        )
                        for est in (m.estudios or [])
                    ],
                )
                for m in (evento.muestras or [])
            ]

            # Diagnósticos del evento
            response.diagnosticos = [
                DiagnosticoInfo(
                    id=d.id,
                    diagnostico=getattr(d, "metodo_diagnostico", None) or getattr(d, "resultado", None),
                    fecha=getattr(d, "fecha_diagnostico", None),
                    es_principal=None,
                )
                for d in (evento.diagnosticos or [])
            ]

            # Tratamientos del evento
            response.tratamientos = [
                TratamientoInfo(
                    id=t.id,
                    descripcion=getattr(t, "descripcion_tratamiento", None),
                    establecimiento=getattr(t, "establecimiento_tratamiento", None),
                    fecha_inicio=getattr(t, "fecha_inicio_tratamiento", None),
                    fecha_fin=getattr(t, "fecha_fin_tratamiento", None),
                    resultado=getattr(t, "resultado_tratamiento", None),
                    recibio_tratamiento=None,  # Este campo no existe en el modelo
                )
                for t in (evento.tratamientos or [])
            ]

            # Internaciones del evento
            response.internaciones = [
                InternacionInfo(
                    id=i.id,
                    fecha_internacion=getattr(i, "fecha_internacion", None),
                    fecha_alta=getattr(i, "fecha_alta_internacion", None),
                    requirio_uci=getattr(i, "requirio_uci", None),
                )
                for i in (evento.internaciones or [])
            ]

            # Investigaciones del evento
            response.investigaciones = [
                InvestigacionInfo(
                    id=inv.id,
                    es_usuario_centinela=getattr(inv, "es_usuario_centinela", None),
                    es_evento_centinela=getattr(inv, "es_evento_centinela", None),
                    participo_usuario_centinela=getattr(inv, "participo_usuario_centinela", None),
                    id_usuario_centinela_participante=getattr(inv, "id_usuario_centinela_participante", None),
                    id_usuario_registro=getattr(inv, "id_usuario_registro", None),
                    id_snvs_evento=getattr(inv, "id_snvs_evento", None),
                    es_investigacion_terreno=getattr(inv, "es_investigacion_terreno", None),
                    fecha_investigacion=getattr(inv, "fecha_investigacion", None),
                    tipo_lugar_investigacion=getattr(inv, "tipo_y_lugar_investigacion", None),
                    origen_financiamiento=getattr(inv, "origen_financiamiento", None),
                )
                for inv in (evento.investigaciones or [])
            ]

            # Contactos del evento
            response.contactos = [
                ContactoInfo(
                    id=c.id,
                    contacto_caso_confirmado=getattr(
                        c, "hubo_contacto_con_caso_confirmado", None
                    ),
                    contacto_caso_sospechoso=getattr(
                        c, "hubo_contacto_con_caso_sospechoso", None
                    ),
                    contactos_menores_un_ano=getattr(
                        c, "cantidad_contactos_menores_un_anio", None
                    ),
                    contactos_vacunados=getattr(
                        c, "cantidad_contactos_vacunados", None
                    ),
                    contactos_embarazadas=getattr(
                        c, "cantidad_contactos_embarazadas", None
                    ),
                )
                for c in (evento.contactos or [])
            ]

            # Ámbitos de concurrencia del evento
            response.ambitos_concurrencia = [
                AmbitoConcurrenciaInfo(
                    id=amb.id,
                    nombre_lugar=getattr(amb, "nombre_lugar_ocurrencia", None),
                    tipo_lugar=getattr(amb, "tipo_lugar_ocurrencia", None),
                    localidad=getattr(amb, "localidad_ambito_ocurrencia", None),
                    fecha_ocurrencia=getattr(amb, "fecha_ambito_ocurrencia", None),
                    frecuencia_concurrencia=(
                        str(getattr(amb, "frecuencia_concurrencia", None))
                        if getattr(amb, "frecuencia_concurrencia", None)
                        else None
                    ),
                )
                for amb in (evento.ambitos_concurrencia or [])
            ]

            # Antecedentes epidemiológicos del evento
            response.antecedentes = [
                AntecedenteInfo(
                    id=ant.id,
                    descripcion=(
                        getattr(ant.antecedente_epidemiologico_rel, "descripcion", None)
                        if hasattr(ant, "antecedente_epidemiologico_rel")
                        else None
                    ),
                    fecha_antecedente=getattr(
                        ant, "fecha_antecedente_epidemiologico", None
                    ),
                )
                for ant in (evento.antecedentes or [])
            ]

            # Vacunas relacionadas al evento
            response.vacunas = [
                VacunaInfo(
                    id=v.id,
                    nombre_vacuna=getattr(v, "nombre_vacuna", None),
                    fecha_ultima_dosis=getattr(v, "fecha_ultima_dosis", None),
                    dosis_total=getattr(v, "dosis_total", None),
                )
                for v in (evento.vacunas or [])
            ]

        logger.info(f"✅ Detalle de evento {evento_id} obtenido")
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error obteniendo evento {evento_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo evento: {str(e)}",
        )

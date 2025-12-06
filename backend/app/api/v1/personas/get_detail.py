"""
Get persona detail endpoint - Vista PERSON-CENTERED
Muestra toda la información de una persona y TODOS sus eventos completos.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAnyRole
from app.domains.vigilancia_nominal.models.salud import MuestraCasoEpidemiologico
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.models.caso import (    DetalleCasoSintomas, CasoEpidemiologico, CasoGrupoEnfermedad)
from app.domains.vigilancia_nominal.models.sujetos import Animal
from app.domains.vigilancia_nominal.models.sujetos import (
    Ciudadano,
    CiudadanoDomicilio,
)
from app.domains.territorio.geografia_models import Domicilio

# =============================================================================
# SCHEMAS PARA DATOS DEL EVENTO (similares a eventos/get_detail.py)
# =============================================================================


class SintomaInfo(BaseModel):
    """Información de un síntoma"""

    id: int
    nombre: str
    fecha_inicio: Optional[date] = None


class MuestraInfo(BaseModel):
    """Información de una muestra"""

    id: int
    tipo_muestra: Optional[str] = None
    fecha_toma: Optional[date] = None
    fecha_recepcion: Optional[date] = None
    resultado: Optional[str] = None


class EstudioInfo(BaseModel):
    """Información de un estudio"""

    id: int
    determinacion: Optional[str] = None
    tecnica: Optional[str] = None
    resultado: Optional[str] = None
    fecha_estudio: Optional[date] = None


class DiagnosticoInfo(BaseModel):
    """Información de un diagnóstico"""

    id: int
    diagnostico: str
    fecha: Optional[date] = None


class TratamientoInfo(BaseModel):
    """Información de tratamiento"""

    id: int
    tratamiento: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    resultado: Optional[str] = None


class InternacionInfo(BaseModel):
    """Información de internación"""

    id: int
    establecimiento: Optional[str] = None
    fecha_internacion: Optional[date] = None
    fecha_alta: Optional[date] = None
    cuidados_intensivos: bool = False


class VacunaInfo(BaseModel):
    """Información de vacuna"""

    id: int
    vacuna: str
    dosis: Optional[int] = None
    fecha_aplicacion: Optional[date] = None


class DomicilioGeograficoInfo(BaseModel):
    """Información geográfica del domicilio"""

    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    localidad: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None


class CasoEpidemiologicoCompleto(BaseModel):
    """CasoEpidemiologico completo con toda su información"""

    # Identificación
    id: int
    id_evento_caso: int
    tipo_eno_id: Optional[int] = None
    tipo_eno_nombre: Optional[str] = None
    grupos_eno_nombres: List[str] = Field(default_factory=list, description="Nombres de grupos ENO (puede pertenecer a múltiples)")

    # Fechas
    fecha_minima_caso: Optional[date] = None
    fecha_inicio_sintomas: Optional[date] = None
    fecha_apertura: Optional[date] = None

    # Clasificación
    clasificacion_estrategia: Optional[str] = None
    clasificacion_manual: Optional[str] = None
    clasificacion_algoritmo: Optional[str] = None

    # Semanas epidemiológicas
    semana_epidemiologica_apertura: Optional[int] = None
    anio_epidemiologico_apertura: Optional[int] = None

    # Flags
    es_sintomatico: bool = False
    requiere_revision: bool = False

    # Domicilio del evento
    domicilio: Optional[DomicilioGeograficoInfo] = None

    # Datos clínicos
    sintomas: List[SintomaInfo] = []
    muestras: List[MuestraInfo] = []
    estudios: List[EstudioInfo] = []
    diagnosticos: List[DiagnosticoInfo] = []
    tratamientos: List[TratamientoInfo] = []
    internaciones: List[InternacionInfo] = []
    vacunas: List[VacunaInfo] = []

    model_config = ConfigDict(from_attributes=True)


class DomicilioInfo(BaseModel):
    """Información de domicilio actual"""

    calle: Optional[str] = None
    numero: Optional[str] = None
    barrio: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None


class PersonaDetailResponse(BaseModel):
    """Respuesta detallada de una persona (PERSON-CENTERED)"""

    # Identificación
    tipo_sujeto: str = Field(..., description="Tipo: humano/animal")
    persona_id: int = Field(..., description="ID de la persona")

    # Datos personales (ciudadano)
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    nombre_completo: str = Field(..., description="Nombre completo")
    documento_tipo: Optional[str] = None
    documento_numero: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    edad_actual: Optional[int] = None
    sexo_biologico: Optional[str] = None
    genero_autopercibido: Optional[str] = None

    # Datos de animal
    especie: Optional[str] = None
    raza: Optional[str] = None
    identificacion_animal: Optional[str] = None

    # Ubicación
    domicilio: Optional[DomicilioInfo] = None
    provincia: Optional[str] = None
    localidad: Optional[str] = None

    # Contacto
    telefono: Optional[str] = None
    obra_social: Optional[str] = None

    # CasoEpidemiologicos COMPLETOS (toda la información)
    total_eventos: int = Field(..., description="Total de eventos")
    eventos: List[CasoEpidemiologicoCompleto] = Field(
        default_factory=list, description="Lista completa de eventos"
    )

    # Estadísticas agregadas
    tipos_eventos_unicos: int = Field(
        0, description="Cantidad de tipos de eventos diferentes"
    )
    eventos_confirmados: int = 0
    eventos_sospechosos: int = 0
    eventos_probables: int = 0
    eventos_descartados: int = 0

    # Fechas relevantes
    primer_evento_fecha: Optional[date] = None
    ultimo_evento_fecha: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


logger = logging.getLogger(__name__)


async def get_persona_detail(
    tipo_sujeto: str = Path(..., description="Tipo de sujeto: humano o animal"),
    persona_id: int = Path(..., description="ID de la persona"),
    include_relations: bool = Query(
        True, description="Incluir relaciones completas (síntomas, muestras, etc.)"
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> SuccessResponse[PersonaDetailResponse]:
    """
    Obtiene el detalle completo de una persona (ciudadano o animal).

    **Vista PERSON-CENTERED:**
    - Toda la información de la persona
    - TODOS sus eventos completos con síntomas, muestras, estudios, etc.
    - Estadísticas agregadas por tipo de evento
    """

    logger.info(
        f"🔍 Obteniendo detalle de persona {tipo_sujeto}/{persona_id} para usuario {current_user.email}"
    )

    try:
        if tipo_sujeto == "humano":
            # Buscar ciudadano
            query = (
                select(Ciudadano)
                .where(Ciudadano.codigo_ciudadano == persona_id)
                .options(
                    selectinload(Ciudadano.domicilios)
                    .selectinload(CiudadanoDomicilio.domicilio),  # Cambiado de localidad a domicilio
                    selectinload(Ciudadano.datos),
                )
            )
            result = await db.execute(query)
            persona = result.scalar_one_or_none()

            if not persona:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ciudadano {persona_id} no encontrado",
                )

            # Obtener todos los eventos del ciudadano CON EAGER LOADING
            eventos_query = select(CasoEpidemiologico).where(CasoEpidemiologico.codigo_ciudadano == persona_id)

            if include_relations:
                eventos_query = eventos_query.options(
                    selectinload(CasoEpidemiologico.enfermedad),  # Cambiado de tipo_eno a enfermedad
                    selectinload(CasoEpidemiologico.caso_grupos).selectinload(CasoGrupoEnfermedad.grupo),  # Cambiado de grupos_enfermedad a caso_grupos
                    selectinload(CasoEpidemiologico.domicilio)
                    .selectinload(Domicilio.localidad),
                    selectinload(CasoEpidemiologico.sintomas).selectinload(
                        DetalleCasoSintomas.sintoma
                    ),
                    selectinload(CasoEpidemiologico.muestras).selectinload(MuestraCasoEpidemiologico.muestra),
                    selectinload(CasoEpidemiologico.muestras).selectinload(MuestraCasoEpidemiologico.estudios),
                    selectinload(CasoEpidemiologico.diagnosticos),
                    selectinload(CasoEpidemiologico.tratamientos),
                    selectinload(CasoEpidemiologico.internaciones),
                    selectinload(CasoEpidemiologico.vacunas),
                )

            eventos_result = await db.execute(eventos_query)
            eventos = eventos_result.scalars().all()

            # Preparar datos de domicilio
            domicilio_info = None
            if persona.domicilios:
                primer_domicilio = persona.domicilios[0]
                provincia_nombre = None
                localidad_nombre = None
                # Acceder a localidad a través de la relación domicilio
                if primer_domicilio.domicilio and primer_domicilio.domicilio.localidad:
                    localidad_nombre = primer_domicilio.domicilio.localidad.nombre

                # Access domicilio fields through the relationship
                domicilio_obj = primer_domicilio.domicilio
                
                domicilio_info = DomicilioInfo(
                    calle=domicilio_obj.calle if domicilio_obj else None,
                    numero=domicilio_obj.numero if domicilio_obj else None,
                    barrio=None,  # Barrio field does not exist in Domicilio model
                    localidad=localidad_nombre,
                    provincia=provincia_nombre,
                )

            # Datos de contacto
            telefono = None
            obra_social = None
            if persona.datos:
                primer_datos = persona.datos[0]
                telefono = primer_datos.informacion_contacto
                obra_social = primer_datos.cobertura_social_obra_social

            # Preparar respuesta base
            response = PersonaDetailResponse(
                tipo_sujeto="humano",
                persona_id=persona.codigo_ciudadano,
                nombre=persona.nombre,
                apellido=persona.apellido,
                nombre_completo=f"{persona.nombre or ''} {persona.apellido or ''}".strip()
                or "Sin nombre",
                documento_tipo=persona.tipo_documento,
                documento_numero=(
                    str(persona.numero_documento) if persona.numero_documento else None
                ),
                fecha_nacimiento=persona.fecha_nacimiento,
                edad_actual=None,  # TODO: calcular edad actual
                sexo_biologico=persona.sexo_biologico,
                genero_autopercibido=persona.genero_autopercibido,
                domicilio=domicilio_info,
                provincia=domicilio_info.provincia if domicilio_info else None,
                localidad=domicilio_info.localidad if domicilio_info else None,
                telefono=telefono,
                obra_social=obra_social,
                total_eventos=len(eventos),
                eventos=[],
            )

        elif tipo_sujeto == "animal":
            # Buscar animal
            query = (
                select(Animal)
                .where(Animal.id == persona_id)
                .options(
                    selectinload(Animal.localidad),
                )
            )
            result = await db.execute(query)
            persona = result.scalar_one_or_none()

            if not persona:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Animal {persona_id} no encontrado",
                )

            # Obtener todos los eventos del animal
            eventos_query = select(CasoEpidemiologico).where(CasoEpidemiologico.id_animal == persona_id)

            if include_relations:
                eventos_query = eventos_query.options(
                    selectinload(CasoEpidemiologico.enfermedad),  # Cambiado de tipo_eno a enfermedad
                    selectinload(CasoEpidemiologico.caso_grupos).selectinload(CasoGrupoEnfermedad.grupo),  # Cambiado de grupos_enfermedad a caso_grupos
                    selectinload(CasoEpidemiologico.domicilio)
                    .selectinload(Domicilio.localidad),
                    selectinload(CasoEpidemiologico.sintomas).selectinload(
                        DetalleCasoSintomas.sintoma
                    ),
                    selectinload(CasoEpidemiologico.muestras).selectinload(MuestraCasoEpidemiologico.muestra),
                    selectinload(CasoEpidemiologico.muestras).selectinload(MuestraCasoEpidemiologico.estudios),
                    selectinload(CasoEpidemiologico.diagnosticos),
                    selectinload(CasoEpidemiologico.tratamientos),
                    selectinload(CasoEpidemiologico.internaciones),
                    selectinload(CasoEpidemiologico.vacunas),
                )

            eventos_result = await db.execute(eventos_query)
            eventos = eventos_result.scalars().all()

            # Preparar respuesta base
            response = PersonaDetailResponse(
                tipo_sujeto="animal",
                persona_id=persona.id,
                nombre_completo=persona.identificacion or f"{persona.especie} #{persona.id}",
                especie=persona.especie,
                raza=persona.raza,
                identificacion_animal=persona.identificacion,
                provincia=persona.provincia,
                localidad=persona.localidad,
                total_eventos=len(eventos),
                eventos=[],
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tipo_sujeto debe ser 'humano' o 'animal'",
            )

        # Procesar eventos completos (común para ambos)
        eventos_completos = []
        tipos_eventos_set = set()
        confirmados = 0
        sospechosos = 0
        probables = 0
        descartados = 0

        for evento in eventos:
            # Preparar domicilio del evento
            domicilio_evento = None
            if evento.domicilio:
                localidad_nombre = None
                departamento_nombre = None
                provincia_nombre = None

                if evento.domicilio.localidad:
                    localidad_nombre = evento.domicilio.localidad.nombre

                domicilio_evento = DomicilioGeograficoInfo(
                    latitud=evento.domicilio.latitud,
                    longitud=evento.domicilio.longitud,
                    calle=evento.domicilio.calle,
                    numero=evento.domicilio.numero,
                    localidad=localidad_nombre,
                    departamento=departamento_nombre,
                    provincia=provincia_nombre,
                )

            # Preparar síntomas
            sintomas_info = []
            if include_relations and evento.sintomas:
                for sintoma_rel in evento.sintomas:
                    sintomas_info.append(
                        SintomaInfo(
                            id=sintoma_rel.id,
                            nombre=(
                                sintoma_rel.sintoma.signo_sintoma
                                if sintoma_rel.sintoma
                                else "Desconocido"
                            ),
                            fecha_inicio=sintoma_rel.fecha_inicio_sintoma,
                        )
                    )

            # Preparar muestras
            muestras_info = []
            if include_relations and evento.muestras:
                for muestra in evento.muestras:
                    muestras_info.append(
                        MuestraInfo(
                            id=muestra.id,
                            tipo_muestra=muestra.muestra.descripcion if muestra.muestra else None,
                            fecha_toma=muestra.fecha_toma_muestra,
                            fecha_recepcion=None,  # Este campo no existe en MuestraCasoEpidemiologico
                            resultado=muestra.valor,  # Campo valor contiene el resultado general
                        )
                    )

            # Preparar estudios desde las muestras
            estudios_info = []
            if include_relations and evento.muestras:
                for muestra in evento.muestras:
                    if hasattr(muestra, 'estudios') and muestra.estudios:
                        for estudio in muestra.estudios:
                            estudios_info.append(
                                EstudioInfo(
                                    id=estudio.id,
                                    determinacion=estudio.determinacion,
                                    tecnica=estudio.tecnica,
                                    resultado=estudio.resultado,
                                    fecha_estudio=estudio.fecha_estudio,
                                )
                            )

            # Preparar diagnósticos
            diagnosticos_info = []
            if include_relations and evento.diagnosticos:
                for diagnostico in evento.diagnosticos:
                    diagnosticos_info.append(
                        DiagnosticoInfo(
                            id=diagnostico.id,
                            diagnostico=diagnostico.diagnostico_referido or "Sin diagnóstico",
                            fecha=diagnostico.fecha_diagnostico_referido,
                        )
                    )

            # Preparar tratamientos
            tratamientos_info = []
            if include_relations and evento.tratamientos:
                for tratamiento in evento.tratamientos:
                    tratamientos_info.append(
                        TratamientoInfo(
                            id=tratamiento.id,
                            tratamiento=tratamiento.descripcion_tratamiento,
                            fecha_inicio=tratamiento.fecha_inicio_tratamiento,
                            fecha_fin=tratamiento.fecha_fin_tratamiento,
                            resultado=tratamiento.resultado_tratamiento,
                        )
                    )

            # Preparar internaciones
            internaciones_info = []
            if include_relations and evento.internaciones:
                for internacion in evento.internaciones:
                    internaciones_info.append(
                        InternacionInfo(
                            id=internacion.id,
                            establecimiento=internacion.establecimiento_internacion,
                            fecha_internacion=internacion.fecha_internacion,
                            fecha_alta=internacion.fecha_alta_medica,
                            cuidados_intensivos=internacion.requirio_cuidado_intensivo or False,
                        )
                    )

            # Preparar vacunas del evento (si las tiene)
            vacunas_info = []
            if include_relations and hasattr(evento, 'vacunas') and evento.vacunas:
                for vacuna in evento.vacunas:
                    vacunas_info.append(
                        VacunaInfo(
                            id=vacuna.id,
                            vacuna=getattr(vacuna, 'nombre_vacuna', None) or str(vacuna.id),
                            dosis=getattr(vacuna, 'dosis_total', None),
                            fecha_aplicacion=getattr(vacuna, 'fecha_ultima_dosis', None),
                        )
                    )

            # Obtener nombres de grupos desde la relación many-to-many
            grupos_nombres = []
            if hasattr(evento, 'caso_grupos') and evento.caso_grupos:  # Cambiado de grupos_enfermedad a caso_grupos
                grupos_nombres = [
                    eg.grupo.nombre
                    for eg in evento.caso_grupos  # Cambiado de grupos_enfermedad a caso_grupos
                    if eg.grupo
                ]

            # Crear evento completo
            eventos_completos.append(
                CasoEpidemiologicoCompleto(
                    id=evento.id,
                    id_evento_caso=evento.id_snvs,  # Cambiado de id_evento_caso a id_snvs
                    tipo_eno_id=evento.id_enfermedad,
                    tipo_eno_nombre=evento.enfermedad.nombre if evento.enfermedad else None,  # Cambiado de tipo_eno a enfermedad
                    grupos_eno_nombres=grupos_nombres,
                    fecha_minima_caso=evento.fecha_minima_caso,  # Cambiado de fecha_minima_caso a fecha_minima_caso
                    fecha_inicio_sintomas=evento.fecha_inicio_sintomas,
                    fecha_apertura=evento.fecha_apertura_caso,
                    clasificacion_estrategia=evento.clasificacion_estrategia,
                    clasificacion_manual=evento.clasificacion_manual,
                    clasificacion_algoritmo=None,  # No existe este campo en el modelo
                    semana_epidemiologica_apertura=evento.semana_epidemiologica_apertura,
                    anio_epidemiologico_apertura=evento.anio_epidemiologico_apertura,
                    es_sintomatico=evento.es_caso_sintomatico or False,
                    requiere_revision=evento.requiere_revision_especie or False,
                    domicilio=domicilio_evento,
                    sintomas=sintomas_info,
                    muestras=muestras_info,
                    estudios=estudios_info,
                    diagnosticos=diagnosticos_info,
                    tratamientos=tratamientos_info,
                    internaciones=internaciones_info,
                    vacunas=vacunas_info,
                )
            )

            # Estadísticas
            tipos_eventos_set.add(evento.id_enfermedad)
            if evento.clasificacion_estrategia == "CONFIRMADOS":
                confirmados += 1
            elif evento.clasificacion_estrategia == "SOSPECHOSOS":
                sospechosos += 1
            elif evento.clasificacion_estrategia == "PROBABLES":
                probables += 1
            elif evento.clasificacion_estrategia == "DESCARTADOS":
                descartados += 1

        # Actualizar response con eventos y estadísticas
        response.eventos = sorted(
            eventos_completos, key=lambda x: x.fecha_minima_caso or date.min, reverse=True  # fecha_minima_caso es el campo del schema de respuesta
        )
        response.tipos_eventos_unicos = len(tipos_eventos_set)
        response.eventos_confirmados = confirmados
        response.eventos_sospechosos = sospechosos
        response.eventos_probables = probables
        response.eventos_descartados = descartados

        if eventos:
            response.primer_evento_fecha = min(
                e.fecha_minima_caso for e in eventos if e.fecha_minima_caso
            )
            response.ultimo_evento_fecha = max(
                e.fecha_minima_caso for e in eventos if e.fecha_minima_caso
            )

        logger.info(
            f"✅ Detalle de persona {tipo_sujeto}/{persona_id} obtenido con {len(eventos)} eventos completos"
        )
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 Error obteniendo persona {tipo_sujeto}/{persona_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo persona: {str(e)}",
        )

"""
Shared query criteria/builder for Evento filtering.

This module ensures consistent filtering logic across all endpoints
that query eventos (list, dashboard, charts, etc).

IMPORTANTE: Todos los filtros de provincia deben usar ESTABLECIMIENTO DE NOTIFICACIÓN,
no domicilio del ciudadano, para consistencia epidemiológica.
"""

from datetime import date
from typing import List, Optional

from sqlalchemy import String, and_, func, or_

from app.domains.eventos_epidemiologicos.eventos.models import (
    Evento,
    TipoEno,
    TipoEnoGrupoEno,
)
from app.domains.sujetos_epidemiologicos.animales_models import Animal
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia


class EventoQueryBuilder:
    """
    Builder pattern para construir queries de Evento con criterios consistentes.

    Garantiza que:
    - Todos los JOINs se aplican en el mismo orden
    - El filtro de provincia siempre usa establecimiento de notificación
    - Los filtros se aplican de manera uniforme
    """

    @staticmethod
    def add_base_joins(query):
        """
        Agrega los JOINs base necesarios para filtrar eventos.

        IMPORTANTE:
        - El filtro de provincia se aplica por ESTABLECIMIENTO DE NOTIFICACIÓN, no por domicilio
        - NO incluye JOIN con TipoEnoGrupoEno (causa duplicados) - se agrega solo cuando se necesita

        Args:
            query: SQLAlchemy query base (select(Evento) o similar)

        Returns:
            Query con JOINs aplicados
        """
        return (
            query
            .outerjoin(TipoEno, Evento.id_tipo_eno == TipoEno.id)
            .outerjoin(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
            .outerjoin(Animal, Evento.id_animal == Animal.id)
            # JOINs para filtro de provincia por ESTABLECIMIENTO DE NOTIFICACIÓN
            .outerjoin(Establecimiento, Evento.id_establecimiento_notificacion == Establecimiento.id)
            .outerjoin(Localidad, Establecimiento.id_localidad_indec == Localidad.id_localidad_indec)
            .outerjoin(Departamento, Localidad.id_departamento_indec == Departamento.id_departamento_indec)
            .outerjoin(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        )

    @staticmethod
    def build_filter_conditions(
        tipo_eno_ids: Optional[List[int]] = None,
        grupo_eno_ids: Optional[List[int]] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        clasificacion: Optional[List[str]] = None,
        provincia_ids_establecimiento_notificacion: Optional[List[int]] = None,
        tipo_sujeto: Optional[str] = None,
        requiere_revision: Optional[bool] = None,
        edad_min: Optional[int] = None,
        edad_max: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List:
        """
        Construye las condiciones de filtro de manera uniforme.

        Args:
            tipo_eno_ids: Lista de IDs de tipos ENO
            grupo_eno_ids: Lista de IDs de grupos ENO
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
            clasificacion: Lista de clasificaciones estratégicas
            provincia_ids_establecimiento_notificacion: Lista de códigos INDEC de provincias
                                                       (filtro por ESTABLECIMIENTO DE NOTIFICACIÓN)
            tipo_sujeto: Tipo de sujeto (humano/animal/desconocido)
            requiere_revision: Si requiere revisión
            edad_min: Edad mínima
            edad_max: Edad máxima
            search: Búsqueda por ID, nombre o documento

        Returns:
            Lista de condiciones SQLAlchemy para aplicar con and_()
        """
        conditions = []

        # Filtro de tipo ENO
        if tipo_eno_ids:
            conditions.append(Evento.id_tipo_eno.in_(tipo_eno_ids))

        # Filtro por grupos de ENO
        if grupo_eno_ids:
            conditions.append(TipoEnoGrupoEno.id_grupo_eno.in_(grupo_eno_ids))

        # Filtros de fecha
        if fecha_desde:
            conditions.append(Evento.fecha_minima_evento >= fecha_desde)

        if fecha_hasta:
            conditions.append(Evento.fecha_minima_evento <= fecha_hasta)

        # Clasificaciones múltiples
        if clasificacion:
            if isinstance(clasificacion, list):
                conditions.append(Evento.clasificacion_estrategia.in_(clasificacion))
            else:
                conditions.append(Evento.clasificacion_estrategia == clasificacion)

        # Provincias múltiples (por código INDEC - ESTABLECIMIENTO DE NOTIFICACIÓN)
        if provincia_ids_establecimiento_notificacion:
            conditions.append(Provincia.id_provincia_indec.in_(provincia_ids_establecimiento_notificacion))

        # Tipo de sujeto
        if tipo_sujeto:
            if tipo_sujeto == "humano":
                conditions.append(Evento.codigo_ciudadano.isnot(None))
            elif tipo_sujeto == "animal":
                conditions.append(Evento.id_animal.isnot(None))

        # Requiere revisión
        if requiere_revision is not None:
            conditions.append(Evento.requiere_revision_especie == requiere_revision)

        # Filtros de edad (calcular edad a partir de fecha_nacimiento y fecha_apertura_caso)
        # Solo aplica si tenemos ambas fechas
        if edad_min is not None or edad_max is not None:
            # Calcular edad usando AGE(fecha_apertura_caso, fecha_nacimiento)
            edad_calculada = func.extract(
                'year',
                func.age(Evento.fecha_apertura_caso, Evento.fecha_nacimiento)
            )
            # Asegurarse de que ambas fechas existan
            conditions.append(Evento.fecha_nacimiento.isnot(None))
            conditions.append(Evento.fecha_apertura_caso.isnot(None))

            if edad_min is not None:
                conditions.append(edad_calculada >= edad_min)
            if edad_max is not None:
                conditions.append(edad_calculada <= edad_max)

        # Búsqueda por texto
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Evento.id_evento_caso.cast(String).ilike(search_term),
                    Ciudadano.nombre.ilike(search_term),
                    Ciudadano.apellido.ilike(search_term),
                    Ciudadano.numero_documento.cast(String).ilike(search_term),
                    Animal.especie.ilike(search_term),
                )
            )

        return conditions

    @staticmethod
    def apply_filters(query, **filter_kwargs):
        """
        Aplica JOINs y filtros a una query de manera consistente.

        Args:
            query: SQLAlchemy query base
            **filter_kwargs: Filtros a aplicar (mismo formato que build_filter_conditions)

        Returns:
            Query con JOINs y filtros aplicados
        """
        # Agregar JOINs base (sin TipoEnoGrupoEno)
        query = EventoQueryBuilder.add_base_joins(query)

        # Si hay filtro de grupos, agregar JOIN con TipoEnoGrupoEno
        # (solo cuando se necesita para evitar duplicados)
        if filter_kwargs.get('grupo_eno_ids'):
            query = query.outerjoin(TipoEnoGrupoEno, TipoEno.id == TipoEnoGrupoEno.id_tipo_eno)

        # Construir y aplicar condiciones
        conditions = EventoQueryBuilder.build_filter_conditions(**filter_kwargs)

        if conditions:
            query = query.where(and_(*conditions))

        return query

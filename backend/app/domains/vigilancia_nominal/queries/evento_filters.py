"""
Shared query criteria/builder for CasoEpidemiologico filtering.

This module ensures consistent filtering logic across all endpoints
that query eventos (list, dashboard, charts, etc).

IMPORTANTE: Todos los filtros de provincia deben usar ESTABLECIMIENTO DE NOTIFICACIÓN,
no domicilio del ciudadano, para consistencia epidemiológica.
"""

from datetime import date
from typing import Any, List, Optional

from sqlalchemy import String, and_, cast, func, or_
from sqlmodel import col

from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    EnfermedadGrupo,
)
from app.domains.vigilancia_nominal.models.sujetos import Animal, Ciudadano


class CasoEpidemiologicoQueryBuilder:
    """
    Builder pattern para construir queries de CasoEpidemiologico con criterios consistentes.

    Garantiza que:
    - Todos los JOINs se aplican en el mismo orden
    - El filtro de provincia siempre usa establecimiento de notificación
    - Los filtros se aplican de manera uniforme
    """

    @staticmethod
    def add_base_joins(query: Any) -> Any:
        """
        Agrega los JOINs base necesarios para filtrar eventos.

        IMPORTANTE:
        - El filtro de provincia se aplica por ESTABLECIMIENTO DE NOTIFICACIÓN, no por domicilio
        - NO incluye JOIN con EnfermedadGrupo (causa duplicados) - se agrega solo cuando se necesita

        Args:
            query: SQLAlchemy query base (select(CasoEpidemiologico) o similar)

        Returns:
            Query con JOINs aplicados
        """
        return (
            query.outerjoin(
                Enfermedad, CasoEpidemiologico.id_enfermedad == Enfermedad.id
            )
            .outerjoin(
                Ciudadano,
                CasoEpidemiologico.codigo_ciudadano == Ciudadano.codigo_ciudadano,
            )
            .outerjoin(Animal, CasoEpidemiologico.id_animal == Animal.id)
            # JOINs para filtro de provincia por ESTABLECIMIENTO DE NOTIFICACIÓN
            .outerjoin(
                Establecimiento,
                CasoEpidemiologico.id_establecimiento_notificacion
                == Establecimiento.id,
            )
            .outerjoin(
                Localidad,
                Establecimiento.id_localidad_indec == Localidad.id_localidad_indec,
            )
            .outerjoin(
                Departamento,
                Localidad.id_departamento_indec == Departamento.id_departamento_indec,
            )
            .outerjoin(
                Provincia,
                Departamento.id_provincia_indec == Provincia.id_provincia_indec,
            )
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
            conditions.append(col(CasoEpidemiologico.id_enfermedad).in_(tipo_eno_ids))

        # Filtro por grupos de ENO
        if grupo_eno_ids:
            conditions.append(col(EnfermedadGrupo.id_grupo).in_(grupo_eno_ids))

        # Filtros de fecha
        if fecha_desde:
            conditions.append(col(CasoEpidemiologico.fecha_minima_caso) >= fecha_desde)

        if fecha_hasta:
            conditions.append(col(CasoEpidemiologico.fecha_minima_caso) <= fecha_hasta)

        # Clasificaciones múltiples
        if clasificacion:
            if isinstance(clasificacion, list):
                conditions.append(
                    col(CasoEpidemiologico.clasificacion_estrategia).in_(clasificacion)
                )
            else:
                conditions.append(
                    col(CasoEpidemiologico.clasificacion_estrategia) == clasificacion
                )

        # Provincias múltiples (por código INDEC - ESTABLECIMIENTO DE NOTIFICACIÓN)
        if provincia_ids_establecimiento_notificacion:
            conditions.append(
                col(Provincia.id_provincia_indec).in_(
                    provincia_ids_establecimiento_notificacion
                )
            )

        # Tipo de sujeto
        if tipo_sujeto:
            if tipo_sujeto == "humano":
                conditions.append(col(CasoEpidemiologico.codigo_ciudadano).isnot(None))
            elif tipo_sujeto == "animal":
                conditions.append(col(CasoEpidemiologico.id_animal).isnot(None))

        # Requiere revisión
        if requiere_revision is not None:
            conditions.append(
                col(CasoEpidemiologico.requiere_revision_especie) == requiere_revision
            )

        # Filtros de edad (calcular edad a partir de fecha_nacimiento y fecha_apertura_caso)
        # Solo aplica si tenemos ambas fechas
        if edad_min is not None or edad_max is not None:
            # Calcular edad usando AGE(fecha_apertura_caso, fecha_nacimiento)
            edad_calculada = func.extract(
                "year",
                func.age(
                    CasoEpidemiologico.fecha_apertura_caso,
                    CasoEpidemiologico.fecha_nacimiento,
                ),
            )
            # Asegurarse de que ambas fechas existan
            conditions.append(col(CasoEpidemiologico.fecha_nacimiento).isnot(None))
            conditions.append(col(CasoEpidemiologico.fecha_apertura_caso).isnot(None))

            if edad_min is not None:
                conditions.append(edad_calculada >= edad_min)
            if edad_max is not None:
                conditions.append(edad_calculada <= edad_max)

        # Búsqueda por texto
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    cast(col(CasoEpidemiologico.id_snvs), String).ilike(search_term),
                    col(Ciudadano.nombre).ilike(search_term),
                    col(Ciudadano.apellido).ilike(search_term),
                    cast(col(Ciudadano.numero_documento), String).ilike(search_term),
                    col(Animal.especie).ilike(search_term),
                )
            )

        return conditions

    @staticmethod
    def apply_filters(query: Any, **filter_kwargs: Any) -> Any:
        """
        Aplica JOINs y filtros a una query de manera consistente.

        Args:
            query: SQLAlchemy query base
            **filter_kwargs: Filtros a aplicar (mismo formato que build_filter_conditions)

        Returns:
            Query con JOINs y filtros aplicados
        """
        # Agregar JOINs base (sin EnfermedadGrupo)
        query = CasoEpidemiologicoQueryBuilder.add_base_joins(query)

        # Si hay filtro de grupos, agregar JOIN con EnfermedadGrupo
        # (solo cuando se necesita para evitar duplicados)
        if filter_kwargs.get("grupo_eno_ids"):
            query = query.outerjoin(
                EnfermedadGrupo, Enfermedad.id == EnfermedadGrupo.id_enfermedad
            )

        # Construir y aplicar condiciones
        conditions = CasoEpidemiologicoQueryBuilder.build_filter_conditions(
            **filter_kwargs
        )

        if conditions:
            query = query.where(and_(*conditions))

        return query

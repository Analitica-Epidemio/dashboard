"""
Repository layer para el dominio de estrategias.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.vigilancia_nominal.clasificacion.models import (
    ClassificationRule,
    EventClassificationAudit,
    EstrategiaClasificacion,
    FilterCondition,
    TipoClasificacion,
)
from app.domains.vigilancia_nominal.clasificacion.schemas import (
    EstrategiaClasificacionCreate,
    EstrategiaClasificacionUpdate,
)
from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad


class EstrategiaClasificacionRepository:
    """Repository para gestión completa de estrategias de clasificación."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        active_only: Optional[bool] = None,
        id_enfermedad: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EstrategiaClasificacion]:
        """
        Obtiene todas las estrategias con filtros opcionales.

        Args:
            active_only: Filtrar por estado activo
            id_enfermedad: Filtrar por tipo de evento
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            Lista de estrategias
        """
        # Join con Enfermedad para obtener el nombre
        query = (
            select(EstrategiaClasificacion)
            .outerjoin(Enfermedad, EstrategiaClasificacion.id_enfermedad == Enfermedad.id)
            .options(
                selectinload(EstrategiaClasificacion.classification_rules).selectinload(
                    ClassificationRule.filters
                )
            )
        )

        if active_only is not None:
            query = query.where(EstrategiaClasificacion.is_active == active_only)

        if id_enfermedad is not None:
            query = query.where(EstrategiaClasificacion.id_enfermedad == id_enfermedad)

        query = query.order_by(EstrategiaClasificacion.name).offset(skip).limit(limit)

        result = await self.session.execute(query)
        strategies = list(result.scalars().all())

        # Obtener los nombres de Enfermedad para cada estrategia
        if strategies:
            id_enfermedads = list(set(s.id_enfermedad for s in strategies))
            tipo_query = select(Enfermedad).where(Enfermedad.id.in_(id_enfermedads))
            tipo_result = await self.session.execute(tipo_query)
            tipos = {t.id: t for t in tipo_result.scalars().all()}

            # Asignar nombres a las estrategias
            for strategy in strategies:
                if strategy.id_enfermedad in tipos:
                    strategy.tipo_enfermedad_name = tipos[strategy.id_enfermedad].nombre

        return strategies

    async def get_by_id(
        self, strategy_id: int, include_rules: bool = True
    ) -> Optional[EstrategiaClasificacion]:
        """
        Obtiene una estrategia por ID.

        Args:
            strategy_id: ID de la estrategia
            include_rules: Si incluir reglas y filtros relacionados

        Returns:
            Estrategia encontrada o None
        """
        query = select(EstrategiaClasificacion).where(EstrategiaClasificacion.id == strategy_id)

        if include_rules:
            query = query.options(
                selectinload(EstrategiaClasificacion.classification_rules).selectinload(
                    ClassificationRule.filters
                )
            )

        result = await self.session.execute(query)
        strategy = result.scalar_one_or_none()

        # Obtener el nombre del Enfermedad
        if strategy:
            tipo_query = select(Enfermedad).where(Enfermedad.id == strategy.id_enfermedad)
            tipo_result = await self.session.execute(tipo_query)
            tipo_enfermedad = tipo_result.scalar_one_or_none()
            if tipo_enfermedad:
                strategy.tipo_enfermedad_name = tipo_enfermedad.nombre

        return strategy

    async def get_by_id_enfermedad(
        self,
        id_enfermedad: int,
        active_only: bool = True,
        fecha: Optional[datetime] = None,
    ) -> Optional[EstrategiaClasificacion]:
        """
        Obtiene una estrategia por tipo de ENO válida en una fecha específica.

        Args:
            id_enfermedad: ID del tipo de ENO
            active_only: Solo estrategias activas
            fecha: Fecha para la cual buscar estrategia válida (default: ahora)

        Returns:
            Estrategia encontrada o None
        """
        if fecha is None:
            fecha = datetime.utcnow()

        query = (
            select(EstrategiaClasificacion)
            .where(EstrategiaClasificacion.id_enfermedad == id_enfermedad)
            .options(
                selectinload(EstrategiaClasificacion.classification_rules).selectinload(
                    ClassificationRule.filters
                )
            )
        )

        if active_only:
            query = query.where(EstrategiaClasificacion.is_active.is_(True))

        # Filtrar por validez temporal:
        # La estrategia es válida si:
        # - fecha >= valid_from AND
        # - (valid_until IS NULL OR fecha < valid_until)
        query = query.where(
            and_(
                EstrategiaClasificacion.valid_from <= fecha,
                (EstrategiaClasificacion.valid_until.is_(None)) | (EstrategiaClasificacion.valid_until > fecha),
            )
        )

        result = await self.session.execute(query)
        strategy = result.scalar_one_or_none()

        # Obtener el nombre del Enfermedad
        if strategy:
            tipo_query = select(Enfermedad).where(Enfermedad.id == strategy.id_enfermedad)
            tipo_result = await self.session.execute(tipo_query)
            tipo_enfermedad = tipo_result.scalar_one_or_none()
            if tipo_enfermedad:
                strategy.tipo_enfermedad_name = tipo_enfermedad.nombre

        return strategy

    # Alias para compatibilidad con el servicio existente
    async def get_by_tipo_enfermedad(
        self, id_enfermedad: int, include_rules: bool = True
    ) -> Optional[EstrategiaClasificacion]:
        """
        Alias para get_by_id_enfermedad para compatibilidad.
        """
        return await self.get_by_id_enfermedad(id_enfermedad, active_only=True)

    async def create(
        self, strategy_data: EstrategiaClasificacionCreate, created_by: str = "system"
    ) -> EstrategiaClasificacion:
        """
        Crea una nueva estrategia.

        Args:
            strategy_data: Datos de la estrategia
            created_by: Usuario que crea la estrategia

        Returns:
            Estrategia creada
        """
        # Crear la estrategia principal
        strategy = EstrategiaClasificacion(
            name=strategy_data.name,
            id_enfermedad=strategy_data.id_enfermedad,
            is_active=strategy_data.active,
            confidence_threshold=strategy_data.confidence_threshold,
            description=strategy_data.description,
            config=strategy_data.config,
            valid_from=strategy_data.valid_from,
            valid_until=strategy_data.valid_until,
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(strategy)
        await self.session.flush()  # Para obtener el ID

        # Crear reglas de clasificación
        for rule_data in strategy_data.classification_rules:
            rule = ClassificationRule(
                strategy_id=strategy.id,
                classification=rule_data.classification,
                priority=rule_data.priority,
                is_active=rule_data.is_active,
                auto_approve=rule_data.auto_approve,
                required_confidence=rule_data.required_confidence,
            )
            self.session.add(rule)
            await self.session.flush()  # Para obtener el ID de la regla

            # Crear filtros para la regla
            for filter_data in rule_data.filters:
                filter_condition = FilterCondition(
                    rule_id=rule.id,
                    filter_type=filter_data.filter_type,
                    field_name=filter_data.field_name,
                    value=filter_data.value,
                    values=filter_data.values,
                    logical_operator=filter_data.logical_operator,
                    order=filter_data.order,
                    config=filter_data.config,
                    extracted_metadata_field=filter_data.extracted_metadata_field,
                )
                self.session.add(filter_condition)

        # Crear extractores de metadata
        for extractor_data in strategy_data.metadata_extractors:
            extractor = FilterCondition(
                strategy_id=strategy.id,
                filter_type=extractor_data.filter_type,
                field_name=extractor_data.field_name,
                value=extractor_data.value,
                values=extractor_data.values,
                logical_operator=extractor_data.logical_operator,
                order=extractor_data.order,
                config=extractor_data.config,
                extracted_metadata_field=extractor_data.extracted_metadata_field,
            )
            self.session.add(extractor)

        await self.session.commit()
        await self.session.refresh(strategy)

        # Log de creación
        await self._log_audit(
            strategy_id=strategy.id,
            action="CREATE",
            field_changed="strategy",
            new_value=f"Strategy '{strategy.name}' created",
            changed_by=created_by,
        )

        return await self.get_by_id(strategy.id)  # Retornar con relaciones cargadas

    async def update(
        self,
        strategy_id: int,
        strategy_data: EstrategiaClasificacionUpdate,
        updated_by: str = "system",
    ) -> EstrategiaClasificacion:
        """
        Actualiza una estrategia existente.

        Args:
            strategy_id: ID de la estrategia a actualizar
            strategy_data: Datos de actualización
            updated_by: Usuario que realiza la actualización

        Returns:
            Estrategia actualizada
        """
        strategy = await self.get_by_id(strategy_id, include_rules=False)
        if not strategy:
            raise ValueError(f"Estrategia {strategy_id} no encontrada")

        # Guardar valores anteriores para auditoría
        changes = []

        # Actualizar campos básicos
        if strategy_data.name is not None and strategy_data.name != strategy.name:
            changes.append(f"name: {strategy.name} → {strategy_data.name}")
            strategy.name = strategy_data.name

        if (
            strategy_data.active is not None
            and strategy_data.active != strategy.is_active
        ):
            changes.append(f"active: {strategy.is_active} → {strategy_data.active}")
            strategy.is_active = strategy_data.active

        if (
            strategy_data.config is not None
            and strategy_data.config != strategy.config
        ):
            changes.append("config updated")
            strategy.config = strategy_data.config

        if (
            strategy_data.confidence_threshold is not None
            and strategy_data.confidence_threshold != strategy.confidence_threshold
        ):
            changes.append(
                f"confidence_threshold: {strategy.confidence_threshold} → {strategy_data.confidence_threshold}"
            )
            strategy.confidence_threshold = strategy_data.confidence_threshold

        if (
            strategy_data.description is not None
            and strategy_data.description != strategy.description
        ):
            changes.append("description updated")
            strategy.description = strategy_data.description

        if (
            strategy_data.valid_from is not None
            and strategy_data.valid_from != strategy.valid_from
        ):
            changes.append(
                f"valid_from: {strategy.valid_from} → {strategy_data.valid_from}"
            )
            strategy.valid_from = strategy_data.valid_from

        if strategy_data.valid_until != strategy.valid_until:
            changes.append(
                f"valid_until: {strategy.valid_until} → {strategy_data.valid_until}"
            )
            strategy.valid_until = strategy_data.valid_until

        strategy.updated_by = updated_by

        # Si hay reglas nuevas, reemplazar todas
        if strategy_data.classification_rules is not None:
            # Eliminar reglas existentes
            await self.session.execute(
                select(ClassificationRule).where(
                    ClassificationRule.strategy_id == strategy_id
                )
            )
            existing_rules = (
                (
                    await self.session.execute(
                        select(ClassificationRule).where(
                            ClassificationRule.strategy_id == strategy_id
                        )
                    )
                )
                .scalars()
                .all()
            )

            for rule in existing_rules:
                await self.session.delete(rule)

            # Crear nuevas reglas
            for rule_data in strategy_data.classification_rules:
                rule = ClassificationRule(
                    strategy_id=strategy.id,
                    classification=rule_data.classification,
                    priority=rule_data.priority,
                    is_active=rule_data.is_active,
                    auto_approve=rule_data.auto_approve,
                    required_confidence=rule_data.required_confidence,
                )
                self.session.add(rule)
                await self.session.flush()

                # Crear filtros para la regla
                for filter_data in rule_data.filters:
                    filter_condition = FilterCondition(
                        rule_id=rule.id,
                        filter_type=filter_data.filter_type,
                        field_name=filter_data.field_name,
                        value=filter_data.value,
                        values=filter_data.values,
                        logical_operator=filter_data.logical_operator,
                        order=filter_data.order,
                        config=filter_data.config,
                        extracted_metadata_field=filter_data.extracted_metadata_field,
                    )
                    self.session.add(filter_condition)

            changes.append(
                f"classification_rules updated ({len(strategy_data.classification_rules)} rules)"
            )

        await self.session.commit()

        # Log de cambios
        if changes:
            await self._log_audit(
                strategy_id=strategy_id,
                action="UPDATE",
                field_changed="multiple",
                new_value="; ".join(changes),
                changed_by=updated_by,
            )

        return await self.get_by_id(strategy_id)

    async def delete(self, strategy_id: int, deleted_by: str = "system") -> bool:
        """
        Elimina una estrategia.

        Args:
            strategy_id: ID de la estrategia a eliminar
            deleted_by: Usuario que elimina

        Returns:
            True si se eliminó exitosamente
        """
        strategy = await self.get_by_id(strategy_id, include_rules=False)
        if not strategy:
            return False

        strategy_name = strategy.name

        await self.session.delete(strategy)
        await self.session.commit()

        # Log de eliminación
        await self._log_audit(
            strategy_id=strategy_id,
            action="DELETE",
            field_changed="strategy",
            old_value=f"Strategy '{strategy_name}' deleted",
            changed_by=deleted_by,
        )

        return True

    async def activate(
        self, strategy_id: int, activated_by: str = "system"
    ) -> EstrategiaClasificacion:
        """
        Activa una estrategia y desactiva otras del mismo tipo de evento.

        Args:
            strategy_id: ID de la estrategia a activar
            activated_by: Usuario que activa

        Returns:
            Estrategia activada
        """
        strategy = await self.get_by_id(strategy_id, include_rules=False)
        if not strategy:
            raise ValueError(f"Estrategia {strategy_id} no encontrada")

        # Desactivar otras estrategias del mismo tipo de evento
        await self.session.execute(
            select(EstrategiaClasificacion).where(
                and_(
                    EstrategiaClasificacion.id_enfermedad == strategy.id_enfermedad,
                    EstrategiaClasificacion.id != strategy_id,
                )
            )
        )
        other_strategies = (
            (
                await self.session.execute(
                    select(EstrategiaClasificacion).where(
                        and_(
                            EstrategiaClasificacion.id_enfermedad == strategy.id_enfermedad,
                            EstrategiaClasificacion.id != strategy_id,
                            EstrategiaClasificacion.is_active.is_(True),
                        )
                    )
                )
            )
            .scalars()
            .all()
        )

        for other_strategy in other_strategies:
            other_strategy.is_active = False
            await self._log_audit(
                strategy_id=other_strategy.id,
                action="DEACTIVATE",
                field_changed="active",
                old_value="true",
                new_value="false",
                changed_by=activated_by,
            )

        # Activar la estrategia seleccionada
        strategy.is_active = True
        strategy.updated_by = activated_by

        await self.session.commit()

        # Log de activación
        await self._log_audit(
            strategy_id=strategy_id,
            action="ACTIVATE",
            field_changed="active",
            old_value="false",
            new_value="true",
            changed_by=activated_by,
        )

        return await self.get_by_id(strategy_id)

    async def get_audit_log(
        self, strategy_id: int, limit: int = 50
    ) -> List[EventClassificationAudit]:
        """
        Obtiene el historial de auditoría de una estrategia.

        Args:
            strategy_id: ID de la estrategia
            limit: Número máximo de entradas a retornar

        Returns:
            Lista de entradas de auditoría
        """
        result = await self.session.execute(
            select(EventClassificationAudit)
            .where(EventClassificationAudit.id_caso == strategy_id)
            .order_by(desc(EventClassificationAudit.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def check_date_overlap(
        self,
        id_enfermedad: int,
        valid_from: datetime,
        valid_until: Optional[datetime],
        exclude_strategy_id: Optional[int] = None,
    ) -> List[EstrategiaClasificacion]:
        """
        Verifica si existen estrategias con solapamiento de fechas.

        Args:
            id_enfermedad: ID del tipo de ENO
            valid_from: Fecha de inicio del nuevo período
            valid_until: Fecha de fin del nuevo período (None = sin fin)
            exclude_strategy_id: ID de estrategia a excluir (para updates)

        Returns:
            Lista de estrategias que se solapan con el período especificado
        """
        # Construir query base
        query = select(EstrategiaClasificacion).where(EstrategiaClasificacion.id_enfermedad == id_enfermedad)

        # Excluir estrategia específica si se proporciona (para updates)
        if exclude_strategy_id is not None:
            query = query.where(EstrategiaClasificacion.id != exclude_strategy_id)

        # Lógica de solapamiento:
        # Dos rangos [A_start, A_end] y [B_start, B_end] se solapan si:
        # A_start < B_end AND A_end > B_start
        #
        # Casos especiales con None (sin fin):
        # - Si valid_until es None, el rango nuevo termina en infinito
        # - Si strategy.valid_until es None, el rango existente termina en infinito

        # Condición 1: El nuevo período empieza antes de que termine el existente
        # valid_from < strategy.valid_until OR strategy.valid_until IS NULL
        if valid_until is not None:
            # El nuevo período tiene fin, entonces:
            # No hay solapamiento si el nuevo período termina antes de que empiece el existente
            # O si el nuevo período empieza después de que termine el existente
            query = query.where(
                and_(
                    # El nuevo período termina después de que empiece el existente
                    valid_until > EstrategiaClasificacion.valid_from,
                    # El nuevo período empieza antes de que termine el existente (o el existente no tiene fin)
                    and_(
                        (EstrategiaClasificacion.valid_until.is_(None))
                        | (valid_from < EstrategiaClasificacion.valid_until)
                    ),
                )
            )
        else:
            # El nuevo período no tiene fin (termina en infinito)
            # Hay solapamiento si el período existente termina después de que empiece el nuevo
            # o si el período existente tampoco tiene fin
            query = query.where(
                (EstrategiaClasificacion.valid_until.is_(None))
                | (EstrategiaClasificacion.valid_until > valid_from)
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _log_audit(
        self,
        strategy_id: int,
        action: str,
        field_changed: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        changed_by: str = "system",
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Registra una entrada en el log de auditoría.

        Args:
            strategy_id: ID de la estrategia
            action: Acción realizada
            field_changed: Campo modificado
            old_value: Valor anterior
            new_value: Nuevo valor
            changed_by: Usuario que realizó el cambio
            ip_address: Dirección IP
        """
        audit_entry = EventClassificationAudit(
            id_caso=strategy_id,
            tipo_sujeto_detectado=None,
            confidence_score=None,
            metadata_extraida={
                "action": action,
                "field_changed": field_changed,
                "old_value": old_value,
                "new_value": new_value,
                "changed_by": changed_by,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        self.session.add(audit_entry)
        # No hacer commit aquí, se hace en la operación principal


class ClassificationRuleRepository:
    """Repository para gestión de reglas de clasificación."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_strategy(
        self,
        strategy_id: int,
        classification: Optional[TipoClasificacion] = None,
        active_only: bool = True,
    ) -> List[ClassificationRule]:
        """
        Obtiene reglas de una estrategia.

        Args:
            strategy_id: ID de la estrategia
            classification: Filtrar por tipo de clasificación
            active_only: Solo reglas activas

        Returns:
            Lista de reglas encontradas
        """
        query = select(ClassificationRule).where(
            ClassificationRule.strategy_id == strategy_id
        )

        if classification:
            query = query.where(ClassificationRule.classification == classification)

        if active_only:
            query = query.where(ClassificationRule.is_active.is_(True))

        query = query.options(selectinload(ClassificationRule.filters)).order_by(
            ClassificationRule.priority
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())


class FilterConditionRepository:
    """Repository para gestión de condiciones de filtro."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_rule(self, rule_id: int) -> List[FilterCondition]:
        """
        Obtiene todas las condiciones de una regla.

        Args:
            rule_id: ID de la regla

        Returns:
            Lista de condiciones
        """
        result = await self.session.execute(
            select(FilterCondition)
            .where(FilterCondition.rule_id == rule_id)
            .order_by(FilterCondition.order)
        )
        return list(result.scalars().all())

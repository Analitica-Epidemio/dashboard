"""
Repository layer para el dominio de estrategias.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.estrategias.models import (
    ClassificationRule,
    EventClassificationAudit,
    EventStrategy,
    FilterCondition,
    TipoClasificacion,
)
from app.domains.estrategias.schemas import (
    EventStrategyCreate,
    EventStrategyUpdate,
)
from app.domains.eventos_epidemiologicos.eventos.models import TipoEno


class EventStrategyRepository:
    """Repository para gestión completa de estrategias de clasificación."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        active_only: Optional[bool] = None,
        tipo_eno_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EventStrategy]:
        """
        Obtiene todas las estrategias con filtros opcionales.

        Args:
            active_only: Filtrar por estado activo
            tipo_eno_id: Filtrar por tipo de evento
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            Lista de estrategias
        """
        # Join con TipoEno para obtener el nombre
        query = (
            select(EventStrategy)
            .outerjoin(TipoEno, EventStrategy.tipo_eno_id == TipoEno.id)
            .options(
                selectinload(EventStrategy.classification_rules).selectinload(
                    ClassificationRule.filters
                )
            )
        )

        if active_only is not None:
            query = query.where(EventStrategy.is_active == active_only)

        if tipo_eno_id is not None:
            query = query.where(EventStrategy.tipo_eno_id == tipo_eno_id)

        query = query.order_by(EventStrategy.name).offset(skip).limit(limit)

        result = await self.session.execute(query)
        strategies = list(result.scalars().all())

        # Obtener los nombres de TipoEno para cada estrategia
        if strategies:
            tipo_eno_ids = list(set(s.tipo_eno_id for s in strategies))
            tipo_query = select(TipoEno).where(TipoEno.id.in_(tipo_eno_ids))
            tipo_result = await self.session.execute(tipo_query)
            tipos = {t.id: t for t in tipo_result.scalars().all()}

            # Asignar nombres a las estrategias
            for strategy in strategies:
                if strategy.tipo_eno_id in tipos:
                    strategy.tipo_eno_name = tipos[strategy.tipo_eno_id].nombre

        return strategies

    async def get_by_id(
        self, strategy_id: int, include_rules: bool = True
    ) -> Optional[EventStrategy]:
        """
        Obtiene una estrategia por ID.

        Args:
            strategy_id: ID de la estrategia
            include_rules: Si incluir reglas y filtros relacionados

        Returns:
            Estrategia encontrada o None
        """
        query = select(EventStrategy).where(EventStrategy.id == strategy_id)

        if include_rules:
            query = query.options(
                selectinload(EventStrategy.classification_rules).selectinload(
                    ClassificationRule.filters
                )
            )

        result = await self.session.execute(query)
        strategy = result.scalar_one_or_none()

        # Obtener el nombre del TipoEno
        if strategy:
            tipo_query = select(TipoEno).where(TipoEno.id == strategy.tipo_eno_id)
            tipo_result = await self.session.execute(tipo_query)
            tipo_eno = tipo_result.scalar_one_or_none()
            if tipo_eno:
                strategy.tipo_eno_name = tipo_eno.nombre

        return strategy

    async def get_by_tipo_eno_id(
        self, tipo_eno_id: int, active_only: bool = True
    ) -> Optional[EventStrategy]:
        """
        Obtiene una estrategia por tipo de ENO.

        Args:
            tipo_eno_id: ID del tipo de ENO
            active_only: Solo estrategias activas

        Returns:
            Estrategia encontrada o None
        """
        query = (
            select(EventStrategy)
            .where(EventStrategy.tipo_eno_id == tipo_eno_id)
            .options(
                selectinload(EventStrategy.classification_rules).selectinload(
                    ClassificationRule.filters
                )
            )
        )

        if active_only:
            query = query.where(EventStrategy.is_active == True)

        result = await self.session.execute(query)
        strategy = result.scalar_one_or_none()

        # Obtener el nombre del TipoEno
        if strategy:
            tipo_query = select(TipoEno).where(TipoEno.id == strategy.tipo_eno_id)
            tipo_result = await self.session.execute(tipo_query)
            tipo_eno = tipo_result.scalar_one_or_none()
            if tipo_eno:
                strategy.tipo_eno_name = tipo_eno.nombre

        return strategy

    # Alias para compatibilidad con el servicio existente
    async def get_by_tipo_eno(
        self, tipo_eno_id: int, include_rules: bool = True
    ) -> Optional[EventStrategy]:
        """
        Alias para get_by_tipo_eno_id para compatibilidad.
        """
        return await self.get_by_tipo_eno_id(tipo_eno_id, active_only=True)

    async def create(
        self, strategy_data: EventStrategyCreate, created_by: str = "system"
    ) -> EventStrategy:
        """
        Crea una nueva estrategia.

        Args:
            strategy_data: Datos de la estrategia
            created_by: Usuario que crea la estrategia

        Returns:
            Estrategia creada
        """
        # Crear la estrategia principal
        strategy = EventStrategy(
            name=strategy_data.name,
            tipo_eno_id=strategy_data.tipo_eno_id,
            is_active=strategy_data.active,
            usa_provincia_carga=strategy_data.usa_provincia_carga,
            provincia_field=strategy_data.provincia_field,
            confidence_threshold=strategy_data.confidence_threshold,
            description=strategy_data.description,
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
        strategy_data: EventStrategyUpdate,
        updated_by: str = "system",
    ) -> EventStrategy:
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
            strategy_data.usa_provincia_carga is not None
            and strategy_data.usa_provincia_carga != strategy.usa_provincia_carga
        ):
            changes.append(
                f"usa_provincia_carga: {strategy.usa_provincia_carga} → {strategy_data.usa_provincia_carga}"
            )
            strategy.usa_provincia_carga = strategy_data.usa_provincia_carga

        if (
            strategy_data.provincia_field is not None
            and strategy_data.provincia_field != strategy.provincia_field
        ):
            changes.append(
                f"provincia_field: {strategy.provincia_field} → {strategy_data.provincia_field}"
            )
            strategy.provincia_field = strategy_data.provincia_field

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
    ) -> EventStrategy:
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
            select(EventStrategy).where(
                and_(
                    EventStrategy.tipo_eno_id == strategy.tipo_eno_id,
                    EventStrategy.id != strategy_id,
                )
            )
        )
        other_strategies = (
            (
                await self.session.execute(
                    select(EventStrategy).where(
                        and_(
                            EventStrategy.tipo_eno_id == strategy.tipo_eno_id,
                            EventStrategy.id != strategy_id,
                            EventStrategy.is_active == True,
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
            .where(EventClassificationAudit.id_evento == strategy_id)
            .order_by(desc(EventClassificationAudit.created_at))
            .limit(limit)
        )
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
            id_evento=strategy_id,
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
            query = query.where(ClassificationRule.is_active == True)

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

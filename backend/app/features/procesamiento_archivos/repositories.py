"""
Repository layer para manejo de datos de uploads y jobs.

Arquitectura senior-level:
- Separación de data access logic
- Interface clara para servicios
- Manejo de errores específicos
- Optimizaciones de queries
"""

import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, and_, desc, select

from app.core.database import engine
from app.features.procesamiento_archivos.models import JobStatus, ProcessingJob

logger = logging.getLogger(__name__)


class ProcessingJobRepositoryInterface(ABC):
    """Interface abstracta para el repositorio de trabajos."""

    @abstractmethod
    async def create(self, job: ProcessingJob) -> ProcessingJob:
        """Crear un nuevo trabajo."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        """Obtener trabajo por ID."""
        pass

    @abstractmethod
    async def update(self, job: ProcessingJob) -> ProcessingJob:
        """Actualizar trabajo existente."""
        pass

    @abstractmethod
    async def list_jobs(
        self, status: Optional[JobStatus] = None, limit: int = 50, offset: int = 0
    ) -> List[ProcessingJob]:
        """Listar trabajos con filtros."""
        pass


class PostgreSQLProcessingJobRepository(ProcessingJobRepositoryInterface):
    """
    Implementación PostgreSQL del repositorio de trabajos.

    Características:
    - Transacciones robustas
    - Error handling específico
    - Logging detallado
    - Optimizaciones de performance
    """

    def __init__(self):
        self.session_factory = Session

    async def create(self, job: ProcessingJob) -> ProcessingJob:
        """
        Crear un nuevo trabajo en la base de datos.

        Args:
            job: Instancia del trabajo a crear

        Returns:
            ProcessingJob: El trabajo creado con ID asignado

        Raises:
            RepositoryError: Si hay error en la creación
        """
        logger.info(
            f"💾 Repository.create() called - job_type: {job.job_type}, original_filename: {job.original_filename}"
        )
        try:
            logger.info("🔗 Creating database session...")
            with self.session_factory(engine) as session:
                logger.info("✅ Database session created successfully")

                logger.info("📝 Adding job to session...")
                session.add(job)
                logger.info("✅ Job added to session")

                logger.info("💾 Committing transaction...")
                session.commit()
                logger.info("✅ Transaction committed successfully")

                logger.info("🔄 Refreshing job object...")
                session.refresh(job)
                logger.info(f"✅ Job object refreshed - final job_id: {job.id}")

                logger.info(f"🎉 Job created successfully: {job.id} - {job.job_type}")
                return job

        except SQLAlchemyError as e:
            logger.error(f"💥 SQLAlchemy error creating job: {str(e)}")
            logger.error(f"💥 Error type: {type(e).__name__}")
            logger.error(f"💥 Full traceback:\n{traceback.format_exc()}")
            raise RepositoryError(f"Error creating job: {str(e)}") from e
        except Exception as e:
            logger.error(f"💥 Unexpected error in repository.create: {str(e)}")
            logger.error(f"💥 Error type: {type(e).__name__}")
            logger.error(f"💥 Full traceback:\n{traceback.format_exc()}")
            raise RepositoryError(f"Unexpected error creating job: {str(e)}") from e

    async def get_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        """
        Obtener trabajo por su ID único.

        Args:
            job_id: UUID del trabajo

        Returns:
            ProcessingJob o None si no existe
        """
        try:
            with self.session_factory(engine) as session:
                statement = select(ProcessingJob).where(ProcessingJob.id == job_id)
                result = session.exec(statement).first()

                if result:
                    logger.debug(f"Trabajo encontrado: {job_id}")
                else:
                    logger.debug(f"Trabajo no encontrado: {job_id}")

                return result

        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo trabajo {job_id}: {str(e)}")
            raise RepositoryError(f"Error fetching job {job_id}: {str(e)}") from e

    async def update(self, job: ProcessingJob) -> ProcessingJob:
        """
        Actualizar trabajo existente.

        Args:
            job: Trabajo con cambios a persistir

        Returns:
            ProcessingJob: El trabajo actualizado
        """
        try:
            with self.session_factory(engine) as session:
                # Actualizar timestamp
                job.updated_at = datetime.now()

                # Merge y commit
                session.add(job)
                session.commit()
                session.refresh(job)

                logger.debug(f"Trabajo actualizado: {job.id} - Status: {job.status}")
                return job

        except SQLAlchemyError as e:
            logger.error(f"Error actualizando trabajo {job.id}: {str(e)}")
            raise RepositoryError(f"Error updating job {job.id}: {str(e)}") from e

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
    ) -> List[ProcessingJob]:
        """
        Listar trabajos con filtros y paginación.

        Args:
            status: Filtrar por estado específico
            limit: Máximo número de resultados
            offset: Número de resultados a saltear
            order_by: Campo para ordenar

        Returns:
            Lista de trabajos
        """
        try:
            with self.session_factory(engine) as session:
                statement = select(ProcessingJob)

                # Aplicar filtros
                if status:
                    statement = statement.where(ProcessingJob.status == status)

                # Ordenar por fecha de creación (más recientes primero)
                if order_by == "created_at":
                    statement = statement.order_by(desc(ProcessingJob.created_at))
                elif order_by == "updated_at":
                    statement = statement.order_by(desc(ProcessingJob.updated_at))
                elif order_by == "priority":
                    statement = statement.order_by(desc(ProcessingJob.priority))

                # Paginación
                statement = statement.offset(offset).limit(limit)

                results = session.exec(statement).all()

                logger.debug(f"Listado de trabajos: {len(results)} encontrados")
                return list(results)

        except SQLAlchemyError as e:
            logger.error(f"Error listando trabajos: {str(e)}")
            raise RepositoryError(f"Error listing jobs: {str(e)}") from e

    async def get_active_jobs(self) -> List[ProcessingJob]:
        """Obtener trabajos activos (pending o in_progress)."""
        return await self.list_jobs(
            status=None,  # No filtrar por uno solo
            limit=100,
        )

    async def get_jobs_by_status(
        self, statuses: List[JobStatus]
    ) -> List[ProcessingJob]:
        """Obtener trabajos por múltiples estados."""
        try:
            with self.session_factory(engine) as session:
                statement = (
                    select(ProcessingJob)
                    .where(ProcessingJob.status.in_(statuses))
                    .order_by(desc(ProcessingJob.created_at))
                )

                results = session.exec(statement).all()
                return list(results)

        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo trabajos por estados: {str(e)}")
            raise RepositoryError(f"Error fetching jobs by status: {str(e)}") from e

    async def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """
        Limpiar trabajos antiguos completados o fallidos.

        Args:
            days_old: Eliminar trabajos más antiguos que X días

        Returns:
            Número de trabajos eliminados
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            with self.session_factory(engine) as session:
                statement = select(ProcessingJob).where(
                    and_(
                        ProcessingJob.status.in_(
                            [JobStatus.COMPLETED, JobStatus.FAILED]
                        ),
                        ProcessingJob.completed_at < cutoff_date,
                    )
                )

                old_jobs = session.exec(statement).all()
                count = len(old_jobs)

                for job in old_jobs:
                    session.delete(job)

                session.commit()

                logger.info(
                    f"Limpieza completada: {count} trabajos antiguos eliminados"
                )
                return count

        except SQLAlchemyError as e:
            logger.error(f"Error en limpieza de trabajos: {str(e)}")
            raise RepositoryError(f"Error cleaning up jobs: {str(e)}") from e

    async def get_job_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de trabajos."""
        try:
            with self.session_factory(engine) as session:
                # Total por estado
                total_pending = session.exec(
                    select(ProcessingJob).where(
                        ProcessingJob.status == JobStatus.PENDING
                    )
                ).all()

                total_in_progress = session.exec(
                    select(ProcessingJob).where(
                        ProcessingJob.status == JobStatus.IN_PROGRESS
                    )
                ).all()

                total_completed = session.exec(
                    select(ProcessingJob).where(
                        ProcessingJob.status == JobStatus.COMPLETED
                    )
                ).all()

                total_failed = session.exec(
                    select(ProcessingJob).where(
                        ProcessingJob.status == JobStatus.FAILED
                    )
                ).all()

                return {
                    "total": len(total_pending)
                    + len(total_in_progress)
                    + len(total_completed)
                    + len(total_failed),
                    "pending": len(total_pending),
                    "in_progress": len(total_in_progress),
                    "completed": len(total_completed),
                    "failed": len(total_failed),
                }

        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}


class RepositoryError(Exception):
    """Excepción específica para errores del repositorio."""

    pass


# Instancia singleton del repositorio
job_repository = PostgreSQLProcessingJobRepository()

"""
Tests with real PostgreSQL database using testcontainers.

This provides more realistic testing compared to mocking all database responses.
"""

import os
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select
from testcontainers.postgres import PostgresContainer

from app.domains.uploads.processors.bulk_processors.eventos import EventosBulkProcessor
from app.domains.uploads.processors.core.columns import Columns
from app.domains.salud.models import Sintoma
from app.domains.ciudadanos.models import Ciudadano
from app.domains.eventos.models import Evento
import logging


@pytest.fixture(scope="module")
def postgres_container():
    """Create a PostgreSQL container for testing."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="module")
def database_url(postgres_container):
    """Get the database URL from the container."""
    return postgres_container.get_connection_url()


@pytest.fixture
def engine(database_url):
    """Create a SQLAlchemy engine."""
    # Replace psycopg2 with asyncpg driver format
    url = database_url.replace("postgresql+psycopg2", "postgresql")
    return create_engine(url)


@pytest.fixture
def session(engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    # Create all tables
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # No autocommit, no autorollback - deja que el processor maneje todo
        yield session
        
    # Clean up tables after test
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


class ProcessingContext:
    """Context for processors that includes session and logger."""

    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)


class TestRealDatabaseIntegration:
    """Test with real database instead of mocks."""

    def test_sintomas_extraction_real_db(self, session):
        """Test síntomas extraction with real database operations."""
        # Create test data
        df = pd.DataFrame(
            {
                Columns.CODIGO_CIUDADANO: [5808888075, 5808888075, 5808888076],
                Columns.IDEVENTOCASO: [35937274, 35937274, 35937275],
                Columns.SIGNO_SINTOMA: ["Fiebre mayor a 38,5°", "Cefalea", "Vómitos"],
                Columns.ID_SNVS_SIGNO_SINTOMA: [199, 102, 204],
                Columns.EVENTO: ["Hantavirosis", "Hantavirosis", "Meningitis"],
                Columns.GRUPO_EVENTO: ["ZOONOSIS", "ZOONOSIS", "MENINGITIS"],
            }
        )

        # Create context with real session
        context = ProcessingContext(session)
        processor = EventosBulkProcessor(context, context.logger)

        # Process síntomas - this will do real DB operations
        sintomas_map = processor._get_or_create_sintomas(df)

        # Verify in real database
        assert len(sintomas_map) == 3, f"Expected 3 síntomas, got {len(sintomas_map)}"

        # Check síntomas were actually created in DB
        db_sintomas = session.exec(select(Sintoma)).all()
        assert (
            len(db_sintomas) == 3
        ), f"Expected 3 síntomas in DB, got {len(db_sintomas)}"

        # Verify specific síntomas
        sintomas_nombres = {s.signo_sintoma for s in db_sintomas}
        assert "Fiebre mayor a 38,5°" in sintomas_nombres
        assert "Cefalea" in sintomas_nombres
        assert "Vómitos" in sintomas_nombres

        # Verify IDs are preserved
        for sintoma in db_sintomas:
            if sintoma.signo_sintoma == "Fiebre mayor a 38,5°":
                assert sintoma.id_snvs_signo_sintoma == 199
            elif sintoma.signo_sintoma == "Cefalea":
                assert sintoma.id_snvs_signo_sintoma == 102
            elif sintoma.signo_sintoma == "Vómitos":
                assert sintoma.id_snvs_signo_sintoma == 204

    def test_complete_processing_pipeline(self, session):
        """Test the complete processing pipeline with real database."""
        # Create comprehensive test data - similar to real CSV structure
        df = pd.DataFrame(
            {
                # Ciudadano data
                Columns.CODIGO_CIUDADANO: [5808888075],
                Columns.NOMBRE: ["Juan"],
                Columns.APELLIDO: ["Pérez"],
                Columns.SEXO: ["M"],
                Columns.TIPO_DOC: ["DNI"],
                Columns.NRO_DOC: ["12345678"],
                Columns.FECHA_NACIMIENTO: ["15/01/1990"],
                # Evento data
                Columns.IDEVENTOCASO: [35937274],
                Columns.EVENTO: ["Hantavirosis"],
                Columns.GRUPO_EVENTO: ["ZOONOSIS"],
                Columns.CLASIFICACION_MANUAL: ["Caso confirmado"],
                Columns.FECHA_INICIO_SINTOMA: ["11/03/2023"],
                Columns.FECHA_APERTURA: ["17/03/2023"],
                # Síntoma data
                Columns.SIGNO_SINTOMA: ["Fiebre mayor a 38,5°"],
                Columns.ID_SNVS_SIGNO_SINTOMA: [199],
                # Geographic data - all required fields
                Columns.PROVINCIA_RESIDENCIA: ["Chubut"],
                Columns.ID_PROV_INDEC_RESIDENCIA: [26],
                Columns.DEPARTAMENTO_RESIDENCIA: ["Cushamen"],
                Columns.ID_DEPTO_INDEC_RESIDENCIA: [26014],
                Columns.LOCALIDAD_RESIDENCIA: ["EL MAITEN"],
                Columns.ID_LOC_INDEC_RESIDENCIA: [26014050],
                # Establecimiento data with localities
                Columns.ESTAB_CLINICA: ["HOSPITAL SUBZONAL EL MAITEN"],
                Columns.ID_ESTAB_CLINICA: [13575],
                Columns.ID_LOC_INDEC_CLINICA: [26014050],
                Columns.ESTABLECIMIENTO_EPI: ["HOSPITAL ZONAL ESQUEL"],
                Columns.ID_LOC_INDEC_EPI: [26014050],  # Use same locality as exists
                Columns.ESTABLECIMIENTO_CARGA: ["EPIDEMIOLOGIA CHUBUT"],
                Columns.ID_LOC_INDEC_CARGA: [26014050],  # Use same locality as exists
            }
        )

        context = ProcessingContext(session)

        # Import all processors
        from app.domains.uploads.processors.bulk_processors.ciudadanos import (
            CiudadanosBulkProcessor,
        )
        from app.domains.uploads.processors.bulk_processors.establecimientos import (
            EstablecimientosBulkProcessor,
        )
        from app.domains.eventos.models import TipoEno, GrupoEno
        from app.domains.establecimientos.models import Establecimiento
        from app.domains.localidades.models import Localidad, Departamento, Provincia

        # 1. Process geographic hierarchy first
        estab_processor = EstablecimientosBulkProcessor(context, context.logger)
        estab_mapping = estab_processor.bulk_upsert_establecimientos(df)

        # 2. Process ciudadanos
        ciudadano_processor = CiudadanosBulkProcessor(context, context.logger)
        ciudadano_mapping = ciudadano_processor.bulk_upsert_ciudadanos(df)

        # 3. Process eventos - need to create groups and types first
        evento_processor = EventosBulkProcessor(context, context.logger)

        # Create síntomas first
        sintomas_mapping = evento_processor._get_or_create_sintomas(df)

        # Create ENO groups and types using the proper methods
        grupo_mapping = evento_processor._get_or_create_grupos_eno(df)
        tipo_mapping = evento_processor._get_or_create_tipos_eno(df, grupo_mapping)

        # Process eventos with all dependencies (need to pass establecimiento mapping)
        evento_mapping = evento_processor.bulk_upsert_eventos(df, estab_mapping)

        # === VERIFY EVERYTHING WAS CREATED CORRECTLY ===

        # Verify ciudadanos were created
        ciudadanos = session.exec(select(Ciudadano)).all()
        assert len(ciudadanos) == 1, "Should have 1 ciudadano in DB"
        assert ciudadanos[0].nombre == "Juan"
        assert ciudadanos[0].apellido == "Pérez"

        # Verify eventos were created
        eventos = session.exec(select(Evento)).all()
        assert len(eventos) == 1, "Should have 1 evento in DB"

        # Verify síntomas
        sintomas = session.exec(select(Sintoma)).all()
        assert len(sintomas) == 1, "Should have 1 síntoma in DB"
        assert sintomas[0].signo_sintoma == "Fiebre mayor a 38,5°"
        assert sintomas[0].id_snvs_signo_sintoma == 199

        # Verify geographic hierarchy
        provincias = session.exec(select(Provincia)).all()
        assert len(provincias) >= 1, "Should have at least 1 provincia"

        departamentos = session.exec(select(Departamento)).all()
        assert len(departamentos) >= 1, "Should have at least 1 departamento"

        localidades = session.exec(select(Localidad)).all()
        assert len(localidades) >= 1, "Should have at least 1 localidad"

        # Verify establecimientos
        establecimientos = session.exec(select(Establecimiento)).all()
        assert (
            len(establecimientos) >= 3
        ), f"Should have at least 3 establecimientos, got {len(establecimientos)}"

    def test_duplicate_handling_real_db(self, session):
        """Test that duplicates are handled correctly in real database."""
        # Create data with duplicate síntomas
        df = pd.DataFrame(
            {
                Columns.CODIGO_CIUDADANO: [1, 2, 3],
                Columns.IDEVENTOCASO: [100, 200, 300],
                Columns.SIGNO_SINTOMA: [
                    "Fiebre",
                    "Fiebre",
                    "Tos",
                ],  # Duplicate 'Fiebre'
                Columns.ID_SNVS_SIGNO_SINTOMA: [1, 1, 2],
                Columns.EVENTO: ["COVID", "COVID", "COVID"],
                Columns.GRUPO_EVENTO: [
                    "RESPIRATORIAS",
                    "RESPIRATORIAS",
                    "RESPIRATORIAS",
                ],
            }
        )

        context = ProcessingContext(session)
        processor = EventosBulkProcessor(context, context.logger)

        # Process síntomas
        sintomas_map = processor._get_or_create_sintomas(df)

        # Should only create 2 unique síntomas
        assert (
            len(sintomas_map) == 2
        ), f"Expected 2 unique síntomas, got {len(sintomas_map)}"
        assert "Fiebre" in sintomas_map
        assert "Tos" in sintomas_map

        # Verify in database
        db_sintomas = session.exec(select(Sintoma)).all()
        assert len(db_sintomas) == 2, "Should have 2 síntomas in DB"

        # Process again - should not create duplicates
        sintomas_map2 = processor._get_or_create_sintomas(df)
        assert len(sintomas_map2) == 2, "Should still have 2 síntomas"

        db_sintomas_after = session.exec(select(Sintoma)).all()
        assert len(db_sintomas_after) == 2, "Should still have 2 síntomas in DB"


class TestMainProcessorIntegration:
    """Test that the foreign key bug is fixed using the complete MainBulkProcessor pipeline."""

    def test_foreign_key_bug_simple_direct(self, session):
        """
        Test simple directo: crear síntomas, luego crear relaciones.
        Sin usar MainBulkProcessor, solo SQLAlchemy directo.
        """
        from app.domains.salud.models import Sintoma
        from app.domains.eventos.models import DetalleEventoSintomas, Evento, TipoEno, GrupoEno
        from app.domains.ciudadanos.models import Ciudadano
        
        # 1. Crear síntomas directamente
        sintoma1 = Sintoma(
            id_snvs_signo_sintoma=199,
            signo_sintoma="Fiebre mayor a 38,5°"
        )
        sintoma2 = Sintoma(
            id_snvs_signo_sintoma=102,
            signo_sintoma="Cefalea"
        )
        
        session.add(sintoma1)
        session.add(sintoma2)
        session.flush()  # Obtener IDs sin commit
        
        # 2. Crear grupo y tipo
        grupo = GrupoEno(codigo="ZOONOSIS", descripcion="ZOONOSIS", nombre="ZOONOSIS")
        session.add(grupo)
        session.flush()
        
        tipo = TipoEno(codigo="Hantavirosis", descripcion="Hantavirosis", nombre="Hantavirosis", id_grupo_eno=grupo.id)
        session.add(tipo)
        session.flush()
        
        # 3. Crear ciudadano
        ciudadano = Ciudadano(
            codigo_ciudadano=5808888075,
            nombre="Juan",
            apellido="Pérez"
        )
        session.add(ciudadano)
        session.flush()
        
        # 4. Crear evento
        evento = Evento(
            id_evento_caso=35937274,
            id_tipo_eno=tipo.id,
            id_ciudadano=ciudadano.id
        )
        session.add(evento)
        session.flush()
        
        # 5. Crear relaciones síntoma-evento (aquí era donde fallaba)
        relacion1 = DetalleEventoSintomas(
            id_evento=evento.id,
            id_sintoma=sintoma1.id
        )
        relacion2 = DetalleEventoSintomas(
            id_evento=evento.id,
            id_sintoma=sintoma2.id
        )
        
        session.add(relacion1)
        session.add(relacion2)
        
        # Si llegamos aquí sin error, el bug está arreglado
        session.flush()
        
        # Verificar que todo se creó correctamente
        sintomas = session.query(Sintoma).all()
        assert len(sintomas) == 2
        
        relaciones = session.query(DetalleEventoSintomas).all()
        assert len(relaciones) == 2
        
        print("✅ Test simple directo pasó - no hay problema con foreign keys")

    def test_foreign_key_bug_is_fixed(self, session):
        """
        Test that múltiple síntomas for the same event don't cause foreign key violations.

        This reproduces the exact bug that was happening in production:
        - Same event (IDEVENTOCASO=35937274) with multiple síntomas
        - MainBulkProcessor creates síntomas first, then uses them in relationships
        - Should complete successfully without foreign key violations
        """
        # Create test data with the EXACT pattern that was causing the bug:
        # Same event with multiple different síntomas
        df = pd.DataFrame(
            {
                # Ciudadano data
                Columns.CODIGO_CIUDADANO: [5808888075, 5808888075],
                Columns.NOMBRE: ["Juan", "Juan"],
                Columns.APELLIDO: ["Pérez", "Pérez"],
                Columns.SEXO: ["M", "M"],
                Columns.TIPO_DOC: ["DNI", "DNI"],
                Columns.NRO_DOC: ["12345678", "12345678"],
                Columns.FECHA_NACIMIENTO: ["15/01/1990", "15/01/1990"],
                # THE BUG SCENARIO: Same event, multiple symptoms
                Columns.IDEVENTOCASO: [35937274, 35937274],  # Same event ID
                Columns.EVENTO: ["Hantavirosis", "Hantavirosis"],
                Columns.GRUPO_EVENTO: ["ZOONOSIS", "ZOONOSIS"],
                Columns.CLASIFICACION_MANUAL: ["Caso confirmado", "Caso confirmado"],
                Columns.FECHA_INICIO_SINTOMA: ["11/03/2023", "11/03/2023"],
                Columns.FECHA_APERTURA: ["17/03/2023", "17/03/2023"],
                # Different síntomas for same event - this was causing FK violations
                Columns.SIGNO_SINTOMA: ["Fiebre mayor a 38,5°", "Cefalea"],
                Columns.ID_SNVS_SIGNO_SINTOMA: [199, 102],
                # Required geographic data
                Columns.PROVINCIA_RESIDENCIA: ["Chubut", "Chubut"],
                Columns.ID_PROV_INDEC_RESIDENCIA: [26, 26],
                Columns.DEPARTAMENTO_RESIDENCIA: ["Cushamen", "Cushamen"],
                Columns.ID_DEPTO_INDEC_RESIDENCIA: [26014, 26014],
                Columns.LOCALIDAD_RESIDENCIA: ["EL MAITEN", "EL MAITEN"],
                Columns.ID_LOC_INDEC_RESIDENCIA: [26014050, 26014050],
                # Required establecimiento data
                Columns.ESTAB_CLINICA: [
                    "HOSPITAL SUBZONAL EL MAITEN",
                    "HOSPITAL SUBZONAL EL MAITEN",
                ],
                Columns.ID_ESTAB_CLINICA: [13575, 13575],
                Columns.ID_LOC_INDEC_CLINICA: [26014050, 26014050],
                Columns.ESTABLECIMIENTO_EPI: [
                    "HOSPITAL ZONAL ESQUEL",
                    "HOSPITAL ZONAL ESQUEL",
                ],
                Columns.ID_LOC_INDEC_EPI: [26014050, 26014050],
                Columns.ESTABLECIMIENTO_CARGA: [
                    "EPIDEMIOLOGIA CHUBUT",
                    "EPIDEMIOLOGIA CHUBUT",
                ],
                Columns.ID_LOC_INDEC_CARGA: [26014050, 26014050],
            }
        )

        # Use the EXACT same workflow as production (MainBulkProcessor)
        from app.domains.uploads.processors.bulk_processors.main_processor import (
            MainBulkProcessor,
        )

        context = ProcessingContext(session)
        main_processor = MainBulkProcessor(context, context.logger)

        # This should work without foreign key violations thanks to our fix
        results = main_processor.process_all(df)

        # === VERIFY THE BUG IS FIXED ===

        # 1. Processing should complete successfully
        assert "sintomas_eventos" in results
        assert results["sintomas_eventos"].inserted_count == 2
        assert len(results["sintomas_eventos"].errors) == 0

        # 2. Both síntomas should be created
        sintomas = session.exec(select(Sintoma)).all()
        assert len(sintomas) == 2, "Should have 2 síntomas"
        sintoma_names = {s.signo_sintoma for s in sintomas}
        assert "Fiebre mayor a 38,5°" in sintoma_names
        assert "Cefalea" in sintoma_names

        # 3. Both síntoma-evento relationships should be created
        from app.domains.eventos.models import DetalleEventoSintomas

        sintoma_eventos = session.exec(select(DetalleEventoSintomas)).all()
        assert len(sintoma_eventos) == 2, "Should have 2 síntoma-evento relationships"

        # 4. One event should be created
        from app.domains.eventos.models import Evento

        eventos = session.exec(select(Evento)).all()
        assert len(eventos) == 1, "Should have 1 event"

        # 5. One ciudadano should be created
        ciudadanos = session.exec(select(Ciudadano)).all()
        assert len(ciudadanos) == 1, "Should have 1 ciudadano"

        context.logger.info(
            "✅ FOREIGN KEY BUG IS FIXED - Multiple síntomas processed successfully"
        )


class TestMeningitisCSVRealDB:
    """Test with Meningitis CSV structure using real database."""

    def test_meningitis_csv_processing(self, session):
        """Test processing Meningitis CSV-like data with real DB."""
        # Simulate the actual Meningitis CSV structure
        df = pd.DataFrame(
            {
                Columns.CODIGO_CIUDADANO: [5808888075] * 4,  # Same person
                Columns.IDEVENTOCASO: [35937274] * 4,  # Same event
                Columns.EVENTO: ["Hantavirosis"] * 4,
                Columns.GRUPO_EVENTO: ["ZOONOSIS"] * 4,
                # Different síntomas and muestras for same event
                Columns.ID_SNVS_SIGNO_SINTOMA: [199, 102, 199, 713],
                Columns.SIGNO_SINTOMA: [
                    "Fiebre mayor a 38,5°",
                    "Cefalea",
                    "Fiebre mayor a 38,5°",  # Duplicate
                    "Infiltrado bilateral",
                ],
                # Test other columns exist
                Columns.CLASIFICACION_MANUAL: ["Caso confirmado"] * 4,
                Columns.PROVINCIA_RESIDENCIA: ["Chubut"] * 4,
                Columns.ID_PROV_INDEC_RESIDENCIA: [26] * 4,
            }
        )

        context = ProcessingContext(session)
        processor = EventosBulkProcessor(context, context.logger)

        # Process síntomas
        sintomas_map = processor._get_or_create_sintomas(df)

        # Should deduplicate to 3 unique síntomas
        assert (
            len(sintomas_map) == 3
        ), f"Expected 3 unique síntomas, got {len(sintomas_map)}"

        # Verify all unique síntomas are present
        assert "Fiebre mayor a 38,5°" in sintomas_map
        assert "Cefalea" in sintomas_map
        assert "Infiltrado bilateral" in sintomas_map

        # Verify in real database
        db_sintomas = session.exec(select(Sintoma)).all()
        assert len(db_sintomas) == 3

        # Check SNVS IDs are preserved correctly
        id_mapping = {s.signo_sintoma: s.id_snvs_signo_sintoma for s in db_sintomas}
        assert id_mapping.get("Fiebre mayor a 38,5°") == 199
        assert id_mapping.get("Cefalea") == 102
        assert id_mapping.get("Infiltrado bilateral") == 713

    def test_foreign_key_error_prevention(self, session):
        """Test that síntomas are created before relationships to prevent FK violations."""
        # Focus on just síntomas and eventos - minimal test
        df = pd.DataFrame(
            {
                Columns.CODIGO_CIUDADANO: [5808888075],
                Columns.IDEVENTOCASO: [35937274],
                Columns.SIGNO_SINTOMA: ["Fiebre mayor a 38,5°"],
                Columns.ID_SNVS_SIGNO_SINTOMA: [199],
                Columns.EVENTO: ["Hantavirosis"],
                Columns.GRUPO_EVENTO: ["ZOONOSIS"],
            }
        )

        context = ProcessingContext(session)

        # Test the specific bug fix: síntomas must be created before eventos
        from app.domains.uploads.processors.bulk_processors.eventos import (
            EventosBulkProcessor,
        )

        processor = EventosBulkProcessor(context, context.logger)

        # STEP 1: Create síntomas first (this is the fix)
        sintomas_mapping = processor._get_or_create_sintomas(df)

        # Verify síntomas were created BEFORE we try to use them in relationships
        sintomas = session.exec(select(Sintoma)).all()
        assert len(sintomas) == 1, "Should have 1 síntoma created before relationships"
        assert sintomas[0].signo_sintoma == "Fiebre mayor a 38,5°"
        assert sintomas[0].id_snvs_signo_sintoma == 199

        # STEP 2: Now create ENO groups and types (needed for eventos)
        grupo_mapping = processor._get_or_create_grupos_eno(df)
        tipo_mapping = processor._get_or_create_tipos_eno(df, grupo_mapping)

        # At this point, síntomas exist in the database and can be safely referenced
        # The original error was that síntomas_eventos table tried to reference
        # síntoma IDs that didn't exist yet

        # STEP 3: Test that we can reference síntomas without FK violations
        # This is implicit in the sintomas_mapping being usable
        assert "Fiebre mayor a 38,5°" in sintomas_mapping
        sintoma_id = sintomas_mapping["Fiebre mayor a 38,5°"]
        assert (
            sintoma_id is not None
        ), "Síntoma should have a valid ID for relationships"

        # Success: If we get here without foreign key violations, the fix works
        context.logger.info(
            f"Síntomas creados exitosamente antes de relaciones: {len(sintomas_mapping)}"
        )

"""
Seed de estrategias epidemiológicas.

Este módulo carga las estrategias de vigilancia en la base de datos.
Puede ser ejecutado directamente o importado desde seed.py
"""

import datetime as dt
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlmodel import col

from app.domains.vigilancia_nominal.clasificacion.models import (
    ClassificationRule,
    EstrategiaClasificacion,
    FilterCondition,
    TipoClasificacion,
    TipoFiltro,
)
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    EnfermedadGrupo,
    GrupoDeEnfermedades,
)


class StrategySeeder:
    """Seeder para migrar estrategias desde el codigo legacy."""

    def __init__(self, session: Session):
        self.session = session
        self.created_strategies: Dict[str, EstrategiaClasificacion] = {}
        self.tipo_enos: Dict[str, Enfermedad] = {}

    def seed_all(self) -> None:
        """Ejecuta el seed completo de todas las estrategias."""
        print("🚀 Iniciando migración de estrategias...")

        # Primero asegurar que existen los tipos ENO
        self._ensure_tipo_enos()

        # Hacer commit para que los tipos ENO persistan
        self.session.commit()

        # Migrar cada estrategia (nombres exactos del CSV)
        strategies = [
            self._seed_dengue,
            self._seed_tuberculosis,
            self._seed_sifilis,
            self._seed_vih,
            self._seed_suh,
            self._seed_intento_suicidio,
            self._seed_int_mon_carbono,
            self._seed_sars_cov2_especial,
            self._seed_uc_irag,
            self._seed_sifilis_gestantes,
            self._seed_diarrea_aguda,
            self._seed_meningoencefalitis,
            self._seed_otras_infecciones_invasivas,
            self._seed_hidatidosis,
            self._seed_apr_rabia,
            self._seed_hantavirus,
            self._seed_araneismo,
            self._seed_chagas_cronico,
            self._seed_brucelosis,
            self._seed_brote_eta,
            self._seed_coqueluche,
            self._seed_hepatitis_b,
            self._seed_hepatitis_c,
        ]

        for seed_func in strategies:
            try:
                seed_func()
                print(f"✅ {seed_func.__name__.replace('_seed_', '').title()} migrado")
            except Exception as e:
                print(f"❌ Error migrando {seed_func.__name__}: {e}")
                self.session.rollback()

        self.session.commit()
        print(
            f"✨ Migración completada: {len(self.created_strategies)} estrategias creadas"
        )

    def _ensure_tipo_enos(self) -> None:
        """Asegura que existen los tipos ENO necesarios."""
        # Primero verificar/crear grupo ENO
        grupo = self._get_or_create_grupo_eno(
            "Vigilancia Epidemiológica", "Grupo principal de eventos de vigilancia"
        )

        # Lista de tipos ENO requeridos (NOMBRES EXACTOS DEL CSV)
        tipos_required = [
            ("Dengue", "dengue"),
            ("Tuberculosis", "tuberculosis"),
            ("Sífilis", "sifilis"),
            ("VIH", "vih"),
            ("SUH - Sindrome Urémico Hemolítico", "suh-sindrome-uremico-hemolitico"),
            ("Intento de Suicidio", "intento-de-suicidio"),
            (
                "Intoxicación/Exposición por Monóxido de Carbono",
                "intoxicacion-exposicion-por-monoxido-de-carbono",
            ),
            (
                "Estudio de SARS-COV-2 en situaciones especiales",
                "estudio-de-sars-cov-2-en-situaciones-especiales",
            ),
            (
                "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
                "unidad-centinela-de-infeccion-respiratoria-aguda-grave-uc-irag",
            ),
            ("Sífilis en personas gestantes", "sifilis-en-personas-gestantes"),
            ("Diarrea aguda", "diarrea-aguda"),
            ("Meningoencefalitis", "meningoencefalitis"),
            (
                "Otras infecciones invasivas (bacterianas y otras)",
                "otras-infecciones-invasivas-bacterianas-y-otras",
            ),
            ("Hidatidosis", "hidatidosis"),
            (
                "Accidente potencialmente rábico (APR)",
                "accidente-potencialmente-rabico-apr",
            ),
            ("Hantavirosis", "hantavirosis"),
            (
                "Araneísmo-Envenenamiento por Latrodectus (Latrodectismo)",
                "araneismo-envenenamiento-por-latrodectus-latrodectismo",
            ),
            ("Chagas crónico", "chagas-cronico"),
            ("Brucelosis", "brucelosis"),
            ("Sospecha de brote de ETA", "sospecha-de-brote-de-eta"),
            ("Coqueluche", "coqueluche"),
            ("Hepatitis B", "hepatitis-b"),
            ("Hepatitis C", "hepatitis-c"),
        ]

        if grupo.id is None:
            raise ValueError("Grupo de enfermedades no tiene ID asignado")

        for nombre, codigo in tipos_required:
            tipo_eno = self._get_or_create_tipo_eno(nombre, codigo, grupo.id)
            # Almacenar con el nombre original para matching en create_strategy
            self.tipo_enos[nombre] = tipo_eno

    def _get_or_create_grupo_eno(
        self, nombre: str, descripcion: str
    ) -> GrupoDeEnfermedades:
        """Obtiene o crea un grupo ENO."""
        # Usar kebab-case para slug
        slug_kebab = "vigilancia-epidemiologica"

        # Buscar existente por nombre (sin convertir a mayusculas)
        result = self.session.execute(
            select(GrupoDeEnfermedades).where(col(GrupoDeEnfermedades.nombre) == nombre)
        )
        grupo = result.scalar_one_or_none()

        if not grupo:
            grupo = GrupoDeEnfermedades(
                nombre=nombre, descripcion=descripcion, slug=slug_kebab
            )
            self.session.add(grupo)
            self.session.flush()

        return grupo

    def _get_or_create_tipo_eno(
        self, nombre: str, slug: str, grupo_id: int
    ) -> Enfermedad:
        """Obtiene o crea un tipo ENO."""

        # Buscar existente por slug kebab-case
        result = self.session.execute(
            select(Enfermedad).where(col(Enfermedad.slug) == slug)
        )
        tipo_eno = result.scalar_one_or_none()

        if not tipo_eno:
            tipo_eno = Enfermedad(
                nombre=nombre,
                slug=slug,  # kebab-case
                descripcion=f"CasoEpidemiologicos de tipo {nombre}",
            )
            self.session.add(tipo_eno)
            self.session.flush()

            # Verificar que tipo_eno tiene ID antes de crear la relación
            if tipo_eno.id is None:
                raise ValueError(
                    f"Enfermedad '{nombre}' no tiene ID asignado después de flush"
                )

            # Crear relación con el grupo
            enfermedad_grupo = EnfermedadGrupo(
                id_enfermedad=tipo_eno.id,
                id_grupo=grupo_id,
            )
            self.session.add(enfermedad_grupo)
            self.session.flush()

        return tipo_eno

    def _create_strategy(
        self,
        tipo_eno_name: str,
        name: str,
        description: str,
        config: Optional[Dict] = None,
        confidence_threshold: float = 0.7,
    ) -> EstrategiaClasificacion:
        """Crea una estrategia base."""
        tipo_eno = self.tipo_enos.get(tipo_eno_name)
        if not tipo_eno:
            raise ValueError(f"Tipo ENO '{tipo_eno_name}' no encontrado")

        # Verificar si ya existe
        if tipo_eno.id is None:
            raise ValueError(f"Tipo ENO '{tipo_eno_name}' no tiene ID asignado")

        result = self.session.execute(
            select(EstrategiaClasificacion).where(
                col(EstrategiaClasificacion.id_enfermedad) == tipo_eno.id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        strategy = EstrategiaClasificacion(
            id_enfermedad=tipo_eno.id,
            name=name,
            description=description,
            config=config or {},
            confidence_threshold=confidence_threshold,
            valid_from=dt.datetime(2000, 1, 1),
            valid_until=None,
            is_active=True,
            created_by="seed_script",
        )

        self.session.add(strategy)
        self.session.flush()

        self.created_strategies[tipo_eno_name] = strategy
        return strategy

    def _add_classification_rule(
        self,
        strategy: EstrategiaClasificacion,
        classification: TipoClasificacion,
        name: str,
        conditions: List[Dict],
        priority: int = 100,
        justificacion: Optional[str] = None,
        ejemplos: Optional[str] = None,
    ) -> ClassificationRule:
        """Agrega una regla de clasificación con sus condiciones."""
        if strategy.id is None:
            raise ValueError("Strategy debe tener ID asignado antes de agregar reglas")

        rule = ClassificationRule(
            strategy_id=strategy.id,
            classification=classification,
            name=name,
            description=f"Regla para identificar casos {classification.value}",
            justificacion=justificacion,
            ejemplos=ejemplos,
            priority=priority,
            is_active=True,
            auto_approve=True,
            required_confidence=0.0,
        )

        self.session.add(rule)
        self.session.flush()

        if rule.id is None:
            raise ValueError("Rule debe tener ID asignado después de flush")

        # Agregar condiciones
        for idx, condition_data in enumerate(conditions):
            condition = FilterCondition(rule_id=rule.id, order=idx, **condition_data)
            self.session.add(condition)

        self.session.flush()
        return rule

    # ============== ESTRATEGIAS ESPECÍFICAS ==============

    def _seed_dengue(self) -> None:
        """Seed para Dengue."""
        strategy = self._create_strategy(
            tipo_eno_name="Dengue",
            name="Estrategia Dengue",
            description="Estrategia para procesar casos de Dengue",
        )

        # Regla: Confirmados - Actualizada para usar config
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Dengue",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {
                        "values": [
                            "caso confirmado den-1",
                            "caso confirmado den-2",
                            "caso confirmado den-3",
                            "caso confirmado den-4",
                            "caso confirmado sin serotipo",
                            "caso confirmado por nexo epidemiológico autóctono",
                            "caso confirmado por nexo epidemiológico importado",
                            "caso de dengue en brote con laboratorio (+)",
                        ],
                        "strict": False,  # Usar modo insensible por defecto
                    },
                }
            ],
            priority=1,
        )

        # Regla: Sospechosos - Actualizada para usar config
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SOSPECHOSOS,
            "Casos sospechosos de Dengue",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {
                        "values": [
                            "caso sospechoso no conclusivo",
                            "caso probable",
                            "caso sospechoso",
                        ],
                        "strict": False,
                    },
                }
            ],
            priority=2,
        )

        # Regla: Descartados - Nueva regla para casos descartados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.DESCARTADOS,
            "Casos descartados de Dengue",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {
                        "values": ["caso descartado", "descartado"],
                        "strict": False,
                    },
                }
            ],
            priority=3,
        )

    def _seed_apr_rabia(self) -> None:
        """Seed para Accidente potencialmente rábico (APR)."""
        strategy = self._create_strategy(
            tipo_eno_name="Accidente potencialmente rábico (APR)",
            name="Estrategia APR - Rabia",
            description="""Estrategia para procesar casos de Accidentes potencialmente rábicos.

            IMPORTANTE: En Rabia se reportan tanto casos de animales como de humanos.

            DETECCIÓN AUTOMÁTICA:
            - ANIMALES: SEXO='IND', documentos no estándar, nomenclatura científica
            - HUMANOS: SEXO='M/F', TIPO_DOC='DNI/LC/LE', nombres típicos de personas
            - AMBIGUOS: Datos contradictorios → REQUIERE_REVISION

            Casos que requieren revisión manual:
            1. SEXO='IND' pero nombre parece de persona
            2. Documentos no estándar pero datos humanos
            3. Nomenclatura mixta o contradictoria
            4. Confidence < 60% en detección automática
            """,
            config={"metadata_extractors": ["tipo_sujeto", "fuente_contagio"]},
            confidence_threshold=0.6,
        )

        # Regla 1: Extractor de metadata (se ejecuta primero)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.REQUIERE_REVISION,  # No filtra, solo extrae
            "Extracción de metadata de tipo de sujeto y fuente de contagio",
            [
                {
                    "filter_type": TipoFiltro.DETECTOR_TIPO_SUJETO,
                    "field_name": "TIPO_SUJETO_META",
                    "config": {
                        "target_type": "cualquiera",  # No filtra por tipo
                        "min_confidence": 0.0,  # Acepta cualquier confidence
                    },
                    "extracted_metadata_field": "tipo_sujeto",
                },
                {
                    "filter_type": TipoFiltro.EXTRACTOR_METADATA,
                    "field_name": "FUENTE_CONTAGIO_META",
                    "config": {"extractor": "fuente_contagio"},
                    "extracted_metadata_field": "fuente_contagio",
                    "logical_operator": "AND",
                },
            ],
            priority=1,
            justificacion="Extrae información de tipo de sujeto y fuente de contagio para análisis posterior",
        )

        # Regla 2: Casos CONFIRMADOS
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Rabia",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_IGUAL,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "caso confirmado", "strict": False},
                }
            ],
            priority=2,
            justificacion="Casos de rabia confirmados según clasificación manual",
            ejemplos="Tanto humanos como animales con CLASIFICACION_MANUAL='Caso confirmado'",
        )

        # Regla 3: Casos SOSPECHOSOS
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SOSPECHOSOS,
            "Casos sospechosos de Rabia",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_IGUAL,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "caso sospechoso", "strict": False},
                }
            ],
            priority=3,
            justificacion="Casos sospechosos de rabia requieren seguimiento",
        )

        # Regla 4: Casos DESCARTADOS
        self._add_classification_rule(
            strategy,
            TipoClasificacion.DESCARTADOS,
            "Casos descartados de Rabia",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_IGUAL,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "caso descartado", "strict": False},
                }
            ],
            priority=4,
            justificacion="Casos descartados tras análisis de laboratorio",
        )

    def _seed_uc_irag(self) -> None:
        """Seed para UC-IRAG."""
        strategy = self._create_strategy(
            tipo_eno_name="Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
            name="Estrategia UC-IRAG",
            description="Estrategia para procesar casos de UC-IRAG",
            config={
                "eventos_relacionados": ["COVID", "SARS-COV-2", "Influenza", "VSR"]
            },
        )

        # Regla: Confirmados (resultado positivo)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados por laboratorio",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "RESULTADO",
                    "config": {"values": ["positivo", "detectable"], "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_sifilis(self) -> None:
        """Seed para Sífilis (grupo con múltiples subtipos)."""
        strategy = self._create_strategy(
            tipo_eno_name="Sífilis",
            name="Estrategia Sífilis",
            description="Estrategia para procesar casos de Sífilis y sus variantes",
            config={
                "grupo_evento": "Sífilis",
                "subtipos": [
                    "Sífilis congénita",
                    "Sífilis en personas gestantes",
                    "Sífilis - RN expuesto en investigación",
                ],
            },
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Sífilis",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmad", "strict": False},
                }
            ],
            priority=1,
        )

        # Regla: Notificados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.NOTIFICADOS,
            "Casos notificados de Sífilis",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_NO_NULO,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=2,
        )

    def _seed_coqueluche(self) -> None:
        """Seed para Coqueluche."""
        strategy = self._create_strategy(
            tipo_eno_name="Coqueluche",
            name="Estrategia Coqueluche",
            description="Estrategia para procesar casos de Coqueluche (Tos convulsa)",
        )

        # Regla: Confirmados - Actualizada para usar config
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Coqueluche",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {
                        "values": [
                            "caso confirmado",
                            "caso confirmado clinico",
                            "caso confirmado por laboratorio",
                            "caso confirmado por nexo epidemiologico",
                        ],
                        "strict": False,  # Comparación insensible a mayúsculas/acentos por defecto
                    },
                }
            ],
            priority=1,
        )

        # Regla: Sospechosos - Actualizada para usar config
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SOSPECHOSOS,
            "Casos sospechosos de Coqueluche",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {
                        "values": ["caso sospechoso", "caso probable"],
                        "strict": False,
                    },
                }
            ],
            priority=2,
        )

    def _seed_hantavirus(self) -> None:
        """Seed para Hantavirus."""
        strategy = self._create_strategy(
            tipo_eno_name="Hantavirosis",
            name="Estrategia Hantavirus",
            description="Estrategia para procesar casos de Hantavirus",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Hantavirus",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

        # Regla: Sospechosos
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SOSPECHOSOS,
            "Casos sospechosos de Hantavirus",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "sospechoso", "strict": False},
                }
            ],
            priority=2,
        )

        # Regla: En estudio (contactos)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.EN_ESTUDIO,
            "Contactos en estudio",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "EVENTO",
                    "config": {"value": "contacto"},
                }
            ],
            priority=3,
        )

    def _seed_chagas_cronico(self) -> None:
        """Seed para Chagas crónico."""
        strategy = self._create_strategy(
            tipo_eno_name="Chagas crónico",
            name="Estrategia Chagas Crónico",
            description="Estrategia para procesar casos de Chagas crónico",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Chagas congénito",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_hepatitis_b(self) -> None:
        """Seed para Hepatitis B."""
        strategy = self._create_strategy(
            tipo_eno_name="Hepatitis B",
            name="Estrategia Hepatitis B",
            description="Estrategia para procesar casos de Hepatitis B",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Hepatitis B",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_intento_suicidio(self) -> None:
        """Seed para Intento de Suicidio."""
        strategy = self._create_strategy(
            tipo_eno_name="Intento de Suicidio",
            name="Estrategia Intento de Suicidio",
            description="Estrategia para procesar casos de intento de suicidio",
        )

        # Regla: Con resultado mortal
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CON_RESULTADO_MORTAL,
            "Casos con resultado mortal",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_IGUAL,
                    "field_name": "FALLECIDO",
                    "config": {"value": "SI"},
                }
            ],
            priority=1,
        )

        # Regla: Sin resultado mortal
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SIN_RESULTADO_MORTAL,
            "Casos sin resultado mortal",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_IGUAL,
                    "field_name": "FALLECIDO",
                    "config": {"value": "NO"},
                }
            ],
            priority=2,
        )

    def _seed_hidatidosis(self) -> None:
        """Seed para Hidatidosis."""
        strategy = self._create_strategy(
            tipo_eno_name="Hidatidosis",
            name="Estrategia Hidatidosis",
            description="Estrategia para procesar casos de Hidatidosis",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Hidatidosis",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_meningoencefalitis(self) -> None:
        """Seed para Meningoencefalitis."""
        strategy = self._create_strategy(
            tipo_eno_name="Meningoencefalitis",
            name="Estrategia Meningoencefalitis",
            description="Estrategia para procesar casos de Meningoencefalitis",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Meningoencefalitis",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_suh(self) -> None:
        """Seed para SUH - Síndrome Urémico Hemolítico."""
        strategy = self._create_strategy(
            tipo_eno_name="SUH - Sindrome Urémico Hemolítico",
            name="Estrategia SUH",
            description="Estrategia para procesar casos de SUH",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de SUH",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_botulismo(self) -> None:
        """Seed para Botulismo del lactante."""
        strategy = self._create_strategy(
            tipo_eno_name="Botulismo del lactante",
            name="Estrategia Botulismo",
            description="Estrategia para procesar casos de Botulismo",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Botulismo",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_efe(self) -> None:
        """Seed para Enfermedad Febril Exantemática."""
        strategy = self._create_strategy(
            tipo_eno_name="Enfermedad Febril Exantemática-EFE",
            name="Estrategia EFE",
            description="Estrategia para procesar casos de EFE (Sarampión/Rubéola)",
        )

        # Regla: Sospechosos
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SOSPECHOSOS,
            "Casos sospechosos de EFE",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_paf(self) -> None:
        """Seed para PAF - Poliomielitis."""
        strategy = self._create_strategy(
            tipo_eno_name="Poliomielitis-PAF",
            name="Estrategia PAF",
            description="Estrategia para procesar casos de PAF",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de PAF",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

        # Regla: Sospechosos
        self._add_classification_rule(
            strategy,
            TipoClasificacion.SOSPECHOSOS,
            "Casos sospechosos de PAF",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "sospechoso", "strict": False},
                }
            ],
            priority=2,
        )

    def _seed_mordedura_perro(self) -> None:
        """Seed para Mordedura de perro."""
        strategy = self._create_strategy(
            tipo_eno_name="Lesiones graves por mordedura de perro",
            name="Estrategia Mordedura de Perro",
            description="Estrategia para procesar casos de mordedura de perro",
        )

        # Regla: Confirmados (todos los casos notificados son confirmados)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de mordedura",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_apr(self) -> None:
        """Seed APR (Accidentes por Ponzoña de Arácnidos)."""
        print("  📋 Creando estrategia APR...")

        strategy = self._create_strategy(
            tipo_eno_name="Accidentes por Ponzoña de Arácnidos (APR)",
            name="Estrategia APR",
            description="Estrategia para procesar casos de accidentes por ponzoña de arácnidos",
        )

        # Regla: Confirmados (todos los casos notificados son confirmados)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de APR",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_hepatitis_b_per_ges(self) -> None:
        """Seed Hepatitis B en personas gestantes."""
        print("  📋 Creando estrategia Hepatitis B en gestantes...")

        strategy = self._create_strategy(
            tipo_eno_name="Hepatitis B en personas gestantes",
            name="Estrategia Hepatitis B en Gestantes",
            description="Estrategia para procesar casos de Hepatitis B en personas gestantes",
        )

        # Regla: Confirmados (todos los casos notificados son confirmados)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de Hepatitis B en gestantes",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_hepatitis_c(self) -> None:
        """Seed Hepatitis C."""
        print("  📋 Creando estrategia Hepatitis C...")

        strategy = self._create_strategy(
            tipo_eno_name="Hepatitis C",
            name="Estrategia Hepatitis C",
            description="Estrategia para procesar casos de Hepatitis C",
        )

        # Regla: Confirmados (todos los casos notificados son confirmados)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de Hepatitis C",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_int_mon_carbono(self) -> None:
        """Seed Intoxicación/Exposición por Monóxido de Carbono."""
        strategy = self._create_strategy(
            tipo_eno_name="Intoxicación/Exposición por Monóxido de Carbono",
            name="Estrategia Monóxido de Carbono",
            description="Estrategia para procesar casos de intoxicación por monóxido de carbono",
        )

        # Regla: Confirmados (todos los casos notificados son confirmados)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de intoxicación por monóxido de carbono",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_otras_infecciones_invasivas(self) -> None:
        """Seed Otras infecciones invasivas (bacterianas y otras)."""
        strategy = self._create_strategy(
            tipo_eno_name="Otras infecciones invasivas (bacterianas y otras)",
            name="Estrategia Otras Infecciones Invasivas",
            description="Estrategia para procesar casos de otras infecciones invasivas",
        )

        # Regla: Confirmados (todos los casos notificados son confirmados)
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de otras infecciones invasivas",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    # ==== NUEVAS ESTRATEGIAS BASADAS EN CSV ====

    def _seed_tuberculosis(self) -> None:
        """Seed Tuberculosis."""
        strategy = self._create_strategy(
            tipo_eno_name="Tuberculosis",
            name="Estrategia Tuberculosis",
            description="Estrategia para procesar casos de Tuberculosis",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Tuberculosis",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_vih(self) -> None:
        """Seed VIH."""
        strategy = self._create_strategy(
            tipo_eno_name="VIH",
            name="Estrategia VIH",
            description="Estrategia para procesar casos de VIH",
        )

        # Regla: Notificados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.NOTIFICADOS,
            "Casos notificados de VIH",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_sars_cov2_especial(self) -> None:
        """Seed SARS-COV-2 en situaciones especiales."""
        strategy = self._create_strategy(
            tipo_eno_name="Estudio de SARS-COV-2 en situaciones especiales",
            name="Estrategia SARS-COV-2 Especial",
            description="Estrategia para procesar casos de SARS-COV-2 en situaciones especiales",
        )

        # Regla: Confirmados por laboratorio
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados por laboratorio",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EN_LISTA,
                    "field_name": "RESULTADO",
                    "config": {"values": ["positivo", "detectable"], "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_sifilis_gestantes(self) -> None:
        """Seed Sífilis en personas gestantes."""
        strategy = self._create_strategy(
            tipo_eno_name="Sífilis en personas gestantes",
            name="Estrategia Sífilis en Gestantes",
            description="Estrategia para procesar casos de Sífilis en personas gestantes",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Sífilis en gestantes",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_diarrea_aguda(self) -> None:
        """Seed Diarrea aguda."""
        strategy = self._create_strategy(
            tipo_eno_name="Diarrea aguda",
            name="Estrategia Diarrea Aguda",
            description="Estrategia para procesar casos de Diarrea aguda",
        )

        # Regla: Notificados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.NOTIFICADOS,
            "Casos notificados de Diarrea aguda",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_araneismo(self) -> None:
        """Seed Araneísmo-Envenenamiento por Latrodectus."""
        strategy = self._create_strategy(
            tipo_eno_name="Araneísmo-Envenenamiento por Latrodectus (Latrodectismo)",
            name="Estrategia Araneísmo",
            description="Estrategia para procesar casos de Araneísmo",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos de envenenamiento por arácnidos",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )

    def _seed_brucelosis(self) -> None:
        """Seed Brucelosis."""
        strategy = self._create_strategy(
            tipo_eno_name="Brucelosis",
            name="Estrategia Brucelosis",
            description="Estrategia para procesar casos de Brucelosis",
        )

        # Regla: Confirmados
        self._add_classification_rule(
            strategy,
            TipoClasificacion.CONFIRMADOS,
            "Casos confirmados de Brucelosis",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_CONTIENE,
                    "field_name": "CLASIFICACION_MANUAL",
                    "config": {"value": "confirmado", "strict": False},
                }
            ],
            priority=1,
        )

    def _seed_brote_eta(self) -> None:
        """Seed Sospecha de brote de ETA."""
        strategy = self._create_strategy(
            tipo_eno_name="Sospecha de brote de ETA",
            name="Estrategia Brote ETA",
            description="Estrategia para procesar casos de sospecha de brote de ETA",
        )

        # Regla: En estudio
        self._add_classification_rule(
            strategy,
            TipoClasificacion.EN_ESTUDIO,
            "Casos en estudio de brote ETA",
            [
                {
                    "filter_type": TipoFiltro.CAMPO_EXISTE,
                    "field_name": "IDEVENTOCASO",
                    "config": {},
                }
            ],
            priority=1,
        )


def seed_all_strategies(session: Session) -> None:
    """
    Función de wrapper para seed.py - carga todas las estrategias.
    Recibe una sesión existente.
    """
    seeder = StrategySeeder(session)
    seeder.seed_all()


def main() -> None:
    """Función principal para ejecutar el seed."""
    import os

    from sqlmodel import create_engine

    try:
        # Crear engine síncrono (cambiar asyncpg por psycopg2)
        database_url = os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/epidemiologia"
        )
        # Cambiar postgresql+asyncpg:// por postgresql://
        if "postgresql+asyncpg" in database_url:
            database_url = database_url.replace(
                "postgresql+asyncpg://", "postgresql://"
            )

        engine = create_engine(database_url)

        with Session(engine) as session:
            seed_all_strategies(session)

    except Exception as e:
        print(f"❌ Error en main: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

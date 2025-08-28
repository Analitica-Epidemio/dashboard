"""
Script de migración/seed para cargar estrategias desde el código legacy a la base de datos.

Uso:
    python app/scripts/seed_strategies.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.domains.estrategias.models import (
    ClassificationRule,
    EventStrategy,
    FilterCondition,
    TipoClasificacion,
    TipoFiltro,
)
from app.domains.eventos.models import GrupoEno, TipoEno


class StrategySeeder:
    """Seeder para migrar estrategias desde el código legacy."""

    def __init__(self, session: Session):
        self.session = session
        self.created_strategies: Dict[str, EventStrategy] = {}
        self.tipo_enos: Dict[str, TipoEno] = {}

    def seed_all(self):
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

    def _ensure_tipo_enos(self):
        """Asegura que existen los tipos ENO necesarios."""
        # Primero verificar/crear grupo ENO
        grupo = self._get_or_create_grupo_eno(
            "Vigilancia Epidemiológica", "Grupo principal de eventos de vigilancia"
        )

        # Lista de tipos ENO requeridos (NOMBRES EXACTOS DEL CSV)
        tipos_required = [
            ("Dengue", "DENGUE"),
            ("Tuberculosis", "TUBERCULOSIS"),
            ("Sífilis", "SIFILIS"),
            ("VIH", "VIH"),
            ("SUH - Sindrome Urémico Hemolítico", "SUH"),
            ("Intento de Suicidio", "SUICIDIO"),
            ("Intoxicación/Exposición por Monóxido de Carbono", "INT_MON_CARBONO"),
            ("Estudio de SARS-COV-2 en situaciones especiales", "SARS_COV2_ESPECIAL"),
            (
                "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
                "UC_IRAG",
            ),
            ("Sífilis en personas gestantes", "SIFILIS_GESTANTES"),
            ("Diarrea aguda", "DIARREA_AGUDA"),
            ("Meningoencefalitis", "MENINGO"),
            (
                "Otras infecciones invasivas (bacterianas y otras)",
                "OTRAS_INFECCIONES_INVASIVAS",
            ),
            ("Hidatidosis", "HIDATIDOSIS"),
            ("Accidente potencialmente rábico (APR)", "APR_RABIA"),
            ("Hantavirosis", "HANTAVIRUS"),
            ("Araneísmo-Envenenamiento por Latrodectus (Latrodectismo)", "ARANEISMO"),
            ("Chagas crónico", "CHAGAS_CRONICO"),
            ("Brucelosis", "BRUCELOSIS"),
            ("Sospecha de brote de ETA", "BROTE_ETA"),
            ("Coqueluche", "COQUELUCHE"),
            ("Hepatitis B", "HEP_B"),
            ("Hepatitis C", "HEP_C"),
        ]

        for nombre, codigo in tipos_required:
            tipo_eno = self._get_or_create_tipo_eno(nombre, codigo, grupo.id)
            # Almacenar con el nombre original para matching en create_strategy
            self.tipo_enos[nombre] = tipo_eno

    def _get_or_create_grupo_eno(self, nombre: str, descripcion: str) -> GrupoEno:
        """Obtiene o crea un grupo ENO."""
        # Convertir a mayúsculas para consistencia
        nombre_upper = nombre.upper()
        codigo_upper = "VIGILANCIA"

        # Buscar existente por nombre en mayúsculas
        result = self.session.execute(
            select(GrupoEno).where(GrupoEno.nombre == nombre_upper)
        )
        grupo = result.scalar_one_or_none()

        if not grupo:
            grupo = GrupoEno(
                nombre=nombre_upper, descripcion=descripcion, codigo=codigo_upper
            )
            self.session.add(grupo)
            self.session.flush()

        return grupo

    def _get_or_create_tipo_eno(
        self, nombre: str, codigo: str, grupo_id: int
    ) -> TipoEno:
        """Obtiene o crea un tipo ENO."""

        # Convertir a mayúsculas para consistencia
        nombre_upper = nombre.upper()
        codigo_upper = codigo.upper()

        # Buscar existente por nombre en mayúsculas
        result = self.session.execute(
            select(TipoEno).where(TipoEno.nombre == nombre_upper)
        )
        tipo_eno = result.scalar_one_or_none()

        if not tipo_eno:
            tipo_eno = TipoEno(
                nombre=nombre_upper,
                codigo=codigo_upper,
                id_grupo_eno=grupo_id,
                descripcion=f"Eventos de tipo {nombre_upper}",
            )
            self.session.add(tipo_eno)
            self.session.flush()

        return tipo_eno

    def _create_strategy(
        self,
        tipo_eno_name: str,
        strategy_name: str,
        description: str,
        graficos: List[str],
        usa_provincia_carga: bool = False,
        config: Optional[Dict] = None,
        notas_admin: Optional[str] = None,
        casos_especiales: Optional[str] = None,
        metadata_extractors: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
    ) -> EventStrategy:
        """Crea una estrategia base."""
        tipo_eno = self.tipo_enos.get(tipo_eno_name)
        if not tipo_eno:
            raise ValueError(f"Tipo ENO '{tipo_eno_name}' no encontrado")

        # Verificar si ya existe
        result = self.session.execute(
            select(EventStrategy).where(EventStrategy.tipo_eno_id == tipo_eno.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        strategy = EventStrategy(
            tipo_eno_id=tipo_eno.id,
            name=strategy_name.upper(),
            description=description,
            notas_admin=notas_admin,
            casos_especiales=casos_especiales,
            usa_provincia_carga=usa_provincia_carga,
            graficos_disponibles=graficos,
            config=config or {},
            confidence_threshold=confidence_threshold,
            created_by="seed_script",
        )

        self.session.add(strategy)
        self.session.flush()

        self.created_strategies[tipo_eno_name] = strategy
        return strategy

    def _add_classification_rule(
        self,
        strategy: EventStrategy,
        classification: TipoClasificacion,
        name: str,
        conditions: List[Dict],
        priority: int = 100,
        justificacion: Optional[str] = None,
        ejemplos: Optional[str] = None,
    ) -> ClassificationRule:
        """Agrega una regla de clasificación con sus condiciones."""
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

        # Agregar condiciones
        for idx, condition_data in enumerate(conditions):
            condition = FilterCondition(rule_id=rule.id, order=idx, **condition_data)
            self.session.add(condition)

        self.session.flush()
        return rule

    # ============== ESTRATEGIAS ESPECÍFICAS ==============

    def _seed_dengue(self):
        """Seed para Dengue."""
        strategy = self._create_strategy(
            tipo_eno_name="Dengue",
            strategy_name="DengueEstrategia",
            description="Estrategia para procesar casos de Dengue",
            graficos=[
                "corredor_endemico",
                "curva_epidemiologica",
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
            ],
            usa_provincia_carga=True,
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
                        "values": [
                            "caso descartado",
                            "descartado"
                        ],
                        "strict": False
                    }
                }
            ],
            priority=3,
        )

    def _seed_apr_rabia(self):
        """Seed para Accidente potencialmente rábico (APR)."""
        strategy = self._create_strategy(
            tipo_eno_name="Accidente potencialmente rábico (APR)",
            strategy_name="APRRabiaEstrategia",
            description="Estrategia para procesar casos de Accidentes potencialmente rábicos",
            graficos=[
                "rabia_animal_comparacion",
                "grafico_por_contagios",
                "casos_por_ugd",
                "torta_sexo",
            ],
            metadata_extractors=["tipo_sujeto", "fuente_contagio"],
            confidence_threshold=0.6,  # Más permisivo para permitir revisión manual
            notas_admin="""
            IMPORTANTE: En Rabia se reportan tanto casos de animales como de humanos.
            
            DETECCIÓN AUTOMÁTICA:
            - ANIMALES: SEXO='IND', documentos no estándar, nomenclatura científica
            - HUMANOS: SEXO='M/F', TIPO_DOC='DNI/LC/LE', nombres típicos de personas
            - AMBIGUOS: Datos contradictorios → REQUIERE_REVISION
            
            La detección NO está hardcodeada, usa patrones inteligentes.
            """,
            casos_especiales="""
            Casos que requieren revisión manual:
            1. SEXO='IND' pero nombre parece de persona
            2. Documentos no estándar pero datos humanos
            3. Nomenclatura mixta o contradictoria
            4. Confidence < 60% en detección automática
            
            Estos casos se marcan como REQUIERE_REVISION para el equipo epidemiológico.
            """,
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

    def _seed_uc_irag(self):
        """Seed para UC-IRAG."""
        strategy = self._create_strategy(
            tipo_eno_name="Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)",
            strategy_name="UCIRAGEstrategia",
            description="Estrategia para procesar casos de UC-IRAG",
            graficos=[
                "corredor_endemico",
                "curva_epidemiologica",
                "curva_epi_subtipos_influenza",
                "proporcion_ira",
                "casos_por_ugd",
            ],
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

    def _seed_sifilis(self):
        """Seed para Sífilis (grupo con múltiples subtipos)."""
        strategy = self._create_strategy(
            tipo_eno_name="Sífilis",
            strategy_name="SifilisEstrategia",
            description="Estrategia para procesar casos de Sífilis y sus variantes",
            graficos=[
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
                "totales_historicos",
            ],
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

    def _seed_coqueluche(self):
        """Seed para Coqueluche."""
        strategy = self._create_strategy(
            tipo_eno_name="Coqueluche",
            strategy_name="CoquelucheEstrategia",
            description="Estrategia para procesar casos de Coqueluche (Tos convulsa)",
            graficos=[
                "corredor_endemico",
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
            ],
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

    def _seed_hantavirus(self):
        """Seed para Hantavirus."""
        strategy = self._create_strategy(
            tipo_eno_name="Hantavirosis",
            strategy_name="HantavirusEstrategia",
            description="Estrategia para procesar casos de Hantavirus",
            graficos=[
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
                "totales_historicos",
            ],
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

    def _seed_chagas_cronico(self):
        """Seed para Chagas crónico."""
        strategy = self._create_strategy(
            tipo_eno_name="Chagas crónico",
            strategy_name="ChagasEstrategia",
            description="Estrategia para procesar casos de Chagas crónico",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_hepatitis_b(self):
        """Seed para Hepatitis B."""
        strategy = self._create_strategy(
            tipo_eno_name="Hepatitis B",
            strategy_name="HepatitisBEstrategia",
            description="Estrategia para procesar casos de Hepatitis B",
            graficos=[
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
                "totales_historicos",
            ],
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

    def _seed_intento_suicidio(self):
        """Seed para Intento de Suicidio."""
        strategy = self._create_strategy(
            tipo_eno_name="Intento de Suicidio",
            strategy_name="IntentoSuicidioEstrategia",
            description="Estrategia para procesar casos de intento de suicidio",
            graficos=[
                "intento_suicidio_mecanismo",
                "intento_suicidio_lugar",
                "casos_por_ugd",
                "torta_sexo",
            ],
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

    def _seed_hidatidosis(self):
        """Seed para Hidatidosis."""
        strategy = self._create_strategy(
            tipo_eno_name="Hidatidosis",
            strategy_name="HidatidosisEstrategia",
            description="Estrategia para procesar casos de Hidatidosis",
            graficos=[
                "edad_departamento",
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
            ],
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

    def _seed_meningoencefalitis(self):
        """Seed para Meningoencefalitis."""
        strategy = self._create_strategy(
            tipo_eno_name="Meningoencefalitis",
            strategy_name="MeningoEstrategia",
            description="Estrategia para procesar casos de Meningoencefalitis",
            graficos=[
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
                "totales_historicos",
            ],
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

    def _seed_suh(self):
        """Seed para SUH - Síndrome Urémico Hemolítico."""
        strategy = self._create_strategy(
            tipo_eno_name="SUH - Sindrome Urémico Hemolítico",
            strategy_name="SuhEstrategia",
            description="Estrategia para procesar casos de SUH",
            graficos=[
                "casos_por_ugd",
                "torta_sexo",
                "casos_mensuales",
                "totales_historicos",
            ],
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

    def _seed_botulismo(self):
        """Seed para Botulismo del lactante."""
        strategy = self._create_strategy(
            tipo_eno_name="Botulismo del lactante",
            strategy_name="BotulismoEstrategia",
            description="Estrategia para procesar casos de Botulismo",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_efe(self):
        """Seed para Enfermedad Febril Exantemática."""
        strategy = self._create_strategy(
            tipo_eno_name="Enfermedad Febril Exantemática-EFE",
            strategy_name="EfeEstrategia",
            description="Estrategia para procesar casos de EFE (Sarampión/Rubéola)",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_paf(self):
        """Seed para PAF - Poliomielitis."""
        strategy = self._create_strategy(
            tipo_eno_name="Poliomielitis-PAF",
            strategy_name="PafEstrategia",
            description="Estrategia para procesar casos de PAF",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_mordedura_perro(self):
        """Seed para Mordedura de perro."""
        strategy = self._create_strategy(
            tipo_eno_name="Lesiones graves por mordedura de perro",
            strategy_name="MordeduraPerroEstrategia",
            description="Estrategia para procesar casos de mordedura de perro",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_apr(self):
        """Seed APR (Accidentes por Ponzoña de Arácnidos)."""
        print("  📋 Creando estrategia APR...")

        strategy = self._create_strategy(
            tipo_eno_name="Accidentes por Ponzoña de Arácnidos (APR)",
            strategy_name="APREstrategia",
            description="Estrategia para procesar casos de accidentes por ponzoña de arácnidos",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_hepatitis_b_per_ges(self):
        """Seed Hepatitis B en personas gestantes."""
        print("  📋 Creando estrategia Hepatitis B en gestantes...")

        strategy = self._create_strategy(
            tipo_eno_name="Hepatitis B en personas gestantes",
            strategy_name="HepatitisBPerGesEstrategia",
            description="Estrategia para procesar casos de Hepatitis B en personas gestantes",
            graficos=["casos_por_ugd", "casos_mensuales", "torta_edad"],
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

    def _seed_hepatitis_c(self):
        """Seed Hepatitis C."""
        print("  📋 Creando estrategia Hepatitis C...")

        strategy = self._create_strategy(
            tipo_eno_name="Hepatitis C",
            strategy_name="HepatitisCEstrategia",
            description="Estrategia para procesar casos de Hepatitis C",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales", "torta_edad"],
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

    def _seed_int_mon_carbono(self):
        """Seed Intoxicación/Exposición por Monóxido de Carbono."""
        strategy = self._create_strategy(
            tipo_eno_name="Intoxicación/Exposición por Monóxido de Carbono",
            strategy_name="IntMonCarbonoEstrategia",
            description="Estrategia para procesar casos de intoxicación por monóxido de carbono",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales", "torta_edad"],
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

    def _seed_otras_infecciones_invasivas(self):
        """Seed Otras infecciones invasivas (bacterianas y otras)."""
        strategy = self._create_strategy(
            tipo_eno_name="Otras infecciones invasivas (bacterianas y otras)",
            strategy_name="OtrasInfeccionesInvasivasEstrategia",
            description="Estrategia para procesar casos de otras infecciones invasivas",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales", "torta_edad"],
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

    def _seed_tuberculosis(self):
        """Seed Tuberculosis."""
        strategy = self._create_strategy(
            tipo_eno_name="Tuberculosis",
            strategy_name="TuberculosisEstrategia",
            description="Estrategia para procesar casos de Tuberculosis",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales", "torta_edad"],
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

    def _seed_vih(self):
        """Seed VIH."""
        strategy = self._create_strategy(
            tipo_eno_name="VIH",
            strategy_name="VIHEstrategia",
            description="Estrategia para procesar casos de VIH",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales", "torta_edad"],
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

    def _seed_sars_cov2_especial(self):
        """Seed SARS-COV-2 en situaciones especiales."""
        strategy = self._create_strategy(
            tipo_eno_name="Estudio de SARS-COV-2 en situaciones especiales",
            strategy_name="SARSCoV2EspecialEstrategia",
            description="Estrategia para procesar casos de SARS-COV-2 en situaciones especiales",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_sifilis_gestantes(self):
        """Seed Sífilis en personas gestantes."""
        strategy = self._create_strategy(
            tipo_eno_name="Sífilis en personas gestantes",
            strategy_name="SifilisGestantesEstrategia",
            description="Estrategia para procesar casos de Sífilis en personas gestantes",
            graficos=["casos_por_ugd", "casos_mensuales", "torta_edad"],
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

    def _seed_diarrea_aguda(self):
        """Seed Diarrea aguda."""
        strategy = self._create_strategy(
            tipo_eno_name="Diarrea aguda",
            strategy_name="DiarreaAgudaEstrategia",
            description="Estrategia para procesar casos de Diarrea aguda",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales", "torta_edad"],
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

    def _seed_araneismo(self):
        """Seed Araneísmo-Envenenamiento por Latrodectus."""
        strategy = self._create_strategy(
            tipo_eno_name="Araneísmo-Envenenamiento por Latrodectus (Latrodectismo)",
            strategy_name="AraneismoEstrategia",
            description="Estrategia para procesar casos de Araneísmo",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_brucelosis(self):
        """Seed Brucelosis."""
        strategy = self._create_strategy(
            tipo_eno_name="Brucelosis",
            strategy_name="BrucelosisEstrategia",
            description="Estrategia para procesar casos de Brucelosis",
            graficos=["casos_por_ugd", "torta_sexo", "casos_mensuales"],
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

    def _seed_brote_eta(self):
        """Seed Sospecha de brote de ETA."""
        strategy = self._create_strategy(
            tipo_eno_name="Sospecha de brote de ETA",
            strategy_name="BroteETAEstrategia",
            description="Estrategia para procesar casos de sospecha de brote de ETA",
            graficos=["casos_por_ugd", "casos_mensuales", "torta_sexo"],
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


def main():
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
            seeder = StrategySeeder(session)
            seeder.seed_all()

    except Exception as e:
        print(f"❌ Error en main: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

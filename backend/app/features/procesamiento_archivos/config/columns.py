"""
Sistema centralizado de columnas epidemiológicas con tipos EXPLÍCITOS.

Sincronizado con frontend/src/app/inicio/constants.ts para mantener consistencia.
Cada columna se define UNA SOLA VEZ con nombre + tipo + si es requerida.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

# === TIPOS DE DATOS ===

class ColumnType(Enum):
    """Tipos de datos para columnas epidemiológicas."""
    TEXT = "text"
    NUMERIC = "numeric"  # Usará Int64 (nullable integer) en pandas
    DATE = "date"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"


@dataclass(frozen=True)
class Column:
    """
    Definición de una columna epidemiológica.

    Uso:
        df[Columns.IDEVENTOCASO.name]  # ✅ SIEMPRE usar .name para acceder a DataFrame
        Columns.IDEVENTOCASO.type      # ✅ Obtener tipo
        Columns.IDEVENTOCASO.required  # ✅ Saber si es requerida
    """
    name: str
    type: ColumnType
    required: bool = False


# === DEFINICIÓN ÚNICA DE COLUMNAS ===
# FUENTE ÚNICA DE VERDAD - Todo se deriva de esta clase

class Columns:
    """
    Definición completa de columnas epidemiológicas.

    Cada atributo es un objeto Column con:
    - name: nombre de la columna en CSV/DataFrame
    - type: tipo de dato (NUMERIC, DATE, TEXT, BOOLEAN, CATEGORICAL)
    - required: si es columna crítica

    Uso:
        Columns.IDEVENTOCASO.name  # → "IDEVENTOCASO"
        Columns.IDEVENTOCASO.type  # → ColumnType.NUMERIC
        Columns.IDEVENTOCASO.required  # → True

        # O simplemente como string:
        df[Columns.IDEVENTOCASO]  # → df["IDEVENTOCASO"]
    """

    # === IDs y códigos críticos ===
    IDEVENTOCASO = Column("IDEVENTOCASO", ColumnType.NUMERIC, required=True)
    ID_SNVS_EVENTO = Column("ID_SNVS_EVENTO", ColumnType.NUMERIC)
    CODIGO_CIUDADANO = Column("CODIGO_CIUDADANO", ColumnType.NUMERIC, required=True)
    NRO_DOC = Column("NRO_DOC", ColumnType.NUMERIC)

    # === Identificadores SNVS ===
    ID_SNVS_MUESTRA = Column("ID_SNVS_MUESTRA", ColumnType.NUMERIC)
    ID_SNVS_EVENTO_MUESTRA = Column("ID_SNVS_EVENTO_MUESTRA", ColumnType.NUMERIC)
    ID_SNVS_PRUEBA_MUESTRA = Column("ID_SNVS_PRUEBA_MUESTRA", ColumnType.NUMERIC)
    ID_SNVS_RESULTADO = Column("ID_SNVS_RESULTADO", ColumnType.NUMERIC)
    ID_SNVS_PRUEBA = Column("ID_SNVS_PRUEBA", ColumnType.NUMERIC)
    ID_SNVS_TIPO_PRUEBA = Column("ID_SNVS_TIPO_PRUEBA", ColumnType.NUMERIC)
    ID_SNVS_INTERPRET_USR = Column("ID_SNVS_INTERPRET_USR", ColumnType.NUMERIC)
    ID_SNVS_VIAJE_EPIDEMIO = Column("ID_SNVS_VIAJE_EPIDEMIO", ColumnType.NUMERIC)
    ID_SNVS_SIGNO_SINTOMA = Column("ID_SNVS_SIGNO_SINTOMA", ColumnType.NUMERIC)
    ID_SNVS_ANTECEDENTE_EPIDEMIO = Column("ID_SNVS_ANTECEDENTE_EPIDEMIO", ColumnType.NUMERIC)
    ID_SNVS_VACUNA = Column("ID_SNVS_VACUNA", ColumnType.NUMERIC)

    # === Clasificación (crítico) ===
    EVENTO = Column("EVENTO", ColumnType.CATEGORICAL, required=True)
    GRUPO_EVENTO = Column("GRUPO_EVENTO", ColumnType.CATEGORICAL)
    TIPO_EVENTO = Column("TIPO_EVENTO", ColumnType.CATEGORICAL)
    CLASIFICACION_MANUAL = Column("CLASIFICACION_MANUAL", ColumnType.CATEGORICAL, required=True)
    CLASIFICACION_AUTOMATICA = Column("CLASIFICACION_AUTOMATICA", ColumnType.CATEGORICAL)
    CLASIFICACION_ALGORITMO = Column("CLASIFICACION_ALGORITMO", ColumnType.CATEGORICAL)
    USER_CENTINELA = Column("USER_CENTINELA", ColumnType.TEXT)
    EVENTO_CENTINELA = Column("EVENTO_CENTINELA", ColumnType.BOOLEAN)

    # === Datos personales ===
    NOMBRE = Column("NOMBRE", ColumnType.TEXT)
    APELLIDO = Column("APELLIDO", ColumnType.TEXT)
    SEXO = Column("SEXO", ColumnType.CATEGORICAL)
    GENERO = Column("GENERO", ColumnType.CATEGORICAL)
    SEXO_AL_NACER = Column("SEXO_AL_NACER", ColumnType.CATEGORICAL)
    TIPO_DOC = Column("TIPO_DOC", ColumnType.CATEGORICAL)
    FECHA_NACIMIENTO = Column("FECHA_NACIMIENTO", ColumnType.DATE)

    # === Edades ===
    EDAD_ACTUAL = Column("EDAD_ACTUAL", ColumnType.NUMERIC)
    EDAD_DIAGNOSTICO = Column("EDAD_DIAGNOSTICO", ColumnType.NUMERIC)
    EDAD_APERTURA = Column("EDAD_APERTURA", ColumnType.NUMERIC)
    GRUPO_ETARIO = Column("GRUPO_ETARIO", ColumnType.CATEGORICAL)

    # === Fechas críticas ===
    FECHA_APERTURA = Column("FECHA_APERTURA", ColumnType.DATE, required=True)
    FECHA_CONSULTA = Column("FECHA_CONSULTA", ColumnType.DATE)
    FIS = Column("FIS", ColumnType.DATE)  # Fecha Inicio Síntomas

    # === Semanas/Años epidemiológicos ===
    SEPI_APERTURA = Column("SEPI_APERTURA", ColumnType.NUMERIC)
    SEPI_SINTOMA = Column("SEPI_SINTOMA", ColumnType.NUMERIC)
    SEPI_CONSULTA = Column("SEPI_CONSULTA", ColumnType.NUMERIC)
    SEPI_MUESTRA = Column("SEPI_MUESTRA", ColumnType.NUMERIC)
    ANIO_EPI_APERTURA = Column("ANIO_EPI_APERTURA", ColumnType.NUMERIC)
    ANIO_EPI_SINTOMA = Column("ANIO_EPI_SINTOMA", ColumnType.NUMERIC)
    ANIO_EPI_CONSULTA = Column("ANIO_EPI_CONSULTA", ColumnType.NUMERIC)
    ANIO_EPI_MUESTRA = Column("ANIO_EPI_MUESTRA", ColumnType.NUMERIC)
    SEM_MIN = Column("SEM_MIN", ColumnType.NUMERIC)
    AÑO_MIN = Column("AÑO_MIN", ColumnType.NUMERIC)

    # === Ubicación residencia ===
    IDPAISRESIDENCIA = Column("IDPAISRESIDENCIA", ColumnType.NUMERIC)
    PAIS_RESIDENCIA = Column("PAIS_RESIDENCIA", ColumnType.TEXT)
    ID_PROV_INDEC_RESIDENCIA = Column("ID_PROV_INDEC_RESIDENCIA", ColumnType.NUMERIC)
    ID_PROVINCIA_RESIDENCIA = Column("ID_PROVINCIA_RESIDENCIA", ColumnType.NUMERIC)
    PROVINCIA_RESIDENCIA = Column("PROVINCIA_RESIDENCIA", ColumnType.TEXT)
    ID_DEPTO_INDEC_RESIDENCIA = Column("ID_DEPTO_INDEC_RESIDENCIA", ColumnType.NUMERIC)
    DEPARTAMENTO_RESIDENCIA = Column("DEPARTAMENTO_RESIDENCIA", ColumnType.TEXT)
    ID_LOC_INDEC_RESIDENCIA = Column("ID_LOC_INDEC_RESIDENCIA", ColumnType.NUMERIC)
    LOCALIDAD_RESIDENCIA = Column("LOCALIDAD_RESIDENCIA", ColumnType.TEXT)
    CALLE_DOMICILIO = Column("CALLE_DOMICILIO", ColumnType.TEXT)
    NUMERO_DOMICILIO = Column("NUMERO_DOMICILIO", ColumnType.TEXT)  # TEXT porque puede tener "S/N", "123 A", etc

    # === Ubicación intervención ===
    PROVINCIA_INTERVIENEN = Column("PROVINCIA_INTERVIENEN", ColumnType.TEXT)
    REGION_SANITARIA_INTERVIENEN = Column("REGION_SANITARIA_INTERVIENEN", ColumnType.TEXT)
    DEPARTAMENTO_INTERVIENEN = Column("DEPARTAMENTO_INTERVIENEN", ColumnType.TEXT)
    LOCALIDAD_INTERVIENEN = Column("LOCALIDAD_INTERVIENEN", ColumnType.TEXT)
    ESTABLECIMIENTOS_INTERVIENEN = Column("ESTABLECIMIENTOS_INTERVIENEN", ColumnType.TEXT)

    # === Ámbitos y lugares de ocurrencia ===
    TIPO_LUGAR_OCURRENCIA = Column("TIPO_LUGAR_OCURRENCIA", ColumnType.TEXT)
    NOMBRE_LUGAR_OCURRENCIA = Column("NOMBRE_LUGAR_OCURRENCIA", ColumnType.TEXT)
    LOCALIDAD_AMBITO_OCURRENCIA = Column("LOCALIDAD_AMBITO_OCURRENCIA", ColumnType.TEXT)
    SITIO_PROBABLE_ADQUISICION = Column("SITIO_PROBABLE_ADQUISICION", ColumnType.TEXT)
    SITIO_PROBABLE_DISEMINACION = Column("SITIO_PROBABLE_DISEMINACION", ColumnType.TEXT)
    FRECUENCIA = Column("FRECUENCIA", ColumnType.TEXT)
    FECHA_AMBITO_OCURRENCIA = Column("FECHA_AMBITO_OCURRENCIA", ColumnType.DATE)

    # === Ubicación clínica ===
    ID_PROV_INDEC_CLINICA = Column("ID_PROV_INDEC_CLINICA", ColumnType.NUMERIC)
    ID_PROVINCIA_CLINICA = Column("ID_PROVINCIA_CLINICA", ColumnType.NUMERIC)
    PROV_CLINICA = Column("PROV_CLINICA", ColumnType.TEXT)
    ID_DEPTO_INDEC_CLINICA = Column("ID_DEPTO_INDEC_CLINICA", ColumnType.NUMERIC)
    DEPTO_CLINICA = Column("DEPTO_CLINICA", ColumnType.TEXT)
    ID_LOC_INDEC_CLINICA = Column("ID_LOC_INDEC_CLINICA", ColumnType.NUMERIC)
    LOCA_CLINICA = Column("LOCA_CLINICA", ColumnType.TEXT)
    ID_ESTAB_CLINICA = Column("ID_ESTAB_CLINICA", ColumnType.NUMERIC)
    ESTAB_CLINICA = Column("ESTAB_CLINICA", ColumnType.TEXT)
    REGION_SANITARIA_CLINICA = Column("REGION_SANITARIA_CLINICA", ColumnType.TEXT)

    # === Estado clínico ===
    SINTOMATICO = Column("SINTOMATICO", ColumnType.BOOLEAN)
    EMBARAZADA = Column("EMBARAZADA", ColumnType.BOOLEAN)
    INTERNADO = Column("INTERNADO", ColumnType.BOOLEAN)
    CURADO = Column("CURADO", ColumnType.BOOLEAN)
    FALLECIDO = Column("FALLECIDO", ColumnType.BOOLEAN)
    CUIDADO_INTENSIVO = Column("CUIDADO_INTENSIVO", ColumnType.BOOLEAN)
    FECHA_INTERNACION = Column("FECHA_INTERNACION", ColumnType.DATE)
    FECHA_CUI_INTENSIVOS = Column("FECHA_CUI_INTENSIVOS", ColumnType.DATE)
    FECHA_ALTA_MEDICA = Column("FECHA_ALTA_MEDICA", ColumnType.DATE)
    FECHA_FALLECIMIENTO = Column("FECHA_FALLECIMIENTO", ColumnType.DATE)
    ESTABLECIMIENTO_INTERNACION = Column("ESTABLECIMIENTO_INTERNACION", ColumnType.TEXT)

    # === Muestras ===
    MUESTRA = Column("MUESTRA", ColumnType.CATEGORICAL)
    FTM = Column("FTM", ColumnType.DATE)  # Fecha Toma Muestra
    ID_ESTABLECIMIENTO_MUESTRA = Column("ID_ESTABLECIMIENTO_MUESTRA", ColumnType.NUMERIC)
    ESTABLECIMIENTO_MUESTRA = Column("ESTABLECIMIENTO_MUESTRA", ColumnType.TEXT)
    ID_PROV_INDEC_MUESTRA = Column("ID_PROV_INDEC_MUESTRA", ColumnType.NUMERIC)
    ID_PROVINCIA_MUESTRA = Column("ID_PROVINCIA_MUESTRA", ColumnType.NUMERIC)
    PROVINCIA_MUESTRA = Column("PROVINCIA_MUESTRA", ColumnType.TEXT)
    ID_DEPTO_INDEC_MUESTRA = Column("ID_DEPTO_INDEC_MUESTRA", ColumnType.NUMERIC)
    DEPARTAMENTO_MUESTRA = Column("DEPARTAMENTO_MUESTRA", ColumnType.TEXT)
    ID_LOC_INDEC_MUESTRA = Column("ID_LOC_INDEC_MUESTRA", ColumnType.NUMERIC)
    LOCALIDAD_MUESTRA = Column("LOCALIDAD_MUESTRA", ColumnType.TEXT)
    REGION_SANITARIA_MUESTRA = Column("REGION_SANITARIA_MUESTRA", ColumnType.TEXT)
    FECHA_PAPEL = Column("FECHA_PAPEL", ColumnType.DATE)

    # === Estudios/Diagnóstico ===
    FECHA_ESTUDIO = Column("FECHA_ESTUDIO", ColumnType.DATE)
    DETERMINACION = Column("DETERMINACION", ColumnType.CATEGORICAL)
    TECNICA = Column("TECNICA", ColumnType.CATEGORICAL)
    RESULTADO = Column("RESULTADO", ColumnType.CATEGORICAL)
    FECHA_RECEPCION = Column("FECHA_RECEPCION", ColumnType.DATE)
    ID_ESTABLECIMIENTO_DIAG = Column("ID_ESTABLECIMIENTO_DIAG", ColumnType.NUMERIC)
    ESTABLECIMIENTO_DIAG = Column("ESTABLECIMIENTO_DIAG", ColumnType.TEXT)
    ID_PROV_INDEC_DIAG = Column("ID_PROV_INDEC_DIAG", ColumnType.NUMERIC)
    PROVINCIA_DIAG = Column("PROVINCIA_DIAG", ColumnType.TEXT)
    ID_DEPTO_INDEC_DIAG = Column("ID_DEPTO_INDEC_DIAG", ColumnType.NUMERIC)
    DEPARTAMENTO_DIAG = Column("DEPARTAMENTO_DIAG", ColumnType.TEXT)
    ID_LOC_INDEC_DIAG = Column("ID_LOC_INDEC_DIAG", ColumnType.NUMERIC)
    LOCALIDAD_DIAG = Column("LOCALIDAD_DIAG", ColumnType.TEXT)
    DIAGNOSTICO = Column("DIAGNOSTICO", ColumnType.TEXT)
    DIAG_REFERIDO = Column("DIAG_REFERIDO", ColumnType.TEXT)
    FECHA_DIAG_REFERIDO = Column("FECHA_DIAG_REFERIDO", ColumnType.DATE)

    # === Establecimiento Epidemiología ===
    ESTABLECIMIENTO_EPI = Column("ESTABLECIMIENTO_EPI", ColumnType.TEXT)
    ID_PROV_INDEC_EPI = Column("ID_PROV_INDEC_EPI", ColumnType.NUMERIC)
    PROVINCIA_EPI = Column("PROVINCIA_EPI", ColumnType.TEXT)
    ID_DEPTO_INDEC_EPI = Column("ID_DEPTO_INDEC_EPI", ColumnType.NUMERIC)
    DEPARTAMENTO_EPI = Column("DEPARTAMENTO_EPI", ColumnType.TEXT)
    ID_LOC_INDEC_EPI = Column("ID_LOC_INDEC_EPI", ColumnType.NUMERIC)
    LOCALIDAD_EPI = Column("LOCALIDAD_EPI", ColumnType.TEXT)
    ID_ORIGEN = Column("ID_ORIGEN", ColumnType.NUMERIC)  # ID del establecimiento de epidemiología/origen

    # === Establecimiento Carga ===
    ESTABLECIMIENTO_CARGA = Column("ESTABLECIMIENTO_CARGA", ColumnType.TEXT)
    ID_ESTABLECIMIENTO_CARGA = Column("ID_ESTABLECIMIENTO_CARGA", ColumnType.NUMERIC)
    ID_PROV_INDEC_CARGA = Column("ID_PROV_INDEC_CARGA", ColumnType.NUMERIC)
    ID_DEPTO_INDEC_CARGA = Column("ID_DEPTO_INDEC_CARGA", ColumnType.NUMERIC)
    DEPARTAMENTO_CARGA = Column("DEPARTAMENTO_CARGA", ColumnType.TEXT)
    ID_LOC_INDEC_CARGA = Column("ID_LOC_INDEC_CARGA", ColumnType.NUMERIC)
    LOCALIDAD_CARGA = Column("LOCALIDAD_CARGA", ColumnType.TEXT)

    # === Viajes ===
    FECHA_INICIO_VIAJE = Column("FECHA_INICIO_VIAJE", ColumnType.DATE)
    FECHA_FIN_VIAJE = Column("FECHA_FIN_VIAJE", ColumnType.DATE)
    ID_PAIS_VIAJE = Column("ID_PAIS_VIAJE", ColumnType.NUMERIC)
    ID_PROV_INDEC_VIAJE = Column("ID_PROV_INDEC_VIAJE", ColumnType.NUMERIC)
    ID_PROVINCIA_VIAJE = Column("ID_PROVINCIA_VIAJE", ColumnType.NUMERIC)
    PROV_VIAJE = Column("PROV_VIAJE", ColumnType.TEXT)
    PAIS_VIAJE = Column("PAIS_VIAJE", ColumnType.TEXT)
    ID_LOC_INDEC_VIAJE = Column("ID_LOC_INDEC_VIAJE", ColumnType.NUMERIC)
    LOC_VIAJE = Column("LOC_VIAJE", ColumnType.TEXT)

    # === Investigación ===
    INVESTIGACION = Column("INVESTIGACION", ColumnType.BOOLEAN)
    INVESTIGACION_TERRENO = Column("INVESTIGACION_TERRENO", ColumnType.BOOLEAN)
    FECHA_INVESTIGACION = Column("FECHA_INVESTIGACION", ColumnType.DATE)
    TIPO_Y_LUGAR_INVESTIGACION = Column("TIPO_Y_LUGAR_INVESTIGACION", ColumnType.TEXT)
    CONTACTO_CON_CONFIR = Column("CONTACTO_CON_CONFIR", ColumnType.BOOLEAN)
    CONTACTO_CON_SOSPECHOSO = Column("CONTACTO_CON_SOSPECHOSO", ColumnType.BOOLEAN)
    CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS = Column("CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS", ColumnType.NUMERIC)
    CONTACTOS_MENORES_1 = Column("CONTACTOS_MENORES_1", ColumnType.NUMERIC)
    CONTACTO_EMBARAZADAS = Column("CONTACTO_EMBARAZADAS", ColumnType.NUMERIC)
    CONTACTOS_VACUNADOS = Column("CONTACTOS_VACUNADOS", ColumnType.NUMERIC)

    # === Vacunas, síntomas, tratamientos ===
    VACUNA = Column("VACUNA", ColumnType.TEXT)
    FECHA_APLICACION = Column("FECHA_APLICACION", ColumnType.DATE)
    DOSIS = Column("DOSIS", ColumnType.NUMERIC)
    SIGNO_SINTOMA = Column("SIGNO_SINTOMA", ColumnType.TEXT)  # Alias de SINTOMA
    SINTOMA = Column("SINTOMA", ColumnType.TEXT)
    FECHA_INICIO_SINTOMA = Column("FECHA_INICIO_SINTOMA", ColumnType.DATE)
    TRATAMIENTO = Column("TRATAMIENTO", ColumnType.TEXT)
    TRATAMIENTO_2 = Column("TRATAMIENTO_2", ColumnType.TEXT)
    ESTAB_TTO = Column("ESTAB_TTO", ColumnType.TEXT)
    FECHA_INICIO_TRAT = Column("FECHA_INICIO_TRAT", ColumnType.DATE)
    FECHA_FIN_TRAT = Column("FECHA_FIN_TRAT", ColumnType.DATE)
    RESULTADO_TRATAMIENTO = Column("RESULTADO_TRATAMIENTO", ColumnType.TEXT)
    ANTECEDENTE = Column("ANTECEDENTE", ColumnType.TEXT)
    ANTECEDENTE_EPIDEMIOLOGICO = Column("ANTECEDENTE_EPIDEMIOLOGICO", ColumnType.TEXT)
    FECHA_ANTECEDENTE_EPI = Column("FECHA_ANTECEDENTE_EPI", ColumnType.DATE)

    # === Otros campos ===
    OBSERVACIONES = Column("OBSERVACIONES", ColumnType.TEXT)
    COMORBILIDAD = Column("COMORBILIDAD", ColumnType.TEXT)
    ID_PROVINCIA_CARGA = Column("ID_PROVINCIA_CARGA", ColumnType.NUMERIC)
    PROVINCIA_CARGA = Column("PROVINCIA_CARGA", ColumnType.TEXT)
    REGION_SANITARIA_CARGA = Column("REGION_SANITARIA_CARGA", ColumnType.TEXT)
    OCUPACION = Column("OCUPACION", ColumnType.TEXT)
    VALIDACION = Column("VALIDACION", ColumnType.TEXT)
    INFO_CONTACTO = Column("INFO_CONTACTO", ColumnType.TEXT)
    COBERTURA_SOCIAL = Column("COBERTURA_SOCIAL", ColumnType.TEXT)
    VALOR = Column("VALOR", ColumnType.NUMERIC)
    ORIGEN_FINANCIAMIENTO = Column("ORIGEN_FINANCIAMIENTO", ColumnType.TEXT)
    PUEBLO_INDIGENA = Column("PUEBLO_INDIGENA", ColumnType.BOOLEAN)
    SE_DECLARA_PUEBLO_INDIGENA = Column("SE_DECLARA_PUEBLO_INDIGENA", ColumnType.BOOLEAN)
    ETNIA = Column("ETNIA", ColumnType.TEXT)
    BARRIO_POPULAR = Column("BARRIO_POPULAR", ColumnType.BOOLEAN)
    CENTINELA = Column("CENTINELA", ColumnType.BOOLEAN)
    ID_USER_REGISTRO = Column("ID_USER_REGISTRO", ColumnType.NUMERIC)
    USER_CENT_PARTICIPO = Column("USER_CENT_PARTICIPO", ColumnType.TEXT)
    ID_USER_CENT_PARTICIPO = Column("ID_USER_CENT_PARTICIPO", ColumnType.NUMERIC)


# === FUNCIONES DE UTILIDAD (derivadas automáticamente) ===

def _get_all_columns() -> List[Column]:
    """Obtiene todas las columnas definidas en la clase Columns."""
    return [
        getattr(Columns, attr)
        for attr in dir(Columns)
        if not attr.startswith('_') and isinstance(getattr(Columns, attr), Column)
    ]


def get_column_names() -> List[str]:
    """Retorna lista de nombres de todas las columnas."""
    return [col.name for col in _get_all_columns()]


def get_required_columns() -> List[str]:
    """Retorna lista de nombres de columnas requeridas."""
    return [col.name for col in _get_all_columns() if col.required]


def get_columns_by_type(column_type: ColumnType) -> List[str]:
    """Retorna nombres de columnas por tipo."""
    return [col.name for col in _get_all_columns() if col.type == column_type]


def validate_dataframe(df) -> dict:
    """
    Valida que el DataFrame tenga las columnas requeridas.

    Returns:
        Dict con:
        - is_valid: bool
        - missing_required: list de columnas requeridas faltantes
        - matched_columns: int cantidad de columnas mapeadas presentes
        - coverage_percentage: float porcentaje de cobertura
    """
    df_columns = set(df.columns)
    required = set(get_required_columns())
    all_mapped = set(get_column_names())

    missing_required = list(required - df_columns)
    matched = len(df_columns & all_mapped)
    coverage = (matched / len(df_columns) * 100) if df_columns else 0

    return {
        "is_valid": len(missing_required) == 0,
        "missing_required": missing_required,
        "matched_columns": matched,
        "coverage_percentage": coverage,
    }


# === CONSTANTES DE COMPATIBILIDAD (para código existente) ===

ALL_COLUMNS = get_column_names()
REQUIRED_COLUMNS = get_required_columns()
DATE_COLUMNS = get_columns_by_type(ColumnType.DATE)
NUMERIC_COLUMNS = get_columns_by_type(ColumnType.NUMERIC)
BOOLEAN_COLUMNS = get_columns_by_type(ColumnType.BOOLEAN)
CATEGORICAL_COLUMNS = get_columns_by_type(ColumnType.CATEGORICAL)
TEXT_COLUMNS = get_columns_by_type(ColumnType.TEXT)

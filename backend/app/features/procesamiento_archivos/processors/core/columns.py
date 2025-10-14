"""
Sistema centralizado de columnas epidemiológicas con chequeo en tiempo de compilación.

Sincronizado con frontend/src/app/inicio/constants.ts para mantener consistencia.
Provee acceso seguro a columnas con validación y debugging mejorado.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Literal

import pandas as pd

# === DEFINICIÓN COMPLETA DE COLUMNAS (Sincronizado con frontend) ===

# Columnas exactas del frontend constants.ts
ALL_COLUMNS = [
    "CODIGO_CIUDADANO",
    "IDEVENTOCASO",
    "EVENTO",
    "NOMBRE",
    "APELLIDO",
    "SEXO",
    "TIPO_DOC",
    "NRO_DOC",
    "FECHA_NACIMIENTO",
    "EDAD_ACTUAL",
    "EDAD_DIAGNOSTICO",
    "GRUPO_ETARIO",
    "SEPI_APERTURA",
    "SEPI_SINTOMA",
    "SEPI_CONSULTA",
    "SEPI_MUESTRA",
    "IDPAISRESIDENCIA",
    "PAIS_RESIDENCIA",
    "ID_PROV_INDEC_RESIDENCIA",
    "PROVINCIA_RESIDENCIA",
    "ID_DEPTO_INDEC_RESIDENCIA",
    "DEPARTAMENTO_RESIDENCIA",
    "ID_LOC_INDEC_RESIDENCIA",
    "LOCALIDAD_RESIDENCIA",
    "CALLE_DOMICILIO",
    "NUMERO_DOMICILIO",
    "CLASIFICACION_MANUAL",
    "CLASIFICACION_AUTOMATICA",
    "FECHA_APERTURA",
    "PROVINCIA_INTERVIENEN",
    "REGION_SANITARIA_INTERVIENEN",
    "DEPARTAMENTO_INTERVIENEN",
    "LOCALIDAD_INTERVIENEN",
    "ESTABLECIMIENTOS_INTERVIENEN",
    "FECHA_CONSULTA",
    "ID_PROV_INDEC_CLINICA",
    "PROV_CLINICA",
    "ID_DEPTO_INDEC_CLINICA",
    "DEPTO_CLINICA",
    "ID_LOC_INDEC_CLINICA",
    "LOCA_CLINICA",
    "ID_ESTAB_CLINICA",
    "ESTAB_CLINICA",
    "SINTOMATICO",
    "FIS",
    "EMBARAZADA",
    "INTERNADO",
    "CURADO",
    "FECHA_INTERNACION",
    "CUIDADO_INTENSIVO",
    "FECHA_CUI_INTENSIVOS",
    "FECHA_ALTA_MEDICA",
    "FALLECIDO",
    "FECHA_FALLECIMIENTO",
    "MUESTRA",
    "ID_SNVS_EVENTO_MUESTRA",
    "FTM",
    "ID_ESTABLECIMIENTO_MUESTRA",
    "ESTABLECIMIENTO_MUESTRA",
    "ID_PROV_INDEC_MUESTRA",
    "PROVINCIA_MUESTRA",
    "ID_DEPTO_INDEC_MUESTRA",
    "DEPARTAMENTO_MUESTRA",
    "ID_LOC_INDEC_MUESTRA",
    "LOCALIDAD_MUESTRA",
    "ID_SNVS_PRUEBA_MUESTRA",
    "FECHA_ESTUDIO",
    "DETERMINACION",
    "TECNICA",
    "RESULTADO",
    "FECHA_RECEPCION",
    "ID_ESTABLECIMIENTO_DIAG",
    "ESTABLECIMIENTO_DIAG",
    "ID_PROV_INDEC_DIAG",
    "PROVINCIA_DIAG",
    "ID_DEPTO_INDEC_DIAG",
    "DEPARTAMENTO_DIAG",
    "ID_LOC_INDEC_DIAG",
    "LOCALIDAD_DIAG",
    "ID_SNVS_VIAJE_EPIDEMIO",
    "FECHA_INICIO_VIAJE",
    "FECHA_FIN_VIAJE",
    "ID_PAIS_VIAJE",
    "PAIS_VIAJE",
    "ID_PROV_INDEC_VIAJE",
    "PROV_VIAJE",
    "ID_LOC_INDEC_VIAJE",
    "LOC_VIAJE",
    "ID_SNVS_ANTECEDENTE_EPIDEMIO",
    "ANTECEDENTE_EPIDEMIOLOGICO",
    "ID_SNVS_VACUNA",
    "VACUNA",
    "DOSIS",
    "FECHA_APLICACION",
    "FECHA_INICIO_SINTOMA",
    "ID_SNVS_SIGNO_SINTOMA",
    "SIGNO_SINTOMA",
    "ESTAB_TTO",
    "TRATAMIENTO_2",
    "FECHA_INICIO_TRAT",
    "FECHA_FIN_TRAT",
    "RESULTADO_TRATAMIENTO",
    "GRUPO_EVENTO",
    "ID_ORIGEN",
    "ESTABLECIMIENTO_EPI",
    "ID_PROV_INDEC_EPI",
    "PROVINCIA_EPI",
    "ID_DEPTO_INDEC_EPI",
    "DEPARTAMENTO_EPI",
    "ID_LOC_INDEC_EPI",
    "LOCALIDAD_EPI",
    "ID_ESTABLECIMIENTO_CARGA",
    "ESTABLECIMIENTO_CARGA",
    "ID_PROV_INDEC_CARGA",
    "PROVINCIA_CARGA",
    "ID_DEPTO_INDEC_CARGA",
    "DEPARTAMENTO_CARGA",
    "ID_LOC_INDEC_CARGA",
    "LOCALIDAD_CARGA",
    "ID_SNVS_EVENTO",
    "USER_CENTINELA",
    "EVENTO_CENTINELA",
    "ID_USER_REGISTRO",
    "USER_CENT_PARTICIPO",
    "ID_USER_CENT_PARTICIPO",
    "TIPO_LUGAR_OCURRENCIA",
    "NOMBRE_LUGAR_OCURRENCIA",
    "LOCALIDAD_AMBITO_OCURRENCIA",
    "SITIO_PROBABLE_ADQUISICION",
    "SITIO_PROBABLE_DISEMINACION",
    "FRECUENCIA",
    "FECHA_AMBITO_OCURRENCIA",
    "FECHA_ANTECEDENTE_EPI",
    "INVESTIGACION_TERRENO",
    "FECHA_INVESTIGACION",
    "TIPO_Y_LUGAR_INVESTIGACION",
    "CONTACTO_CON_CONFIR",
    "CONTACTO_CON_SOSPECHOSO",
    "CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS",
    "CONTACTOS_MENORES_1",
    "CONTACTO_EMBARAZADAS",
    "CONTACTOS_VACUNADOS",
    "OBSERVACIONES",
    "COMORBILIDAD",
    "DIAG_REFERIDO",
    "FECHA_DIAG_REFERIDO",
    "REGION_SANITARIA_MUESTRA",
    "REGION_SANITARIA_CLINICA",
    "REGION_SANITARIA_CARGA",
    "ANIO_EPI_APERTURA",
    "ANIO_EPI_SINTOMA",
    "ANIO_EPI_CONSULTA",
    "ANIO_EPI_MUESTRA",
    "ID_PROVINCIA_RESIDENCIA",
    "ID_PROVINCIA_CLINICA",
    "ID_PROVINCIA_MUESTRA",
    "ID_PROVINCIA_VIAJE",
    "ID_PROVINCIA_CARGA",
    "ESTABLECIMIENTO_INTERNACION",
    "OCUPACION",
    "VALIDACION",
    "INFO_CONTACTO",
    "CLASIFICACION_ALGORITMO",
    "EDAD_APERTURA",
    "COBERTURA_SOCIAL",
    "VALOR",
    "ORIGEN_FINANCIAMIENTO",
    "SE_DECLARA_PUEBLO_INDIGENA",
    "ETNIA",
    "ID_SNVS_INTERPRET_USR",
    "ID_SNVS_MUESTRA",
    "ID_SNVS_TIPO_PRUEBA",
    "ID_SNVS_PRUEBA",
    "ID_SNVS_RESULTADO",
    "GENERO",
    "SEXO_AL_NACER",
    "FECHA_PAPEL",
    "BARRIO_POPULAR",
    "SEM_MIN",
    "AÑO_MIN",
]


# === TYPES PARA COMPILACIÓN ===

# Type literals para chequeo estático
ColumnName = Literal[
    "CODIGO_CIUDADANO",
    "IDEVENTOCASO",
    "EVENTO",
    "NOMBRE",
    "APELLIDO",
    "SEXO",
    "TIPO_DOC",
    "NRO_DOC",
    "FECHA_NACIMIENTO",
    "EDAD_ACTUAL",
    "EDAD_DIAGNOSTICO",
    "GRUPO_ETARIO",
    "SEPI_APERTURA",
    "SEPI_SINTOMA",
    "SEPI_CONSULTA",
    "SEPI_MUESTRA",
    "IDPAISRESIDENCIA",
    "PAIS_RESIDENCIA",
    "ID_PROV_INDEC_RESIDENCIA",
    "PROVINCIA_RESIDENCIA",
    "ID_DEPTO_INDEC_RESIDENCIA",
    "DEPARTAMENTO_RESIDENCIA",
    "ID_LOC_INDEC_RESIDENCIA",
    "LOCALIDAD_RESIDENCIA",
    "CALLE_DOMICILIO",
    "NUMERO_DOMICILIO",
    "CLASIFICACION_MANUAL",
    "CLASIFICACION_AUTOMATICA",
    "FECHA_APERTURA",
    "PROVINCIA_INTERVIENEN",
    "REGION_SANITARIA_INTERVIENEN",
    "DEPARTAMENTO_INTERVIENEN",
    "LOCALIDAD_INTERVIENEN",
    "ESTABLECIMIENTOS_INTERVIENEN",
    "FECHA_CONSULTA",
    "ID_PROV_INDEC_CLINICA",
    "PROV_CLINICA",
    "ID_DEPTO_INDEC_CLINICA",
    "DEPTO_CLINICA",
    "ID_LOC_INDEC_CLINICA",
    "LOCA_CLINICA",
    "ID_ESTAB_CLINICA",
    "ESTAB_CLINICA",
    "SINTOMATICO",
    "FIS",
    "EMBARAZADA",
    "INTERNADO",
    "CURADO",
    "FECHA_INTERNACION",
    "CUIDADO_INTENSIVO",
    "FECHA_CUI_INTENSIVOS",
    "FECHA_ALTA_MEDICA",
    "FALLECIDO",
    "FECHA_FALLECIMIENTO",
    "MUESTRA",
    "ID_SNVS_EVENTO_MUESTRA",
    "FTM",
    "ID_ESTABLECIMIENTO_MUESTRA",
    "ESTABLECIMIENTO_MUESTRA",
    "ID_PROV_INDEC_MUESTRA",
    "PROVINCIA_MUESTRA",
    "ID_DEPTO_INDEC_MUESTRA",
    "DEPARTAMENTO_MUESTRA",
    "ID_LOC_INDEC_MUESTRA",
    "LOCALIDAD_MUESTRA",
    "ID_SNVS_PRUEBA_MUESTRA",
    "FECHA_ESTUDIO",
    "DETERMINACION",
    "TECNICA",
    "RESULTADO",
    "FECHA_RECEPCION",
    "ID_ESTABLECIMIENTO_DIAG",
    "ESTABLECIMIENTO_DIAG",
    "ID_PROV_INDEC_DIAG",
    "PROVINCIA_DIAG",
    "ID_DEPTO_INDEC_DIAG",
    "DEPARTAMENTO_DIAG",
    "ID_LOC_INDEC_DIAG",
    "LOCALIDAD_DIAG",
    "ID_SNVS_VIAJE_EPIDEMIO",
    "FECHA_INICIO_VIAJE",
    "FECHA_FIN_VIAJE",
    "ID_PAIS_VIAJE",
    "PAIS_VIAJE",
    "ID_PROV_INDEC_VIAJE",
    "PROV_VIAJE",
    "ID_LOC_INDEC_VIAJE",
    "LOC_VIAJE",
    "ID_SNVS_ANTECEDENTE_EPIDEMIO",
    "ANTECEDENTE_EPIDEMIOLOGICO",
    "ID_SNVS_VACUNA",
    "VACUNA",
    "DOSIS",
    "FECHA_APLICACION",
    "FECHA_INICIO_SINTOMA",
    "ID_SNVS_SIGNO_SINTOMA",
    "SIGNO_SINTOMA",
    "ESTAB_TTO",
    "TRATAMIENTO_2",
    "FECHA_INICIO_TRAT",
    "FECHA_FIN_TRAT",
    "RESULTADO_TRATAMIENTO",
    "GRUPO_EVENTO",
    "ID_ORIGEN",
    "ESTABLECIMIENTO_EPI",
    "ID_PROV_INDEC_EPI",
    "PROVINCIA_EPI",
    "ID_DEPTO_INDEC_EPI",
    "DEPARTAMENTO_EPI",
    "ID_LOC_INDEC_EPI",
    "LOCALIDAD_EPI",
    "ID_ESTABLECIMIENTO_CARGA",
    "ESTABLECIMIENTO_CARGA",
    "ID_PROV_INDEC_CARGA",
    "PROVINCIA_CARGA",
    "ID_DEPTO_INDEC_CARGA",
    "DEPARTAMENTO_CARGA",
    "ID_LOC_INDEC_CARGA",
    "LOCALIDAD_CARGA",
    "ID_SNVS_EVENTO",
    "USER_CENTINELA",
    "EVENTO_CENTINELA",
    "ID_USER_REGISTRO",
    "USER_CENT_PARTICIPO",
    "ID_USER_CENT_PARTICIPO",
    "TIPO_LUGAR_OCURRENCIA",
    "NOMBRE_LUGAR_OCURRENCIA",
    "LOCALIDAD_AMBITO_OCURRENCIA",
    "SITIO_PROBABLE_ADQUISICION",
    "SITIO_PROBABLE_DISEMINACION",
    "FRECUENCIA",
    "FECHA_AMBITO_OCURRENCIA",
    "FECHA_ANTECEDENTE_EPI",
    "INVESTIGACION_TERRENO",
    "FECHA_INVESTIGACION",
    "TIPO_Y_LUGAR_INVESTIGACION",
    "CONTACTO_CON_CONFIR",
    "CONTACTO_CON_SOSPECHOSO",
    "CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS",
    "CONTACTOS_MENORES_1",
    "CONTACTO_EMBARAZADAS",
    "CONTACTOS_VACUNADOS",
    "OBSERVACIONES",
    "COMORBILIDAD",
    "DIAG_REFERIDO",
    "FECHA_DIAG_REFERIDO",
    "REGION_SANITARIA_MUESTRA",
    "REGION_SANITARIA_CLINICA",
    "REGION_SANITARIA_CARGA",
    "ANIO_EPI_APERTURA",
    "ANIO_EPI_SINTOMA",
    "ANIO_EPI_CONSULTA",
    "ANIO_EPI_MUESTRA",
    "ID_PROVINCIA_RESIDENCIA",
    "ID_PROVINCIA_CLINICA",
    "ID_PROVINCIA_MUESTRA",
    "ID_PROVINCIA_VIAJE",
    "ID_PROVINCIA_CARGA",
    "ESTABLECIMIENTO_INTERNACION",
    "OCUPACION",
    "VALIDACION",
    "INFO_CONTACTO",
    "CLASIFICACION_ALGORITMO",
    "EDAD_APERTURA",
    "COBERTURA_SOCIAL",
    "VALOR",
    "ORIGEN_FINANCIAMIENTO",
    "SE_DECLARA_PUEBLO_INDIGENA",
    "ETNIA",
    "ID_SNVS_INTERPRET_USR",
    "ID_SNVS_MUESTRA",
    "ID_SNVS_TIPO_PRUEBA",
    "ID_SNVS_PRUEBA",
    "ID_SNVS_RESULTADO",
    "GENERO",
    "SEXO_AL_NACER",
    "FECHA_PAPEL",
    "BARRIO_POPULAR",
    "SEM_MIN",
    "AÑO_MIN",
]


class ColumnType(Enum):
    """Tipos de columnas para procesamiento automático."""

    TEXT = "text"
    DATE = "date"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"


@dataclass(frozen=True)
class ColumnInfo:
    """Información completa de una columna."""

    name: str
    data_type: ColumnType
    is_required: bool = False
    is_key: bool = False
    description: str = ""
    validation_rules: Dict = None


# === DICCIONARIO PRINCIPAL DE COLUMNAS ===


class EpiColumns:
    """
    Diccionario centralizado de columnas epidemiológicas.

    Provee acceso seguro y tipado a todas las columnas disponibles.

    Ejemplos de uso:
        # Acceso seguro con autocompletado:
        cols = EpiColumns()
        evento_col = cols.EVENTO          # ✅ Autocompletado del IDE
        nombre_col = cols.NOMBRE          # ✅ Compilador valida existencia

        # Validación de existencia:
        cols.validate_column("EVENTO")    # ✅ True
        cols.validate_column("FAKE_COL")  # ❌ Raises ValueError

        # Acceso a info de columnas:
        info = cols.get_info("EVENTO")
        print(info.data_type)  # ColumnType.CATEGORICAL

        # Filtrar DataFrames:
        required_df = cols.select_required(df)
        date_df = cols.select_by_type(df, ColumnType.DATE)
    """

    # === COLUMNAS PRIMARIAS ===
    CODIGO_CIUDADANO: ColumnName = "CODIGO_CIUDADANO"
    IDEVENTOCASO: ColumnName = "IDEVENTOCASO"
    EVENTO: ColumnName = "EVENTO"

    # === DATOS PERSONALES ===
    NOMBRE: ColumnName = "NOMBRE"
    APELLIDO: ColumnName = "APELLIDO"
    SEXO: ColumnName = "SEXO"
    GENERO: ColumnName = "GENERO"
    SEXO_AL_NACER: ColumnName = "SEXO_AL_NACER"
    TIPO_DOC: ColumnName = "TIPO_DOC"
    NRO_DOC: ColumnName = "NRO_DOC"
    FECHA_NACIMIENTO: ColumnName = "FECHA_NACIMIENTO"
    EDAD_ACTUAL: ColumnName = "EDAD_ACTUAL"
    EDAD_DIAGNOSTICO: ColumnName = "EDAD_DIAGNOSTICO"
    EDAD_APERTURA: ColumnName = "EDAD_APERTURA"
    GRUPO_ETARIO: ColumnName = "GRUPO_ETARIO"
    OCUPACION: ColumnName = "OCUPACION"
    COBERTURA_SOCIAL: ColumnName = "COBERTURA_SOCIAL"
    ETNIA: ColumnName = "ETNIA"
    SE_DECLARA_PUEBLO_INDIGENA: ColumnName = "SE_DECLARA_PUEBLO_INDIGENA"

    # === FECHAS Y PERÍODOS EPIDEMIOLÓGICOS ===
    SEPI_APERTURA: ColumnName = "SEPI_APERTURA"
    SEPI_SINTOMA: ColumnName = "SEPI_SINTOMA"
    SEPI_CONSULTA: ColumnName = "SEPI_CONSULTA"
    SEPI_MUESTRA: ColumnName = "SEPI_MUESTRA"
    FECHA_APERTURA: ColumnName = "FECHA_APERTURA"
    FECHA_CONSULTA: ColumnName = "FECHA_CONSULTA"
    FECHA_INICIO_SINTOMA: ColumnName = "FECHA_INICIO_SINTOMA"
    ANIO_EPI_APERTURA: ColumnName = "ANIO_EPI_APERTURA"
    ANIO_EPI_SINTOMA: ColumnName = "ANIO_EPI_SINTOMA"
    ANIO_EPI_CONSULTA: ColumnName = "ANIO_EPI_CONSULTA"
    ANIO_EPI_MUESTRA: ColumnName = "ANIO_EPI_MUESTRA"

    # === CLASIFICACIÓN ===
    CLASIFICACION_MANUAL: ColumnName = "CLASIFICACION_MANUAL"
    CLASIFICACION_AUTOMATICA: ColumnName = "CLASIFICACION_AUTOMATICA"
    CLASIFICACION_ALGORITMO: ColumnName = "CLASIFICACION_ALGORITMO"
    VALIDACION: ColumnName = "VALIDACION"

    # === RESIDENCIA ===
    IDPAISRESIDENCIA: ColumnName = "IDPAISRESIDENCIA"
    PAIS_RESIDENCIA: ColumnName = "PAIS_RESIDENCIA"
    ID_PROV_INDEC_RESIDENCIA: ColumnName = "ID_PROV_INDEC_RESIDENCIA"
    ID_PROVINCIA_RESIDENCIA: ColumnName = "ID_PROVINCIA_RESIDENCIA"
    PROVINCIA_RESIDENCIA: ColumnName = "PROVINCIA_RESIDENCIA"
    ID_DEPTO_INDEC_RESIDENCIA: ColumnName = "ID_DEPTO_INDEC_RESIDENCIA"
    DEPARTAMENTO_RESIDENCIA: ColumnName = "DEPARTAMENTO_RESIDENCIA"
    ID_LOC_INDEC_RESIDENCIA: ColumnName = "ID_LOC_INDEC_RESIDENCIA"
    LOCALIDAD_RESIDENCIA: ColumnName = "LOCALIDAD_RESIDENCIA"
    CALLE_DOMICILIO: ColumnName = "CALLE_DOMICILIO"
    NUMERO_DOMICILIO: ColumnName = "NUMERO_DOMICILIO"
    BARRIO_POPULAR: ColumnName = "BARRIO_POPULAR"

    # === INTERVENCION ===
    # No se deberían guardar en la db directo
    PROVINCIA_INTERVIENEN: ColumnName = "PROVINCIA_INTERVIENEN"
    REGION_SANITARIA_INTERVIENEN: ColumnName = "REGION_SANITARIA_INTERVIENEN"
    DEPARTAMENTO_INTERVIENEN: ColumnName = "DEPARTAMENTO_INTERVIENEN"
    LOCALIDAD_INTERVIENEN: ColumnName = "LOCALIDAD_INTERVIENEN"
    ESTABLECIMIENTOS_INTERVIENEN: ColumnName = "ESTABLECIMIENTOS_INTERVIENEN"

    # === CLINICA ===
    ID_PROV_INDEC_CLINICA: ColumnName = "ID_PROV_INDEC_CLINICA"
    PROV_CLINICA: ColumnName = "PROV_CLINICA"
    ID_PROVINCIA_CLINICA: ColumnName = "ID_PROVINCIA_CLINICA"
    ID_DEPTO_INDEC_CLINICA: ColumnName = "ID_DEPTO_INDEC_CLINICA"
    DEPTO_CLINICA: ColumnName = "DEPTO_CLINICA"
    ID_LOC_INDEC_CLINICA: ColumnName = "ID_LOC_INDEC_CLINICA"
    LOCA_CLINICA: ColumnName = "LOCA_CLINICA"
    ID_ESTAB_CLINICA: ColumnName = "ID_ESTAB_CLINICA"
    ESTAB_CLINICA: ColumnName = "ESTAB_CLINICA"
    REGION_SANITARIA_CLINICA: ColumnName = "REGION_SANITARIA_CLINICA"

    # === CONDICIONES CLINICAS ===
    SINTOMATICO: ColumnName = "SINTOMATICO"
    FIS: ColumnName = "FIS"
    EMBARAZADA: ColumnName = "EMBARAZADA"
    INTERNADO: ColumnName = "INTERNADO"
    CURADO: ColumnName = "CURADO"
    FECHA_INTERNACION: ColumnName = "FECHA_INTERNACION"
    CUIDADO_INTENSIVO: ColumnName = "CUIDADO_INTENSIVO"
    FECHA_CUI_INTENSIVOS: ColumnName = "FECHA_CUI_INTENSIVOS"
    FECHA_ALTA_MEDICA: ColumnName = "FECHA_ALTA_MEDICA"
    FALLECIDO: ColumnName = "FALLECIDO"
    FECHA_FALLECIMIENTO: ColumnName = "FECHA_FALLECIMIENTO"
    ESTABLECIMIENTO_INTERNACION: ColumnName = "ESTABLECIMIENTO_INTERNACION"

    # === MUESTRAS ===
    MUESTRA: ColumnName = "MUESTRA"
    ID_SNVS_EVENTO_MUESTRA: ColumnName = "ID_SNVS_EVENTO_MUESTRA"
    FTM: ColumnName = "FTM"
    ID_ESTABLECIMIENTO_MUESTRA: ColumnName = "ID_ESTABLECIMIENTO_MUESTRA"
    ESTABLECIMIENTO_MUESTRA: ColumnName = "ESTABLECIMIENTO_MUESTRA"
    ID_PROV_INDEC_MUESTRA: ColumnName = "ID_PROV_INDEC_MUESTRA"
    PROVINCIA_MUESTRA: ColumnName = "PROVINCIA_MUESTRA"
    ID_PROVINCIA_MUESTRA: ColumnName = "ID_PROVINCIA_MUESTRA"
    ID_DEPTO_INDEC_MUESTRA: ColumnName = "ID_DEPTO_INDEC_MUESTRA"
    DEPARTAMENTO_MUESTRA: ColumnName = "DEPARTAMENTO_MUESTRA"
    ID_LOC_INDEC_MUESTRA: ColumnName = "ID_LOC_INDEC_MUESTRA"
    LOCALIDAD_MUESTRA: ColumnName = "LOCALIDAD_MUESTRA"
    REGION_SANITARIA_MUESTRA: ColumnName = "REGION_SANITARIA_MUESTRA"
    ID_SNVS_PRUEBA_MUESTRA: ColumnName = "ID_SNVS_PRUEBA_MUESTRA"

    # === ESTUDIOS Y RESULTADOS ===
    FECHA_ESTUDIO: ColumnName = "FECHA_ESTUDIO"
    DETERMINACION: ColumnName = "DETERMINACION"
    TECNICA: ColumnName = "TECNICA"
    RESULTADO: ColumnName = "RESULTADO"
    FECHA_RECEPCION: ColumnName = "FECHA_RECEPCION"

    # === DIAGNOSTICO ===
    ID_ESTABLECIMIENTO_DIAG: ColumnName = "ID_ESTABLECIMIENTO_DIAG"
    ESTABLECIMIENTO_DIAG: ColumnName = "ESTABLECIMIENTO_DIAG"
    ID_PROV_INDEC_DIAG: ColumnName = "ID_PROV_INDEC_DIAG"
    PROVINCIA_DIAG: ColumnName = "PROVINCIA_DIAG"
    ID_DEPTO_INDEC_DIAG: ColumnName = "ID_DEPTO_INDEC_DIAG"
    DEPARTAMENTO_DIAG: ColumnName = "DEPARTAMENTO_DIAG"
    ID_LOC_INDEC_DIAG: ColumnName = "ID_LOC_INDEC_DIAG"
    LOCALIDAD_DIAG: ColumnName = "LOCALIDAD_DIAG"

    # === VIAJES ===
    ID_SNVS_VIAJE_EPIDEMIO: ColumnName = "ID_SNVS_VIAJE_EPIDEMIO"
    FECHA_INICIO_VIAJE: ColumnName = "FECHA_INICIO_VIAJE"
    FECHA_FIN_VIAJE: ColumnName = "FECHA_FIN_VIAJE"
    ID_PAIS_VIAJE: ColumnName = "ID_PAIS_VIAJE"
    PAIS_VIAJE: ColumnName = "PAIS_VIAJE"
    ID_PROV_INDEC_VIAJE: ColumnName = "ID_PROV_INDEC_VIAJE"
    PROV_VIAJE: ColumnName = "PROV_VIAJE"
    ID_PROVINCIA_VIAJE: ColumnName = "ID_PROVINCIA_VIAJE"
    ID_LOC_INDEC_VIAJE: ColumnName = "ID_LOC_INDEC_VIAJE"
    LOC_VIAJE: ColumnName = "LOC_VIAJE"

    # === ANTECEDENTES ===
    ID_SNVS_ANTECEDENTE_EPIDEMIO: ColumnName = "ID_SNVS_ANTECEDENTE_EPIDEMIO"
    ANTECEDENTE_EPIDEMIOLOGICO: ColumnName = "ANTECEDENTE_EPIDEMIOLOGICO"

    # === VACUNAS ===
    ID_SNVS_VACUNA: ColumnName = "ID_SNVS_VACUNA"
    VACUNA: ColumnName = "VACUNA"
    DOSIS: ColumnName = "DOSIS"
    FECHA_APLICACION: ColumnName = "FECHA_APLICACION"

    # === SINTOMAS ===
    ID_SNVS_SIGNO_SINTOMA: ColumnName = "ID_SNVS_SIGNO_SINTOMA"
    SIGNO_SINTOMA: ColumnName = "SIGNO_SINTOMA"

    # === TRATAMIENTO ===
    ESTAB_TTO: ColumnName = "ESTAB_TTO"
    TRATAMIENTO_2: ColumnName = "TRATAMIENTO_2"
    FECHA_INICIO_TRAT: ColumnName = "FECHA_INICIO_TRAT"
    FECHA_FIN_TRAT: ColumnName = "FECHA_FIN_TRAT"
    RESULTADO_TRATAMIENTO: ColumnName = "RESULTADO_TRATAMIENTO"

    # === GRUPO EVENTO (IMPORTANTÍSIMO) ===
    GRUPO_EVENTO: ColumnName = "GRUPO_EVENTO"

    # === EPIDEMIOLOGIA ===
    ID_ORIGEN: ColumnName = "ID_ORIGEN"
    ESTABLECIMIENTO_EPI: ColumnName = "ESTABLECIMIENTO_EPI"
    ID_PROV_INDEC_EPI: ColumnName = "ID_PROV_INDEC_EPI"
    PROVINCIA_EPI: ColumnName = "PROVINCIA_EPI"
    ID_DEPTO_INDEC_EPI: ColumnName = "ID_DEPTO_INDEC_EPI"
    DEPARTAMENTO_EPI: ColumnName = "DEPARTAMENTO_EPI"
    ID_LOC_INDEC_EPI: ColumnName = "ID_LOC_INDEC_EPI"
    LOCALIDAD_EPI: ColumnName = "LOCALIDAD_EPI"

    # === CARGA ===
    ID_ESTABLECIMIENTO_CARGA: ColumnName = "ID_ESTABLECIMIENTO_CARGA"
    ESTABLECIMIENTO_CARGA: ColumnName = "ESTABLECIMIENTO_CARGA"
    ID_PROV_INDEC_CARGA: ColumnName = "ID_PROV_INDEC_CARGA"
    PROVINCIA_CARGA: ColumnName = "PROVINCIA_CARGA"
    ID_PROVINCIA_CARGA: ColumnName = "ID_PROVINCIA_CARGA"
    ID_DEPTO_INDEC_CARGA: ColumnName = "ID_DEPTO_INDEC_CARGA"
    DEPARTAMENTO_CARGA: ColumnName = "DEPARTAMENTO_CARGA"
    ID_LOC_INDEC_CARGA: ColumnName = "ID_LOC_INDEC_CARGA"
    LOCALIDAD_CARGA: ColumnName = "LOCALIDAD_CARGA"
    REGION_SANITARIA_CARGA: ColumnName = "REGION_SANITARIA_CARGA"

    # === SISTEMA ===
    ID_SNVS_EVENTO: ColumnName = "ID_SNVS_EVENTO"
    USER_CENTINELA: ColumnName = "USER_CENTINELA"
    EVENTO_CENTINELA: ColumnName = "EVENTO_CENTINELA"
    ID_USER_REGISTRO: ColumnName = "ID_USER_REGISTRO"
    USER_CENT_PARTICIPO: ColumnName = "USER_CENT_PARTICIPO"
    ID_USER_CENT_PARTICIPO: ColumnName = "ID_USER_CENT_PARTICIPO"

    # === OCURRENCIA ===
    TIPO_LUGAR_OCURRENCIA: ColumnName = "TIPO_LUGAR_OCURRENCIA"
    NOMBRE_LUGAR_OCURRENCIA: ColumnName = "NOMBRE_LUGAR_OCURRENCIA"
    LOCALIDAD_AMBITO_OCURRENCIA: ColumnName = "LOCALIDAD_AMBITO_OCURRENCIA"
    SITIO_PROBABLE_ADQUISICION: ColumnName = "SITIO_PROBABLE_ADQUISICION"
    SITIO_PROBABLE_DISEMINACION: ColumnName = "SITIO_PROBABLE_DISEMINACION"
    FRECUENCIA: ColumnName = "FRECUENCIA"
    FECHA_AMBITO_OCURRENCIA: ColumnName = "FECHA_AMBITO_OCURRENCIA"
    FECHA_ANTECEDENTE_EPI: ColumnName = "FECHA_ANTECEDENTE_EPI"

    # === INVESTIGACION ===
    INVESTIGACION_TERRENO: ColumnName = "INVESTIGACION_TERRENO"
    FECHA_INVESTIGACION: ColumnName = "FECHA_INVESTIGACION"
    TIPO_Y_LUGAR_INVESTIGACION: ColumnName = "TIPO_Y_LUGAR_INVESTIGACION"

    # === CONTACTOS ===
    CONTACTO_CON_CONFIR: ColumnName = "CONTACTO_CON_CONFIR"
    CONTACTO_CON_SOSPECHOSO: ColumnName = "CONTACTO_CON_SOSPECHOSO"
    CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS: ColumnName = (
        "CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS"
    )
    CONTACTOS_MENORES_1: ColumnName = "CONTACTOS_MENORES_1"
    CONTACTO_EMBARAZADAS: ColumnName = "CONTACTO_EMBARAZADAS"
    CONTACTOS_VACUNADOS: ColumnName = "CONTACTOS_VACUNADOS"

    # === ADICIONALES ===
    OBSERVACIONES: ColumnName = "OBSERVACIONES"
    COMORBILIDAD: ColumnName = "COMORBILIDAD"
    DIAG_REFERIDO: ColumnName = "DIAG_REFERIDO"
    FECHA_DIAG_REFERIDO: ColumnName = "FECHA_DIAG_REFERIDO"
    INFO_CONTACTO: ColumnName = "INFO_CONTACTO"
    VALOR: ColumnName = "VALOR"
    ORIGEN_FINANCIAMIENTO: ColumnName = "ORIGEN_FINANCIAMIENTO"
    FECHA_PAPEL: ColumnName = "FECHA_PAPEL"

    # === SISTEMA SNVS ===
    ID_SNVS_INTERPRET_USR: ColumnName = "ID_SNVS_INTERPRET_USR"
    ID_SNVS_MUESTRA: ColumnName = "ID_SNVS_MUESTRA"
    ID_SNVS_TIPO_PRUEBA: ColumnName = "ID_SNVS_TIPO_PRUEBA"
    ID_SNVS_PRUEBA: ColumnName = "ID_SNVS_PRUEBA"
    ID_SNVS_RESULTADO: ColumnName = "ID_SNVS_RESULTADO"

    # === SEMANAS Y AÑOS MINIMOS ===
    SEM_MIN: ColumnName = "SEM_MIN"
    AÑO_MIN: ColumnName = "AÑO_MIN"

    @classmethod
    def all_columns(cls) -> List[str]:
        """Retorna todas las columnas disponibles."""
        return ALL_COLUMNS.copy()

    @classmethod
    def validate_column(cls, column_name: str) -> bool:
        """Valida si una columna existe."""
        if column_name not in ALL_COLUMNS:
            raise ValueError(
                f"Columna '{column_name}' no existe. "
                f"Columnas disponibles: {', '.join(ALL_COLUMNS[:10])}... "
                f"(total: {len(ALL_COLUMNS)})"
            )
        return True

    @classmethod
    def get_info(cls, column_name: str) -> ColumnInfo:
        """Obtiene información detallada de una columna."""
        cls.validate_column(column_name)

        # Mapeo de tipos basado en el nombre
        if any(
            date_word in column_name.upper()
            for date_word in ["FECHA", "SEPI", "FTM", "FIS"]
        ):
            data_type = ColumnType.DATE
        elif any(
            id_word in column_name.upper()
            for id_word in [
                "ID_",
                "NRO_",
                "EDAD_",
                "NUMERO_",
                "VALOR",
                "DOSIS",
                "SEM_",
                "AÑO_",
            ]
        ):
            data_type = ColumnType.NUMERIC
        elif any(
            bool_word in column_name.upper()
            for bool_word in [
                "SINTOMATICO",
                "EMBARAZADA",
                "INTERNADO",
                "CURADO",
                "FALLECIDO",
                # "MUESTRA" NO es booleana - es categorical (tipo de muestra: Suero, LCR, etc.)
                "PUEBLO_INDIGENA",
                "BARRIO_POPULAR",
                "CUIDADO_INTENSIVO",
                # "FIS" NO es booleana - es fecha (FIS = Fecha de Inicio de Síntomas)
                "CENTINELA",
                "INVESTIGACION",
            ]
        ):
            data_type = ColumnType.BOOLEAN
        elif column_name.upper() in [
            "EVENTO",
            "CLASIFICACION_MANUAL",
            "CLASIFICACION_AUTOMATICA",
            "SEXO",
            "TIPO_DOC",
            "MUESTRA",  # Tipo de muestra (Suero, LCR, Sangre entera, etc.)
        ]:
            data_type = ColumnType.CATEGORICAL
        else:
            data_type = ColumnType.TEXT

        # Columnas críticas
        is_required = column_name in [
            "IDEVENTOCASO",
            "EVENTO",
            "CODIGO_CIUDADANO",
            "CLASIFICACION_MANUAL",
            "FECHA_APERTURA",
        ]

        is_key = column_name in ["IDEVENTOCASO", "CODIGO_CIUDADANO"]

        return ColumnInfo(
            name=column_name,
            data_type=data_type,
            is_required=is_required,
            is_key=is_key,
            description=f"Columna epidemiológica: {column_name}",
        )

    @classmethod
    def select_required(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Selecciona solo las columnas requeridas del DataFrame."""
        required_cols = [col for col in ALL_COLUMNS if cls.get_info(col).is_required]
        available_cols = [col for col in required_cols if col in df.columns]
        return df[available_cols]

    @classmethod
    def select_by_type(cls, df: pd.DataFrame, column_type: ColumnType) -> pd.DataFrame:
        """Selecciona columnas por tipo de datos."""
        type_cols = [
            col
            for col in ALL_COLUMNS
            if col in df.columns and cls.get_info(col).data_type == column_type
        ]
        return df[type_cols] if type_cols else pd.DataFrame()

    @classmethod
    def get_missing_columns(
        cls, df: pd.DataFrame, required_only: bool = True
    ) -> List[str]:
        """Obtiene columnas faltantes en el DataFrame."""
        if required_only:
            expected_cols = [
                col for col in ALL_COLUMNS if cls.get_info(col).is_required
            ]
        else:
            expected_cols = ALL_COLUMNS

        return [col for col in expected_cols if col not in df.columns]

    @classmethod
    def validate_dataframe(
        cls, df: pd.DataFrame, strict: bool = False
    ) -> Dict[str, any]:
        """Valida estructura del DataFrame."""
        missing_required = cls.get_missing_columns(df, required_only=True)
        missing_all = cls.get_missing_columns(df, required_only=False)
        extra_columns = [col for col in df.columns if col not in ALL_COLUMNS]

        coverage_pct = ((len(ALL_COLUMNS) - len(missing_all)) / len(ALL_COLUMNS)) * 100

        is_valid = len(missing_required) == 0 and (
            not strict or len(extra_columns) == 0
        )

        return {
            "is_valid": is_valid,
            "missing_required": missing_required,
            "missing_optional": [
                col for col in missing_all if col not in missing_required
            ],
            "extra_columns": extra_columns,
            "coverage_percentage": round(coverage_pct, 1),
            "total_columns": len(df.columns),
            "matched_columns": len(ALL_COLUMNS) - len(missing_all),
        }


# === INSTANCIA GLOBAL ===
# Para uso conveniente en todo el sistema
Columns = EpiColumns()

# === CONSTANTES DE COMPATIBILIDAD ===
# Para mantener compatibilidad con código existente
REQUIRED_COLUMNS = [col for col in ALL_COLUMNS if Columns.get_info(col).is_required]
DATE_COLUMNS = [
    col for col in ALL_COLUMNS if Columns.get_info(col).data_type == ColumnType.DATE
]
NUMERIC_COLUMNS = [
    col for col in ALL_COLUMNS if Columns.get_info(col).data_type == ColumnType.NUMERIC
]
BOOLEAN_COLUMNS = [
    col for col in ALL_COLUMNS if Columns.get_info(col).data_type == ColumnType.BOOLEAN
]
CATEGORICAL_COLUMNS = [
    col
    for col in ALL_COLUMNS
    if Columns.get_info(col).data_type == ColumnType.CATEGORICAL
]

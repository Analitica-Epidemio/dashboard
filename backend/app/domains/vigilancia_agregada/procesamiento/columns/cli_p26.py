"""
Definiciones de columnas para CLI_P26 (Casos Clínicos Ambulatorios).

Basado en análisis de tmp/agrupados/CLI_P26.md
- 28 columnas
- 67,302 registros de ejemplo
- Columnas clave: ANIO, SEMANA, ORIGEN, NOMBREEVENTOAGRP, GRUPO, CANTIDAD
"""

from .base import ColumnDefinition, ColumnRegistry, ColumnType

CLI_P26_COLUMNS = ColumnRegistry(
    file_type="CLI_P26",
    columns=[
        # Identificadores
        ColumnDefinition(
            source_name="ID_ENCABEZADO",
            target_name="id_encabezado",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="ID_AGRP_CLINICA",
            target_name="id_agrp_clinica",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        # Establecimiento
        ColumnDefinition(
            source_name="ID_ORIGEN",
            target_name="id_origen",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="ORIGEN",
            target_name="nombre_origen",
            col_type=ColumnType.STRING,
            required=True,
        ),
        # Geografía
        ColumnDefinition(
            source_name="CODIGO_LOCALIDAD",
            target_name="codigo_localidad",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="LOCALIDAD",
            target_name="nombre_localidad",
            col_type=ColumnType.STRING,
            required=False,
        ),
        ColumnDefinition(
            source_name="CODIGO_DEPTO",
            target_name="codigo_depto",
            col_type=ColumnType.INTEGER,
            required=False,
        ),
        ColumnDefinition(
            source_name="DEPARTAMENTO",
            target_name="nombre_depto",
            col_type=ColumnType.STRING,
            required=False,
        ),
        ColumnDefinition(
            source_name="CODIGO_PROVINCIA",
            target_name="codigo_provincia",
            col_type=ColumnType.INTEGER,
            required=False,
        ),
        ColumnDefinition(
            source_name="PROVINCIA",
            target_name="nombre_provincia",
            col_type=ColumnType.STRING,
            required=False,
        ),
        # Temporal
        ColumnDefinition(
            source_name="ANIO",
            target_name="anio",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="SEMANA",
            target_name="semana",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        # Estado
        ColumnDefinition(
            source_name="IDESTADO",
            target_name="id_estado",
            col_type=ColumnType.INTEGER,
            required=False,
        ),
        ColumnDefinition(
            source_name="ESTADO",
            target_name="estado",
            col_type=ColumnType.STRING,
            required=False,
        ),
        # Fechas de registro
        ColumnDefinition(
            source_name="FECHAREGISTROENCABEZADO",
            target_name="fecha_registro_encabezado",
            col_type=ColumnType.DATETIME,
            required=False,
        ),
        ColumnDefinition(
            source_name="USUARIOREGISTROENCABEZADO",
            target_name="usuario_registro_encabezado",
            col_type=ColumnType.STRING,
            required=False,
        ),
        # Evento
        ColumnDefinition(
            source_name="IDEVENTOAGRUPADO",
            target_name="id_evento_agrupado",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="NOMBREGRPEVENTOAGRP",
            target_name="nombre_grupo_evento",
            col_type=ColumnType.STRING,
            required=True,
        ),
        ColumnDefinition(
            source_name="ID_SNVS_EVENTO_AGRP",
            target_name="id_snvs_evento",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="NOMBREEVENTOAGRP",
            target_name="nombre_evento",
            col_type=ColumnType.STRING,
            required=True,
        ),
        # Grupo etario
        ColumnDefinition(
            source_name="IDEDAD",
            target_name="id_edad",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="GRUPO",
            target_name="nombre_grupo_etario",
            col_type=ColumnType.STRING,
            required=True,
        ),
        # Sexo (muy incompleto: 6.6%)
        ColumnDefinition(
            source_name="SEXO",
            target_name="sexo",
            col_type=ColumnType.STRING,
            required=False,
            nullable=True,
        ),
        # Flags opcionales (1.1% completitud)
        ColumnDefinition(
            source_name="RESIDENTE",
            target_name="residente",
            col_type=ColumnType.STRING,
            required=False,
            nullable=True,
        ),
        ColumnDefinition(
            source_name="AMBULATORIO",
            target_name="ambulatorio",
            col_type=ColumnType.STRING,
            required=False,
            nullable=True,
        ),
        # Valor principal
        ColumnDefinition(
            source_name="CANTIDAD",
            target_name="cantidad",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        # Metadata de registro
        ColumnDefinition(
            source_name="FECHAREGISTROCLINICA",
            target_name="fecha_registro_clinica",
            col_type=ColumnType.DATETIME,
            required=False,
        ),
        ColumnDefinition(
            source_name="USERREGISTROCLINICA",
            target_name="usuario_registro_clinica",
            col_type=ColumnType.STRING,
            required=False,
        ),
    ],
)

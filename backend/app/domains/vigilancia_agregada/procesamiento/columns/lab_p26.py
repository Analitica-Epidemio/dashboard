"""
Definiciones de columnas para LAB_P26 (Estudios de Laboratorio).

Basado en análisis de tmp/agrupados/LAB_P26.md
- 30 columnas (2 más que CLI_P26)
- 63,978 registros de ejemplo
- Columnas específicas: ESTUDIADAS, POSITIVAS (no CANTIDAD)
- EVENTO = agente etiológico
"""

from .base import ColumnDefinition, ColumnRegistry, ColumnType

LAB_P26_COLUMNS = ColumnRegistry(
    file_type="LAB_P26",
    columns=[
        # Identificadores
        ColumnDefinition(
            source_name="ID_ENCABEZADO",
            target_name="id_encabezado",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="ID_AGRP_LABO",  # Diferente a CLI_P26
            target_name="id_agrp_labo",
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
            source_name="NOMBRE_ORIGEN",  # Diferente: NOMBRE_ORIGEN vs ORIGEN
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
            source_name="ID_SNVS_AGRP_ENC_ESTADO",  # Diferente nombre
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
        # Fechas y usuarios
        ColumnDefinition(
            source_name="FECHA_REGISTRO1",
            target_name="fecha_registro_1",
            col_type=ColumnType.DATETIME,
            required=False,
        ),
        ColumnDefinition(
            source_name="FECHA_MODIFICACION",  # Solo 1.8% completitud
            target_name="fecha_modificacion",
            col_type=ColumnType.DATETIME,
            required=False,
            nullable=True,
        ),
        ColumnDefinition(
            source_name="ID_USUARIO_REGISTRO",
            target_name="id_usuario_registro",
            col_type=ColumnType.INTEGER,
            required=False,
        ),
        ColumnDefinition(
            source_name="USER_REGISTRO",
            target_name="usuario_registro",
            col_type=ColumnType.STRING,
            required=False,
        ),
        # Grupo de evento (tipo de estudio: ITS, Bancos de Sangre, etc.)
        ColumnDefinition(
            source_name="ID_SNVS_GRP_EVENTO_AGRP",
            target_name="id_grupo_evento",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="NOMBRE",  # Nombre del grupo de evento
            target_name="nombre_grupo_evento",
            col_type=ColumnType.STRING,
            required=True,
        ),
        # Evento específico (agente etiológico)
        ColumnDefinition(
            source_name="ID_SNVS_EVENTO_AGRP",
            target_name="id_snvs_evento",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="EVENTO",  # Diferente: EVENTO vs NOMBREEVENTOAGRP
            target_name="nombre_evento",
            col_type=ColumnType.STRING,
            required=True,
        ),
        # Grupo etario
        ColumnDefinition(
            source_name="ID_SNVS_GRUPO_EDAD_AGRP",
            target_name="id_edad",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="EDAD NOMBRE",  # Con espacio!
            target_name="nombre_grupo_etario",
            col_type=ColumnType.STRING,
            required=True,
        ),
        # Sexo (21.7% completitud)
        ColumnDefinition(
            source_name="SEXO",
            target_name="sexo",
            col_type=ColumnType.STRING,
            required=False,
            nullable=True,
        ),
        # Flags
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
        # Valores principales (2 métricas)
        ColumnDefinition(
            source_name="ESTUDIADAS",  # En lugar de CANTIDAD
            target_name="estudiadas",
            col_type=ColumnType.INTEGER,
            required=True,
        ),
        ColumnDefinition(
            source_name="POSITIVAS",  # Solo 8.5% completitud
            target_name="positivas",
            col_type=ColumnType.FLOAT,
            required=False,
            nullable=True,
            default=0,
        ),
        # Fecha final
        ColumnDefinition(
            source_name="FECHA_REGISTRO2",
            target_name="fecha_registro_2",
            col_type=ColumnType.DATETIME,
            required=False,
        ),
    ],
)

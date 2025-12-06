#!/usr/bin/env python3
"""
Script para analizar establecimientos con más eventos y sugerir mapeos SNVS-IGN.

Este script:
1. Consulta los top 200 establecimientos con más eventos relacionados
2. Genera un listado detallado en formato texto
3. Sugiere mapeos automáticos entre establecimientos SNVS e IGN usando similitud de nombres
"""

import difflib
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Agregar el directorio raíz al path para imports
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


@dataclass
class Establecimiento:
    """Representa un establecimiento con sus eventos."""

    id: int
    nombre: str
    source: str
    codigo_refes: Optional[str]
    codigo_snvs: Optional[str]
    localidad_nombre: Optional[str]
    departamento_nombre: Optional[str]
    provincia_nombre: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    eventos_consulta: int
    eventos_notificacion: int
    eventos_carga: int
    eventos_muestra: int
    eventos_diagnostico: int
    eventos_tratamiento: int
    total_eventos: int


@dataclass
class MapeoSugerido:
    """Representa una sugerencia de mapeo SNVS-IGN."""

    snvs_nombre: str
    snvs_id: int
    ign_nombre: str
    ign_id: int
    ign_codigo_refes: str
    score: float
    razon: str
    localidad_snvs: Optional[str]
    localidad_ign: Optional[str]


def conectar_db() -> Session:
    """Conecta a la base de datos PostgreSQL."""
    # Dentro del contenedor Docker, el host es 'db' y el puerto es 5432
    database_url = "postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db"
    engine = create_engine(database_url, echo=False)
    return Session(engine)


def obtener_top_establecimientos(
    conn: Session, limit: int = 200
) -> List[Establecimiento]:
    """
    Obtiene los top N establecimientos ordenados por total de eventos.

    Consulta similar a la del endpoint list_con_eventos.py pero más simple.
    """
    query = """
    WITH eventos_consulta AS (
        SELECT
            id_establecimiento_consulta as id_estab,
            COUNT(*) as count
        FROM evento
        WHERE id_establecimiento_consulta IS NOT NULL
        GROUP BY id_establecimiento_consulta
    ),
    eventos_notif AS (
        SELECT
            id_establecimiento_notificacion as id_estab,
            COUNT(*) as count
        FROM evento
        WHERE id_establecimiento_notificacion IS NOT NULL
        GROUP BY id_establecimiento_notificacion
    ),
    eventos_carga AS (
        SELECT
            id_establecimiento_carga as id_estab,
            COUNT(*) as count
        FROM evento
        WHERE id_establecimiento_carga IS NOT NULL
        GROUP BY id_establecimiento_carga
    ),
    muestras AS (
        SELECT
            id_establecimiento as id_estab,
            COUNT(*) as count
        FROM muestra_evento
        WHERE id_establecimiento IS NOT NULL
        GROUP BY id_establecimiento
    ),
    diagnosticos AS (
        SELECT
            id_establecimiento_diagnostico as id_estab,
            COUNT(*) as count
        FROM diagnostico_evento
        WHERE id_establecimiento_diagnostico IS NOT NULL
        GROUP BY id_establecimiento_diagnostico
    ),
    tratamientos AS (
        SELECT
            id_establecimiento_tratamiento as id_estab,
            COUNT(*) as count
        FROM tratamiento_evento
        WHERE id_establecimiento_tratamiento IS NOT NULL
        GROUP BY id_establecimiento_tratamiento
    )
    SELECT
        e.id,
        e.nombre,
        e.source,
        e.codigo_refes,
        e.codigo_snvs,
        l.nombre as localidad_nombre,
        d.nombre as departamento_nombre,
        p.nombre as provincia_nombre,
        e.latitud,
        e.longitud,
        COALESCE(ec.count, 0) as eventos_consulta,
        COALESCE(en.count, 0) as eventos_notificacion,
        COALESCE(eca.count, 0) as eventos_carga,
        COALESCE(m.count, 0) as eventos_muestra,
        COALESCE(diag.count, 0) as eventos_diagnostico,
        COALESCE(trat.count, 0) as eventos_tratamiento,
        COALESCE(ec.count, 0) +
        COALESCE(en.count, 0) +
        COALESCE(eca.count, 0) +
        COALESCE(m.count, 0) +
        COALESCE(diag.count, 0) +
        COALESCE(trat.count, 0) as total_eventos
    FROM establecimiento e
    LEFT JOIN localidad l ON e.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    LEFT JOIN provincia p ON d.id_provincia_indec = p.id_provincia_indec
    LEFT JOIN eventos_consulta ec ON e.id = ec.id_estab
    LEFT JOIN eventos_notif en ON e.id = en.id_estab
    LEFT JOIN eventos_carga eca ON e.id = eca.id_estab
    LEFT JOIN muestras m ON e.id = m.id_estab
    LEFT JOIN diagnosticos diag ON e.id = diag.id_estab
    LEFT JOIN tratamientos trat ON e.id = trat.id_estab
    ORDER BY total_eventos DESC
    LIMIT :limit
    """

    result = conn.execute(text(query), {"limit": limit})
    rows = result.fetchall()

    # Convertir Row a dict
    establecimientos = []
    for row in rows:
        establecimientos.append(
            Establecimiento(
                id=int(row.id),
                nombre=str(row.nombre),
                source=str(row.source),
                codigo_refes=str(row.codigo_refes)
                if row.codigo_refes is not None
                else None,
                codigo_snvs=str(row.codigo_snvs)
                if row.codigo_snvs is not None
                else None,
                localidad_nombre=str(row.localidad_nombre)
                if row.localidad_nombre is not None
                else None,
                departamento_nombre=str(row.departamento_nombre)
                if row.departamento_nombre is not None
                else None,
                provincia_nombre=str(row.provincia_nombre)
                if row.provincia_nombre is not None
                else None,
                latitud=float(row.latitud) if row.latitud is not None else None,
                longitud=float(row.longitud) if row.longitud is not None else None,
                eventos_consulta=int(row.eventos_consulta),
                eventos_notificacion=int(row.eventos_notificacion),
                eventos_carga=int(row.eventos_carga),
                eventos_muestra=int(row.eventos_muestra),
                eventos_diagnostico=int(row.eventos_diagnostico),
                eventos_tratamiento=int(row.eventos_tratamiento),
                total_eventos=int(row.total_eventos),
            )
        )

    return establecimientos


def obtener_todos_ign(conn: Session) -> List[Establecimiento]:
    """
    Obtiene TODOS los establecimientos IGN para usar como candidatos en matching.
    No necesitamos los conteos de eventos, solo los datos básicos.
    """
    query = """
    SELECT
        e.id,
        e.nombre,
        e.source,
        e.codigo_refes,
        e.codigo_snvs,
        l.nombre as localidad_nombre,
        d.nombre as departamento_nombre,
        p.nombre as provincia_nombre,
        e.latitud,
        e.longitud,
        0 as eventos_consulta,
        0 as eventos_notificacion,
        0 as eventos_carga,
        0 as eventos_muestra,
        0 as eventos_diagnostico,
        0 as eventos_tratamiento,
        0 as total_eventos
    FROM establecimiento e
    LEFT JOIN localidad l ON e.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    LEFT JOIN provincia p ON d.id_provincia_indec = p.id_provincia_indec
    WHERE e.source = 'IGN'
    """

    result = conn.execute(text(query))
    rows = result.fetchall()

    establecimientos = []
    for row in rows:
        establecimientos.append(
            Establecimiento(
                id=int(row.id),
                nombre=str(row.nombre),
                source=str(row.source),
                codigo_refes=str(row.codigo_refes)
                if row.codigo_refes is not None
                else None,
                codigo_snvs=str(row.codigo_snvs)
                if row.codigo_snvs is not None
                else None,
                localidad_nombre=str(row.localidad_nombre)
                if row.localidad_nombre is not None
                else None,
                departamento_nombre=str(row.departamento_nombre)
                if row.departamento_nombre is not None
                else None,
                provincia_nombre=str(row.provincia_nombre)
                if row.provincia_nombre is not None
                else None,
                latitud=float(row.latitud) if row.latitud is not None else None,
                longitud=float(row.longitud) if row.longitud is not None else None,
                eventos_consulta=0,
                eventos_notificacion=0,
                eventos_carga=0,
                eventos_muestra=0,
                eventos_diagnostico=0,
                eventos_tratamiento=0,
                total_eventos=0,
            )
        )

    return establecimientos


def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre de establecimiento para comparación."""
    if not nombre:
        return ""

    # Convertir a minúsculas
    nombre = nombre.lower()

    # Reemplazos comunes
    reemplazos = {
        "hosp.": "hospital",
        "ctro.": "centro",
        "cs": "centro de salud",
        "caps": "centro de atencion primaria",
        "samic": "servicio de atencion medica integral",
    }

    for abrev, completo in reemplazos.items():
        nombre = nombre.replace(abrev, completo)

    # Remover caracteres especiales comunes
    nombre = nombre.replace("-", " ").replace("_", " ")

    # Normalizar espacios
    nombre = " ".join(nombre.split())

    return nombre


def calcular_similitud_nombre(nombre1: str, nombre2: str) -> float:
    """
    Calcula similitud entre dos nombres usando SequenceMatcher.

    Retorna un score de 0 a 100.
    """
    if not nombre1 or not nombre2:
        return 0.0

    norm1 = normalizar_nombre(nombre1)
    norm2 = normalizar_nombre(nombre2)

    # Similitud básica
    similitud = difflib.SequenceMatcher(None, norm1, norm2).ratio()

    # Bonus si uno contiene al otro (puede ser nombre completo vs abreviado)
    if norm1 in norm2 or norm2 in norm1:
        similitud = max(similitud, 0.85)

    return similitud * 100


def calcular_distancia_geografica(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calcula distancia aproximada en km usando fórmula haversine simplificada.
    """
    from math import atan2, cos, radians, sin, sqrt

    R = 6371  # Radio de la Tierra en km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def encontrar_mejores_matches(
    snvs_estab: Establecimiento,
    ign_establecimientos: List[Establecimiento],
    top_n: int = 3,
) -> List[MapeoSugerido]:
    """
    Encuentra los mejores N matches de IGN para un establecimiento SNVS.

    Mejoras v2:
    - Filtrar por provincia (descarta si son diferentes)
    - Dar bonus fuerte si departamento coincide
    - Penalizar menos si no hay localidad en IGN
    """
    candidatos = []

    for ign in ign_establecimientos:
        # FILTRO CRÍTICO: Si las provincias son diferentes y ambas están definidas, skip
        if (
            snvs_estab.provincia_nombre
            and ign.provincia_nombre
            and snvs_estab.provincia_nombre.lower() != ign.provincia_nombre.lower()
        ):
            continue  # Descarta este candidato

        # Score base: similitud de nombre (60% del peso, reducido para dar más peso a geografía)
        score_nombre = calcular_similitud_nombre(snvs_estab.nombre, ign.nombre)
        score = score_nombre * 0.6

        razones = [f"similitud nombre: {score_nombre:.1f}%"]

        # Bonus por provincia coincidente (10% del peso)
        if (
            snvs_estab.provincia_nombre
            and ign.provincia_nombre
            and snvs_estab.provincia_nombre.lower() == ign.provincia_nombre.lower()
        ):
            score += 10
            razones.append(f"provincia: {snvs_estab.provincia_nombre}")

        # Bonus por departamento coincidente (15% del peso)
        if (
            snvs_estab.departamento_nombre
            and ign.departamento_nombre
            and snvs_estab.departamento_nombre.lower()
            == ign.departamento_nombre.lower()
        ):
            score += 15
            razones.append(f"mismo depto: {snvs_estab.departamento_nombre}")

        # Bonus por localidad coincidente (15% del peso)
        if (
            snvs_estab.localidad_nombre
            and ign.localidad_nombre
            and snvs_estab.localidad_nombre.lower() == ign.localidad_nombre.lower()
        ):
            score += 15
            razones.append("misma localidad")

        # Si score de nombre es perfecto (100%) y departamento coincide, es muy confiable
        if (
            score_nombre == 100
            and snvs_estab.departamento_nombre
            and ign.departamento_nombre
            and snvs_estab.departamento_nombre.lower()
            == ign.departamento_nombre.lower()
        ):
            score = max(score, 85)  # Garantizar alta confianza

        if score >= 50:  # Solo considerar si score mínimo
            candidatos.append(
                MapeoSugerido(
                    snvs_nombre=snvs_estab.nombre,
                    snvs_id=snvs_estab.id,
                    ign_nombre=ign.nombre,
                    ign_id=ign.id,
                    ign_codigo_refes=ign.codigo_refes or "N/A",
                    score=score,
                    razon=" + ".join(razones),
                    localidad_snvs=snvs_estab.localidad_nombre,
                    localidad_ign=ign.localidad_nombre,
                )
            )

    # Ordenar por score descendente y retornar top N
    candidatos.sort(key=lambda x: x.score, reverse=True)
    return candidatos[:top_n]


def generar_reporte(
    establecimientos: List[Establecimiento],
    mapeos_sugeridos: List[MapeoSugerido],
    output_path: str,
) -> None:
    """Genera el archivo de reporte en formato texto."""

    # Separar por source
    ign_estabs = [e for e in establecimientos if e.source == "IGN"]
    snvs_estabs = [e for e in establecimientos if e.source == "SNVS"]

    # Contar SNVS mapeados vs no mapeados
    snvs_mapeados = [e for e in snvs_estabs if e.codigo_refes]
    snvs_no_mapeados = [e for e in snvs_estabs if not e.codigo_refes]

    with open(output_path, "w", encoding="utf-8") as f:
        # ===== SECCIÓN 1: RESUMEN ESTADÍSTICO =====
        f.write("=" * 80 + "\n")
        f.write("ANÁLISIS DE TOP 200 ESTABLECIMIENTOS CON MÁS EVENTOS\n")
        f.write("=" * 80 + "\n\n")

        f.write("RESUMEN GENERAL:\n")
        f.write(f"  • Total establecimientos analizados: {len(establecimientos)}\n")
        f.write(f"  • Establecimientos IGN: {len(ign_estabs)}\n")
        f.write(f"  • Establecimientos SNVS: {len(snvs_estabs)}\n")
        f.write(f"    - SNVS mapeados a IGN: {len(snvs_mapeados)}\n")
        f.write(f"    - SNVS sin mapear: {len(snvs_no_mapeados)}\n\n")

        if establecimientos:
            total_eventos = sum(e.total_eventos for e in establecimientos)
            max_eventos = max(e.total_eventos for e in establecimientos)
            min_eventos = min(e.total_eventos for e in establecimientos)
            promedio = total_eventos // len(establecimientos)

            f.write("EVENTOS:\n")
            f.write(f"  • Total eventos: {total_eventos:,}\n")
            f.write(f"  • Rango: {min_eventos} - {max_eventos:,} eventos\n")
            f.write(f"  • Promedio: {promedio:,} eventos por establecimiento\n\n")

        # Distribución geográfica
        provincias = defaultdict(int)
        for e in establecimientos:
            if e.provincia_nombre:
                provincias[e.provincia_nombre] += 1

        if provincias:
            f.write("DISTRIBUCIÓN GEOGRÁFICA (Top 5 provincias):\n")
            for prov, count in sorted(
                provincias.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                f.write(f"  • {prov}: {count} establecimientos\n")
            f.write("\n")

        # ===== SECCIÓN 2: LISTADO DETALLADO =====
        f.write("\n" + "=" * 80 + "\n")
        f.write("LISTADO DETALLADO DE ESTABLECIMIENTOS\n")
        f.write("=" * 80 + "\n\n")

        # Establecimientos IGN
        if ign_estabs:
            f.write(f"\n{'─' * 80}\n")
            f.write(f"ESTABLECIMIENTOS IGN ({len(ign_estabs)} establecimientos)\n")
            f.write(f"{'─' * 80}\n\n")

            for e in ign_estabs:
                f.write(f"• [{e.id}] {e.nombre}\n")
                f.write(f"  SOURCE: {e.source} | REFES: {e.codigo_refes or 'N/A'}")
                if e.codigo_snvs:
                    f.write(f" | SNVS: {e.codigo_snvs}")
                f.write("\n")

                ubicacion_parts = []
                if e.localidad_nombre:
                    ubicacion_parts.append(e.localidad_nombre)
                if e.departamento_nombre:
                    ubicacion_parts.append(e.departamento_nombre)
                if e.provincia_nombre:
                    ubicacion_parts.append(e.provincia_nombre)

                f.write(
                    f"  UBICACIÓN: {', '.join(ubicacion_parts) if ubicacion_parts else 'N/A'}\n"
                )

                if e.latitud and e.longitud:
                    f.write(f"  COORDENADAS: {e.latitud:.4f}, {e.longitud:.4f}\n")

                f.write(f"  EVENTOS: {e.total_eventos:,} total ")
                f.write(
                    f"(consulta: {e.eventos_consulta}, notificación: {e.eventos_notificacion}, "
                )
                f.write(f"carga: {e.eventos_carga}, muestra: {e.eventos_muestra}, ")
                f.write(
                    f"diagnóstico: {e.eventos_diagnostico}, tratamiento: {e.eventos_tratamiento})\n\n"
                )

        # Establecimientos SNVS
        if snvs_estabs:
            f.write(f"\n{'─' * 80}\n")
            f.write(f"ESTABLECIMIENTOS SNVS ({len(snvs_estabs)} establecimientos)\n")
            f.write(f"{'─' * 80}\n\n")

            for e in snvs_estabs:
                mapeo_status = "✓ MAPEADO" if e.codigo_refes else "✗ SIN MAPEAR"
                f.write(f"• [{e.id}] {e.nombre} [{mapeo_status}]\n")
                f.write(f"  SOURCE: {e.source} | SNVS: {e.codigo_snvs or 'N/A'}")
                if e.codigo_refes:
                    f.write(f" | REFES: {e.codigo_refes}")
                f.write("\n")

                ubicacion_parts = []
                if e.localidad_nombre:
                    ubicacion_parts.append(e.localidad_nombre)
                if e.departamento_nombre:
                    ubicacion_parts.append(e.departamento_nombre)
                if e.provincia_nombre:
                    ubicacion_parts.append(e.provincia_nombre)

                f.write(
                    f"  UBICACIÓN: {', '.join(ubicacion_parts) if ubicacion_parts else 'N/A'}\n"
                )

                if e.latitud and e.longitud:
                    f.write(f"  COORDENADAS: {e.latitud:.4f}, {e.longitud:.4f}\n")

                f.write(f"  EVENTOS: {e.total_eventos:,} total ")
                f.write(
                    f"(consulta: {e.eventos_consulta}, notificación: {e.eventos_notificacion}, "
                )
                f.write(f"carga: {e.eventos_carga}, muestra: {e.eventos_muestra}, ")
                f.write(
                    f"diagnóstico: {e.eventos_diagnostico}, tratamiento: {e.eventos_tratamiento})\n\n"
                )

        # ===== SECCIÓN 3: SUGERENCIAS DE MAPEO =====
        if mapeos_sugeridos:
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUGERENCIAS DE MAPEO SNVS → IGN\n")
            f.write("=" * 80 + "\n\n")

            # Separar por nivel de confianza
            alta_confianza = [m for m in mapeos_sugeridos if m.score >= 85]
            media_confianza = [m for m in mapeos_sugeridos if 70 <= m.score < 85]
            baja_confianza = [m for m in mapeos_sugeridos if 50 <= m.score < 70]

            if alta_confianza:
                f.write(f"\n{'─' * 80}\n")
                f.write(
                    f"MAPEOS DE ALTA CONFIANZA (score ≥ 85) - {len(alta_confianza)} sugerencias\n"
                )
                f.write(f"{'─' * 80}\n\n")

                for m in alta_confianza:
                    f.write(f'• SNVS: "{m.snvs_nombre}" [ID: {m.snvs_id}]\n')
                    f.write(f'  → IGN: "{m.ign_nombre}" [ID: {m.ign_id}]\n')
                    f.write(f"  Score: {m.score:.1f} | Razón: {m.razon}\n")
                    f.write(f"  REFES: {m.ign_codigo_refes}\n")
                    if m.localidad_snvs or m.localidad_ign:
                        f.write(f"  Localidad SNVS: {m.localidad_snvs or 'N/A'} | ")
                        f.write(f"Localidad IGN: {m.localidad_ign or 'N/A'}\n")
                    f.write("\n")

            if media_confianza:
                f.write(f"\n{'─' * 80}\n")
                f.write(
                    f"MAPEOS DE CONFIANZA MEDIA (score 70-84) - {len(media_confianza)} sugerencias\n"
                )
                f.write(f"{'─' * 80}\n\n")

                for m in media_confianza:
                    f.write(f'• SNVS: "{m.snvs_nombre}" [ID: {m.snvs_id}]\n')
                    f.write(f'  → IGN: "{m.ign_nombre}" [ID: {m.ign_id}]\n')
                    f.write(f"  Score: {m.score:.1f} | Razón: {m.razon}\n")
                    f.write(f"  REFES: {m.ign_codigo_refes}\n")
                    if m.localidad_snvs or m.localidad_ign:
                        f.write(f"  Localidad SNVS: {m.localidad_snvs or 'N/A'} | ")
                        f.write(f"Localidad IGN: {m.localidad_ign or 'N/A'}\n")
                    f.write("\n")

            if baja_confianza:
                f.write(f"\n{'─' * 80}\n")
                f.write(
                    f"MAPEOS DE BAJA CONFIANZA (score 50-69) - {len(baja_confianza)} sugerencias\n"
                )
                f.write(f"{'─' * 80}\n\n")

                for m in baja_confianza:
                    f.write(f'• SNVS: "{m.snvs_nombre}" [ID: {m.snvs_id}]\n')
                    f.write(f'  → IGN: "{m.ign_nombre}" [ID: {m.ign_id}]\n')
                    f.write(f"  Score: {m.score:.1f} | Razón: {m.razon}\n")
                    f.write(f"  REFES: {m.ign_codigo_refes}\n")
                    if m.localidad_snvs or m.localidad_ign:
                        f.write(f"  Localidad SNVS: {m.localidad_snvs or 'N/A'} | ")
                        f.write(f"Localidad IGN: {m.localidad_ign or 'N/A'}\n")
                    f.write("\n")

            # Estadísticas finales
            f.write(f"\n{'─' * 80}\n")
            f.write("ESTADÍSTICAS DE MAPEO\n")
            f.write(f"{'─' * 80}\n\n")

            # Contar SNVS únicos en sugerencias
            snvs_unicos = len(set(m.snvs_id for m in mapeos_sugeridos))

            f.write(f"  • Total SNVS sin mapear en top 200: {len(snvs_no_mapeados)}\n")
            f.write(f"  • SNVS con sugerencias encontradas: {snvs_unicos}\n")
            f.write(f"  • Mapeos sugeridos con score ≥ 85: {len(alta_confianza)}\n")
            f.write(
                f"  • Mapeos sugeridos con score ≥ 70: {len(alta_confianza) + len(media_confianza)}\n"
            )
            f.write(f"  • Total sugerencias: {len(mapeos_sugeridos)}\n\n")

            # Calcular potencial cobertura
            if snvs_no_mapeados:
                cobertura_alta = (
                    len(set(m.snvs_id for m in alta_confianza)) / len(snvs_no_mapeados)
                ) * 100
                cobertura_media = (
                    len(set(m.snvs_id for m in alta_confianza + media_confianza))
                    / len(snvs_no_mapeados)
                ) * 100

                f.write(
                    f"  • Potencial cobertura con alta confianza: +{cobertura_alta:.1f}%\n"
                )
                f.write(
                    f"  • Potencial cobertura con media-alta confianza: +{cobertura_media:.1f}%\n"
                )


def main() -> None:
    """Función principal del script."""
    print("Conectando a la base de datos...")
    conn = conectar_db()

    try:
        print("Consultando top 200 establecimientos...")
        establecimientos = obtener_top_establecimientos(conn, limit=200)
        print(f"  ✓ Obtenidos {len(establecimientos)} establecimientos")

        # Separar IGN y SNVS
        ign_establecimientos = [e for e in establecimientos if e.source == "IGN"]
        snvs_establecimientos = [e for e in establecimientos if e.source == "SNVS"]
        snvs_no_mapeados = [e for e in snvs_establecimientos if not e.codigo_refes]

        print(
            f"  ✓ IGN: {len(ign_establecimientos)}, SNVS: {len(snvs_establecimientos)}"
        )
        print(f"  ✓ SNVS sin mapear: {len(snvs_no_mapeados)}")

        # Obtener TODOS los establecimientos IGN para matching (no solo los del top 200)
        print("\nCargando todos los establecimientos IGN para matching...")
        todos_ign = obtener_todos_ign(conn)
        print(f"  ✓ Cargados {len(todos_ign)} establecimientos IGN")

        # Buscar matches para SNVS no mapeados
        print("\nBuscando mapeos automáticos para SNVS sin mapear...")
        mapeos_sugeridos = []

        for i, snvs in enumerate(snvs_no_mapeados, 1):
            if i % 10 == 0:
                print(f"  Procesando {i}/{len(snvs_no_mapeados)}...")

            # Usar TODOS los IGN, no solo los del top 200
            matches = encontrar_mejores_matches(snvs, todos_ign, top_n=3)
            mapeos_sugeridos.extend(matches)

        print(f"  ✓ Encontradas {len(mapeos_sugeridos)} sugerencias de mapeo")

        # Ordenar por score
        mapeos_sugeridos.sort(key=lambda x: x.score, reverse=True)

        # Generar reporte
        output_path = backend_dir / "temp" / "establecimientos.txt"
        print(f"\nGenerando reporte en {output_path}...")
        generar_reporte(establecimientos, mapeos_sugeridos, str(output_path))
        print("  ✓ Reporte generado exitosamente")

        # Resumen en consola
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"Total establecimientos analizados: {len(establecimientos)}")
        print(f"SNVS sin mapear: {len(snvs_no_mapeados)}")
        print(f"Sugerencias de mapeo encontradas: {len(mapeos_sugeridos)}")
        alta = len([m for m in mapeos_sugeridos if m.score >= 85])
        media = len([m for m in mapeos_sugeridos if 70 <= m.score < 85])
        print(f"  - Alta confianza (≥85): {alta}")
        print(f"  - Media confianza (70-84): {media}")
        print(f"\nReporte completo disponible en:\n  {output_path}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

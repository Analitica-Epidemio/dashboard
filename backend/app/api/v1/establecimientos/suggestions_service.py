"""Servicio de sugerencias automáticas para mapeo de establecimientos SNVS → IGN."""

import unicodedata
from difflib import SequenceMatcher
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlmodel import Session

from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para matching:
    - Convierte a mayúsculas
    - Remueve acentos/tildes usando NFD decomposition
    - Remueve puntuación innecesaria
    """
    if not texto:
        return ""

    texto = texto.upper()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
    texto = texto.replace('.', ' ').replace(',', ' ').replace('-', ' ')
    texto = ' '.join(texto.split())

    return texto.strip()


def calcular_similitud_nombre(nombre1: str, nombre2: str) -> float:
    """Calcula porcentaje de similitud entre dos nombres (0-100)."""
    if not nombre1 or not nombre2:
        return 0.0

    nombre1_norm = normalizar_texto(nombre1)
    nombre2_norm = normalizar_texto(nombre2)

    ratio = SequenceMatcher(None, nombre1_norm, nombre2_norm).ratio()
    return round(ratio * 100, 1)


def calcular_score_match(
    similitud_nombre: float,
    provincia_match: bool,
    departamento_match: bool,
    localidad_match: bool
) -> float:
    """
    Calcula score total de match (0-100):
    - 60% similitud de nombre
    - 10% provincia
    - 15% departamento
    - 15% localidad
    """
    score = (similitud_nombre * 0.6)
    if provincia_match:
        score += 10
    if departamento_match:
        score += 15
    if localidad_match:
        score += 15

    return round(score, 1)


def determinar_confianza(score: float, similitud_nombre: float) -> str:
    """Determina nivel de confianza basado en score y similitud."""
    if score >= 85 or similitud_nombre >= 90:
        return "HIGH"
    elif score >= 70 or similitud_nombre >= 75:
        return "MEDIUM"
    else:
        return "LOW"


def generar_razon_match(
    similitud_nombre: float,
    provincia_match: bool,
    departamento_match: bool,
    localidad_match: bool,
    provincia_snvs: Optional[str] = None,
    departamento_snvs: Optional[str] = None,
    localidad_snvs: Optional[str] = None
) -> str:
    """Genera descripción legible de la razón del match."""
    partes = [f"similitud nombre: {similitud_nombre}%"]

    if provincia_match and provincia_snvs:
        partes.append(f"provincia: {provincia_snvs}")

    if departamento_match and departamento_snvs:
        partes.append(f"mismo depto: {departamento_snvs}")

    if localidad_match and localidad_snvs:
        partes.append("misma localidad")

    return " + ".join(partes)


async def buscar_sugerencias_para_establecimiento(
    session: Session,
    nombre_snvs: str,
    provincia_nombre_snvs: Optional[str],
    departamento_nombre_snvs: Optional[str],
    localidad_nombre_snvs: Optional[str],
    limit: int = 5
) -> List[dict]:
    """
    Busca sugerencias de establecimientos IGN para un establecimiento SNVS.

    Args:
        session: Sesión de base de datos
        nombre_snvs: Nombre del establecimiento SNVS
        provincia_nombre_snvs: Nombre de provincia del establecimiento SNVS
        departamento_nombre_snvs: Nombre de departamento del establecimiento SNVS
        localidad_nombre_snvs: Nombre de localidad del establecimiento SNVS
        limit: Número máximo de sugerencias a retornar

    Returns:
        Lista de sugerencias ordenadas por score descendente
    """
    # Buscar establecimientos IGN
    query = (
        select(
            Establecimiento,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.nombre.label("departamento_nombre"),
            Provincia.nombre.label("provincia_nombre")
        )
        .outerjoin(Localidad, Establecimiento.id_localidad_indec == Localidad.id_localidad_indec)
        .outerjoin(Departamento, Localidad.id_departamento_indec == Departamento.id_departamento_indec)
        .outerjoin(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        .where(Establecimiento.source == "IGN")
    )

    # Filtrar por provincia si está disponible
    if provincia_nombre_snvs:
        query = query.where(
            or_(
                Provincia.nombre == provincia_nombre_snvs,
                Provincia.nombre.is_(None)  # Incluir también los que no tienen provincia
            )
        )

    result = session.exec(query).all()

    sugerencias = []

    for row in result:
        estab_ign = row[0]
        localidad_nombre = row[1]
        departamento_nombre = row[2]
        provincia_nombre = row[3]

        # Calcular similitud de nombre
        similitud_nombre = calcular_similitud_nombre(nombre_snvs, estab_ign.nombre or "")

        # Skip si similitud es muy baja (< 50%)
        if similitud_nombre < 50:
            continue

        # Verificar matches geográficos
        provincia_match = (
            provincia_nombre_snvs and provincia_nombre and
            normalizar_texto(provincia_nombre_snvs) == normalizar_texto(provincia_nombre)
        )
        departamento_match = (
            departamento_nombre_snvs and departamento_nombre and
            normalizar_texto(departamento_nombre_snvs) == normalizar_texto(departamento_nombre)
        )
        localidad_match = (
            localidad_nombre_snvs and localidad_nombre and
            normalizar_texto(localidad_nombre_snvs) == normalizar_texto(localidad_nombre)
        )

        # Calcular score
        score = calcular_score_match(
            similitud_nombre,
            provincia_match,
            departamento_match,
            localidad_match
        )

        # Determinar confianza
        confianza = determinar_confianza(score, similitud_nombre)

        # Generar razón
        razon = generar_razon_match(
            similitud_nombre,
            provincia_match,
            departamento_match,
            localidad_match,
            provincia_nombre,
            departamento_nombre,
            localidad_nombre_snvs
        )

        sugerencias.append({
            "id_establecimiento_ign": estab_ign.id,
            "nombre_ign": estab_ign.nombre,
            "codigo_refes": estab_ign.codigo_refes,
            "localidad_nombre": localidad_nombre,
            "departamento_nombre": departamento_nombre,
            "provincia_nombre": provincia_nombre,
            "similitud_nombre": similitud_nombre,
            "score": score,
            "confianza": confianza,
            "razon": razon,
            "provincia_match": provincia_match,
            "departamento_match": departamento_match,
            "localidad_match": localidad_match,
        })

    # Ordenar por score descendente y retornar top N
    sugerencias.sort(key=lambda x: x["score"], reverse=True)
    return sugerencias[:limit]


async def buscar_establecimientos_ign(
    session: Session,
    query: Optional[str] = None,
    provincia_nombre: Optional[str] = None,
    departamento_nombre: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[List[dict], int]:
    """
    Busca establecimientos IGN con filtros.

    Returns:
        Tupla (lista de establecimientos, total_count)
    """
    # Construir query base
    base_query = (
        select(
            Establecimiento,
            Localidad.nombre.label("localidad_nombre"),
            Departamento.nombre.label("departamento_nombre"),
            Provincia.nombre.label("provincia_nombre")
        )
        .outerjoin(Localidad, Establecimiento.id_localidad_indec == Localidad.id_localidad_indec)
        .outerjoin(Departamento, Localidad.id_departamento_indec == Departamento.id_departamento_indec)
        .outerjoin(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
        .where(Establecimiento.source == "IGN")
    )

    # Aplicar filtros
    if query:
        query_norm = normalizar_texto(query)
        # Buscar en nombre o código REFES
        base_query = base_query.where(
            or_(
                func.upper(func.unaccent(Establecimiento.nombre)).contains(query_norm),
                Establecimiento.codigo_refes.contains(query)
            )
        )

    if provincia_nombre:
        base_query = base_query.where(Provincia.nombre == provincia_nombre)

    if departamento_nombre:
        base_query = base_query.where(Departamento.nombre == departamento_nombre)

    # Contar total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = session.exec(count_query).one()

    # Obtener resultados paginados
    results_query = base_query.offset(offset).limit(limit)
    results = session.exec(results_query).all()

    establecimientos = []
    for row in results:
        estab = row[0]
        establecimientos.append({
            "id": estab.id,
            "nombre": estab.nombre,
            "codigo_refes": estab.codigo_refes,
            "localidad_nombre": row[1],
            "departamento_nombre": row[2],
            "provincia_nombre": row[3],
            "latitud": estab.latitud,
            "longitud": estab.longitud,
        })

    return establecimientos, total

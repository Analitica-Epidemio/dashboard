"""
Router de Geografía - Endpoints para GeoJSON de provincias y departamentos.

Sirve geometrías desde la base de datos PostGIS para mapas coropléticos.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter(prefix="/geografia", tags=["Geografía"])


@router.get("/provincias/geojson")
async def get_provincias_geojson(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Retorna todas las provincias como GeoJSON FeatureCollection.

    Incluye geometría (MultiPolygon) y propiedades básicas.
    Solo retorna provincias que tienen geometría cargada.
    """
    query = text("""
        SELECT
            id_provincia_indec,
            nombre,
            poblacion,
            latitud,
            longitud,
            ST_AsGeoJSON(geometria)::json as geometry
        FROM provincia
        WHERE geometria IS NOT NULL
        ORDER BY nombre
    """)

    result = await session.execute(query)
    rows = result.fetchall()

    features = []
    for row in rows:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": row.id_provincia_indec,
                    "id_provincia_indec": row.id_provincia_indec,
                    "nombre": row.nombre,
                    "poblacion": row.poblacion,
                    "centroide": {
                        "lat": row.latitud,
                        "lon": row.longitud,
                    }
                    if row.latitud and row.longitud
                    else None,
                },
                "geometry": row.geometry,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/provincias/geojson-con-eventos")
async def get_provincias_con_eventos(
    id_grupo: int | None = Query(None, description="Filtrar por grupo ENO"),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Retorna provincias con conteo de eventos para mapa coroplético.

    Incluye total_eventos y total_casos en properties para colorear el mapa.
    """
    params: dict[str, Any] = {}

    evento_join_condition = ""
    if id_grupo:
        evento_join_condition = "AND e.id_grupo = :id_grupo"
        params["id_grupo"] = id_grupo

    query = text(f"""
        SELECT
            p.id_provincia_indec,
            p.nombre,
            p.poblacion,
            p.latitud,
            p.longitud,
            ST_AsGeoJSON(p.geometria)::json as geometry,
            COALESCE(stats.total_eventos, 0) as total_eventos,
            COALESCE(stats.total_casos, 0) as total_casos
        FROM provincia p
        LEFT JOIN (
            SELECT
                d.id_provincia_indec,
                COUNT(DISTINCT e.id) as total_eventos,
                COUNT(DISTINCT e.codigo_ciudadano) as total_casos
            FROM departamento d
            JOIN localidad l ON l.id_departamento_indec = d.id_departamento_indec
            JOIN domicilio dom ON dom.id_localidad_indec = l.id_localidad_indec
            JOIN evento e ON e.id_domicilio = dom.id
            WHERE 1=1 {evento_join_condition}
            GROUP BY d.id_provincia_indec
        ) stats ON stats.id_provincia_indec = p.id_provincia_indec
        WHERE p.geometria IS NOT NULL
        ORDER BY p.nombre
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()

    features = []
    max_eventos = 0

    for row in rows:
        if row.total_eventos > max_eventos:
            max_eventos = row.total_eventos

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": row.id_provincia_indec,
                    "id_provincia_indec": row.id_provincia_indec,
                    "nombre": row.nombre,
                    "poblacion": row.poblacion,
                    "total_eventos": row.total_eventos,
                    "total_casos": row.total_casos,
                    "tasa_incidencia": round(
                        row.total_casos / row.poblacion * 100000, 2
                    )
                    if row.poblacion
                    else None,
                    "centroide": {
                        "lat": row.latitud,
                        "lon": row.longitud,
                    }
                    if row.latitud and row.longitud
                    else None,
                },
                "geometry": row.geometry,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "max_eventos": max_eventos,
            "total_provincias": len(features),
        },
    }


@router.get("/departamentos/geojson")
async def get_departamentos_geojson(
    id_provincia_indec: int | None = Query(None, description="Filtrar por provincia"),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Retorna departamentos como GeoJSON FeatureCollection.

    Opcionalmente filtrado por provincia.
    Solo retorna departamentos que tienen geometría cargada.
    """
    if id_provincia_indec:
        query = text("""
            SELECT
                d.id_departamento_indec,
                d.id_provincia_indec,
                d.nombre,
                d.poblacion,
                d.latitud,
                d.longitud,
                p.nombre as provincia_nombre,
                ST_AsGeoJSON(d.geometria)::json as geometry
            FROM departamento d
            JOIN provincia p ON p.id_provincia_indec = d.id_provincia_indec
            WHERE d.geometria IS NOT NULL
              AND d.id_provincia_indec = :id_provincia
            ORDER BY d.nombre
        """)
        result = await session.execute(query, {"id_provincia": id_provincia_indec})
    else:
        query = text("""
            SELECT
                d.id_departamento_indec,
                d.id_provincia_indec,
                d.nombre,
                d.poblacion,
                d.latitud,
                d.longitud,
                p.nombre as provincia_nombre,
                ST_AsGeoJSON(d.geometria)::json as geometry
            FROM departamento d
            JOIN provincia p ON p.id_provincia_indec = d.id_provincia_indec
            WHERE d.geometria IS NOT NULL
            ORDER BY p.nombre, d.nombre
        """)
        result = await session.execute(query)

    rows = result.fetchall()

    features = []
    for row in rows:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": row.id_departamento_indec,
                    "id_departamento_indec": row.id_departamento_indec,
                    "id_provincia_indec": row.id_provincia_indec,
                    "nombre": row.nombre,
                    "provincia": row.provincia_nombre,
                    "poblacion": row.poblacion,
                    "centroide": {
                        "lat": row.latitud,
                        "lon": row.longitud,
                    }
                    if row.latitud and row.longitud
                    else None,
                },
                "geometry": row.geometry,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/departamentos/geojson-con-eventos")
async def get_departamentos_con_eventos(
    id_provincia_indec: int | None = Query(None, description="Filtrar por provincia"),
    id_grupo: int | None = Query(None, description="Filtrar por grupo ENO"),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Retorna departamentos con conteo de eventos para mapa coroplético.

    Incluye total_eventos y total_casos en properties para colorear el mapa.
    """
    # Query base con LEFT JOIN a eventos
    params: dict[str, Any] = {}

    where_clauses = ["d.geometria IS NOT NULL"]

    if id_provincia_indec:
        where_clauses.append("d.id_provincia_indec = :id_provincia")
        params["id_provincia"] = id_provincia_indec

    evento_join_condition = ""
    if id_grupo:
        evento_join_condition = "AND e.id_grupo = :id_grupo"
        params["id_grupo"] = id_grupo

    where_sql = " AND ".join(where_clauses)

    query = text(f"""
        SELECT
            d.id_departamento_indec,
            d.id_provincia_indec,
            d.nombre,
            d.poblacion,
            d.latitud,
            d.longitud,
            p.nombre as provincia_nombre,
            ST_AsGeoJSON(d.geometria)::json as geometry,
            COALESCE(stats.total_eventos, 0) as total_eventos,
            COALESCE(stats.total_casos, 0) as total_casos
        FROM departamento d
        JOIN provincia p ON p.id_provincia_indec = d.id_provincia_indec
        LEFT JOIN (
            SELECT
                l.id_departamento_indec,
                COUNT(DISTINCT e.id) as total_eventos,
                COUNT(DISTINCT e.codigo_ciudadano) as total_casos
            FROM localidad l
            JOIN domicilio dom ON dom.id_localidad_indec = l.id_localidad_indec
            JOIN evento e ON e.id_domicilio = dom.id
            WHERE 1=1 {evento_join_condition}
            GROUP BY l.id_departamento_indec
        ) stats ON stats.id_departamento_indec = d.id_departamento_indec
        WHERE {where_sql}
        ORDER BY p.nombre, d.nombre
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()

    features = []
    max_eventos = 0

    for row in rows:
        if row.total_eventos > max_eventos:
            max_eventos = row.total_eventos

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": row.id_departamento_indec,
                    "id_departamento_indec": row.id_departamento_indec,
                    "id_provincia_indec": row.id_provincia_indec,
                    "nombre": row.nombre,
                    "provincia": row.provincia_nombre,
                    "poblacion": row.poblacion,
                    "total_eventos": row.total_eventos,
                    "total_casos": row.total_casos,
                    "tasa_incidencia": round(
                        row.total_casos / row.poblacion * 100000, 2
                    )
                    if row.poblacion
                    else None,
                    "centroide": {
                        "lat": row.latitud,
                        "lon": row.longitud,
                    }
                    if row.latitud and row.longitud
                    else None,
                },
                "geometry": row.geometry,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "max_eventos": max_eventos,
            "total_departamentos": len(features),
        },
    }

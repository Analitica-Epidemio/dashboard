#!/usr/bin/env python3
"""
Script para verificar relaciones entre TipoEno y GrupoEno.

Verifica que todos los tipos de eventos tengan al menos un grupo asignado.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_engine
from app.domains.eventos_epidemiologicos.eventos.models import (
    TipoEno,
    GrupoEno,
    TipoEnoGrupoEno,
)


async def verificar_relaciones():
    """Verifica las relaciones entre TipoEno y GrupoEno."""
    print("=" * 70)
    print("🔍 VERIFICANDO RELACIONES TIPO_ENO ↔ GRUPO_ENO")
    print("=" * 70)
    print()

    async with AsyncSession(async_engine) as db:
        # 1. Contar tipos totales
        result = await db.execute(select(func.count(TipoEno.id)))
        total_tipos = result.scalar() or 0
        print(f"📊 Total de Tipos ENO: {total_tipos}")

        # 2. Contar grupos totales
        result = await db.execute(select(func.count(GrupoEno.id)))
        total_grupos = result.scalar() or 0
        print(f"📊 Total de Grupos ENO: {total_grupos}")

        # 3. Contar relaciones en tabla intermedia
        result = await db.execute(select(func.count(TipoEnoGrupoEno.id)))
        total_relaciones = result.scalar() or 0
        print(f"📊 Total de Relaciones: {total_relaciones}")
        print()

        # 4. Encontrar tipos SIN grupo asignado
        query_sin_grupo = (
            select(TipoEno)
            .outerjoin(
                TipoEnoGrupoEno,
                TipoEno.id == TipoEnoGrupoEno.id_tipo_eno
            )
            .where(TipoEnoGrupoEno.id_tipo_eno.is_(None))
        )
        result = await db.execute(query_sin_grupo)
        tipos_sin_grupo = result.scalars().all()

        if tipos_sin_grupo:
            print("⚠️  TIPOS SIN GRUPO ASIGNADO:")
            print("-" * 70)
            for tipo in tipos_sin_grupo:
                print(f"   ID: {tipo.id:3d} | Código: {tipo.codigo or 'N/A':15s} | {tipo.nombre}")
            print()
        else:
            print("✅ Todos los tipos tienen al menos un grupo asignado")
            print()

        # 5. Mostrar tipos CON grupo
        query_con_grupo = (
            select(TipoEno)
            .options(selectinload(TipoEno.tipo_grupos).selectinload(TipoEnoGrupoEno.grupo_eno))
            .limit(10)
        )
        result = await db.execute(query_con_grupo)
        tipos_con_grupo = result.scalars().all()

        print("📋 EJEMPLOS DE TIPOS CON GRUPOS (primeros 10):")
        print("-" * 70)
        for tipo in tipos_con_grupo:
            grupos_nombres = [
                tg.grupo_eno.nombre
                for tg in tipo.tipo_grupos
                if tg.grupo_eno
            ]
            grupos_str = ", ".join(grupos_nombres) if grupos_nombres else "❌ SIN GRUPO"
            print(f"   {tipo.nombre:40s} → {grupos_str}")
        print()

        # 6. Mostrar grupos y cuántos tipos tienen
        query_grupos = select(GrupoEno).options(
            selectinload(GrupoEno.grupo_tipos).selectinload(TipoEnoGrupoEno.tipo_eno)
        )
        result = await db.execute(query_grupos)
        grupos = result.scalars().all()

        print("📊 GRUPOS Y CANTIDAD DE TIPOS:")
        print("-" * 70)
        for grupo in grupos:
            count = len(grupo.grupo_tipos)
            print(f"   {grupo.nombre:40s} → {count:3d} tipos")
        print()

        # 7. Resumen
        print("=" * 70)
        print("📈 RESUMEN")
        print("=" * 70)
        print(f"   Total Tipos ENO:        {total_tipos}")
        print(f"   Total Grupos ENO:       {total_grupos}")
        print(f"   Total Relaciones:       {total_relaciones}")
        print(f"   Tipos sin grupo:        {len(tipos_sin_grupo)}")
        print(f"   Promedio tipos/grupo:   {total_relaciones/total_grupos if total_grupos > 0 else 0:.1f}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verificar_relaciones())

#!/usr/bin/env python3
"""
Script para verificar si 'Dengue' existe como grupo y tipo.
"""
import sys
from pathlib import Path
sys.path.append('/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db')
if 'postgresql+asyncpg' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    print('=== Checking for "Dengue" in both GrupoEno and TipoEno ===\n')

    # Check GrupoEno
    print('GrupoEno with "dengue" in codigo or nombre:')
    result = session.execute(text('''
        SELECT id, codigo, nombre
        FROM grupo_eno
        WHERE codigo LIKE '%dengue%' OR LOWER(nombre) LIKE '%dengue%'
        ORDER BY codigo
    ''')).fetchall()

    for row in result:
        print(f'  ID: {row[0]}, Código: {row[1]}, Nombre: {row[2]}')

    print(f'\n  Total: {len(result)} grupos\n')

    # Check TipoEno
    print('TipoEno with "dengue" in codigo or nombre:')
    result = session.execute(text('''
        SELECT te.id, te.codigo, te.nombre, ge.nombre as grupo_nombre, ge.codigo as grupo_codigo
        FROM tipo_eno te
        JOIN grupo_eno ge ON te.id_grupo_eno = ge.id
        WHERE te.codigo LIKE '%dengue%' OR LOWER(te.nombre) LIKE '%dengue%'
        ORDER BY te.codigo
    ''')).fetchall()

    for row in result:
        print(f'  Tipo ID: {row[0]}, Código: {row[1]}, Nombre: {row[2]}')
        print(f'    → Grupo: {row[3]} (código: {row[4]})')

    print(f'\n  Total: {len(result)} tipos\n')

    # Check what grupos event 36829970 has
    print('Event 36829970 assignment:')
    result = session.execute(text('''
        SELECT
            e.id_evento_caso,
            te.nombre as tipo_evento,
            te.codigo as tipo_codigo,
            ge_via_tipo.nombre as grupo_evento_via_tipo,
            ge_via_tipo.codigo as grupo_codigo_via_tipo
        FROM evento e
        JOIN tipo_eno te ON e.id_tipo_eno = te.id
        LEFT JOIN grupo_eno ge_via_tipo ON te.id_grupo_eno = ge_via_tipo.id
        WHERE e.id_evento_caso = 36829970
    ''')).fetchone()

    if result:
        print(f'  Evento: {result[0]}')
        print(f'  Tipo: {result[1]} (código: {result[2]})')
        print(f'  Grupo (via tipo_eno): {result[3]} (código: {result[4]})')

        # Check grupos via many-to-many junction table
        print(f'\n  Grupos asignados directamente (via evento_grupo_eno):')
        grupos_directos = session.execute(text('''
            SELECT ge.nombre, ge.codigo
            FROM evento_grupo_eno ege
            JOIN grupo_eno ge ON ege.id_grupo_eno = ge.id
            JOIN evento e ON ege.id_evento = e.id
            WHERE e.id_evento_caso = 36829970
        ''')).fetchall()

        if grupos_directos:
            for grupo in grupos_directos:
                print(f'    → {grupo[0]} (código: {grupo[1]})')
        else:
            print(f'    → (ninguno)')

        print(f'\n  ✅ El evento puede pertenecer a múltiples grupos via tabla de unión')

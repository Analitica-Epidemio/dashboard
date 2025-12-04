#!/usr/bin/env python3
"""
🔄 MIGRACIÓN DE DOMINIOS - Clean Domain Architecture

Este script migra la estructura de dominios actual a la nueva arquitectura limpia.

ANTES:
- Dominios mezclados con features técnicas
- Dependencias cruzadas confusas
- Estructura no expresiva

DESPUÉS:
- Dominios de negocio puros y screaming
- Features técnicas separadas
- Arquitectura auto-documentante

EJECUCIÓN:
python migrate_domains.py
"""

import shutil
import sys
from pathlib import Path


def main():
    """Ejecuta la migración completa de dominios"""

    print("🦠 MIGRACIÓN DE DOMINIOS - Epidemiología Chubut")
    print("=" * 60)

    # Verificar que estamos en el directorio correcto
    if not Path("app/domains").exists():
        print("❌ Error: Ejecutar desde la raíz del proyecto backend")
        sys.exit(1)

    # 1. Backup de la estructura actual
    print("📦 1. Creando backup de la estructura actual...")
    if Path("app/domains_backup").exists():
        shutil.rmtree("app/domains_backup")
    shutil.copytree("app/domains", "app/domains_backup")
    print("   ✅ Backup creado en app/domains_backup/")

    # 2. Reemplazar estructura antigua con nueva
    print("🔄 2. Aplicando nueva estructura...")
    if Path("app/domains").exists():
        shutil.rmtree("app/domains")
    shutil.move("app/domains_new", "app/domains")
    print("   ✅ Nueva estructura aplicada")

    # 3. Crear structure de features si no existe
    print("🛠️ 3. Verificando estructura de features...")
    if not Path("app/features").exists():
        print("   ❌ Error: app/features no existe. Revisar migración.")
        sys.exit(1)
    print("   ✅ Features structure verificada")

    # 4. Actualizar imports en API
    print("🔗 4. Actualizando imports en API...")
    update_api_imports()
    print("   ✅ Imports de API actualizados")

    # 5. Crear archivos faltantes
    print("📝 5. Creando archivos __init__.py faltantes...")
    create_missing_init_files()
    print("   ✅ Archivos init creados")

    print()
    print("🎉 MIGRACIÓN COMPLETADA!")
    print("=" * 60)
    print("📋 PRÓXIMOS PASOS:")
    print("1. Revisar imports rotos en el código")
    print("2. Ejecutar tests para verificar funcionalidad")
    print("3. Actualizar referencias en frontend si es necesario")
    print("4. Revisar DOMAIN_ARCHITECTURE.md para entender nueva estructura")
    print()
    print("📚 Estructura nueva:")
    print("   domains/epidemiologia/    🦠 Core domain")
    print("   domains/personas/         👥 Supporting")
    print("   domains/territorio/       🗺️ Supporting")
    print("   domains/clinica/          ⚕️ Supporting")
    print("   features/                 🛠️ Technical features")

def update_api_imports():
    """Actualiza imports en la capa API"""

    # Mapeo de imports viejos -> nuevos
    import_mappings = {
        "from app.domains.uploads": "from app.features.procesamiento_archivos",
        "from app.domains.charts": "from app.features.dashboard",
        "from app.domains.reports": "from app.features.reporteria",
        "from app.domains.analytics": "from app.features.analitica",
        "from app.domains.auth": "from app.domains.autenticacion",
        "from app.domains.eventos": "from app.domains.epidemiologia.eventos",
        "from app.domains.eventos_epidemiologicos.clasificacion": "from app.domains.epidemiologia.clasificacion",
        "from app.domains.ciudadanos": "from app.domains.personas.ciudadanos",
        "from app.domains.localidades": "from app.domains.territorio.geografia",
        "from app.domains.establecimientos": "from app.domains.territorio.establecimientos",
        "from app.domains.salud": "from app.domains.clinica.salud",
        "from app.domains.diagnosticos": "from app.domains.clinica.diagnosticos",
        "from app.domains.investigaciones": "from app.domains.clinica.investigaciones"
    }

    # Actualizar archivos en app/api
    api_path = Path("app/api")
    if api_path.exists():
        for python_file in api_path.rglob("*.py"):
            update_file_imports(python_file, import_mappings)

def update_file_imports(file_path: Path, mappings: dict):
    """Actualiza imports en un archivo específico"""

    if not file_path.exists():
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Aplicar cada mapping
        for old_import, new_import in mappings.items():
            content = content.replace(old_import, new_import)

        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   📝 Actualizado: {file_path}")

    except Exception as e:
        print(f"   ⚠️ Error actualizando {file_path}: {e}")

def create_missing_init_files():
    """Crea archivos __init__.py faltantes"""

    # Directorios que necesitan __init__.py
    directories = [
        "app/domains",
        "app/domains/epidemiologia",
        "app/domains/epidemiologia/eventos",
        "app/domains/epidemiologia/clasificacion",
        "app/domains/epidemiologia/seguimiento",
        "app/domains/personas",
        "app/domains/personas/ciudadanos",
        "app/domains/personas/animales",
        "app/domains/territorio",
        "app/domains/territorio/geografia",
        "app/domains/territorio/establecimientos",
        "app/domains/clinica",
        "app/domains/clinica/diagnosticos",
        "app/domains/clinica/salud",
        "app/domains/clinica/investigaciones",
        "app/domains/autenticacion",
        "app/features",
        "app/features/procesamiento_archivos",
        "app/features/dashboard",
        "app/features/reporteria",
        "app/features/analitica",
        "app/shared",
        "app/shared/events",
        "app/shared/exceptions",
        "app/shared/types"
    ]

    for directory in directories:
        dir_path = Path(directory)
        init_file = dir_path / "__init__.py"

        if dir_path.exists() and not init_file.exists():
            init_file.touch()
            print(f"   📝 Creado: {init_file}")

if __name__ == "__main__":
    main()
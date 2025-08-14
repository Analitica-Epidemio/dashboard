#!/usr/bin/env python3

"""
Script de desarrollo para el Sistema de Epidemiología Moderna.

Proporciona comandos útiles para desarrollo local con uv.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configurar ruta base del proyecto
BASE_DIR = Path(__file__).parent.parent
os.chdir(BASE_DIR)


def run_command(cmd: str, description: Optional[str] = None) -> int:
    """
    Ejecuta un comando y muestra la salida.

    Args:
        cmd: Comando a ejecutar
        description: Descripción opcional

    Returns:
        Código de salida del comando
    """
    if description:
        print(f"🔧 {description}")

    print(f"💻 Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True)

    if result.returncode == 0:
        print("✅ Comando completado exitosamente\n")
    else:
        print(f"❌ Error: comando falló con código {result.returncode}\n")

    return result.returncode


def setup_env() -> int:
    """Configura el entorno de desarrollo"""
    print("🚀 Configurando entorno de desarrollo...")

    # Verificar si existe .env
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("📋 Copiando .env.example a .env...")
            subprocess.run("cp .env.example .env", shell=True)
            print("⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones")
        else:
            print("❌ No se encontró .env.example")
            return 1

    # Crear directorios necesarios
    print("📁 Creando directorios...")
    Path("uploads").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    print("✅ Entorno configurado correctamente")
    return 0


def install_deps() -> int:
    """Instala dependencias con uv"""
    return run_command("uv sync", "Instalando dependencias con uv")


def run_server() -> int:
    """Inicia el servidor de desarrollo"""
    setup_env()
    return run_command(
        "uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
        "Iniciando servidor de desarrollo",
    )


def run_migrations() -> int:
    """Ejecuta migrations de base de datos"""
    print("🗄️  Ejecutando migrations...")

    # Generar migration
    result1 = run_command(
        "uv run alembic revision --autogenerate -m 'Initial migration'",
        "Generando migration inicial",
    )

    if result1 == 0:
        # Aplicar migration
        return run_command("uv run alembic upgrade head", "Aplicando migrations")

    return result1


def create_superuser() -> int:
    """Crea un superusuario para desarrollo"""
    print("👤 Creando superusuario de desarrollo...")

    script = """
from app.core.database import get_session
from app.core.user_manager import get_user_manager
import asyncio
import uuid

async def create_dev_user():
    session = next(get_session())
    user_manager = await get_user_manager(None).__anext__()
    
    try:
        user = await user_manager.create(
            {
                "email": "admin@epidemiologia.local",
                "password": "admin123",
                "nombre_completo": "Administrador Sistema",
                "is_superuser": True,
                "is_verified": True
            }
        )
        print(f"✅ Usuario creado: {user.email}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

asyncio.run(create_dev_user())
"""

    with open("temp_create_user.py", "w") as f:
        f.write(script)

    result = run_command("uv run python temp_create_user.py")

    # Limpiar archivo temporal
    Path("temp_create_user.py").unlink(missing_ok=True)

    return result


def run_tests() -> int:
    """Ejecuta los tests"""
    return run_command("uv run pytest", "Ejecutando tests")


def lint_code() -> int:
    """Ejecuta linting del código"""
    return run_command("uv run ruff check . --fix", "Ejecutando linting")


def format_code() -> int:
    """Formatea el código"""
    return run_command("uv run ruff format .", "Formateando código")


def docker_up() -> int:
    """Inicia todo con Docker para DESARROLLO (API + BD + Redis) con hot-reload"""
    return run_command(
        "docker-compose -f docker-compose.dev.yml up",
        "Iniciando stack de desarrollo con Docker y hot-reload",
    )


def docker_down() -> int:
    """Detiene servicios Docker de desarrollo"""
    return run_command(
        "docker-compose -f docker-compose.dev.yml down",
        "Deteniendo servicios Docker de desarrollo",
    )


def docker_prod() -> int:
    """Inicia todo con Docker para PRODUCCIÓN"""
    return run_command(
        "docker-compose up --build", "Iniciando stack de producción con Docker"
    )


def docker_rebuild() -> int:
    """Reconstruye las imágenes Docker"""
    return run_command(
        "docker-compose -f docker-compose.dev.yml up --build",
        "Reconstruyendo y iniciando servicios de desarrollo",
    )


def docker_db_reset() -> int:
    """Reinicia la base de datos Docker desde cero"""
    print("🔄 Reiniciando base de datos Docker desde cero...")

    # Detener servicios
    result1 = run_command(
        "docker-compose -f docker-compose.dev.yml down", "Deteniendo servicios"
    )

    if result1 != 0:
        return result1

    # Eliminar volúmenes de la base de datos
    result2 = run_command(
        "docker volume rm epidemiologia-moderna-backend_postgres_data_dev 2>/dev/null || true",
        "Eliminando volúmenes de la base de datos",
    )

    # Reiniciar servicios
    result3 = run_command(
        "docker-compose -f docker-compose.dev.yml up -d",
        "Reiniciando servicios con DB limpia",
    )

    if result3 == 0:
        print("✅ Base de datos reiniciada exitosamente")
        print(
            "💡 La DB está ahora completamente limpia y lista para nuevas migraciones"
        )

    return result3


def show_status() -> int:
    """Muestra el estado del proyecto"""
    print("📊 Estado del Sistema de Epidemiología Moderna")
    print("=" * 50)

    # Verificar archivos importantes
    files_check = [
        (".env", "Configuración de entorno"),
        ("app/main.py", "Aplicación principal"),
        ("alembic.ini", "Configuración de migrations"),
    ]

    for file_path, description in files_check:
        exists = "✅" if Path(file_path).exists() else "❌"
        print(f"{exists} {description}: {file_path}")

    # Verificar directorios
    dirs_check = [
        ("uploads", "Directorio de archivos"),
        ("logs", "Directorio de logs"),
        ("alembic/versions", "Migrations"),
    ]

    for dir_path, description in dirs_check:
        exists = "✅" if Path(dir_path).exists() else "❌"
        print(f"{exists} {description}: {dir_path}")

    print("\n🚀 Comandos disponibles:")
    print("  python scripts/dev.py setup     - Configurar entorno")
    print("  python scripts/dev.py install   - Instalar dependencias")
    print("  python scripts/dev.py serve     - Iniciar servidor")
    print("  python scripts/dev.py migrate   - Ejecutar migrations")
    print("  python scripts/dev.py superuser - Crear superusuario")
    print("  python scripts/dev.py docker-up - Iniciar servicios Docker")
    print("  python scripts/dev.py db-reset  - Reiniciar DB Docker desde cero")

    return 0


def main() -> None:
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Script de desarrollo para Sistema de Epidemiología"
    )

    parser.add_argument(
        "command",
        choices=[
            "setup",
            "install",
            "serve",
            "migrate",
            "superuser",
            "test",
            "lint",
            "format",
            "docker-up",
            "docker-down",
            "docker-prod",
            "docker-rebuild",
            "db-reset",
            "status",
        ],
        help="Comando a ejecutar",
    )

    args = parser.parse_args()

    commands = {
        "setup": setup_env,
        "install": install_deps,
        "serve": run_server,
        "migrate": run_migrations,
        "superuser": create_superuser,
        "test": run_tests,
        "lint": lint_code,
        "format": format_code,
        "docker-up": docker_up,
        "docker-down": docker_down,
        "docker-prod": docker_prod,
        "docker-rebuild": docker_rebuild,
        "db-reset": docker_db_reset,
        "status": show_status,
    }

    result = commands[args.command]()
    sys.exit(result)


if __name__ == "__main__":
    main()

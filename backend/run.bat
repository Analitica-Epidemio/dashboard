@echo off
REM =============================================================================
REM Sistema de Epidemiología - Comandos para Windows
REM =============================================================================

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="setup" goto setup
if "%1"=="install" goto install
if "%1"=="dev-docker" goto dev-docker
if "%1"=="dev-docker-down" goto dev-docker-down
if "%1"=="dev-docker-rebuild" goto dev-docker-rebuild
if "%1"=="dev-docker-logs" goto dev-docker-logs
if "%1"=="dev-docker-db-reset" goto dev-docker-db-reset
if "%1"=="dev" goto dev
if "%1"=="test" goto test
if "%1"=="test-coverage" goto test-coverage
if "%1"=="lint" goto lint
if "%1"=="format" goto format
if "%1"=="typecheck" goto typecheck
if "%1"=="qa" goto qa
if "%1"=="migrate" goto migrate
if "%1"=="makemigrations" goto makemigrations
if "%1"=="rollback" goto rollback
if "%1"=="db-history" goto db-history
if "%1"=="seed-strategies" goto seed-strategies
if "%1"=="seed-strategies-docker" goto seed-strategies-docker
if "%1"=="docker-prod" goto docker-prod
if "%1"=="docker-build" goto docker-build
if "%1"=="clean" goto clean
if "%1"=="shell" goto shell
if "%1"=="logs" goto logs

goto help

REM =============================================================================
REM AYUDA
REM =============================================================================

:help
echo Sistema de Epidemiología - Comandos disponibles
echo ================================================
echo.
echo INICIO RÁPIDO:
echo   run setup        → Configuración inicial del proyecto (primera vez)
echo   run dev-docker   → Desarrollo CON Docker (incluye DB + Redis)
echo   run dev          → Desarrollo SIN Docker (requiere DB local)
echo.
echo CONFIGURACIÓN:
echo   run setup                 → Configuración inicial completa
echo   run install               → Instala/actualiza dependencias
echo.
echo DESARROLLO CON DOCKER:
echo   run dev-docker            → Inicia desarrollo CON Docker
echo   run dev-docker-down       → Detiene los servicios Docker
echo   run dev-docker-rebuild    → Reconstruye y reinicia servicios Docker  
echo   run dev-docker-logs       → Ver logs de los servicios Docker
echo   run dev-docker-db-reset   → Reinicia la BD Docker desde cero
echo.
echo DESARROLLO SIN DOCKER:
echo   run dev                   → Inicia desarrollo SIN Docker
echo.
echo TESTING Y CALIDAD:
echo   run test                  → Ejecuta los tests
echo   run test-coverage         → Ejecuta tests con reporte de cobertura
echo   run lint                  → Ejecuta el linter y arregla problemas
echo   run format                → Formatea el código
echo   run typecheck             → Verifica tipos con mypy
echo   run qa                    → Ejecuta todos los checks de calidad
echo.
echo BASE DE DATOS:
echo   run migrate               → Ejecuta las migraciones pendientes
echo   run makemigrations        → Genera nueva migración
echo   run rollback              → Rollback de la última migración
echo   run db-history            → Ver historial de migraciones
echo   run seed-strategies       → Carga las estrategias iniciales en la BD
echo   run seed-strategies-docker→ Carga las estrategias en BD (Docker)
echo.
echo PRODUCCIÓN:
echo   run docker-prod           → Construye y ejecuta para producción
echo   run docker-build          → Construye la imagen Docker de producción
echo.
echo UTILIDADES:
echo   run clean                 → Limpia archivos temporales
echo   run shell                 → Abre shell de Python
echo   run logs                  → Ver logs de la aplicación
goto end

REM =============================================================================
REM CONFIGURACIÓN INICIAL
REM =============================================================================

:setup
echo 🚀 Configurando proyecto por primera vez...
echo 1. Verificando archivo .env...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo ✅ Archivo .env creado desde .env.example
        echo ⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones
    ) else (
        echo ❌ No se encontró .env.example
        goto end
    )
) else (
    echo ✅ Archivo .env ya existe
)
echo 2. Creando directorios necesarios...
if not exist uploads mkdir uploads
if not exist logs mkdir logs
echo 3. Instalando dependencias con uv...
uv sync --all-extras
echo.
echo ✅ Configuración completada!
echo.
echo 🔥 PRÓXIMOS PASOS:
echo    1. Edita el archivo .env con tus configuraciones
echo    2. Elige cómo ejecutar el proyecto:
echo       • CON Docker:    run dev-docker
echo       • SIN Docker:    run dev
goto end

:install
echo 📦 Instalando/actualizando dependencias...
uv sync --all-extras
goto end

REM =============================================================================
REM DESARROLLO CON DOCKER
REM =============================================================================

:dev-docker
echo 🐳 Iniciando stack de desarrollo con Docker...
echo    • PostgreSQL en puerto 5432
echo    • Redis en puerto 6379  
echo    • API en puerto 8000 con hot-reload
docker-compose -f docker-compose.dev.yml up
goto end

:dev-docker-down
echo 🛑 Deteniendo servicios Docker...
docker-compose -f docker-compose.dev.yml down
goto end

:dev-docker-rebuild
echo 🔄 Reconstruyendo y reiniciando servicios Docker...
docker-compose -f docker-compose.dev.yml up --build
goto end

:dev-docker-logs
echo 📋 Ver logs de los servicios Docker...
docker-compose -f docker-compose.dev.yml logs -f
goto end

:dev-docker-db-reset
echo ⚠️  ADVERTENCIA: Esto eliminará TODOS los datos de la base de datos
set /p confirm="¿Estás seguro? (y/N): "
if not "%confirm%"=="y" goto end
echo Eliminando servicios Docker...
docker-compose -f docker-compose.dev.yml down
echo Eliminando volumen de base de datos...
docker volume rm epi_dashboard_postgres_data_dev 2>nul
echo ✅ Base de datos eliminada. Se creará una nueva al ejecutar 'run dev-docker'
goto end

REM =============================================================================
REM DESARROLLO SIN DOCKER
REM =============================================================================

:dev
echo 💻 Iniciando servidor de desarrollo local...
echo    ⚠️  Requiere PostgreSQL y Redis instalados localmente
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto end

REM =============================================================================
REM TESTING Y CALIDAD
REM =============================================================================

:test
echo 🧪 Ejecutando tests...
uv run pytest
goto end

:test-coverage
echo 📊 Ejecutando tests con reporte de cobertura...
uv run pytest --cov=app --cov-report=html --cov-report=term
goto end

:lint
echo 🔍 Ejecutando linter...
uv run ruff check . --fix
goto end

:format
echo 💅 Formateando código...
uv run ruff format .
goto end

:typecheck
echo 🔎 Verificando tipos con mypy...
uv run mypy app
goto end

:qa
echo ✅ Ejecutando todos los checks de calidad...
call %0 lint
call %0 format
call %0 typecheck
call %0 test
goto end

REM =============================================================================
REM BASE DE DATOS
REM =============================================================================

:migrate
echo 🗄️ Ejecutando migraciones pendientes...
uv run alembic upgrade head
goto end

:makemigrations
echo 📝 Generando nueva migración...
if "%2"=="" (
    echo Error: Proporciona una descripción. Uso: run makemigrations "descripción"
    goto end
)
uv run alembic revision --autogenerate -m "%2"
goto end

:rollback
echo ↩️ Rollback de la última migración...
uv run alembic downgrade -1
goto end

:db-history
echo 📜 Ver historial de migraciones...
uv run alembic history
goto end

:seed-strategies
echo 🌱 Cargando estrategias iniciales en la BD...
uv run python -m app.scripts.seed_strategies
goto end

:seed-strategies-docker
echo 🌱 Cargando estrategias iniciales en la BD (Docker)...
docker compose -f docker-compose.dev.yml exec api python -m app.scripts.seed_strategies
goto end

REM =============================================================================
REM PRODUCCIÓN
REM =============================================================================

:docker-prod
echo 🚢 Construyendo y ejecutando para producción...
docker-compose up --build
goto end

:docker-build
echo 🏗️ Construyendo imagen Docker de producción...
docker build -t epidemiologia-api .
goto end

REM =============================================================================
REM UTILIDADES
REM =============================================================================

:clean
echo 🧹 Limpiando archivos temporales...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f"
for /r . %%f in (*.coverage) do @if exist "%%f" del /q "%%f"
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (htmlcov) do @if exist "%%d" rd /s /q "%%d"
echo ✅ Limpieza completada
goto end

:shell
echo 🐚 Abriendo shell de Python...
uv run python
goto end

:logs
echo 📜 Ver logs de la aplicación...
if exist logs\*.log (
    powershell -Command "Get-Content logs\*.log -Wait"
) else (
    echo No hay logs disponibles
)
goto end

:end
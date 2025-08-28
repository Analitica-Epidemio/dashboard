@echo off
REM Script para Windows sin Make instalado
REM Uso: run.cmd [comando]

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="logs" goto logs
if "%1"=="test" goto test
if "%1"=="shell" goto shell
if "%1"=="bash" goto bash
if "%1"=="lint" goto lint
if "%1"=="migrate" goto migrate
if "%1"=="seed" goto seed
if "%1"=="reset-db" goto reset-db
if "%1"=="build" goto build
if "%1"=="setup" goto setup

:help
echo Comandos disponibles:
echo   run up        - Iniciar servicios
echo   run down      - Detener servicios  
echo   run logs      - Ver logs
echo   run test      - Ejecutar tests
echo   run shell     - Shell Python
echo   run bash      - Shell Bash
echo   run lint      - Formatear codigo
echo   run migrate   - Ejecutar migraciones
echo   run seed      - Cargar datos iniciales
echo   run reset-db  - Resetear base de datos
echo   run build     - Reconstruir containers
echo   run setup     - Setup inicial
goto :eof

:up
docker compose up
goto :eof

:down
docker compose down
goto :eof

:logs
docker compose logs -f
goto :eof

:test
docker compose exec api uv run pytest
goto :eof

:shell
docker compose exec api uv run python
goto :eof

:bash
docker compose exec api bash
goto :eof

:lint
docker compose exec api uv run ruff check . --fix
docker compose exec api uv run ruff format .
goto :eof

:migrate
docker compose exec api uv run alembic upgrade head
goto :eof

:seed
docker compose exec api uv run python -m app.scripts.seed
goto :eof

:reset-db
echo WARNING: This will delete all database data
set /p confirm=Are you sure? (y/N): 
if not "%confirm%"=="y" goto :eof
docker compose stop db
docker compose rm -f db
docker volume ls -q | findstr postgres > temp.txt
for /f %%i in (temp.txt) do docker volume rm %%i
del temp.txt
docker compose up -d db
timeout /t 5 /nobreak > nul
call :migrate
call :seed
echo Database reset complete!
goto :eof

:build
docker compose build
goto :eof

:setup
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo Created .env file - please edit it
    )
)
if not exist uploads mkdir uploads
if not exist logs mkdir logs
docker compose build
echo Setup complete! Run 'run up' to start
goto :eof

:eof
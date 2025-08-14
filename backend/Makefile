.PHONY: help setup install dev dev-docker dev-docker-down test lint format typecheck qa clean

# =============================================================================
# COMANDOS PRINCIPALES
# =============================================================================

help:  ## 📚 Muestra esta ayuda
	@echo "Sistema de Epidemiología - Comandos disponibles"
	@echo "================================================"
	@echo ""
	@echo "INICIO RÁPIDO:"
	@echo "  make setup        → Configuración inicial del proyecto (primera vez)"
	@echo "  make dev-docker   → Desarrollo CON Docker (incluye DB + Redis)"
	@echo "  make dev          → Desarrollo SIN Docker (requiere DB local)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================

setup:  ## 🎯 Configuración inicial completa (ejecutar la primera vez)
	@echo "🚀 Configurando proyecto por primera vez..."
	@echo "1. Verificando archivo .env..."
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "✅ Archivo .env creado desde .env.example"; \
			echo "⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones"; \
		else \
			echo "❌ No se encontró .env.example"; \
			exit 1; \
		fi \
	else \
		echo "✅ Archivo .env ya existe"; \
	fi
	@echo "2. Creando directorios necesarios..."
	@mkdir -p uploads logs
	@echo "3. Instalando dependencias con uv..."
	@uv sync --all-extras
	@echo ""
	@echo "✅ Configuración completada!"
	@echo ""
	@echo "🔥 PRÓXIMOS PASOS:"
	@echo "   1. Edita el archivo .env con tus configuraciones"
	@echo "   2. Elige cómo ejecutar el proyecto:"
	@echo "      • CON Docker:    make dev-docker"
	@echo "      • SIN Docker:    make dev"

install:  ## 📦 Instala/actualiza las dependencias
	uv sync --all-extras

# =============================================================================
# DESARROLLO CON DOCKER (Recomendado)
# =============================================================================

dev-docker:  ## 🐳 Inicia desarrollo CON Docker (API + DB + Redis con hot-reload)
	@echo "🐳 Iniciando stack de desarrollo con Docker..."
	@echo "   • PostgreSQL en puerto 5432"
	@echo "   • Redis en puerto 6379"
	@echo "   • API en puerto 8000 con hot-reload"
	docker-compose -f docker-compose.dev.yml up

dev-docker-down:  ## 🛑 Detiene los servicios Docker
	docker-compose -f docker-compose.dev.yml down

dev-docker-rebuild:  ## 🔄 Reconstruye y reinicia servicios Docker
	docker-compose -f docker-compose.dev.yml up --build

dev-docker-logs:  ## 📋 Ver logs de los servicios Docker
	docker-compose -f docker-compose.dev.yml logs -f

dev-docker-db-reset:  ## 💣 Reinicia la BD Docker desde cero (BORRA TODOS LOS DATOS)
	@echo "⚠️  ADVERTENCIA: Esto eliminará TODOS los datos de la base de datos"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose -f docker-compose.dev.yml down
	docker volume rm epi_dashboard_postgres_data_dev 2>/dev/null || true
	@echo "✅ Base de datos eliminada. Se creará una nueva al ejecutar 'make dev-docker'"

# =============================================================================
# DESARROLLO SIN DOCKER (Requiere PostgreSQL y Redis locales)
# =============================================================================

dev:  ## 💻 Inicia desarrollo SIN Docker (requiere DB y Redis locales)
	@echo "💻 Iniciando servidor de desarrollo local..."
	@echo "   ⚠️  Requiere PostgreSQL y Redis instalados localmente"
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# TESTING Y CALIDAD DE CÓDIGO
# =============================================================================

test:  ## 🧪 Ejecuta los tests
	uv run pytest

test-watch:  ## 👀 Ejecuta los tests en modo watch
	uv run pytest-watch

test-coverage:  ## 📊 Ejecuta tests con reporte de cobertura
	uv run pytest --cov=app --cov-report=html --cov-report=term

lint:  ## 🔍 Ejecuta el linter y arregla problemas
	uv run ruff check . --fix

format:  ## 💅 Formatea el código
	uv run ruff format .

typecheck:  ## 🔎 Verifica tipos con mypy
	uv run mypy app

qa:  ## ✅ Ejecuta todos los checks de calidad
	@echo "🔍 Ejecutando checks de calidad..."
	@make lint
	@make format
	@make typecheck
	@make test

# =============================================================================
# BASE DE DATOS
# =============================================================================

migrate:  ## 🗄️ Ejecuta las migraciones pendientes
	uv run alembic upgrade head

makemigrations:  ## 📝 Genera nueva migración (uso: make makemigrations m="descripción")
	uv run alembic revision --autogenerate -m "$(m)"

rollback:  ## ↩️ Rollback de la última migración
	uv run alembic downgrade -1

db-history:  ## 📜 Ver historial de migraciones
	uv run alembic history

# =============================================================================
# PRODUCCIÓN
# =============================================================================

docker-prod:  ## 🚢 Construye y ejecuta para producción
	docker-compose up --build

docker-build:  ## 🏗️ Construye la imagen Docker de producción
	docker build -t epidemiologia-api .

# =============================================================================
# UTILIDADES
# =============================================================================

clean:  ## 🧹 Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

pre-commit:  ## 🪝 Instala los hooks de pre-commit
	uv run pre-commit install

pre-commit-run:  ## 🔄 Ejecuta pre-commit en todos los archivos
	uv run pre-commit run --all-files

shell:  ## 🐚 Abre shell de Python con el contexto del proyecto
	uv run python

logs:  ## 📜 Ver logs de la aplicación
	tail -f logs/*.log 2>/dev/null || echo "No hay logs disponibles"
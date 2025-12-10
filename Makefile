# Sistema de Epidemiologia - Development Commands
# Based on: https://docs.docker.com/compose/how-tos/production/
#
# Setup inicial:
#   make install && make up && make migrate && make seed
#
# Desarrollo diario:
#   Terminal 1: make up
#   Terminal 2: make dev
#   Terminal 3: make celery
#   Terminal 4: make frontend

.PHONY: help install up down logs dev celery frontend migrate migration seed superadmin reset lint typecheck test prod

help:
	@echo "Setup:"
	@echo "  install     Instalar dependencias (backend + frontend)"
	@echo ""
	@echo "Desarrollo:"
	@echo "  up          Levantar infraestructura (DB, Redis, pgweb)"
	@echo "  down        Detener contenedores"
	@echo "  logs        Ver logs"
	@echo "  dev         Iniciar backend (hot-reload)"
	@echo "  celery      Iniciar worker Celery (procesa uploads)"
	@echo "  frontend    Iniciar frontend (hot-reload)"
	@echo ""
	@echo "Base de datos:"
	@echo "  migrate     Aplicar migraciones"
	@echo "  migration   Crear migración (make migration m='descripcion')"
	@echo "  seed        Cargar datos iniciales (pregunta si crear admin de dev)"
	@echo "  superadmin  Crear superadmin interactivo (producción)"
	@echo "  reset       Resetear DB (borra todo y re-seedea)"
	@echo ""
	@echo "Calidad:"
	@echo "  lint        Linter + formatter"
	@echo "  typecheck   Type checking"
	@echo "  test        Correr tests"
	@echo ""
	@echo "Producción:"
	@echo "  prod        Levantar stack de producción"

# Setup
install:
	cd backend && uv sync
	cd frontend && pnpm install

# Desarrollo
up:
	docker compose up -d
	@echo ""
	@echo "Infraestructura lista:"
	@echo "  PostgreSQL: localhost:$${DB_PORT:-5433}"
	@echo "  Redis:      localhost:$${REDIS_PORT:-6380}"
	@echo "  pgweb:      http://localhost:$${PGWEB_PORT:-8081}"

down:
	docker compose down

logs:
	docker compose logs -f

dev:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && pnpm dev

celery:
	cd backend && uv run celery -A app.core.celery_app worker -Q default,file_processing,geocoding,maintenance -l info

# Base de datos
migrate:
	cd backend && uv run alembic upgrade head

migration:
	@if [ -z "$(m)" ]; then echo "Uso: make migration m='descripcion'"; exit 1; fi
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

seed:
	cd backend && uv run python app/scripts/seed.py

superadmin:
	cd backend && uv run python -m app.commands.create_superadmin

reset:
	@echo "Esto borrará todos los datos. ¿Continuar? [y/N]" && read ans && [ $${ans:-N} = y ]
	docker compose down -v
	docker compose up -d
	@echo "Base de datos reseteada"

# Calidad
lint:
	cd backend && uv run ruff check . --fix && uv run ruff format .

typecheck:
	cd backend && uv run ty check

test:
	cd backend && uv run pytest

# Producción
prod:
	docker compose -f compose.prod.yaml up -d

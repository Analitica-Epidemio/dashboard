# Backend development commands
# Requires: Docker running, uv installed
#
# Setup inicial:
#   make install && make up && make migrate && make seed
#
# Desarrollo diario:
#   Terminal 1: make up
#   Terminal 2: make dev

.PHONY: help install up down dev logs migrate migration seed reset test lint typecheck

help:
	@echo "Comandos disponibles:"
	@echo ""
	@echo "Setup:"
	@echo "  install   - Instalar dependencias (uv sync)"
	@echo ""
	@echo "Desarrollo:"
	@echo "  up        - Levantar DB + Redis"
	@echo "  down      - Bajar contenedores"
	@echo "  dev       - API con hot-reload"
	@echo "  logs      - Ver logs de contenedores"
	@echo ""
	@echo "Base de datos:"
	@echo "  migrate   - Aplicar migraciones"
	@echo "  migration - Crear migración (make migration m='descripcion')"
	@echo "  seed      - Seed de datos iniciales"
	@echo "  reset     - Resetear DB (borra todo y re-seedea)"
	@echo ""
	@echo "Calidad:"
	@echo "  test      - Correr tests"
	@echo "  lint      - Linter + formatter"
	@echo "  typecheck - Type checking"

# Setup
install:
	uv sync

# Desarrollo
up:
	cd .. && docker compose up -d

down:
	cd .. && docker compose down

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

logs:
	cd .. && docker compose logs -f

# Base de datos
migrate:
	uv run alembic upgrade head

migration:
	@if [ -z "$(m)" ]; then \
		echo "Uso: make migration m='descripcion de la migracion'"; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(m)"

seed:
	uv run python app/scripts/seed.py

reset:
	cd .. && docker compose down -v
	cd .. && docker compose up -d
	@echo "Esperando que la DB esté lista..."
	@sleep 3
	uv run alembic upgrade head
	uv run python app/scripts/seed.py
	@echo "DB reseteada y seedeada"

# Calidad
test:
	uv run pytest

lint:
	uv run ruff check . --fix
	uv run ruff format .

typecheck:
	uv run ty check


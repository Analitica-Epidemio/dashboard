# Makefile - Backend (Desarrollo Local)
#
# Para produccion, usar el Makefile en la raiz del proyecto.
#
.PHONY: help up down logs shell test lint build

help: ## Mostrar ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─────────────────────────────────────────────────────────────────────────────
# Desarrollo
# ─────────────────────────────────────────────────────────────────────────────

up: ## Iniciar stack de desarrollo (API + Celery + DB + Redis)
	docker compose up

up-d: ## Iniciar en background
	docker compose up -d

down: ## Detener stack
	docker compose down

logs: ## Ver logs (make logs o make logs s=api)
	@if [ -z "$(s)" ]; then docker compose logs -f; else docker compose logs -f $(s); fi

build: ## Rebuild containers
	docker compose build

restart: ## Reiniciar servicios
	docker compose restart

ps: ## Ver estado de containers
	docker compose ps

# ─────────────────────────────────────────────────────────────────────────────
# Shell y debug
# ─────────────────────────────────────────────────────────────────────────────

shell: ## Python shell en container
	docker compose exec api uv run python

bash: ## Bash en container api
	docker compose exec api bash

exec: ## Ejecutar comando (make exec c="alembic upgrade head")
	docker compose exec api $(c)

# ─────────────────────────────────────────────────────────────────────────────
# Base de datos
# ─────────────────────────────────────────────────────────────────────────────

migrate: ## Correr migraciones
	docker compose exec api uv run alembic upgrade head

migration: ## Nueva migracion (make migration m="descripcion")
	docker compose exec api uv run alembic revision --autogenerate -m "$(m)"

rollback: ## Rollback ultima migracion
	docker compose exec api uv run alembic downgrade -1

seed: ## Seed completo (solo en DB vacia)
	docker compose exec api uv run python app/scripts/seed.py

truncate: ## Vaciar tablas (mantiene estructura)
	docker compose exec api uv run python -m app.scripts.truncate_all

superadmin: ## Crear superadmin interactivo
	docker compose exec -it api uv run python -m app.commands.create_superadmin

# ─────────────────────────────────────────────────────────────────────────────
# Calidad
# ─────────────────────────────────────────────────────────────────────────────

lint: ## Lint y format
	docker compose exec api uv run ruff check . --fix
	docker compose exec api uv run ruff format .

test: ## Correr tests
	docker compose exec api uv run pytest

# ─────────────────────────────────────────────────────────────────────────────
# Limpieza y reset
# ─────────────────────────────────────────────────────────────────────────────

clean: ## Limpiar cache Python
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

reset-db: ## Reset DB (mantiene Redis)
	@echo "⚠️  Esto borra TODA la base de datos"
	@printf "Continuar? (y/N): "; read confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose stop db
	docker compose rm -f db
	docker volume rm $$(docker volume ls -q | grep postgres_data) 2>/dev/null || true
	docker compose up -d db
	@sleep 5
	@make migrate
	@echo "✅ DB reseteada. Correr 'make seed' para datos iniciales"

reset-all: ## Reset TODO (DB + Redis + containers)
	@echo "⚠️  Esto borra TODOS los datos (DB + Redis)"
	@printf "Continuar? (y/N): "; read confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v
	docker compose up -d db redis
	@sleep 5
	@make migrate
	@echo "✅ Reset completo. Correr 'make seed' para datos iniciales"

nuke: ## Borrar TODO incluyendo imagenes (fresh start)
	@echo "⚠️  Esto borra containers, volumenes e imagenes"
	@printf "Continuar? (y/N): "; read confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v --rmi local
	@echo "✅ Todo borrado. Correr 'make up' para rebuild"

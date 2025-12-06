# Makefile simplificado - Docker-only development (2025)
# Compatible con Windows (Git Bash), macOS y Linux
# Comandos estándar de la industria

.PHONY: help up down logs shell test lint clean build reset-db reset-all

# Comando por defecto
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# DESARROLLO (Docker only)
# =============================================================================

check-ports: ## Check which ports are available
	@echo "🔍 Checking port availability..."
	@for port in 8000 8001 8002 8003; do \
		if lsof -ti:$$port > /dev/null 2>&1; then \
			echo "❌ Port $$port (API): IN USE by $$(lsof -ti:$$port | head -1 | xargs ps -p -o comm= 2>/dev/null || echo 'unknown')"; \
		else \
			echo "✅ Port $$port (API): Available"; \
		fi; \
	done; \
	for port in 5433 5434 5435; do \
		if lsof -ti:$$port > /dev/null 2>&1; then \
			echo "❌ Port $$port (PostgreSQL): IN USE by $$(lsof -ti:$$port | head -1 | xargs ps -p -o comm= 2>/dev/null || echo 'unknown')"; \
		else \
			echo "✅ Port $$port (PostgreSQL): Available"; \
		fi; \
	done; \
	for port in 6380 6381 6382; do \
		if lsof -ti:$$port > /dev/null 2>&1; then \
			echo "❌ Port $$port (Redis): IN USE by $$(lsof -ti:$$port | head -1 | xargs ps -p -o comm= 2>/dev/null || echo 'unknown')"; \
		else \
			echo "✅ Port $$port (Redis): Available"; \
		fi; \
	done

up: ## Start development stack with automatic port conflict detection
	@echo "🔍 Checking for port conflicts..."
	@if [ -f .env.local ]; then \
		echo "📋 Loading port configuration from .env.local"; \
		set -a; . ./.env.local; set +a; \
	fi; \
	API_PORT=$${API_PORT:-8000}; \
	DB_PORT=$${DB_PORT:-5433}; \
	REDIS_PORT=$${REDIS_PORT:-6380}; \
	if lsof -ti:$$API_PORT > /dev/null 2>&1; then \
		echo "⚠️  Port $$API_PORT (API) is in use, finding alternative..."; \
		for port in 8000 8001 8002 8003 8004; do \
			if ! lsof -ti:$$port > /dev/null 2>&1; then \
				API_PORT=$$port; \
				break; \
			fi; \
		done; \
	fi; \
	if lsof -ti:$$DB_PORT > /dev/null 2>&1; then \
		echo "⚠️  Port $$DB_PORT (PostgreSQL) is in use, finding alternative..."; \
		for port in 5433 5434 5435 5436; do \
			if ! lsof -ti:$$port > /dev/null 2>&1; then \
				DB_PORT=$$port; \
				break; \
			fi; \
		done; \
	fi; \
	if lsof -ti:$$REDIS_PORT > /dev/null 2>&1; then \
		echo "⚠️  Port $$REDIS_PORT (Redis) is in use, finding alternative..."; \
		for port in 6380 6381 6382 6383; do \
			if ! lsof -ti:$$port > /dev/null 2>&1; then \
				REDIS_PORT=$$port; \
				break; \
			fi; \
		done; \
	fi; \
	echo "✅ Using ports: API=$$API_PORT, PostgreSQL=$$DB_PORT, Redis=$$REDIS_PORT"; \
	if [ ! -f .env.local ]; then \
		echo "💡 Tip: Create .env.local (see .env.local.example) to set custom ports"; \
	fi; \
	echo "📝 Update your .env file with these ports:"; \
	echo "   DATABASE_URL=postgresql+asyncpg://epidemiologia_user:epidemiologia_password@localhost:$$DB_PORT/epidemiologia_db"; \
	echo "   REDIS_URL=redis://localhost:$$REDIS_PORT/0"; \
	echo "   CELERY_BROKER_URL=redis://localhost:$$REDIS_PORT/0"; \
	API_PORT=$$API_PORT DB_PORT=$$DB_PORT REDIS_PORT=$$REDIS_PORT docker compose up

up-d: ## Start development stack in detached mode with port detection
	@echo "🔍 Checking for port conflicts..."
	@if [ -f .env.local ]; then \
		echo "📋 Loading port configuration from .env.local"; \
		set -a; . ./.env.local; set +a; \
	fi; \
	API_PORT=$${API_PORT:-8000}; \
	DB_PORT=$${DB_PORT:-5433}; \
	REDIS_PORT=$${REDIS_PORT:-6380}; \
	if lsof -ti:$$API_PORT > /dev/null 2>&1; then \
		echo "⚠️  Port $$API_PORT (API) is in use, finding alternative..."; \
		for port in 8000 8001 8002 8003 8004; do \
			if ! lsof -ti:$$port > /dev/null 2>&1; then \
				API_PORT=$$port; \
				break; \
			fi; \
		done; \
	fi; \
	if lsof -ti:$$DB_PORT > /dev/null 2>&1; then \
		echo "⚠️  Port $$DB_PORT (PostgreSQL) is in use, finding alternative..."; \
		for port in 5433 5434 5435 5436; do \
			if ! lsof -ti:$$port > /dev/null 2>&1; then \
				DB_PORT=$$port; \
				break; \
			fi; \
		done; \
	fi; \
	if lsof -ti:$$REDIS_PORT > /dev/null 2>&1; then \
		echo "⚠️  Port $$REDIS_PORT (Redis) is in use, finding alternative..."; \
		for port in 6380 6381 6382 6383; do \
			if ! lsof -ti:$$port > /dev/null 2>&1; then \
				REDIS_PORT=$$port; \
				break; \
			fi; \
		done; \
	fi; \
	echo "✅ Starting in background with ports: API=$$API_PORT, PostgreSQL=$$DB_PORT, Redis=$$REDIS_PORT"; \
	API_PORT=$$API_PORT DB_PORT=$$DB_PORT REDIS_PORT=$$REDIS_PORT docker compose up -d; \
	echo "🚀 Services started! Check logs with 'make logs'"; \
	echo "🌐 API available at: http://localhost:$$API_PORT"

down: ## Stop development stack
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## View logs (use: make logs SERVICE=api)
	@if [ -z "$(SERVICE)" ]; then \
		docker compose logs -f; \
	else \
		docker compose logs -f $(SERVICE); \
	fi

build: ## Rebuild containers
	docker compose build

rebuild: ## Rebuild and start
	docker compose up --build

# =============================================================================
# DESARROLLO INTERACTIVO
# =============================================================================

shell: ## Open Python shell in API container
	docker compose exec api uv run python

bash: ## Open bash shell in API container
	docker compose exec api bash

# =============================================================================
# TESTING Y CALIDAD
# =============================================================================

test: ## Run tests
	docker compose exec api uv run pytest

lint: ## Run linter and formatter
	docker compose exec api uv run ruff check . --fix
	docker compose exec api uv run ruff format .

typecheck: ## Run type checking (strict mode)
	docker compose exec api uv run mypy app --show-error-codes --pretty --show-column-numbers

typecheck-strict: ## Run VERY strict type checking (catches ALL errors)
	docker compose exec api uv run mypy app --follow-imports=normal --show-error-codes --pretty --no-error-summary 2>&1 | head -100

qa: ## Run all quality checks (lint + typecheck + test)
	@make lint
	@make typecheck
	@make test

# =============================================================================
# BASE DE DATOS
# =============================================================================

migrate: ## Run database migrations
	docker compose exec api uv run alembic upgrade head

migration: ## Create new migration (use: make migration MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a message. Usage: make migration MSG=\"description\""; \
		exit 1; \
	fi
	docker compose exec api uv run alembic revision --autogenerate -m "$(MSG)"

rollback: ## Rollback last migration
	docker compose exec api uv run alembic downgrade -1

seed: ## Seed database with complete Argentina data (assumes empty DB)
	docker compose exec api uv run python app/scripts/seed.py

seed-estrategias: ## Seed ONLY strategies and charts (PASO 5 y 6)
	docker compose exec api uv run python app/scripts/seed_estrategias_charts.py

create-superadmin: ## Create initial superadmin user interactively
	docker compose exec -it api uv run python -m app.commands.create_superadmin

# =============================================================================
# LIMPIEZA
# =============================================================================

clean: ## Remove all containers, volumes and clean cache
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

truncate-db: ## Empty all tables but keep structure (TRUNCATE)
	@echo "⚠️  WARNING: This will delete all table data but keep structure"
	@printf "Are you sure? (y/N): "; read confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose exec api uv run python -m app.scripts.truncate_all
	@echo "✅ All tables truncated successfully"

reset-db: ## Reset ONLY database (keeps Redis cache)
	@echo "⚠️  WARNING: This will delete ALL database data (keeps Redis)"
	@printf "Are you sure? (y/N): "; read confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose stop db
	docker compose rm -f db
	docker volume rm $$(docker volume ls -q | grep postgres) 2>/dev/null || true
	docker compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "✅ Database reset complete (Redis intact)"

reset-all: ## Reset EVERYTHING (database + Redis)
	@echo "⚠️  WARNING: This will delete ALL data (database + Redis)"
	@printf "Are you sure? (y/N): "; read confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v
	docker compose up -d db redis
	@sleep 5
	@make migrate
	@make seed
	@echo "✅ Full reset complete"

# =============================================================================
# PRODUCCIÓN
# =============================================================================

prod: ## Build and run production image
	docker build -f Dockerfile -t epidemiologia-api:latest .
	docker run -p 8000:8000 --env-file .env epidemiologia-api:latest

# =============================================================================
# SETUP INICIAL
# =============================================================================

setup: ## Initial setup (run once)
	@echo "Setting up project..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file - please edit it with your settings"; \
	fi
	@mkdir -p uploads logs
	@docker compose build
	@echo "✅ Setup complete! Run 'make up' to start"

# =============================================================================
# UTILIDADES
# =============================================================================

ps: ## Show running containers
	docker compose ps

stats: ## Show container stats
	docker stats --no-stream

exec: ## Execute command in container (use: make exec CMD="command")
	@if [ -z "$(CMD)" ]; then \
		echo "Error: Please provide a command. Usage: make exec CMD=\"command\""; \
		exit 1; \
	fi
	docker compose exec api $(CMD)
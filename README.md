# Sistema de Epidemiología - Stack Moderno

Sistema de vigilancia epidemiológica con dashboard interactivo.

## Tech Stack

| Componente | Tecnología |
|------------|------------|
| **Backend** | FastAPI + SQLModel + Celery |
| **Frontend** | Next.js + TypeScript + TanStack Query |
| **Base de datos** | PostgreSQL 16 + PostGIS |
| **Cache** | Redis |
| **Package Managers** | uv (Python) + pnpm (Node.js) |

## Quick Start

### Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Gestor de paquetes Python
- [pnpm](https://pnpm.io/installation) - Gestor de paquetes Node.js
- Make (preinstalado en macOS/Linux)

### Setup inicial (solo primera vez)

```bash
git clone <repo-url>
cd dashboard

make install   # Instalar dependencias
make up        # Levantar DB + Redis
make migrate   # Crear tablas
make seed      # Cargar datos iniciales
```

### Desarrollo diario

```bash
# Terminal 1 - Infraestructura
make up

# Terminal 2 - Backend API (http://localhost:8000)
make dev

# Terminal 3 - Frontend (http://localhost:3000)
make frontend
```

### Comandos disponibles

```bash
make help       # Ver todos los comandos

# Setup
make install    # Instalar dependencias (backend + frontend)

# Desarrollo
make up         # Levantar DB + Redis + pgweb
make down       # Detener contenedores
make logs       # Ver logs
make dev        # Backend con hot-reload
make frontend   # Frontend con hot-reload

# Base de datos
make migrate    # Aplicar migraciones
make migration m='descripcion'  # Crear migración
make seed       # Cargar datos iniciales
make reset      # Resetear DB (borra todo)

# Calidad
make lint       # Linter + formatter
make typecheck  # Type checking
make test       # Tests

# Producción
make prod       # Levantar stack de producción
```

## Estructura del Proyecto

```
dashboard/
├── compose.yaml           # Desarrollo (solo infraestructura)
├── compose.prod.yaml      # Producción (todos los servicios)
├── Makefile               # Comandos de desarrollo
├── backend/               # FastAPI + Celery
│   ├── app/
│   │   ├── api/           # Endpoints REST
│   │   ├── core/          # Configuración, seguridad, middleware
│   │   ├── domains/       # Lógica de negocio por dominio
│   │   └── scripts/       # Seeds, utilidades
│   ├── pyproject.toml     # Dependencias Python
│   └── Dockerfile
└── frontend/              # Next.js
    ├── src/
    ├── package.json       # Dependencias Node
    └── Dockerfile
```

## Arquitectura

Basado en [Docker Compose best practices](https://docs.docker.com/compose/how-tos/production/):

- `compose.yaml` - Desarrollo (solo infraestructura: DB, Redis, pgweb)
- `compose.prod.yaml` - Producción (todos los servicios containerizados)

### Modo Desarrollo

En desarrollo, solo la infraestructura corre en Docker (DB, Redis). El backend y frontend corren nativamente para hot-reload más rápido.

### Modo Producción

```bash
make prod  # docker compose -f compose.prod.yaml up -d
```

Todos los servicios corren en contenedores Docker con healthchecks y restart policies.

## Documentación API

Con el backend corriendo:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- pgweb (UI de DB): http://localhost:8081

## Más información

- [Backend README](backend/README.md) - Comandos, estructura y estándares de código

# Sistema de Epidemiología - Backend

API REST moderna para el sistema de vigilancia epidemiológica.

## Quick Start

Ver [README principal](../README.md) para setup completo del proyecto.

```bash
# Desde el root del proyecto
make up        # Levantar infraestructura
make dev       # Iniciar backend con hot-reload
```

## Comandos

### Dependencias

```bash
uv sync                    # Instalar dependencias
uv add <paquete>           # Agregar dependencia
uv add --dev <paquete>     # Agregar dependencia de desarrollo
```

### Base de datos

```bash
uv run alembic upgrade head                      # Aplicar migraciones
uv run alembic revision --autogenerate -m "msg"  # Crear nueva migración
uv run python app/scripts/seed.py                # Seed de datos
```

### Calidad de código

```bash
uv run ruff check . --fix  # Linter
uv run ruff format .       # Formatear
uv run ty check            # Type checking
uv run pytest              # Tests
```

## Stack tecnológico

- **FastAPI** - Framework web
- **PostgreSQL + PostGIS** - Base de datos con soporte geoespacial
- **Redis** - Cache y cola de tareas
- **Celery** - Procesamiento asíncrono
- **uv** - Gestión de dependencias (10-100x más rápido que pip)
- **ruff** - Linter y formatter
- **ty** - Type checker (Astral)

## Estructura del proyecto

```
backend/
├── app/
│   ├── api/v1/        # Endpoints REST por recurso
│   ├── core/          # Configuración, seguridad, middleware
│   ├── domains/       # Lógica de negocio por dominio
│   │   ├── autenticacion/
│   │   ├── vigilancia_nominal/
│   │   ├── vigilancia_agregada/
│   │   ├── territorio/
│   │   └── ...
│   └── scripts/       # Seeds, utilidades
├── alembic/           # Migraciones de base de datos
├── tests/
├── pyproject.toml     # Dependencias (uv)
├── Dockerfile         # Imagen de producción
└── Dockerfile.dev     # Imagen de desarrollo
```

## Documentación API

Con el backend corriendo:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contribuir

1. Crear feature branch
2. Hacer cambios
3. Ejecutar checks de calidad antes del commit:
   ```bash
   uv run ruff check . --fix
   uv run ruff format .
   uv run ty check
   uv run pytest
   ```
4. Crear PR

## Licencia

Propiedad del Ministerio de Salud.

---

## Documentacion Tecnica

Para documentacion detallada de la arquitectura, ver **[docs/](docs/README.md)**:

- [Arquitectura de Procesamiento](docs/arquitectura-procesamiento.md) - Como se cargan datos del SNVS
- [Sistema de Metricas](docs/sistema-metricas.md) - Como el frontend consulta datos

---

## Estandar de Codigo (Hybrid Spanglish)

Para mantener la consistencia y facilitar la comunicación con expertos del dominio, utilizamos un estándar híbrido:

### 1. Dominio y Negocio → ESPAÑOL 🇪🇸

Todo lo que represente conceptos del negocio debe estar en español.

- **Clases de Dominio**: `CasoEpidemiologico`, `NotificacionSemanal`, `Paciente`
- **Variables de Negocio**: `fecha_inicio_sintomas`, `edad_paciente`, `tipo_evento`
- **Métodos de Negocio**: `calcular_riesgo()`, `clasificar_caso()`, `iniciar_procesamiento()`

### 2. Infraestructura y Patrones → INGLÉS 🇺🇸

Los componentes puramente técnicos o patrones de diseño se mantienen en inglés.

- **Sufijos de Patrones**: `Repository`, `Service`, `Handler`, `Router`, `DTO`
- **Infraestructura**: `Job`, `Task`, `Cache`, `Session`, `Upload`
- **Ejemplo Combinado**: `CasoEpidemiologicoRepository`, `NotificacionService`

### 3. Documentación y Comentarios → ESPAÑOL 🇪🇸

Todo lo que explica el *qué* y el *por qué* debe estar en el idioma del equipo.

- **Docstrings**: `"""Calcula la tasa de incidencia acumulada."""`
- **Comentarios**: `# Validar si el paciente tiene antecedentes`

# Sistema de Epidemiología - Backend

API REST moderna para el sistema de vigilancia epidemiológica.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Make (macOS/Linux tienen preinstalado, Windows ver abajo)

### Windows
- **Opción 1 (recomendado):** Usar Git Bash (viene con Git)
- **Opción 2:** WSL2
- **Opción 3:** Sin Make, usar `run.cmd` en vez de `make`

### Setup inicial (solo primera vez)
```bash
# macOS/Linux/Git Bash
make setup

# Windows CMD/PowerShell
run.cmd setup
```

### Desarrollo diario
```bash
# macOS/Linux/Git Bash
make up      # Iniciar servicios
make down    # Detener servicios
make logs    # Ver logs

# Windows CMD/PowerShell
run.cmd up   # Iniciar servicios
run.cmd down # Detener servicios
run.cmd logs # Ver logs
```

## 📋 Comandos principales

| Comando | Descripción |
|---------|-------------|
| `make up` | Iniciar stack de desarrollo |
| `make down` | Detener servicios |
| `make logs` | Ver logs |
| `make test` | Ejecutar tests |
| `make lint` | Formatear código |
| `make shell` | Shell Python interactivo |
| `make migrate` | Ejecutar migraciones |

Ver todos los comandos: `make help`

## 🏗️ Stack tecnológico

- **FastAPI** - Framework web
- **PostgreSQL** - Base de datos
- **Redis** - Cache y cola de tareas
- **Celery** - Procesamiento asíncrono
- **Docker** - Containerización
- **uv** - Gestión de dependencias (10x más rápido que pip)

## 📁 Estructura del proyecto

```
backend/
├── app/
│   ├── api/        # Endpoints REST
│   ├── core/       # Configuración
│   ├── models/     # Modelos de DB
│   ├── schemas/    # Esquemas Pydantic
│   └── services/   # Lógica de negocio
├── compose.yaml    # Docker Compose
├── Dockerfile      # Producción
├── Dockerfile.dev  # Desarrollo
└── Makefile        # Comandos
```

## 🔧 Desarrollo

El proyecto usa Docker para desarrollo, garantizando consistencia entre todos los sistemas operativos.

### Testing
```bash
make test        # Ejecutar tests
make qa          # Lint + Type check + Tests
```

### Base de datos
```bash
make migrate                    # Aplicar migraciones
make migration MSG="descripción" # Crear nueva migración
make rollback                   # Revertir última migración
```

### Debugging
```bash
make shell       # Shell Python
make bash        # Shell Bash
make logs        # Ver todos los logs
make logs SERVICE=api  # Logs específicos
```

## 🚢 Producción

```bash
make prod  # Build y ejecutar imagen de producción
```

## 🛠️ Troubleshooting

### Resetear todo
```bash
make clean  # Limpiar containers y cache
make reset  # Resetear DB (⚠️ borra datos)
```

### Ver estado
```bash
make ps     # Containers activos
make stats  # Uso de recursos
```

## 📚 Documentación API

Con los servicios corriendo:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contribuir

1. Crear feature branch
2. Hacer cambios
3. Ejecutar `make qa` antes de commit
4. Crear PR

## 📝 Licencia

Propiedad del Ministerio de Salud.
# Epidemiología API

API del Sistema de Epidemiología

## Descripción

Backend API para el sistema de epidemiología.

## Requisitos Previos

### Instalar UV (Gestor de paquetes Python)

UV es un gestor de paquetes ultra-rápido para Python. Elige una opción según tu sistema:

#### macOS/Linux
```bash
# Opción 1: Instalación rápida con curl (RECOMENDADO)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Opción 2: Con Homebrew (macOS)
brew install uv

# Opción 3: Con pip
pip install uv

# Opción 4: Con pipx
pipx install uv
```

#### Windows
```powershell
# PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# O con pip
pip install uv
```

#### Verificar instalación
```bash
uv --version
```

## Instalación

```bash
# Configuración inicial (primera vez)
make setup

# Instalar/actualizar dependencias
make install
```

## Desarrollo

### Opción 1: Con Docker (Recomendado)
```bash
# Iniciar todos los servicios (API + PostgreSQL + Redis)
make dev-docker

# Detener servicios
make dev-docker-down
```

### Opción 2: Sin Docker
```bash
# Requiere PostgreSQL y Redis instalados localmente
make dev
```

## Comandos Útiles

```bash
# Ver todos los comandos disponibles
make help

# Migraciones de base de datos
make migrate                     # Aplicar migraciones
make makemigrations m="mensaje"  # Crear nueva migración

# Calidad de código
make qa                          # Ejecutar todos los checks
make test                        # Ejecutar tests
make lint                        # Linter
make format                      # Formatear código
```
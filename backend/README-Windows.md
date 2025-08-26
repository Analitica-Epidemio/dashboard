# Sistema de Epidemiología - Guía Windows

Esta guía te ayudará a configurar y ejecutar el Sistema de Epidemiología en Windows.

## 📋 Prerrequisitos

### Opción 1: Con Docker (Recomendado)
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Gestor de paquetes Python

### Opción 2: Sin Docker
- [Python 3.11+](https://www.python.org/downloads/windows/)
- [PostgreSQL 15+](https://www.postgresql.org/download/windows/)
- [Redis](https://github.com/tporadowski/redis/releases) (versión para Windows)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## 🚀 Instalación de uv

```powershell
# PowerShell (recomendado)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# O usando pip
pip install uv
```

## ⚡ Inicio Rápido

### Usando PowerShell (Recomendado)

```powershell
# 1. Configuración inicial (solo la primera vez)
.\run.ps1 setup

# 2. Edita el archivo .env con tus configuraciones

# 3. Opción A: Con Docker (recomendado)
.\run.ps1 dev-docker

# 3. Opción B: Sin Docker (requiere DB local)
.\run.ps1 dev
```

### Usando Batch (Alternativo)

```cmd
# 1. Configuración inicial (solo la primera vez)
run setup

# 2. Edita el archivo .env con tus configuraciones

# 3. Opción A: Con Docker (recomendado)
run dev-docker

# 3. Opción B: Sin Docker (requiere DB local)
run dev
```

## 📚 Comandos Disponibles

### PowerShell (`.\run.ps1`)

```powershell
# Ver todos los comandos disponibles
.\run.ps1 help

# Configuración
.\run.ps1 setup                 # Configuración inicial
.\run.ps1 install               # Instalar dependencias

# Desarrollo con Docker
.\run.ps1 dev-docker            # Iniciar con Docker
.\run.ps1 dev-docker-down       # Detener servicios
.\run.ps1 dev-docker-rebuild    # Reconstruir servicios
.\run.ps1 dev-docker-logs       # Ver logs
.\run.ps1 dev-docker-db-reset   # Reiniciar BD (⚠️ BORRA DATOS)

# Desarrollo sin Docker
.\run.ps1 dev                   # Iniciar servidor local

# Testing y Calidad
.\run.ps1 test                  # Ejecutar tests
.\run.ps1 test-coverage         # Tests con cobertura
.\run.ps1 lint                  # Linter
.\run.ps1 format                # Formatear código
.\run.ps1 typecheck             # Verificar tipos
.\run.ps1 qa                    # Todos los checks

# Base de Datos
.\run.ps1 migrate               # Ejecutar migraciones
.\run.ps1 makemigrations "msg"  # Crear migración
.\run.ps1 rollback              # Rollback migración
.\run.ps1 db-history            # Ver historial

# Utilidades
.\run.ps1 clean                 # Limpiar archivos temporales
.\run.ps1 shell                 # Shell de Python
.\run.ps1 logs                  # Ver logs
```

### Batch (`run.bat`)

```cmd
# Mismos comandos pero usando:
run comando

# Ejemplos:
run help
run setup
run dev-docker
run test
```

## 🐳 Desarrollo con Docker (Recomendado)

Esta es la forma más fácil de empezar:

```powershell
# 1. Configuración inicial
.\run.ps1 setup

# 2. Editar .env si es necesario

# 3. Iniciar todo el stack (PostgreSQL + Redis + API)
.\run.ps1 dev-docker
```

Esto iniciará:
- **PostgreSQL** en puerto `5432`
- **Redis** en puerto `6379`
- **API** en puerto `8000` con hot-reload

### Comandos útiles de Docker:

```powershell
# Ver logs en tiempo real
.\run.ps1 dev-docker-logs

# Detener todo
.\run.ps1 dev-docker-down

# Reconstruir (si cambias dependencias)
.\run.ps1 dev-docker-rebuild

# Reiniciar BD desde cero (⚠️ BORRA TODOS LOS DATOS)
.\run.ps1 dev-docker-db-reset
```

## 💻 Desarrollo sin Docker

Si prefieres instalar PostgreSQL y Redis localmente:

### 1. Instalar PostgreSQL

1. Descargar desde [postgresql.org](https://www.postgresql.org/download/windows/)
2. Durante instalación, recordar usuario/contraseña
3. Crear base de datos:

```sql
-- Conectar como superuser y ejecutar:
CREATE DATABASE epidemiologia_db;
CREATE USER epidemiologia_user WITH PASSWORD 'epidemiologia_password';
GRANT ALL PRIVILEGES ON DATABASE epidemiologia_db TO epidemiologia_user;
```

### 2. Instalar Redis

1. Descargar desde [releases de Redis for Windows](https://github.com/tporadowski/redis/releases)
2. Extraer y ejecutar `redis-server.exe`

### 3. Configurar y ejecutar

```powershell
# 1. Configurar proyecto
.\run.ps1 setup

# 2. Editar .env con la URL de tu BD:
# DATABASE_URL=postgresql+asyncpg://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db

# 3. Ejecutar servidor
.\run.ps1 dev
```

## 🔧 Configuración del Archivo .env

Ejemplo de archivo `.env` para Windows:

```env
# Entorno
ENVIRONMENT=development
DEBUG=true

# Base de Datos - Ajustar según tu configuración
DATABASE_URL=postgresql+asyncpg://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db

# Seguridad
SECRET_KEY=tu_clave_secreta_super_fuerte_cambiar_en_produccion
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS para desarrollo
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

## 🧪 Testing

```powershell
# Ejecutar tests
.\run.ps1 test

# Tests con reporte de cobertura
.\run.ps1 test-coverage

# Ver reporte HTML de cobertura
start htmlcov/index.html
```

## 📝 Calidad de Código

```powershell
# Ejecutar todos los checks
.\run.ps1 qa

# O individualmente:
.\run.ps1 lint      # Linter (ruff)
.\run.ps1 format    # Formatear código
.\run.ps1 typecheck # Verificar tipos (mypy)
```

## 🗄️ Base de Datos

```powershell
# Ver comandos disponibles de BD
.\run.ps1 db-history

# Crear nueva migración (si cambias modelos)
.\run.ps1 makemigrations "descripcion del cambio"

# Aplicar migraciones
.\run.ps1 migrate

# Rollback de la última migración
.\run.ps1 rollback
```

## 🚨 Solución de Problemas

### Error: "uv no se reconoce como comando"
```powershell
# Reinstalar uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Reiniciar PowerShell/CMD
```

### Error: "Docker no funciona"
1. Asegúrate de que Docker Desktop esté ejecutándose
2. Verifica que WSL2 esté instalado y configurado
3. Reinicia Docker Desktop

### Error: "No se puede conectar a PostgreSQL"
1. Verifica que PostgreSQL esté ejecutándose
2. Confirma usuario/contraseña en `.env`
3. Verifica que la BD `epidemiologia_db` existe

### Error: "Puertos ocupados"
```powershell
# Ver qué está usando el puerto 8000
netstat -ano | findstr :8000

# Matar proceso si es necesario (cambiar PID)
taskkill /PID 1234 /F
```

## 📱 Acceso a la Aplicación

Una vez que el servidor esté ejecutándose:

- **API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🆘 Obtener Ayuda

```powershell
# Ver todos los comandos
.\run.ps1 help

# Para problemas específicos, revisar logs
.\run.ps1 logs
```
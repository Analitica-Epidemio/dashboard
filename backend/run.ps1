# =============================================================================
# Sistema de Epidemiología - Script PowerShell para Windows
# =============================================================================

param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Command = "help",
    
    [Parameter(Mandatory=$false, Position=1)]
    [string]$Message = ""
)

# Colores para output
function Write-ColorOutput {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Write-Success { param([string]$Text) Write-ColorOutput $Text "Green" }
function Write-Warning { param([string]$Text) Write-ColorOutput $Text "Yellow" }
function Write-Error { param([string]$Text) Write-ColorOutput $Text "Red" }
function Write-Info { param([string]$Text) Write-ColorOutput $Text "Cyan" }

# =============================================================================
# FUNCIONES PRINCIPALES
# =============================================================================

function Show-Help {
    Write-ColorOutput "Sistema de Epidemiología - Comandos disponibles" "Magenta"
    Write-ColorOutput "================================================" "Magenta"
    Write-Host ""
    Write-ColorOutput "INICIO RÁPIDO:" "Yellow"
    Write-Host "  .\run.ps1 setup        → Configuración inicial del proyecto (primera vez)"
    Write-Host "  .\run.ps1 dev-docker   → Desarrollo CON Docker (incluye DB + Redis)"
    Write-Host "  .\run.ps1 dev          → Desarrollo SIN Docker (requiere DB local)"
    Write-Host ""
    Write-ColorOutput "CONFIGURACIÓN:" "Yellow"
    Write-Host "  setup                 → Configuración inicial completa"
    Write-Host "  install               → Instala/actualiza dependencias"
    Write-Host ""
    Write-ColorOutput "DESARROLLO CON DOCKER:" "Yellow"
    Write-Host "  dev-docker            → Inicia desarrollo CON Docker"
    Write-Host "  dev-docker-down       → Detiene los servicios Docker"
    Write-Host "  dev-docker-rebuild    → Reconstruye y reinicia servicios Docker"
    Write-Host "  dev-docker-logs       → Ver logs de los servicios Docker"
    Write-Host "  dev-docker-db-reset   → Reinicia la BD Docker desde cero"
    Write-Host ""
    Write-ColorOutput "DESARROLLO SIN DOCKER:" "Yellow"
    Write-Host "  dev                   → Inicia desarrollo SIN Docker"
    Write-Host ""
    Write-ColorOutput "TESTING Y CALIDAD:" "Yellow"
    Write-Host "  test                  → Ejecuta los tests"
    Write-Host "  test-coverage         → Ejecuta tests con reporte de cobertura"
    Write-Host "  lint                  → Ejecuta el linter y arregla problemas"
    Write-Host "  format                → Formatea el código"
    Write-Host "  typecheck             → Verifica tipos con mypy"
    Write-Host "  qa                    → Ejecuta todos los checks de calidad"
    Write-Host ""
    Write-ColorOutput "BASE DE DATOS:" "Yellow"
    Write-Host "  migrate               → Ejecuta las migraciones pendientes"
    Write-Host "  makemigrations 'msg'  → Genera nueva migración"
    Write-Host "  rollback              → Rollback de la última migración"
    Write-Host "  db-history            → Ver historial de migraciones"
    Write-Host ""
    Write-ColorOutput "PRODUCCIÓN:" "Yellow"
    Write-Host "  docker-prod           → Construye y ejecuta para producción"
    Write-Host "  docker-build          → Construye la imagen Docker de producción"
    Write-Host ""
    Write-ColorOutput "UTILIDADES:" "Yellow"
    Write-Host "  clean                 → Limpia archivos temporales"
    Write-Host "  shell                 → Abre shell de Python"
    Write-Host "  logs                  → Ver logs de la aplicación"
}

function Setup-Project {
    Write-Info "🚀 Configurando proyecto por primera vez..."
    Write-Host "1. Verificando archivo .env..."
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Success "✅ Archivo .env creado desde .env.example"
            Write-Warning "⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones"
        } else {
            Write-Error "❌ No se encontró .env.example"
            exit 1
        }
    } else {
        Write-Success "✅ Archivo .env ya existe"
    }
    
    Write-Host "2. Creando directorios necesarios..."
    if (-not (Test-Path "uploads")) { New-Item -ItemType Directory -Name "uploads" | Out-Null }
    if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Name "logs" | Out-Null }
    
    Write-Host "3. Instalando dependencias con uv..."
    & uv sync --all-extras
    
    Write-Host ""
    Write-Success "✅ Configuración completada!"
    Write-Host ""
    Write-ColorOutput "🔥 PRÓXIMOS PASOS:" "Yellow"
    Write-Host "   1. Edita el archivo .env con tus configuraciones"
    Write-Host "   2. Elige cómo ejecutar el proyecto:"
    Write-Host "      • CON Docker:    .\run.ps1 dev-docker"
    Write-Host "      • SIN Docker:    .\run.ps1 dev"
}

function Install-Dependencies {
    Write-Info "📦 Instalando/actualizando dependencias..."
    & uv sync --all-extras
}

# =============================================================================
# DESARROLLO CON DOCKER
# =============================================================================

function Start-DevDocker {
    Write-Info "🐳 Iniciando stack de desarrollo con Docker..."
    Write-Host "   • PostgreSQL en puerto 5432"
    Write-Host "   • Redis en puerto 6379"
    Write-Host "   • API en puerto 8000 con hot-reload"
    & docker-compose -f docker-compose.dev.yml up
}

function Stop-DevDocker {
    Write-Info "🛑 Deteniendo servicios Docker..."
    & docker-compose -f docker-compose.dev.yml down
}

function Rebuild-DevDocker {
    Write-Info "🔄 Reconstruyendo y reiniciando servicios Docker..."
    & docker-compose -f docker-compose.dev.yml up --build
}

function Show-DevDockerLogs {
    Write-Info "📋 Ver logs de los servicios Docker..."
    & docker-compose -f docker-compose.dev.yml logs -f
}

function Reset-DevDockerDB {
    Write-Warning "⚠️  ADVERTENCIA: Esto eliminará TODOS los datos de la base de datos"
    $confirm = Read-Host "¿Estás seguro? (y/N)"
    if ($confirm -ne "y") {
        Write-Host "Operación cancelada"
        return
    }
    
    Write-Host "Eliminando servicios Docker..."
    & docker-compose -f docker-compose.dev.yml down
    
    Write-Host "Eliminando volumen de base de datos..."
    & docker volume rm epi_dashboard_postgres_data_dev 2>$null
    
    Write-Success "✅ Base de datos eliminada. Se creará una nueva al ejecutar '.\run.ps1 dev-docker'"
}

# =============================================================================
# DESARROLLO SIN DOCKER
# =============================================================================

function Start-Dev {
    Write-Info "💻 Iniciando servidor de desarrollo local..."
    Write-Warning "   ⚠️  Requiere PostgreSQL y Redis instalados localmente"
    & uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# =============================================================================
# TESTING Y CALIDAD
# =============================================================================

function Run-Tests {
    Write-Info "🧪 Ejecutando tests..."
    & uv run pytest
}

function Run-TestCoverage {
    Write-Info "📊 Ejecutando tests con reporte de cobertura..."
    & uv run pytest --cov=app --cov-report=html --cov-report=term
}

function Run-Lint {
    Write-Info "🔍 Ejecutando linter..."
    & uv run ruff check . --fix
}

function Run-Format {
    Write-Info "💅 Formateando código..."
    & uv run ruff format .
}

function Run-TypeCheck {
    Write-Info "🔎 Verificando tipos con mypy..."
    & uv run mypy app
}

function Run-QA {
    Write-Info "✅ Ejecutando todos los checks de calidad..."
    Run-Lint
    Run-Format
    Run-TypeCheck
    Run-Tests
}

# =============================================================================
# BASE DE DATOS
# =============================================================================

function Run-Migrate {
    Write-Info "🗄️ Ejecutando migraciones pendientes..."
    & uv run alembic upgrade head
}

function Make-Migration {
    if ($Message -eq "") {
        Write-Error "Error: Proporciona una descripción. Uso: .\run.ps1 makemigrations 'descripción'"
        return
    }
    Write-Info "📝 Generando nueva migración..."
    & uv run alembic revision --autogenerate -m $Message
}

function Run-Rollback {
    Write-Info "↩️ Rollback de la última migración..."
    & uv run alembic downgrade -1
}

function Show-DBHistory {
    Write-Info "📜 Ver historial de migraciones..."
    & uv run alembic history
}

# =============================================================================
# PRODUCCIÓN
# =============================================================================

function Start-DockerProd {
    Write-Info "🚢 Construyendo y ejecutando para producción..."
    & docker-compose up --build
}

function Build-Docker {
    Write-Info "🏗️ Construyendo imagen Docker de producción..."
    & docker build -t epidemiologia-api .
}

# =============================================================================
# UTILIDADES
# =============================================================================

function Clean-Project {
    Write-Info "🧹 Limpiando archivos temporales..."
    
    # Eliminar directorios __pycache__
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | ForEach-Object {
        Remove-Item -Path $_ -Recurse -Force
    }
    
    # Eliminar archivos .pyc, .pyo, .coverage
    Get-ChildItem -Path . -Recurse -Include "*.pyc", "*.pyo", "*.coverage" | Remove-Item -Force
    
    # Eliminar otros directorios temporales
    $dirsToRemove = @("*.egg-info", ".pytest_cache", ".mypy_cache", "htmlcov")
    foreach ($pattern in $dirsToRemove) {
        Get-ChildItem -Path . -Recurse -Directory -Name $pattern | ForEach-Object {
            Remove-Item -Path $_ -Recurse -Force
        }
    }
    
    Write-Success "✅ Limpieza completada"
}

function Open-Shell {
    Write-Info "🐚 Abriendo shell de Python..."
    & uv run python
}

function Show-Logs {
    Write-Info "📜 Ver logs de la aplicación..."
    if (Test-Path "logs\*.log") {
        Get-Content "logs\*.log" -Wait
    } else {
        Write-Host "No hay logs disponibles"
    }
}

# =============================================================================
# ROUTER DE COMANDOS
# =============================================================================

switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Setup-Project }
    "install" { Install-Dependencies }
    "dev-docker" { Start-DevDocker }
    "dev-docker-down" { Stop-DevDocker }
    "dev-docker-rebuild" { Rebuild-DevDocker }
    "dev-docker-logs" { Show-DevDockerLogs }
    "dev-docker-db-reset" { Reset-DevDockerDB }
    "dev" { Start-Dev }
    "test" { Run-Tests }
    "test-coverage" { Run-TestCoverage }
    "lint" { Run-Lint }
    "format" { Run-Format }
    "typecheck" { Run-TypeCheck }
    "qa" { Run-QA }
    "migrate" { Run-Migrate }
    "makemigrations" { Make-Migration }
    "rollback" { Run-Rollback }
    "db-history" { Show-DBHistory }
    "docker-prod" { Start-DockerProd }
    "docker-build" { Build-Docker }
    "clean" { Clean-Project }
    "shell" { Open-Shell }
    "logs" { Show-Logs }
    default { 
        Write-Error "Comando no reconocido: $Command"
        Write-Host ""
        Show-Help 
    }
}
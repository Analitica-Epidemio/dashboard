# Dockerfile para Sistema de Epidemiología Moderna
# Soporte opcional de Docker con optimizaciones para producción

# =============================================================================
# STAGE 1: Builder stage con uv para instalar dependencias
# =============================================================================
FROM python:3.11-slim as builder

# Instalar uv para gestión rápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Configurar directorio de trabajo
WORKDIR /app

# Variables de entorno para uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copiar archivos de configuración de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias en un directorio específico
RUN uv sync --frozen --no-install-project --no-dev --no-editable

# =============================================================================
# STAGE 2: Runtime stage optimizado para producción
# =============================================================================
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    libpq5 \
    libmagic1 \
    # Dependencias para Playwright\
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    # Dependencias adicionales para Playwright en slim\
    libglib2.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libharfbuzz0b \
    libhyphen0 \
    libmanette-0.2-0 \
    libopus0 \
    libpango-1.0-0 \
    libsecret-1-0 \
    libwebpdemux2 \
    libwoff1 \
    libx264-163 \
    libenchant-2-2 \
    gstreamer1.0-libav \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r epidemiologia && useradd -r -g epidemiologia epidemiologia

# Configurar directorio de trabajo
WORKDIR /app

# Copiar las dependencias instaladas desde el builder
COPY --from=builder --chown=epidemiologia:epidemiologia /app/.venv /app/.venv

# Configurar PATH para usar el entorno virtual
ENV PATH="/app/.venv/bin:$PATH"

# Copiar código de la aplicación
COPY --chown=epidemiologia:epidemiologia . .

# Instalar Playwright browsers (como root antes de cambiar de usuario)
USER root
RUN python -m playwright install chromium --with-deps
RUN chown -R epidemiologia:epidemiologia /ms-playwright

# Crear directorios necesarios
RUN mkdir -p /app/uploads /app/logs \
    && chown -R epidemiologia:epidemiologia /app/uploads /app/logs

# Variables de entorno para producción
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
# Playwright configuration
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Exponer puerto
EXPOSE 8000

# Cambiar a usuario no-root
USER epidemiologia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
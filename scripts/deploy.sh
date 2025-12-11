#!/usr/bin/env bash
#
# Deploy Blue-Green via SSH (zero downtime)
#
# Uso:
#   ./scripts/deploy.sh          # Deploy blue-green
#   ./scripts/deploy.sh setup    # Setup inicial del servidor
#   ./scripts/deploy.sh status   # Ver estado
#   ./scripts/deploy.sh logs     # Ver logs
#   ./scripts/deploy.sh ssh      # Conectar al servidor
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

log() { echo -e "${BLUE}>>>${NC} $1"; }
ok() { echo -e "${GREEN}[OK]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =============================================================================
# Config
# =============================================================================
load_config() {
    local env_file="${PROJECT_DIR}/.env.deploy"
    [[ -f "$env_file" ]] || env_file="${PROJECT_DIR}/.env"
    [[ -f "$env_file" ]] || err "No existe .env.deploy ni .env"
    source "$env_file"

    : "${SSH_HOST:?'SSH_HOST requerido'}"
    : "${SSH_USER:?'SSH_USER requerido'}"
    APP_NAME="${APP_NAME:-epidemiologia}"
    SSH_PORT="${SSH_PORT:-22}"
    REMOTE_DIR="${REMOTE_DIR:-/opt/$APP_NAME}"

    SSH_OPTS="-o StrictHostKeyChecking=accept-new -A"
    [[ -n "${SSH_KEY:-}" ]] && SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
    SSH="ssh $SSH_OPTS -p $SSH_PORT $SSH_USER@$SSH_HOST"
}

# =============================================================================
# Setup inicial (solo una vez)
# =============================================================================
cmd_setup() {
    log "Setup inicial del servidor..."

    $SSH << EOF
set -e
echo ">>> Creando directorio..."
sudo mkdir -p $REMOTE_DIR
sudo chown \$USER:\$USER $REMOTE_DIR

echo ">>> Inicializando ambiente activo..."
echo "blue" > $REMOTE_DIR/active_env

echo ""
echo "Setup completado. Ahora:"
echo "  1. Clona el repo: cd $REMOTE_DIR && git clone <url> app"
echo "  2. Copia infra/nginx.conf a /etc/nginx/sites-enabled/${APP_NAME}.conf"
echo "  3. Ejecuta: make deploy"
EOF
    ok "Setup completado"
}

# =============================================================================
# Deploy
# =============================================================================
cmd_deploy() {
    log "Conectando a $SSH_USER@$SSH_HOST..."
    $SSH "echo ok" &>/dev/null || err "No se pudo conectar"

    # Determinar ambiente
    local active=$($SSH "cat $REMOTE_DIR/active_env 2>/dev/null || echo blue")
    local target="green"
    [[ "$active" == "green" ]] && target="blue"

    # Puertos
    local frontend_port=3002 api_port=8002
    [[ "$target" == "blue" ]] && frontend_port=3001 api_port=8001

    log "Activo: $active -> Deployando: $target (puertos $frontend_port/$api_port)"

    # Subir .env
    log "Subiendo .env..."
    {
        echo "APP_NAME=${APP_NAME}"
        echo "DB_NAME=${DB_NAME:?requerido}"
        echo "DB_USER=${DB_USER:?requerido}"
        echo "DB_PASSWORD=${DB_PASSWORD:?requerido}"
        echo "SECRET_KEY=${SECRET_KEY:?requerido}"
        echo "NEXTAUTH_SECRET=${NEXTAUTH_SECRET:-$SECRET_KEY}"
        echo "NEXTAUTH_URL=${NEXTAUTH_URL:-$FRONTEND_URL}"
        echo "NEXT_PUBLIC_API_HOST=${NEXT_PUBLIC_API_HOST:-http://localhost:8000}"
        echo "FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}"
        echo "CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000}"
        echo "ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost}"
        echo "GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY:-}"
        echo "ENV_COLOR=$target"
        echo "FRONTEND_PORT=$frontend_port"
        echo "API_PORT=$api_port"
    } | $SSH "cat > $REMOTE_DIR/.env"

    # Deploy
    log "Ejecutando deploy..."
    $SSH << EOF
set -e
cd $REMOTE_DIR

echo ""
echo "1/7 Bajando cambios del repositorio..."
git pull --ff-only

echo ""
echo "2/7 Construyendo nuevas imagenes (esto puede tardar unos minutos)..."
sudo docker compose -f compose.prod.yaml build api frontend

echo ""
echo "3/7 Verificando infraestructura (DB, Redis)..."
sudo docker compose -f compose.prod.infra.yaml -p ${APP_NAME}_infra up -d --no-recreate
sleep 2

echo ""
echo "4/7 Levantando aplicacion ($target)..."
sudo docker compose -f compose.prod.yaml -p ${APP_NAME}_$target up -d

echo ""
echo "5/7 Verificando que la aplicacion responda..."
for i in {1..20}; do
    if curl -sf http://localhost:$api_port/health > /dev/null; then
        echo "    OK - La aplicacion responde correctamente"
        break
    fi
    echo "    Esperando... (intento \$i de 20)"
    sleep 3
done
curl -sf http://localhost:$api_port/health > /dev/null || { echo "ERROR: La aplicacion no responde"; exit 1; }

echo ""
echo "6/7 Aplicando migraciones de base de datos..."
sudo docker compose -f compose.prod.yaml -p ${APP_NAME}_$target exec -T api alembic upgrade head || true

echo ""
echo "7/7 Cambiando trafico a la nueva version ($target)..."
sudo sed -i "s/localhost:300[0-9]/localhost:$frontend_port/g; s/localhost:800[0-9]/localhost:$api_port/g" /etc/nginx/sites-enabled/${APP_NAME}.conf
sudo nginx -t && sudo nginx -s reload
echo "$target" > $REMOTE_DIR/active_env
echo "    Ambiente activo guardado: $target"

echo ""
echo "8/8 Apagando version anterior ($active)..."
sudo docker compose -f compose.prod.yaml -p ${APP_NAME}_$active stop 2>/dev/null || true

echo ""
echo "Limpiando imagenes viejas..."
docker image prune -f > /dev/null
EOF

    ok "Deploy completado - Ambiente activo: $target"
}

# =============================================================================
# Otros comandos
# =============================================================================
cmd_status() {
    $SSH << EOF
echo "=== Ambiente activo ==="
cat $REMOTE_DIR/active_env 2>/dev/null || echo "No configurado"
echo ""
echo "=== Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "${APP_NAME}_|NAMES"
EOF
}

cmd_logs() {
    local active=$($SSH "cat $REMOTE_DIR/active_env 2>/dev/null || echo blue")
    $SSH "cd $REMOTE_DIR && sudo docker compose -f compose.prod.yaml -p ${APP_NAME}_\$active logs -f ${2:-api}"
}

cmd_rollback() {
    log "Iniciando rollback..."

    local active=$($SSH "cat $REMOTE_DIR/active_env 2>/dev/null || echo blue")
    local target="green"
    [[ "$active" == "green" ]] && target="blue"

    local frontend_port=3002 api_port=8002
    [[ "$target" == "blue" ]] && frontend_port=3001 api_port=8001

    log "Volviendo de $active a $target..."

    $SSH << EOF
set -e

echo "1/3 Levantando version anterior ($target)..."
cd $REMOTE_DIR
sudo docker compose -f compose.prod.yaml -p ${APP_NAME}_$target up -d

echo "2/3 Esperando que arranque..."
sleep 10
curl -sf http://localhost:$api_port/health > /dev/null || { echo "ERROR: No responde"; exit 1; }

echo "3/3 Cambiando trafico..."
sudo sed -i "s/localhost:300[0-9]/localhost:$frontend_port/g; s/localhost:800[0-9]/localhost:$api_port/g" /etc/nginx/sites-enabled/${APP_NAME}.conf
sudo nginx -t && sudo nginx -s reload
echo "$target" > $REMOTE_DIR/active_env

echo "Apagando version con bug ($active)..."
sudo docker compose -f compose.prod.yaml -p ${APP_NAME}_$active stop 2>/dev/null || true
EOF

    ok "Rollback completado - Ahora activo: $target"
}

# =============================================================================
# Main
# =============================================================================
load_config

case "${1:-deploy}" in
    deploy)   cmd_deploy ;;
    setup)    cmd_setup ;;
    status)   cmd_status ;;
    logs)     cmd_logs "$@" ;;
    rollback) cmd_rollback ;;
    ssh)      $SSH ;;
    *)        echo "Uso: $0 [deploy|setup|status|logs|rollback|ssh]"; exit 1 ;;
esac

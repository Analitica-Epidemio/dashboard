#!/bin/bash
#
# Script para descargar datos de municipios de Argentina desde datos.gob.ar
#
# Descarga municipios con geometrías de polígonos completas desde la API Georef
# y filtra los municipios de Chubut.
#
# Uso: ./download_municipios.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data/geojson"

echo "======================================================================"
echo "DESCARGA DE MUNICIPIOS DESDE DATOS.GOB.AR"
echo "======================================================================"
echo ""

# Crear directorio si no existe
mkdir -p "$DATA_DIR"

# Descargar todos los municipios de Argentina
echo "1️⃣ Descargando municipios de Argentina..."
curl -L -o "$DATA_DIR/municipios-argentina.geojson" \
  "https://infra.datos.gob.ar/georef/municipios.geojson"

FILE_SIZE=$(ls -lh "$DATA_DIR/municipios-argentina.geojson" | awk '{print $5}')
echo "✅ Descargado: $FILE_SIZE"
echo ""

# Filtrar municipios de Chubut (provincia id = "26")
echo "2️⃣ Filtrando municipios de Chubut..."
jq '.features |= map(select(.properties.provincia.id == "26"))' \
  "$DATA_DIR/municipios-argentina.geojson" > "$DATA_DIR/municipios-chubut.geojson"

CHUBUT_COUNT=$(jq '.features | length' "$DATA_DIR/municipios-chubut.geojson")
CHUBUT_SIZE=$(ls -lh "$DATA_DIR/municipios-chubut.geojson" | awk '{print $5}')
echo "✅ Municipios de Chubut: $CHUBUT_COUNT ($CHUBUT_SIZE)"
echo ""

# Mostrar algunos municipios principales
echo "📍 Municipios principales de Chubut:"
jq -r '.features[].properties | select(.nombre == "Comodoro Rivadavia" or .nombre == "Trelew" or .nombre == "Rawson" or .nombre == "Puerto Madryn") | "  - \(.nombre) (ID: \(.id))"' \
  "$DATA_DIR/municipios-chubut.geojson"

echo ""
echo "======================================================================"
echo "✅ DESCARGA COMPLETADA"
echo "======================================================================"
echo ""
echo "Archivos generados:"
echo "  - $DATA_DIR/municipios-argentina.geojson"
echo "  - $DATA_DIR/municipios-chubut.geojson"
echo ""

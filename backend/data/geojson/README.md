# Datos Geográficos - GeoJSON

Este directorio contiene archivos GeoJSON con datos geográficos de Argentina.

## Archivos

### Municipios

- **`municipios-argentina.geojson`** (~2 MB)
  - Todos los municipios de Argentina con geometrías de polígonos
  - Fuente: [datos.gob.ar - API Georef](https://apis.datos.gob.ar/georef/)
  - Incluye: Municipios, Comunas y Comisiones de fomento
  - Geometría: Polygon y MultiPolygon

- **`municipios-chubut.geojson`** (~83 KB)
  - 46 municipios de la provincia de Chubut
  - Filtrado desde municipios-argentina.geojson
  - Incluye ciudades principales: Comodoro Rivadavia, Trelew, Rawson, Puerto Madryn

### Localidades

- **`chubut_localidades.geojson`** (~46 KB)
  - 91 localidades de Chubut
  - Fuente: API Georef
  - Geometría: Point (centroides solamente, no polígonos)

## Estructura de datos

### Municipios (ejemplo)

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[-69.948, -45.294], ...]]
  },
  "properties": {
    "id": "260049",
    "nombre": "Comodoro Rivadavia",
    "nombre_completo": "Municipio Comodoro Rivadavia",
    "categoria": "Municipio",
    "provincia": {
      "id": "26",
      "nombre": "Chubut"
    },
    "centroide": {
      "lon": -67.5,
      "lat": -45.86
    },
    "fuente": "IGN"
  }
}
```

### Localidades (ejemplo)

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-67.4739, -45.8397]
  },
  "properties": {
    "id": "2602103022",
    "nombre": "Comodoro Rivadavia",
    "departamento_id": "26021",
    "departamento_nombre": "Escalante",
    "provincia_id": "26",
    "provincia_nombre": "Chubut"
  }
}
```

## Cómo actualizar los datos

Para volver a descargar los datos más recientes:

```bash
cd backend
./scripts/download_municipios.sh
```

Este script:
1. Descarga todos los municipios de Argentina desde datos.gob.ar
2. Filtra y guarda solo los municipios de Chubut
3. Reporta el número de municipios descargados

## Diferencias: Municipios vs Localidades

- **Municipios**: Entidades administrativas con polígonos delimitados (fronteras oficiales)
- **Localidades**: Centros urbanos/poblados con solo coordenadas de punto (sin fronteras)

Para visualización en mapas:
- Usar **municipios** para colorear áreas geográficas
- Usar **localidades** para marcadores puntuales

## Referencias

- [API Georef - Documentación](https://datosgobar.github.io/georef-ar-api/)
- [datos.gob.ar - Portal de datos abiertos](https://datos.gob.ar/)
- [IGN - Instituto Geográfico Nacional](https://www.ign.gob.ar/)

# Scripts del Sistema

Carpeta de scripts de mantenimiento y carga de datos.

## Estructura

```
scripts/
├── seed.py           # Orquestador principal
└── seeds/            # Seeds específicos
    ├── strategies.py # Estrategias de vigilancia
    └── *.py         # Otros seeds futuros
```

## Uso

### Ejecutar todos los seeds
```bash
# Con Docker (recomendado)
make seed

# Directamente
python -m app.scripts.seed
```

### Ejecutar seed específico
```bash
python -m app.scripts.seed --only strategies
```

## Agregar nuevo seed

1. Crear archivo en `seeds/nombre.py` con función `main()`
2. Importar en `seeds/__init__.py`
3. Agregar al array en `seed.py`

## Seeds disponibles

- **strategies**: Estrategias de vigilancia epidemiológica
- (Agregar más según se creen)
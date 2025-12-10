# Plan de Migración: Sistema Legacy → Sistema de Métricas

## Resumen Ejecutivo

El backend tiene **dos sistemas paralelos** para consultar datos epidemiológicos:

- **Sistema Legacy**: `charts/`, `analytics/`, `domains/dashboard/`
- **Sistema Nuevo**: `metricas/` - ORM con builders, tipado, extensible

Este documento detalla el plan para migrar todo al sistema de métricas y eliminar el código legacy.

---

## 1. Arquitectura Actual (Problema)

```
┌─────────────────────────────────────────────────────────────────┐
│                      SISTEMA LEGACY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  api/v1/charts/                                                  │
│  ├── get_dashboard.py      → DashboardChart + ChartDataProcessor │
│  ├── get_disponibles.py    → DashboardChart model               │
│  ├── get_indicadores.py    → SQL raw                            │
│  └── generate_spec.py      → ChartSpecGenerator                 │
│                                                                  │
│  api/v1/analytics/                                               │
│  └── router.py             → SQL raw directo                    │
│                                                                  │
│  domains/dashboard/                                              │
│  ├── processors.py                                              │
│  ├── models.py             → DashboardChart (tabla BD)          │
│  ├── conditions.py         → Lógica show/hide charts            │
│  ├── age_groups_config.py  → Config grupos etarios              │
│  └── schemas.py            → Schemas Pydantic                   │
│                                                                  │
│  domains/charts/                                                 │
│  └── services/                                                   │
│      ├── spec_generator.py → Genera specs de charts             │
│      └── renderer.py       → Renderiza charts para PDF          │
│                                                                  │
│  FRONTEND que lo usa:                                            │
│  - features/reports/api.ts  (useChartsDisponibles, etc.)        │
│  - features/boletines/api.ts (useChartsDisponibles)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      SISTEMA NUEVO                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  api/v1/metricas/                                                │
│  └── router.py             → MetricService.query()              │
│                                                                  │
│  domains/metricas/                                               │
│  ├── service.py            → Orquestador principal              │
│  ├── builders/                                                   │
│  │   ├── base.py           → MetricQueryBuilder (ABC)           │
│  │   ├── clinico.py        → Vigilancia clínica                 │
│  │   ├── laboratorio.py    → Vigilancia laboratorio             │
│  │   ├── hospitalario.py   → Vigilancia hospitalaria            │
│  │   └── nominal.py        → Vigilancia nominal                 │
│  ├── registry/                                                   │
│  │   ├── metrics.py        → Definición de métricas             │
│  │   └── dimensions.py     → Definición de dimensiones          │
│  └── criteria/             → Filtros reutilizables              │
│                                                                  │
│  FRONTEND que lo usa:                                            │
│  - features/metricas/      (useMetricQuery, hooks)              │
│  - app/vigilancia/         (clinica, laboratorio, etc.)         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Plan de Migración

### Fase 1: Preparar sistema de métricas

#### 1.1 Agregar métricas faltantes al registry

Revisar qué consultas hace `processors.py` y asegurar que existan en `metricas/registry/metrics.py`:

```python
# Métricas a verificar/agregar:
- casos_por_semana_epidemiologica
- casos_por_grupo_etario
- casos_por_provincia
- casos_por_clasificacion
- piramide_poblacional
- corredor_endemico (ya existe)
- distribucion_agentes (ya existe como muestras_positivas + dimensión)
```

#### 1.2 Agregar endpoint de "chart specs" a metricas

El frontend necesita saber qué charts mostrar. Agregar:

```python
# api/v1/metricas/router.py

@router.get("/charts-disponibles")
async def get_charts_disponibles(
    grupo_id: Optional[int] = None,
    # ... filtros
) -> ChartsDisponiblesResponse:
    """
    Retorna lista de charts disponibles según filtros.
    Reemplaza /api/v1/charts/disponibles
    """
    pass
```

### Fase 2: Migrar frontend

#### 2.1 Migrar `features/reports/api.ts`

**Antes:**

```typescript
export function useChartsDisponibles() {
  return $api.useQuery("get", "/api/v1/charts/disponibles");
}

export function useDashboardCharts(params: ChartFilters) {
  return $api.useQuery("get", "/api/v1/charts/dashboard", { params });
}
```

**Después:**

```typescript
export function useChartsDisponibles() {
  return $api.useQuery('get', '/api/v1/metricas/charts-disponibles');
}

// Reemplazar con queries específicas de métricas
export function useReportData(metric: string, filters: MetricFilters) {
  return useMetricQuery({ metric, dimensions: [...], filters });
}
```

#### 2.2 Migrar `features/boletines/`

Similar - reemplazar llamadas a `/charts/` con `/metricas/query`

### Fase 3: Eliminar código legacy

#### 3.1 Backend - Eliminar en orden:

```bash
# 1. API routers
rm -rf backend/app/api/v1/charts/
rm -rf backend/app/api/v1/analytics/

# 2. Domains
rm -rf backend/app/domains/dashboard/
rm -rf backend/app/domains/charts/

# 3. Seeds
rm backend/app/scripts/seeds/charts.py

# 4. Actualizar router.py (quitar imports)

# 5. Migración: eliminar tabla dashboard_charts
# alembic revision -m "drop_dashboard_charts_table"
```

#### 3.2 Frontend - Limpiar:

```bash
# Ya no se necesitan después de migrar
# - Hooks que llaman a /charts/
# - Tipos de ChartsDisponibles (regenerar desde OpenAPI)
```

### Fase 4: Limpiar base de datos

```sql
-- Migración Alembic
DROP TABLE IF EXISTS dashboard_charts;
```

---

## 4. Mapeo de Funcionalidades

| Legacy (charts/dashboard) | Nuevo (metricas)                               | Estado      |
| ------------------------- | ---------------------------------------------- | ----------- |
| `casos_por_semana`        | `casos_clinicos` + dim `SEMANA_EPIDEMIOLOGICA` | ✅ Existe   |
| `piramide_poblacional`    | `casos_clinicos` + dims `GRUPO_ETARIO`, `SEXO` | ✅ Existe   |
| `corredor_endemico`       | `casos_clinicos` + compute `corredor_endemico` | ✅ Existe   |
| `distribucion_agentes`    | `muestras_positivas` + dim `AGENTE_ETIOLOGICO` | ✅ Existe   |
| `casos_por_provincia`     | `casos_clinicos` + dim `PROVINCIA`             | ✅ Existe   |
| `top_eventos`             | `casos_clinicos` + dim `TIPO_EVENTO`           | ✅ Existe   |
| `indicadores`             | Múltiples queries de métricas                  | 🔄 Componer |

---

## 5. Archivos Afectados

### Backend - ELIMINAR:

```
app/api/v1/charts/
├── __init__.py
├── router.py
├── get_dashboard.py
├── get_disponibles.py
├── get_indicadores.py
└── generate_spec.py

app/api/v1/analytics/
├── __init__.py
└── router.py

app/domains/dashboard/
├── __init__.py
├── processors.py        # 74KB de SQL raw
├── models.py            # DashboardChart
├── conditions.py
├── age_groups_config.py
└── schemas.py

app/domains/charts/
├── __init__.py
├── schemas.py
└── services/
    ├── spec_generator.py
    └── renderer.py

app/scripts/seeds/charts.py
```

### Backend - MODIFICAR:

```
app/api/v1/router.py          # Quitar imports de charts/analytics/dashboard
app/domains/__init__.py       # Quitar export de DashboardChart
```

### Frontend - MODIFICAR:

```
src/features/reports/api.ts   # Migrar a usar metricas
src/features/boletines/api.ts # Migrar a usar metricas
```

---

## 6. Riesgos y Mitigaciones

| Riesgo                          | Mitigación                                             |
| ------------------------------- | ------------------------------------------------------ |
| Reportes PDF dejan de funcionar | Migrar `renderer.py` a usar metricas antes de eliminar |
| Boletines pierden charts        | Verificar cada chart tiene equivalente en metricas     |
| Performance diferente           | Benchmarkear queries antes/después                     |
| Datos diferentes                | Tests de comparación output legacy vs nuevo            |

---

## 7. Orden de Ejecución Sugerido

1. **[✅] Auditar** - Listar TODOS los charts/queries del sistema legacy
2. **[✅] Migrar charts/disponibles** - Movido a `/api/v1/boletines/charts-disponibles`
3. **[✅] Frontend boletines** - Actualizado `useChartsDisponibles` para usar nuevo endpoint
4. **[ ] Verificar** - Confirmar que metricas puede generar los mismos datos
5. **[ ] Migrar comparative-dashboard** - Cambiar a usar metricas en vez de charts/dashboard
6. **[ ] Tests E2E** - Verificar que todo funciona igual
7. **[ ] Eliminar legacy** - Borrar código viejo restante
8. **[ ] Migración BD** - Drop tabla dashboard_charts

### Progreso (2024-12)

**Completado:**
- `GET /api/v1/charts/disponibles` → `GET /api/v1/boletines/charts-disponibles`
- Frontend `features/boletines/api.ts` y `features/reports/api.ts` actualizados
- Archivo `backend/app/api/v1/charts/get_disponibles.py` eliminado

**Pendiente:**
- `GET /api/v1/charts/dashboard` - Usado por `comparative-dashboard.tsx`
- `GET /api/v1/charts/indicadores` - Usado por `comparative-dashboard.tsx`
- `domains/dashboard/` - Procesadores aún en uso por charts
- `domains/charts/` - Generador de specs y renderer aún en uso

---

## 8. Beneficios Post-Migración

- **-74KB** de código SQL raw eliminado
- **-1 tabla** en base de datos
- **1 sistema** en lugar de 2 para consultas
- **Tipado completo** con builders ORM
- **Más fácil** agregar nuevas métricas
- **Tests** más simples (un solo sistema)
- **Documentación** centralizada en registry

---

## 9. Estimación de Esfuerzo

| Tarea                      | Complejidad |
| -------------------------- | ----------- |
| Auditar sistema legacy     | Baja        |
| Agregar métricas faltantes | Media       |
| Migrar reports frontend    | Media       |
| Migrar boletines frontend  | Media       |
| Eliminar código            | Baja        |
| Tests y QA                 | Media       |

**Total estimado**: Tarea significativa pero manejable en fases.

---

## 10. Notas Adicionales

### ¿Por qué no eliminar todo de una vez?

- Reportes PDF y Boletines son funcionalidades críticas
- Mejor migrar gradualmente con tests en cada paso
- Permite rollback si algo falla

### ¿Qué pasa con `domains/charts/services/renderer.py`?

- Este renderiza charts a imagen para PDFs
- Puede necesitar adaptarse para recibir datos de metricas
- Evaluar si se mantiene o se reemplaza con otra solución

### ¿La tabla `dashboard_charts` tiene datos importantes?

- Verificar si hay configuraciones custom
- Exportar backup antes de eliminar
- La config puede moverse a código (registry pattern)

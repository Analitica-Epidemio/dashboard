# Documentacion Tecnica del Backend

Esta carpeta contiene la documentacion de arquitectura del sistema de vigilancia epidemiologica.

## Vision General del Sistema

```mermaid
flowchart TB
    subgraph EXTERNAL ["Sistemas Externos"]
        SNVS["SNVS<br/>(archivos Excel semanales)"]
    end

    subgraph BACKEND ["Backend (FastAPI)"]
        subgraph ENTRADA ["Entrada de Datos"]
            UPLOAD["API Uploads<br/>/uploads/preview<br/>/uploads/process"]
            JOBS["Sistema de Jobs<br/>(Celery + Redis)"]
            PROC["Procesadores<br/>Nominal | Agregado"]
        end

        subgraph ALMACEN ["Almacenamiento"]
            DB[(PostgreSQL<br/>+ PostGIS)]
        end

        subgraph SALIDA ["Salida de Datos"]
            METRICAS["API Metricas<br/>/metricas/query"]
            BUILDERS["Query Builders<br/>Clinico | Lab | Nominal"]
        end
    end

    subgraph FRONTEND ["Frontend (Next.js)"]
        DASH["Dashboards<br/>Vigilancia Clinica<br/>Laboratorio<br/>Hospitalaria<br/>Nominal"]
    end

    SNVS -->|Excel| UPLOAD
    UPLOAD --> JOBS
    JOBS --> PROC
    PROC -->|INSERT| DB
    DB -->|SELECT| METRICAS
    METRICAS --> BUILDERS
    BUILDERS --> DASH
```

## Documentos

| Documento | Descripcion | Cuando leerlo |
|-----------|-------------|---------------|
| [arquitectura-procesamiento.md](arquitectura-procesamiento.md) | Como se cargan los datos del SNVS a la BD | Vas a modificar el upload de archivos o agregar un nuevo tipo de archivo |
| [sistema-metricas.md](sistema-metricas.md) | Como el frontend consulta datos agregados | Vas a agregar una nueva metrica, dimension, o dashboard |

## Flujo de Datos

```
Usuario sube Excel
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  PROCESAMIENTO (arquitectura-procesamiento.md)              │
│                                                             │
│  1. POST /uploads/preview → detecta tipo, muestra preview   │
│  2. POST /uploads/process → crea Job, dispara Celery        │
│  3. Celery Worker ejecuta Procesador segun tipo             │
│  4. Procesador valida, transforma, inserta en BD            │
│  5. Frontend hace polling de estado hasta completar         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
   PostgreSQL (datos normalizados)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  METRICAS (sistema-metricas.md)                             │
│                                                             │
│  1. Frontend pide metrica + dimensiones + filtros           │
│  2. MetricService valida y selecciona QueryBuilder          │
│  3. Builder arma query SQL con JOINs necesarios             │
│  4. Ejecuta, post-procesa (derivadas, corredor endemico)    │
│  5. Retorna JSON listo para graficar                        │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
  Dashboard muestra grafico/tabla
```

## Glosario

| Termino | Significado |
|---------|-------------|
| **SNVS** | Sistema Nacional de Vigilancia de la Salud |
| **CLI_P26** | Planilla 26 Clinica (casos agregados por semana) |
| **LAB_P26** | Planilla 26 Laboratorio (muestras por agente/tecnica) |
| **ETI** | Enfermedad Tipo Influenza |
| **Semana Epidemiologica** | Semana del 1 al 52/53, standard OMS |
| **Corredor Endemico** | Percentiles historicos para detectar brotes |

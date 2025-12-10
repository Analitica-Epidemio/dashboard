# Arquitectura de Procesamiento de Datos

> **Contexto:** Este sistema maneja la **entrada de datos** al sistema. Los archivos Excel del SNVS (Sistema Nacional de Vigilancia de la Salud) se procesan aqui y se guardan en la base de datos. Una vez procesados, los datos estan disponibles para consulta via el [Sistema de Metricas](sistema-metricas.md).

## Que problema resuelve?

El Ministerio de Salud recibe semanalmente archivos Excel con datos de vigilancia epidemiologica:
- **Vigilancia Nominal**: Casos individuales con datos del paciente (~100 columnas)
- **Vigilancia Agregada**: Conteos semanales por establecimiento (CLI_P26, LAB_P26)

Estos archivos pueden tener miles de filas. Procesarlos de forma sincrona bloquearia la interfaz. Este sistema:
1. Recibe el archivo y muestra un preview inmediato
2. Procesa en background (Celery) sin bloquear al usuario
3. Reporta progreso en tiempo real via polling

---

## Vision General

```mermaid
flowchart LR
    subgraph INPUT ["Entrada"]
        SNVS["Archivos SNVS<br/>(Excel)"]
    end

    subgraph PROC ["Este documento"]
        P["Procesamiento<br/>(Jobs + Celery)"]
    end

    subgraph DB ["Base de Datos"]
        D[(PostgreSQL)]
    end

    subgraph QUERY ["sistema-metricas.md"]
        Q["API de Metricas<br/>(Consultas)"]
    end

    subgraph OUT ["Salida"]
        FE["Frontend<br/>(Dashboards)"]
    end

    SNVS --> P --> D --> Q --> FE

    style PROC fill:#e1f5fe
```

---

El sistema de procesamiento de archivos sigue una arquitectura modular y asincrona que permite procesar grandes volumenes de datos sin bloquear la interfaz de usuario.

## Diagrama General de Flujo

```mermaid
flowchart TB
    subgraph Cliente ["🖥️ Cliente (Frontend)"]
        U[Usuario sube archivo]
        P[Visualiza preview]
        C[Confirma procesamiento]
        S[Polling de estado]
    end

    subgraph API ["🌐 API REST"]
        direction TB
        EP1[POST /uploads/preview]
        EP2[POST /uploads/process]
        EP3["GET /jobs/{id}/status"]
    end

    subgraph Jobs ["⚙️ Sistema de Jobs"]
        JM[Job Model]
        JS[Job Service]
        REG[Processor Registry]
    end

    subgraph Celery ["🔄 Celery Worker"]
        CT[execute_job Task]
    end

    subgraph Processors ["📊 Procesadores"]
        direction TB
        NP[SimpleEpidemiologicalProcessor<br/>Vigilancia Nominal]
        AP[AgregadaProcessor<br/>Vigilancia Agregada]
    end

    subgraph Storage ["💾 Almacenamiento"]
        TMP[(Archivos Temp)]
        DB[(PostgreSQL)]
        REDIS[(Redis)]
    end

    U --> EP1
    EP1 --> TMP
    EP1 --> P
    P --> C
    C --> EP2
    EP2 --> JS
    JS --> JM
    JM --> DB
    JS --> CT
    CT --> REDIS
    CT --> REG
    REG --> NP
    REG --> AP
    NP --> DB
    AP --> DB
    S --> EP3
    EP3 --> JM
```

## Arquitectura de Módulos

```mermaid
graph TB
    subgraph api ["📁 app/api/v1/uploads"]
        preview["preview_file.py<br/>Analiza archivo sin procesar"]
        process["process_from_preview.py<br/>Inicia procesamiento"]
        status["get_job_status.py<br/>Consulta estado"]
        cancel["cancel_job.py<br/>Cancela job"]
    end

    subgraph jobs ["📁 app/domains/jobs"]
        models["models.py<br/>Job (modelo genérico)"]
        tasks["tasks.py<br/>execute_job (Celery)"]
        registry["registry.py<br/>Processor Registry"]
        services["services.py<br/>JobService"]
    end

    subgraph nominal ["📁 app/domains/vigilancia_nominal"]
        n_handler["upload_handler.py<br/>NominalUploadHandler"]
        n_processor["processor.py<br/>SimpleEpidemiologicalProcessor"]
        n_bulk["bulk/main.py<br/>MainProcessor"]
        n_validator["validator.py<br/>OptimizedDataValidator"]
    end

    subgraph agregada ["📁 app/domains/vigilancia_agregada"]
        a_handler["upload_handler.py<br/>AgregadaUploadHandler"]
        a_processor["processor.py<br/>AgregadaProcessor"]
        a_types["types/<br/>CLIP26, LabP26..."]
        a_columns["columns/<br/>ColumnRegistry"]
    end

    preview --> process
    process --> n_handler
    process --> a_handler
    n_handler --> services
    a_handler --> services
    services --> models
    services --> tasks
    tasks --> registry
    registry -.-> n_processor
    registry -.-> a_processor
    n_processor --> n_bulk
    n_processor --> n_validator
    a_processor --> a_types
    a_types --> a_columns
    status --> services
```

## Flujo Detallado de Procesamiento

```mermaid
sequenceDiagram
    autonumber
    participant F as Frontend
    participant API as API REST
    participant H as Upload Handler
    participant J as Job Service
    participant C as Celery Worker
    participant R as Registry
    participant P as Processor
    participant DB as PostgreSQL

    F->>API: POST /uploads/preview (archivo)
    API->>API: Validar MIME type
    API->>API: Guardar en /tmp/
    API->>API: Detectar tipo (NOMINAL, CLI_P26, LAB_P26...)
    API-->>F: FilePreviewResponse (upload_id, preview)

    F->>API: POST /uploads/process (upload_id, sheet_name)
    API->>H: iniciar_procesamiento()
    H->>J: crear_job(processor_type)
    J->>DB: INSERT Job (status=PENDING)
    J->>C: execute_job.delay(job_id)
    J-->>API: Job creado
    API-->>F: AsyncJobResponse (job_id)

    C->>DB: SELECT Job WHERE id=job_id
    C->>R: get_processor(processor_type)
    R-->>C: processor_factory
    C->>P: procesar_archivo(ruta, hoja)

    loop Por cada etapa
        P->>P: Procesar datos
        P->>J: callback_progreso(%)
        J->>DB: UPDATE Job SET progress=%
    end

    P->>DB: INSERT datos procesados
    P-->>C: ProcessingResult
    C->>DB: UPDATE Job SET status=COMPLETED

    loop Polling cada 2-5s
        F->>API: GET /jobs/{job_id}/status
        API->>DB: SELECT Job
        API-->>F: JobStatusResponse (status, progress)
    end
```

## Registry Pattern (Desacoplamiento)

El sistema usa un patrón Registry para desacoplar el módulo `jobs` de los procesadores específicos:

```mermaid
graph LR
    subgraph "Registro (al importar módulo)"
        N["vigilancia_nominal/__init__.py"] -->|register_processor| REG["Registry"]
        A["vigilancia_agregada/__init__.py"] -->|register_processor| REG
    end

    subgraph "Ejecución (en Celery)"
        T["tasks.py: execute_job()"] -->|get_processor| REG
        REG -->|factory| P["Processor Instance"]
    end
```

**Código:**
```python
# En vigilancia_nominal/__init__.py
from app.domains.jobs.registry import register_processor
register_processor("vigilancia_nominal", crear_procesador)

# En tasks.py
processor_factory = get_processor(job.processor_type)
processor = processor_factory(session, callback_progreso)
```

## Tipos de Archivos Soportados

| Tipo | Detectado por | Procesador | Datos generados |
|------|---------------|------------|-----------------|
| **NOMINAL** | Columnas de vigilancia nominal (100+) | `SimpleEpidemiologicalProcessor` | Ciudadanos, Casos, Diagnósticos |
| **CLI_P26** | `ID_AGRP_CLINICA` | `CLIP26Processor` | NotificacionSemanal, ConteoCasosClinicos |
| **CLI_P26_INT** | `ID_AGRP_CLINICA` + keywords internación | `CLIP26IntProcessor` | NotificacionSemanal, ConteoCamasIRA |
| **LAB_P26** | `ID_AGRP_LABO` | `LabP26Processor` | NotificacionSemanal, ConteoEstudiosLab |

## Pipeline de Vigilancia Nominal

```mermaid
flowchart LR
    subgraph "SimpleEpidemiologicalProcessor"
        L["1. Cargar<br/>(5%)"] --> V["2. Validar<br/>(10%)"]
        V --> C["3. Limpiar<br/>(15%)"]
        C --> CL["4. Clasificar<br/>(20%)"]
        CL --> S["5. Guardar<br/>(25-95%)"]
    end

    subgraph "MainProcessor (Bulk)"
        S --> E["Establecimientos"]
        E --> CI["Ciudadanos"]
        CI --> CA["Casos Epidemiológicos"]
        CA --> P1["Salud ‖"]
        CA --> P2["Diagnósticos ‖"]
        CA --> P3["Investigaciones ‖"]
    end
```

## Pipeline de Vigilancia Agregada

```mermaid
flowchart LR
    subgraph "AgregadaProcessor"
        L["1. Cargar archivo"] --> D["2. Detectar tipo"]
        D --> G["3. Obtener procesador"]
    end

    subgraph "FileTypeProcessor"
        G --> V["4. Validar columnas"]
        V --> T["5. Transformar datos"]
        T --> S["6. Guardar en BD"]
    end

    D -->|"ID_AGRP_LABO"| LAB["LabP26Processor"]
    D -->|"ID_AGRP_CLINICA + internación"| INT["CLIP26IntProcessor"]
    D -->|"ID_AGRP_CLINICA"| CLI["CLIP26Processor"]
```

## Modelo de Datos: Job

```mermaid
erDiagram
    JOB {
        uuid id PK
        string job_type "file_processing"
        string processor_type "vigilancia_nominal | vigilancia_agregada"
        string status "PENDING | IN_PROGRESS | COMPLETED | FAILED"
        int progress_percentage "0-100"
        json input_data "ruta_archivo, nombre_hoja, etc"
        json output_data "resultados del procesamiento"
        string celery_task_id FK
        datetime created_at
        datetime started_at
        datetime completed_at
        string error_message
    }
```

## Modelo de Datos: Vigilancia Agregada

```mermaid
erDiagram
    NOTIFICACION_SEMANAL ||--o{ CONTEO_CASOS_CLINICOS : tiene
    NOTIFICACION_SEMANAL ||--o{ CONTEO_ESTUDIOS_LAB : tiene
    NOTIFICACION_SEMANAL ||--o{ CONTEO_CAMAS_IRA : tiene
    NOTIFICACION_SEMANAL }o--|| ESTABLECIMIENTO : pertenece

    NOTIFICACION_SEMANAL {
        int id PK
        string id_snvs UK "ID único en SNVS"
        int anio
        int semana
        string origen "CLI_P26 | LAB_P26 | CLI_P26_INT"
        int establecimiento_id FK
    }

    CONTEO_CASOS_CLINICOS {
        int id PK
        string id_snvs UK
        int cantidad
        string sexo "M | F | X"
        bool es_residente
        bool es_ambulatorio
        int notificacion_id FK
        int tipo_evento_id FK
        int rango_etario_id FK
    }

    CONTEO_ESTUDIOS_LAB {
        int id PK
        string id_snvs UK
        int cantidad_estudiadas
        int cantidad_positivas
        int notificacion_id FK
        int agente_id FK
        int tecnica_id FK
    }

    CONTEO_CAMAS_IRA {
        int id PK
        int ocupacion_sala
        int ocupacion_uti
        int notificacion_id FK
    }
```

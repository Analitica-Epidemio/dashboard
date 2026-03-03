# Sistema de Vigilancia Epidemiologica - Documentacion

> Documento unico de referencia para onboarding y consulta del proyecto.

## Indice

1. [Vision General](#1-vision-general)
   - 1.1 [Que es](#11-que-es)
   - 1.2 [Para quien es](#12-para-quien-es)
   - 1.3 [Que problema resuelve](#13-que-problema-resuelve)
2. [Dominio Epidemiologico](#2-dominio-epidemiologico)
   - 2.1 [Glosario](#21-glosario)
   - 2.2 [Tipos de Vigilancia](#22-tipos-de-vigilancia)
   - 2.3 [Eventos de Notificacion Obligatoria](#23-eventos-de-notificacion-obligatoria)
   - 2.4 [Estructura de los Archivos del SNVS](#24-estructura-de-los-archivos-del-snvs)
3. [Requerimientos Funcionales](#3-requerimientos-funcionales)
   - 3.1 [Carga de Datos](#31-carga-de-datos)
   - 3.2 [Procesamiento y Limpieza](#32-procesamiento-y-limpieza)
   - 3.3 [Analisis](#33-analisis)
   - 3.4 [Visualizacion](#34-visualizacion)
   - 3.5 [Reportes y Boletines](#35-reportes-y-boletines)
4. [Arquitectura General](#4-arquitectura-general)
   - 4.1 [Tech Stack](#41-tech-stack)
   - 4.2 [Diagrama de Arquitectura](#42-diagrama-de-arquitectura)
   - 4.3 [Estructura del Monorepo](#43-estructura-del-monorepo)
   - 4.4 [Seguridad y Autenticacion](#44-seguridad-y-autenticacion)
5. [Backend](#5-backend)
   - 5.1 [Estructura de Directorios](#51-estructura-de-directorios)
   - 5.2 [Patrones de Diseno](#52-patrones-de-diseno)
   - 5.3 [Arquitectura de Procesamiento de Datos](#53-arquitectura-de-procesamiento-de-datos)
   - 5.4 [Sistema de Metricas (Motor BI)](#54-sistema-de-metricas-motor-bi)
   - 5.5 [Modelo de Datos](#55-modelo-de-datos)
   - 5.6 [Variables de Entorno](#56-variables-de-entorno)
6. [Frontend](#6-frontend)
   - 6.1 [Estructura de Directorios](#61-estructura-de-directorios)
   - 6.2 [Patrones del Frontend](#62-patrones-del-frontend)
   - 6.3 [Rutas Principales](#63-rutas-principales)
7. [Guia de Desarrollo](#7-guia-de-desarrollo)
   - 7.1 [Prerrequisitos](#71-prerrequisitos)
   - 7.2 [Setup Inicial](#72-setup-inicial)
   - 7.3 [Desarrollo Diario](#73-desarrollo-diario)
   - 7.4 [Comandos Disponibles](#74-comandos-disponibles)
   - 7.5 [Tareas Comunes](#75-tareas-comunes)
   - 7.6 [Convenciones](#76-convenciones)
8. [Produccion y Deploy](#8-produccion-y-deploy)

---

## 1. Vision General

### 1.1 Que es

Sistema web para la vigilancia epidemiologica de una jurisdiccion sanitaria de Argentina. Permite cargar, procesar, analizar y visualizar datos de eventos de notificacion obligatoria provenientes del SNVS (Sistema Nacional de Vigilancia de la Salud).

### 1.2 Para quien es

Equipos de epidemiologia de ministerios o secretarias de salud provinciales/municipales que necesitan:

- Cargar los archivos Excel que exportan semanalmente del SNVS
- Visualizar la situacion epidemiologica actual con dashboards y mapas
- Generar boletines epidemiologicos con graficos y texto editable
- Consultar casos individuales y datos agregados con filtros flexibles

### 1.3 Que problema resuelve

El SNVS exporta datos en archivos Excel crudos que requieren limpieza y procesamiento manual para ser utiles. Este sistema automatiza ese proceso y ofrece herramientas de analisis y visualizacion que antes se hacian manualmente en planillas de calculo.

---

## 2. Dominio Epidemiologico

Esta seccion explica los conceptos del dominio para desarrolladores que no tienen experiencia en epidemiologia.

### 2.1 Glosario

| Termino | Significado |
|---------|-------------|
| **SNVS** | Sistema Nacional de Vigilancia de la Salud. Sistema informatico nacional donde se notifican eventos de salud publica. Es la fuente de datos del sistema. |
| **Evento de notificacion obligatoria (ENO)** | Enfermedad o situacion de salud publica que debe reportarse obligatoriamente (ej: dengue, COVID, sarampion). |
| **Semana epidemiologica (SE)** | Unidad de tiempo estandar en epidemiologia. Hay 52 o 53 por anio. En Argentina cada semana empieza en domingo y la SE 1 es la que incluye el primer jueves del anio. |
| **Corredor endemico** | Grafico que muestra los percentiles historicos (P25, P50, P75) de un evento usando datos de los 5 anios anteriores, para detectar si la cantidad de casos actual esta dentro de lo esperado (zona de exito), en alerta, o en brote. |
| **ETI** | Enfermedad Tipo Influenza. Uno de los eventos respiratorios mas vigilados. |
| **IRA** | Infeccion Respiratoria Aguda. |
| **IRAG** | Infeccion Respiratoria Aguda Grave. |
| **SUH** | Sindrome Uremico Hemolitico. |
| **Agente etiologico** | Microorganismo que causa una enfermedad (ej: virus Influenza A, SARS-CoV-2, Dengue DENV-1). |
| **Tasa de positividad** | Porcentaje de muestras de laboratorio que resultaron positivas sobre el total de estudiadas. |
| **CLI_P26** | Planilla 26 Clinica: contiene casos agregados por semana de vigilancia clinica. |
| **LAB_P26** | Planilla 26 Laboratorio: contiene muestras estudiadas y positivas por agente y tecnica. |
| **Clasificacion de caso** | Categoria asignada a un caso segun criterios especificos: confirmado, sospechoso, probable, descartado, etc. |

### 2.2 Tipos de Vigilancia

El sistema maneja dos modalidades de datos provenientes del SNVS:

**Vigilancia Nominal:** Datos caso por caso con informacion individual del paciente (nombre, edad, domicilio, sintomas, diagnostico, etc). Los archivos tienen ~100 columnas. Se usa para seguimiento epidemiologico detallado y permite clasificar cada caso individualmente.

**Vigilancia Agregada:** Conteos semanales agrupados por establecimiento de salud. Existen tres tipos de planillas:

| Tipo | Identificador en archivo | Contenido |
|------|--------------------------|-----------|
| **CLI_P26** (Clinica) | Columna `ID_AGRP_CLINICA` | Casos clinicos por evento, grupo etario y sexo |
| **CLI_P26_INT** (Internacion) | `ID_AGRP_CLINICA` + keywords de internacion | Ocupacion de camas por IRA (sala comun y UTI) |
| **LAB_P26** (Laboratorio) | Columna `ID_AGRP_LABO` | Muestras estudiadas y positivas por agente y tecnica |

### 2.3 Eventos de Notificacion Obligatoria

El sistema maneja 60+ eventos organizados por categorias. Los principales son:

**Enfermedades transmitidas por vectores:**
- Dengue (4 serotipos + sin especificar)
- Zika
- Chikungunya
- Fiebre Amarilla
- Fiebre del Nilo Occidental
- Encefalitis de San Luis

**Enfermedades respiratorias:**
- ETI (Enfermedad Tipo Influenza)
- Neumonia
- Bronquiolitis
- IRAG (en unidades centinela)
- Coqueluche (tos convulsa)
- Tuberculosis

**Fiebres hemorragicas:**
- Hantavirus
- Fiebre Hemorragica Argentina

**Enfermedades entericas:**
- Diarrea Aguda
- SUH (Sindrome Uremico Hemolitico)
- STEC (E. coli productora de toxina Shiga)
- Brotes de enfermedades transmitidas por alimentos

**Otros:** Psitacosis, Varicela, Parotiditis, Listeriosis, Triquinosis, entre otros.

Cada evento usa un identificador slug (kebab-case): `"dengue"`, `"neumonia"`, `"bronquiolitis"`, etc.

### 2.4 Estructura de los Archivos del SNVS

**Agrupado (~30 columnas):** ID_ENCABEZADO, ID_AGRP_LABO/CLINICA, ID_ORIGEN, NOMBRE_ORIGEN, CODIGO_LOCALIDAD, LOCALIDAD, CODIGO_DEPARTAMENTO, DEPARTAMENTO, CODIGO_PROVINCIA, PROVINCIA, ANIO, SEMANA, ESTADO, FECHA_REGISTRO, EVENTO, EDAD, SEXO, RESIDENTE, AMBULATORIO, ESTUDIADAS, POSITIVAS, entre otros.

**Nominal (~100+ columnas):** Incluye datos personales del paciente (nombre, apellido, fecha de nacimiento, domicilio), datos del establecimiento de salud, fecha de diagnostico, comorbilidades, tratamiento recibido, sintomas, clasificacion del caso, resultado de laboratorio, entre otros.

---

## 3. Requerimientos Funcionales

### 3.1 Carga de Datos

Se suben archivos .csv/.xlsx con datos de eventos de notificacion obligatoria exportados del SNVS. El sistema acepta tanto formato nominal (datos individuales) como agrupado (conteos semanales).

**Que se hace:**
- El usuario selecciona un archivo y lo sube al sistema
- El sistema valida el formato (MIME type, extension)
- Se detecta automaticamente el tipo de archivo (NOMINAL, CLI_P26, LAB_P26, CLI_P26_INT) segun las columnas presentes
- Se muestra un preview con las primeras filas para que el usuario confirme antes de procesar
- El procesamiento se ejecuta en background (Celery) sin bloquear la interfaz, con barra de progreso

**Tipos de archivo soportados:**

| Tipo | Como se detecta | Que datos genera |
|------|-----------------|------------------|
| NOMINAL | Columnas de vigilancia nominal (~100+) | Ciudadanos, Casos, Diagnosticos |
| CLI_P26 | Columna `ID_AGRP_CLINICA` | Notificaciones semanales, Conteos clinicos |
| CLI_P26_INT | `ID_AGRP_CLINICA` + keywords de internacion | Notificaciones semanales, Conteos de camas IRA |
| LAB_P26 | Columna `ID_AGRP_LABO` | Notificaciones semanales, Conteos de estudios de lab |

### 3.2 Procesamiento y Limpieza

Una vez cargados los archivos, los datos crudos no se guardan tal cual: se limpian, normalizan y procesan antes de insertarlos en la base de datos.

#### Pipeline de Vigilancia Nominal (5 fases)

**Fase 1 - Carga del archivo (5% progreso):**
- Acepta CSV/Excel
- Valida integridad del archivo
- Usa Polars (en vez de pandas) para rendimiento (5-54x mas rapido, 50-70% menos memoria)

**Fase 2 - Validacion estructural (10%):**
- Verifica que las columnas requeridas esten presentes
- Valida porcentaje de cobertura de columnas
- Mapea columnas a nombres estandarizados

**Fase 3 - Limpieza de datos (15%):**
- Limpieza vectorizada con Polars
- Mapeo de valores nulos
- Normalizacion de strings (mayusculas en campos especificos)
- Conversion de tipos: fechas, booleanos, provincias (ej: unificar "BUENOS AIRES", "Buenos Aires", "buenos aires"), tipos de documento, sexo
- Eliminacion de duplicados

**Fase 4 - Clasificacion de eventos (20%):**
- Cada caso se clasifica automaticamente segun estrategias de clasificacion configurables por tipo de evento
- Las clasificaciones posibles son:
  - **Confirmado:** Caso confirmado por laboratorio
  - **Probable:** Cumple criterios epidemiologicos
  - **Sospechoso:** En investigacion
  - **Descartado:** Descartado por laboratorio u otro criterio
  - **En estudio:** Pendiente de determinacion final
  - **Notificado:** Solo notificado, sin clasificacion aun
- Las estrategias de clasificacion son especificas por evento (ej: las reglas para clasificar dengue son distintas a las de neumonia)
- Se extrae metadata adicional (tipo de sujeto: humano/animal/indeterminado)

**Fase 5 - Insercion en base de datos (25-95%):**
- Procesamiento por lotes (default: 1000 filas por batch)
- Insercion modular en 18 operaciones secuenciales: ciudadanos, casos epidemiologicos, diagnosticos, investigaciones, sintomas, comorbilidades, etc.
- Progreso reportado en tiempo real al frontend

#### Pipeline de Vigilancia Agregada

- Carga el archivo
- Detecta el tipo (CLI_P26, LAB_P26, CLI_P26_INT) segun las columnas
- Valida las columnas requeridas para ese tipo
- Transforma los datos al formato de la base de datos
- Inserta notificaciones semanales con sus conteos asociados

### 3.3 Analisis

Una vez que los datos estan procesados en la base de datos, el sistema ofrece analisis a traves de un motor de consultas flexible (sistema de metricas/BI engine).

**Metricas disponibles:**

| Metrica | Fuente | Agregacion | Descripcion |
|---------|--------|------------|-------------|
| Casos clinicos | Vigilancia Clinica | SUM(cantidad) | Total de casos notificados por vigilancia pasiva |
| Muestras estudiadas | Laboratorio | SUM(estudiadas) | Total de muestras procesadas en laboratorio |
| Muestras positivas | Laboratorio | SUM(positivas) | Muestras con resultado positivo |
| Tasa de positividad | Laboratorio | Derivada | positivas/estudiadas * 100 |
| Casos nominales | Nominal | COUNT(*) | Cantidad de casos individuales |
| Ocupacion camas IRA | Hospitalario | SUM(cantidad) | Camas ocupadas por IRA |

**Dimensiones de analisis** (no todas aplican a todas las metricas):

| Dimension | Clinico | Lab | Nominal | Hospitalario |
|-----------|:-------:|:---:|:-------:|:------------:|
| Semana epidemiologica | Si | Si | Si | Si |
| Anio epidemiologico | Si | Si | Si | Si |
| Tipo de evento | Si | - | Si | Si |
| Agente etiologico | - | Si | - | - |
| Grupo etario | Si | Si | Si | Si |
| Sexo | Si | - | Si | Si |
| Provincia | Si | Si | Si | Si |
| Departamento | Si | Si | Si | Si |
| Establecimiento | Si | - | - | Si |

**Analisis especificos:**
- **Corredor endemico:** Se calculan percentiles P25, P50 y P75 usando datos de los 5 anios anteriores para cada semana epidemiologica. El anio actual se compara contra estas zonas para detectar situaciones de exito, seguridad, alerta o brote.
- **Metricas derivadas:** La tasa de positividad se calcula post-query dividiendo positivas sobre estudiadas.
- **Comparacion interanual:** Se pueden comparar metricas del anio actual contra el anterior.
- **Tendencia:** Comparacion de las ultimas 4 semanas contra las 4 anteriores.

### 3.4 Visualizacion

Los datos analizados se presentan en 4 dashboards principales, un mapa interactivo y listados de datos.

#### Dashboard de Vigilancia Clinica

Se visualiza para cada evento (o todos) la vigilancia clinica basada en CLI_P26:

- **KPIs:** Total de casos del periodo, promedio semanal, tendencia (ultimas 4 semanas vs anteriores con indicador +/-), comparacion interanual
- **Corredor endemico:** Grafico area/linea/barra compuesto mostrando casos actuales contra zonas P25 (exito), P50 (seguridad), P75 (alerta), y por encima (brote)
- **Distribucion por evento:** Grafico de dona con los top 6 eventos por cantidad de casos
- **Piramide poblacional:** Distribucion por sexo y grupo etario (barras horizontales apiladas)
- **Distribucion geografica:** Mapa coropletico con casos por provincia y porcentajes
- **Tabla de top eventos:** Ranking con casos y variacion interanual en porcentaje
- **Filtros:** Periodo epidemiologico (rango de SE), provincia, modo de comparacion

#### Dashboard de Vigilancia Laboratorio

Se visualiza para cada agente etiologico la actividad de laboratorio basada en LAB_P26:

- **KPIs:** Total muestras estudiadas, total positivas, tasa de positividad (%), agente mas detectado
- **Estudios realizados:** Serie temporal (linea) por agente etiologico
- **Muestras positivas:** Grafico de area apilada por agente
- **Tasa de positividad:** Linea mostrando el % positivas/estudiadas por semana
- **Heatmap de agentes:** Mapa de calor agente × semana con intensidad de detecciones positivas
- **Tabla de laboratorio:** Desglose por agente, semana, grupo etario con conteos
- **Agrupaciones:** Graficos por agrupaciones de agentes (ej: "Influenza A" agrupando subtipos), con drill-down a agentes individuales

#### Dashboard de Vigilancia Hospitalaria

Se visualiza la ocupacion hospitalaria por IRA basada en CLI_P26_INT:

- **KPIs:** Camas UCI ocupadas actualmente, pacientes en asistencia respiratoria mecanica, porcentaje de ocupacion critica, variacion semanal
- **Camas ocupadas por IRA:** Serie temporal (area/linea) por semana
- **Ocupacion por edad:** Barras apiladas por grupo etario
- **Casos criticos:** Pacientes en UTI y en asistencia mecanica
- **Distribucion geografica:** Por departamento y establecimiento

#### Dashboard de Vigilancia Nominal

Se visualiza caso por caso con los datos de vigilancia nominal:

- **KPIs:** Total de casos, confirmados (cantidad y %), hospitalizados (cantidad y % de confirmados), fallecidos (cantidad), tasa de letalidad (%)
- **Curva epidemica:** Grafico de area apilada por clasificacion: confirmados (rojo), probables (naranja), sospechosos (amarillo), descartados (verde)
- **Por clasificacion:** Grafico de torta con proporciones
- **Por grupo etario:** Barras horizontales
- **Indicadores de severidad:** Barras de progreso mostrando tasa de hospitalizacion (%) y tasa de letalidad (%)
- **Distribucion geografica:** Mapa por provincia
- **Listado de casos:** Tabla con registros individuales: ID, fecha de inicio de sintomas, clasificacion, sexo, edad, provincia, estado de hospitalizacion, desenlace
- **Filtros avanzados:** Periodo, provincia, clasificacion (confirmado/probable/sospechoso/descartado), selector jerarquico de eventos (grupo → evento)

#### Mapa Interactivo

- **Vista de domicilios:** Ubicacion de casos individuales en mapa (Leaflet), coloreados por grupo de evento (10 colores), hasta 50.000 casos, click para detalle
- **Vista de establecimientos:** Ubicacion de establecimientos de salud, filtrable por provincia
- **Animacion temporal:** Visualiza aparicion de casos en el tiempo con modos diario/semanal/mensual, modo acumulativo o ventana deslizante (14 dias configurable), controles de play/pausa, velocidad 0.5x a 4x

### 3.5 Reportes y Boletines

#### Boletines Epidemiologicos

El sistema permite crear boletines epidemiologicos con un editor visual (Tiptap/WYSIWYG) y un sistema de templates:

**Estructura de un boletin:**

1. **Contenido base (template):**
   - Portada con titulo, logos, fecha
   - Firmas de autoridades
   - Seccion de metodologia
   - Pie de pagina con atribucion de fuente

2. **Secciones por evento (dinamicas):**
   - Se repiten para cada evento epidemiologico seleccionado
   - Inyectan variables automaticas:
     - Nombre del evento, semana y anio epidemiologico
     - Descripcion de tendencia de casos
     - Datos de comparacion con periodos anteriores
     - Y 15+ variables mas

3. **Bloques dinamicos (graficos embebidos):**
   - Resumen de top eventos (top_enos)
   - Corredor endemico por evento
   - Curva epidemica por agente
   - Distribucion por edad
   - Desglose por agentes
   - Tipos de graficos: linea, area, barras, heatmap

**Que se reporta:**
- Situacion epidemiologica del periodo (semanas epidemiologicas seleccionadas)
- Comparacion con periodos anteriores y deteccion de tendencias
- Distribucion geografica y demografica de los eventos
- Resultados de laboratorio por agente etiologico
- Ocupacion hospitalaria por IRA
- Alertas cuando los casos superan los umbrales del corredor endemico

#### Reportes Exportables

Ademas de los boletines, se pueden exportar:
- Graficos como imagen (html2canvas)
- Datos tabulares a Excel (xlsx)
- Reportes a PDF (jspdf)

---

## 4. Arquitectura General

### 4.1 Tech Stack

| Componente | Tecnologia | Proposito |
|------------|-----------|-----------|
| **Backend** | FastAPI + SQLModel | API REST, logica de negocio |
| **Frontend** | Next.js 15 + React 19 + TypeScript | Interfaz de usuario |
| **Base de datos** | PostgreSQL 16 + PostGIS | Almacenamiento, datos geoespaciales |
| **Cache/Cola** | Redis + Celery | Procesamiento asincrono de archivos |
| **UI** | Tailwind CSS v4 + shadcn/ui (Radix) | Componentes de interfaz |
| **Graficos** | Recharts + D3 | Visualizacion de datos |
| **Mapas** | Leaflet + React Leaflet | Mapas geograficos interactivos |
| **Editor** | Tiptap | Editor WYSIWYG para boletines |
| **API Client** | openapi-fetch + openapi-react-query | Cliente tipado auto-generado desde OpenAPI |
| **Auth** | NextAuth (frontend) + JWT (backend) | Autenticacion |
| **Migraciones** | Alembic | Migraciones de base de datos |
| **Package Managers** | uv (Python) + pnpm (Node.js) | Gestion de dependencias |

### 4.2 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUARIO (Browser)                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                     ┌─────────▼─────────┐
                     │   Next.js :3000    │
                     │  (App Router, SSR) │
                     │  NextAuth session  │
                     └─────────┬─────────┘
                               │ HTTP + JWT Bearer
                     ┌─────────▼─────────┐
                     │  FastAPI :8000     │
                     │  (API REST v1)     │
                     │  JWT validation    │
                     └───┬─────┬─────┬───┘
                         │     │     │
              ┌──────────┘     │     └──────────┐
              │                │                │
    ┌─────────▼──────┐  ┌─────▼──────┐  ┌──────▼─────────┐
    │ PostgreSQL     │  │   Redis    │  │ Celery Worker  │
    │ + PostGIS      │  │  (broker)  │  │ (procesa       │
    │ :5433          │  │  :6380     │  │  archivos)     │
    └────────────────┘  └────────────┘  └────────────────┘
```

**Flujo general:**
```
Archivos SNVS (Excel) ──► Carga ──► Procesamiento (Celery) ──► PostgreSQL
                                                                    │
                                                                    ▼
                                     Dashboards ◄── Metricas API ◄──┘
```

### 4.3 Estructura del Monorepo

```
dashboard/
├── compose.yaml              # Desarrollo: solo infra (DB, Redis, pgweb)
├── compose.prod.yaml         # Produccion: todos los servicios
├── Makefile                  # Comandos de desarrollo
│
├── backend/                  # FastAPI + Celery
│   ├── app/
│   │   ├── main.py           # App factory, middleware, lifespan
│   │   ├── api/v1/           # Endpoints REST organizados por recurso
│   │   ├── core/             # Config, DB, seguridad, middleware
│   │   ├── domains/          # Logica de negocio por dominio
│   │   └── scripts/          # Seeds, utilidades
│   ├── alembic/              # Migraciones de BD
│   ├── tests/
│   ├── docs/                 # Documentacion tecnica detallada del backend
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/                 # Next.js 15
│   ├── src/
│   │   ├── app/              # App Router (paginas y layouts)
│   │   ├── features/         # Modulos por funcionalidad
│   │   ├── components/       # Componentes compartidos (UI, charts, filtros)
│   │   └── lib/              # Utilidades, API client, hooks, tipos
│   ├── package.json
│   └── Dockerfile
│
├── docs/                     # Esta documentacion
└── scripts/                  # Scripts de deploy
```

### 4.4 Seguridad y Autenticacion

El sistema maneja datos medicos sensibles y tiene tres capas de seguridad:

1. **Middleware de Next.js** (primera barrera): Intercepta todas las rutas excepto `/login` y redirige si no hay sesion NextAuth valida.

2. **Layout server-side** (segunda barrera): El layout del dashboard verifica la sesion del lado del servidor con `getServerSession()` antes de renderizar contenido.

3. **JWT en el backend** (tercera barrera): Cada request a la API lleva un token JWT en el header `Authorization: Bearer <token>`. El backend valida el token y aplica RBAC (control de acceso basado en roles).

```
Login form ──► POST /api/v1/auth/login ──► Backend genera JWT
                                               │
            NextAuth almacena JWT en cookie ◄───┘
                    │
                    ▼
            Cada request al backend incluye JWT en header Authorization
```

---

## 5. Backend

### 5.1 Estructura de Directorios

```
backend/app/
├── main.py                   # FastAPI app factory + middleware
├── api/v1/                   # Endpoints REST
│   ├── router.py             # Router principal (incluye sub-routers)
│   ├── auth/                 # Login, logout, gestion de usuarios
│   ├── uploads/              # Preview y procesamiento de archivos
│   ├── boletines/            # CRUD de boletines
│   ├── metricas/             # Motor de consultas BI
│   ├── charts/               # Datos para graficos
│   ├── eventos/              # Eventos epidemiologicos
│   ├── personas/             # Personas/pacientes
│   ├── domicilios/           # Domicilios
│   ├── establecimientos/     # Establecimientos de salud
│   ├── geocoding/            # Geocodificacion
│   ├── geografia/            # Provincias, departamentos
│   ├── agentes/              # Agentes etiologicos
│   ├── grupos_etarios/       # Rangos de edad
│   ├── estrategias/          # Estrategias de clasificacion
│   ├── analytics/            # Consultas analiticas
│   └── reports/              # Reportes
│
├── core/                     # Infraestructura transversal
│   ├── config.py             # Pydantic Settings (lee .env)
│   ├── database.py           # Engine SQLAlchemy + sesiones
│   ├── celery_app.py         # Config Celery (broker, queues)
│   ├── middleware.py         # Middleware personalizado
│   ├── security/             # JWT, RBAC, validacion de tokens
│   ├── uploads/              # Validacion de archivos, storage
│   ├── bulk.py               # Helpers para inserciones masivas
│   ├── epidemiology.py       # Calculos epidemiologicos (SE, corredores)
│   └── csv_reader.py         # Lectura y parseo de archivos
│
└── domains/                  # Logica de negocio por dominio
    ├── autenticacion/        # Usuarios, JWT, roles
    ├── vigilancia_nominal/   # Casos individuales
    │   ├── models.py         # Caso, Paciente, Muestra, etc.
    │   ├── procesamiento/    # Pipeline de procesamiento
    │   ├── clasificacion/    # Clasificacion de casos
    │   └── queries/          # Consultas predefinidas
    ├── vigilancia_agregada/  # Datos agregados
    │   ├── models.py         # NotificacionSemanal, Conteos
    │   ├── procesamiento/    # Pipeline de procesamiento
    │   ├── types/            # Definiciones por tipo de planilla
    │   └── columns/          # Registry de columnas
    ├── eventos_epidemiologicos/ # Catalogo de eventos
    ├── metricas/             # Motor de consultas BI
    │   ├── service.py        # MetricService (facade)
    │   ├── builders/         # Query builders por fuente
    │   ├── criteria/         # Filtros componibles
    │   └── registry/         # Registro de metricas/dimensiones
    ├── boletines/            # Templates e instancias
    ├── jobs/                 # Sistema de jobs asincrono
    │   ├── models.py         # Job (status, progreso)
    │   ├── tasks.py          # Tarea Celery execute_job
    │   └── registry.py       # Registro de procesadores
    ├── territorio/           # Establecimientos, geografia
    ├── catalogos/            # Datos de referencia
    ├── charts/               # Datos para graficos
    ├── reporteria/           # Reportes
    ├── dashboard/            # Consultas del dashboard
    └── analitica/            # Consultas analiticas
```

### 5.2 Patrones de Diseno

**Domain-Driven Design:** Cada dominio tiene su directorio con modelos, servicios y logica separados de la capa API.

**SQLModel:** Combina SQLAlchemy (ORM) con Pydantic (validacion). La misma clase es modelo de BD y schema de validacion.

**Registry Pattern:** Los procesadores de archivos se registran automaticamente al importar el modulo. Desacopla el sistema de jobs de los procesadores especificos:

```python
# En vigilancia_nominal/__init__.py (al importar se registra)
register_processor("vigilancia_nominal", crear_procesador)

# En tasks.py (Celery busca el procesador por tipo)
processor_factory = get_processor(job.processor_type)
```

**Facade Pattern:** `MetricService` es una fachada unica para todas las consultas. El frontend llama a `POST /metricas/query` y el servicio internamente selecciona builder, arma filtros y ejecuta la query.

**Criteria Pattern:** Los filtros son objetos componibles con `&` (AND) y `|` (OR):

```python
criteria = (
    RangoPeriodoCriterion(2025, 1, 2025, 10) &
    TipoEventoCriterion(nombre="ETI") &
    ProvinciaCriterion(ids=[6])
)
```

### 5.3 Arquitectura de Procesamiento de Datos

El sistema de procesamiento maneja la entrada de datos. Los archivos Excel del SNVS se procesan y guardan en la base de datos. Los archivos pueden tener miles de filas, por lo que se procesan de forma asincrona.

#### Flujo General

```
Usuario sube archivo
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  1. POST /uploads/preview                                         │
│     - Valida MIME type                                            │
│     - Guarda en /tmp/                                             │
│     - Detecta tipo (NOMINAL, CLI_P26, LAB_P26, CLI_P26_INT)      │
│     - Devuelve preview con primeras filas                         │
└──────────────────────────────┬────────────────────────────────────┘
                               │ usuario confirma
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│  2. POST /uploads/process                                         │
│     - Upload Handler del tipo correspondiente crea Job            │
│     - Job se guarda en BD con status=PENDING                      │
│     - Se dispara tarea Celery (execute_job.delay)                 │
│     - Devuelve job_id al frontend                                 │
└──────────────────────────────┬────────────────────────────────────┘
                               │ asincrono
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│  3. Celery Worker                                                 │
│     - Busca procesador en registry segun processor_type           │
│     - Ejecuta pipeline (varia segun tipo)                         │
│     - Reporta progreso (0-100%) con callbacks                     │
│     - Actualiza Job en BD al finalizar (COMPLETED/FAILED)         │
└──────────────────────────────┬────────────────────────────────────┘
                               │
        ┌──────────────────────┤
        │                      │
        ▼                      ▼
  Frontend hace           Datos en PostgreSQL
  polling cada            listos para consulta
  2-5 segundos
  GET /jobs/{id}/status
```

#### Modulos Involucrados

```
app/api/v1/uploads/
├── preview_file.py             # Analiza archivo sin procesar
├── process_from_preview.py     # Inicia procesamiento
├── get_job_status.py           # Consulta estado
└── cancel_job.py               # Cancela job

app/domains/jobs/
├── models.py                   # Job (modelo generico)
├── tasks.py                    # execute_job (Celery task)
├── registry.py                 # Processor Registry
└── services.py                 # JobService

app/domains/vigilancia_nominal/
├── upload_handler.py           # NominalUploadHandler
├── processor.py                # SimpleEpidemiologicalProcessor
├── bulk/main.py                # MainProcessor (insercion masiva)
└── validator.py                # OptimizedDataValidator

app/domains/vigilancia_agregada/
├── upload_handler.py           # AgregadaUploadHandler
├── processor.py                # AgregadaProcessor
├── types/                      # CLIP26, LabP26, CLIP26Int
└── columns/                    # ColumnRegistry
```

#### Pipeline de Vigilancia Nominal

```
SimpleEpidemiologicalProcessor:

1. Cargar (5%) ──► 2. Validar (10%) ──► 3. Limpiar (15%) ──► 4. Clasificar (20%) ──► 5. Guardar (25-95%)

                                                                                          │
                                                                                MainProcessor (Bulk):
                                                                                          │
                                                                          Establecimientos ──► Ciudadanos
                                                                                                   │
                                                                                       Casos Epidemiologicos
                                                                                          │     │      │
                                                                                       Salud  Diag.  Invest.
```

#### Pipeline de Vigilancia Agregada

```
AgregadaProcessor:

1. Cargar archivo ──► 2. Detectar tipo ──► 3. Obtener procesador del tipo ──► 4. Validar columnas ──► 5. Transformar ──► 6. Guardar

                           │
                           ├── ID_AGRP_LABO ─────────────────► LabP26Processor
                           ├── ID_AGRP_CLINICA + internacion ─► CLIP26IntProcessor
                           └── ID_AGRP_CLINICA ──────────────► CLIP26Processor
```

#### Modelo de Datos: Job

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | UUID | Identificador unico |
| job_type | string | "file_processing" |
| processor_type | string | "vigilancia_nominal" o "vigilancia_agregada" |
| status | string | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| progress_percentage | int | 0-100 |
| input_data | JSON | Ruta archivo, nombre hoja, etc |
| output_data | JSON | Resultados del procesamiento |
| celery_task_id | string | ID de la tarea en Celery |
| created_at, started_at, completed_at | datetime | Timestamps |
| error_message | string | Mensaje de error si fallo |

#### Modelo de Datos: Vigilancia Agregada

```
NotificacionSemanal (1) ──► (N) ConteoCasosClinicos
                        ──► (N) ConteoEstudiosLab
                        ──► (N) ConteoCamasIRA

NotificacionSemanal pertenece a un Establecimiento

NotificacionSemanal:
  - id, id_snvs (unico en SNVS)
  - anio, semana
  - origen (CLI_P26 | LAB_P26 | CLI_P26_INT)
  - establecimiento_id

ConteoCasosClinicos:
  - id, id_snvs, cantidad, sexo (M/F/X)
  - es_residente, es_ambulatorio
  - notificacion_id, tipo_evento_id, rango_etario_id

ConteoEstudiosLab:
  - id, id_snvs, cantidad_estudiadas, cantidad_positivas
  - notificacion_id, agente_id, tecnica_id

ConteoCamasIRA:
  - id, ocupacion_sala, ocupacion_uti
  - notificacion_id
```

### 5.4 Sistema de Metricas (Motor BI)

El sistema de metricas maneja la salida de datos. Consulta la base de datos y devuelve metricas agregadas para los dashboards. Sin este sistema, cada dashboard tendria su propio endpoint con queries SQL hardcodeadas.

#### Arquitectura

```
app/domains/metricas/
├── service.py              # MetricService - Punto de entrada (Facade)
├── builders/               # Query Builders por fuente de datos
│   ├── base.py             # MetricQueryBuilder (abstracto)
│   ├── clinico.py          # Vigilancia clinica (CLI_P26)
│   ├── laboratorio.py      # Laboratorio (LAB_P26)
│   ├── hospitalario.py     # Ocupacion hospitalaria
│   └── nominal.py          # Casos individuales
├── criteria/               # Filtros componibles
│   ├── base.py             # Criterion + AND/OR
│   ├── temporal.py         # Filtros de tiempo
│   ├── evento.py           # Filtros de evento/agente
│   └── geografico.py       # Filtros geograficos
├── registry/               # Catalogos de definiciones
│   ├── metrics.py          # METRICS dict
│   └── dimensions.py       # DIMENSIONS dict
└── schema/
    └── cubes.py            # Schema BI para frontend
```

**Patrones:**

| Patron | Donde | Que hace |
|--------|-------|----------|
| Facade | MetricService | Punto de entrada unico, oculta complejidad interna |
| Builder | *QueryBuilder | Construye queries SQL de forma fluida |
| Criteria | Criterion y subclases | Filtros componibles con `&` y `\|` |
| Registry | METRICS, DIMENSIONS | Catalogo centralizado de definiciones |

#### API REST

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/metricas/disponibles` | Lista metricas y dimensiones disponibles |
| GET | `/metricas/schema` | Schema completo para BI |
| POST | `/metricas/query` | Ejecutar consulta |

#### Ejemplos de Request

Casos de ETI por semana:
```json
{
  "metric": "casos_clinicos",
  "dimensions": ["SEMANA_EPIDEMIOLOGICA"],
  "filters": {
    "periodo": {
      "anio_desde": 2025, "semana_desde": 1,
      "anio_hasta": 2025, "semana_hasta": 20
    },
    "evento_nombre": "ETI"
  }
}
```

Distribucion por agente etiologico:
```json
{
  "metric": "muestras_positivas",
  "dimensions": ["AGENTE_ETIOLOGICO", "SEMANA_EPIDEMIOLOGICA"],
  "filters": {
    "periodo": {
      "anio_desde": 2025, "semana_desde": 1,
      "anio_hasta": 2025, "semana_hasta": 10
    }
  }
}
```

Corredor endemico:
```json
{
  "metric": "casos_clinicos",
  "dimensions": ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
  "filters": {
    "periodo": {
      "anio_desde": 2020, "semana_desde": 1,
      "anio_hasta": 2025, "semana_hasta": 52
    },
    "evento_nombre": "ETI"
  },
  "compute": "corredor_endemico"
}
```

#### Criterios de Filtrado

**Temporales:**

| Criterio | Parametros |
|----------|------------|
| RangoPeriodoCriterion | anio_desde, semana_desde, anio_hasta, semana_hasta |
| AniosMultiplesCriterion | anios: lista de anios |

**Eventos:**

| Criterio | Parametros |
|----------|------------|
| TipoEventoCriterion | ids, nombre, slug |
| AgenteCriterion | ids, nombre |
| AgrupacionAgentesCriterion | ids, slug |

**Geograficos:**

| Criterio | Parametros |
|----------|------------|
| ProvinciaCriterion | ids, nombre |
| DepartamentoCriterion | ids, nombre |
| EstablecimientoCriterion | ids, nombre |

#### Como Agregar una Nueva Metrica

Agregar en `registry/metrics.py`:

```python
METRICS["mi_metrica"] = MetricDefinition(
    code="mi_metrica",
    label="Mi Metrica",
    description="Descripcion para UI",
    source=MetricSource.CLINICO,
    model=MiModelo,
    aggregation=AggregationType.SUM,
    field_getter=lambda: MiModelo.mi_columna,
    allowed_dimensions=[DimensionCode.SEMANA_EPIDEMIOLOGICA, ...],
)
```

Aparece automaticamente en la API.

#### Como Agregar una Nueva Dimension

1. Agregar codigo en `registry/dimensions.py`
2. Agregar mapeo en cada builder que la soporte (`get_dimension_column()`)
3. Agregar a `allowed_dimensions` de las metricas relevantes

#### Como Agregar un Nuevo Criterio de Filtrado

1. Crear clase en `criteria/` extendiendo `Criterion`
2. Implementar `to_expression()` que devuelve expresion SQLAlchemy
3. Usar: `criteria = RangoPeriodoCriterion(...) & MiCriterion(ids=[1, 2])`

#### Notas Tecnicas

- **Lazy Joins (Nominal):** Solo hace JOINs segun las dimensiones/criterios activos
- **GRUPO_ETARIO no estandarizado:** Agregados usan 19 rangos detallados, Nominal calcula 10 rangos
- **Metricas derivadas:** Se calculan post-query (ej: tasa_positividad = positivas/estudiadas)

### 5.5 Modelo de Datos

#### Datos de Referencia (Seeds)

El sistema se inicializa con datos de referencia:

| Datos | Fuente | Cantidad aproximada |
|-------|--------|---------------------|
| Provincias | Georef API | 24 |
| Departamentos | Georef API | ~530 (con coordenadas) |
| Localidades | Georef API | ~5.000 |
| Poblacion | Censo 2022 INDEC | Por departamento y provincia |
| Establecimientos de salud | REFES | ~8.300 |
| Capas GIS | IGN WFS | Hidrografia, areas urbanas |
| Tipos de evento (ENOs) | Manual | 60+ |
| Agentes etiologicos | Manual | 40+ |
| Agrupaciones de agentes | Manual | Agrupaciones de alto nivel |
| Estrategias de clasificacion | Manual | Reglas por tipo de evento |

### 5.6 Variables de Entorno

Variables requeridas en `.env` del backend:

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | Conexion a PostgreSQL | `postgresql://user:pass@localhost:5433/epi` |
| `SECRET_KEY` | Clave para JWT (generar con `openssl rand -hex 32`) | `abc123...` |
| `REDIS_URL` | Conexion a Redis | `redis://localhost:6380/0` |
| `ENVIRONMENT` | Entorno de ejecucion | `development` / `production` |
| `FRONTEND_URL` | URL del frontend | `http://localhost:3000` |

Opcionales: `ENABLE_GEOCODING`, `GOOGLE_MAPS_API_KEY`, `MAPBOX_ACCESS_TOKEN`, `MAIL_*`, `MAX_FILE_SIZE`.

---

## 6. Frontend

### 6.1 Estructura de Directorios

```
frontend/src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Layout raiz (Providers)
│   ├── page.tsx                  # Redirect a /dashboard
│   ├── login/page.tsx            # Pagina de login
│   ├── api/auth/[...nextauth]/   # NextAuth route handler
│   ├── providers.tsx             # SessionProvider + QueryClientProvider
│   └── dashboard/
│       ├── layout.tsx            # Layout con verificacion de sesion server-side
│       ├── page.tsx              # Dashboard principal
│       ├── mapa/                 # Mapa interactivo
│       ├── boletines/            # Gestion de boletines
│       ├── vigilancia/
│       │   ├── clinica/          # Dashboard vigilancia clinica
│       │   ├── laboratorio/      # Dashboard laboratorio
│       │   ├── hospitalaria/     # Dashboard hospitalaria
│       │   └── nominal/         # Listado de casos nominales
│       ├── eventos/              # Gestion de eventos
│       ├── personas/             # Personas/pacientes
│       ├── domicilios/           # Domicilios
│       ├── establecimientos/     # Establecimientos de salud
│       ├── archivos/subir/       # Subida de archivos
│       ├── catalogos/            # Catalogos
│       ├── reportes/             # Reportes
│       ├── analytics/            # Analytics
│       └── configuracion/        # Configuracion
│
├── features/                     # Modulos por funcionalidad
│   ├── analytics/                # Componentes de analytics
│   ├── auth/                     # Componentes de autenticacion
│   ├── boletines/                # Editor de boletines (Tiptap)
│   ├── dashboard/                # Componentes del dashboard
│   ├── domicilios/               # Formularios de domicilios
│   ├── establecimientos/         # Gestion de establecimientos
│   ├── estrategias/              # Estrategias de vigilancia
│   ├── eventos/                  # Componentes de eventos
│   ├── geocodificacion/          # Geocodificacion
│   ├── layout/                   # Sidebar, navegacion
│   ├── mapa/                     # Mapa con capas (Leaflet)
│   ├── metricas/                 # Graficos de metricas
│   ├── personas/                 # Listados de personas
│   ├── reports/                  # Generacion de reportes
│   └── uploads/                  # Upload y preview de archivos
│
├── components/                   # Componentes compartidos
│   ├── ui/                       # Primitivos shadcn/ui (Button, Dialog, etc)
│   ├── charts/                   # Graficos reutilizables
│   ├── filters/                  # Filtros (fecha, evento, etc)
│   ├── selectors/                # Selectores (provincia, departamento)
│   └── assets/                   # SVGs, logos
│
└── lib/                          # Utilidades
    ├── api/
    │   ├── client.ts             # API client (openapi-fetch + TanStack Query)
    │   ├── types.ts              # Tipos auto-generados del OpenAPI schema
    │   └── config.ts             # Configuracion
    ├── hooks/                    # Custom hooks
    ├── types/                    # Tipos TypeScript compartidos
    ├── auth.ts                   # Configuracion de NextAuth
    └── utils.ts                  # Utilidades generales
```

### 6.2 Patrones del Frontend

**Feature-Based Organization:** El codigo se organiza por funcionalidad. Cada feature tiene sus propios componentes y logica. Los componentes en `components/` son genericos y reutilizables entre features.

**API Client Tipado:** Se usa `openapi-fetch` que genera un cliente HTTP tipado directamente del schema OpenAPI del backend. Combinado con `openapi-react-query`, cada query tiene tipos completos:

```typescript
// El tipo de respuesta se infiere automaticamente
const { data } = $api.useQuery("get", "/api/v1/eventos/");
```

**Providers:**
- `SessionProvider` (NextAuth) - Sesion de usuario
- `QueryClientProvider` (TanStack Query) - Cache de datos con staleTime de 1 minuto

**Componentes UI:** shadcn/ui (Radix UI) para primitivos. Estan en `components/ui/` como codigo del proyecto (no dependencia externa), modificables directamente.

### 6.3 Rutas Principales

| Ruta | Descripcion |
|------|-------------|
| `/login` | Autenticacion |
| `/dashboard` | Pagina principal |
| `/dashboard/mapa` | Mapa geografico con capas y animacion temporal |
| `/dashboard/vigilancia/clinica` | Dashboard de vigilancia clinica (CLI_P26) |
| `/dashboard/vigilancia/laboratorio` | Dashboard de laboratorio (LAB_P26) |
| `/dashboard/vigilancia/hospitalaria` | Dashboard hospitalaria (CLI_P26_INT) |
| `/dashboard/vigilancia/nominal` | Listado y analisis de casos individuales |
| `/dashboard/eventos` | Gestion de eventos epidemiologicos |
| `/dashboard/personas` | Listado de personas/pacientes |
| `/dashboard/boletines` | Gestion de boletines epidemiologicos |
| `/dashboard/archivos/subir` | Subida de archivos CSV/Excel |
| `/dashboard/reportes` | Generacion de reportes |
| `/dashboard/configuracion/*` | Configuracion del sistema |

---

## 7. Guia de Desarrollo

### 7.1 Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) - Para PostgreSQL y Redis
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Gestor de paquetes Python
- [pnpm](https://pnpm.io/installation) - Gestor de paquetes Node.js
- Make (preinstalado en macOS/Linux)

### 7.2 Setup Inicial

```bash
git clone <repo-url>
cd dashboard

make install   # Instalar dependencias backend (uv sync) + frontend (pnpm install)
make up        # Levantar PostgreSQL + Redis + pgweb en Docker
make migrate   # Aplicar migraciones de BD (Alembic)
make seed      # Cargar datos iniciales (eventos, agentes, geografia, etc.)
```

### 7.3 Desarrollo Diario

Se necesitan 4 terminales:

```bash
# Terminal 1 - Infraestructura (DB + Redis)
make up

# Terminal 2 - Backend API (http://localhost:8000)
make dev

# Terminal 3 - Worker Celery (procesa archivos subidos)
make celery

# Terminal 4 - Frontend (http://localhost:3000)
make frontend
```

**URLs utiles en desarrollo:**

| URL | Que es |
|-----|--------|
| http://localhost:3000 | Frontend (Next.js) |
| http://localhost:8000 | Backend (FastAPI) |
| http://localhost:8000/docs | Swagger UI (documentacion interactiva de la API) |
| http://localhost:8000/redoc | ReDoc (documentacion alternativa de la API) |
| http://localhost:8081 | pgweb (UI para explorar la base de datos) |

### 7.4 Comandos Disponibles

```bash
# Setup
make install            # Instalar dependencias

# Desarrollo
make up                 # Levantar infra (DB, Redis, pgweb)
make down               # Detener contenedores
make logs               # Ver logs de contenedores
make dev                # Backend con hot-reload
make celery             # Worker Celery
make frontend           # Frontend con hot-reload

# Base de datos
make migrate            # Aplicar migraciones pendientes
make migration m='desc' # Crear nueva migracion
make seed               # Cargar datos iniciales
make superadmin         # Crear superadmin (interactivo)
make reset              # Borrar BD y re-seedear (DESTRUCTIVO)

# Calidad
make lint               # Ruff check + format (backend)
make typecheck          # Type checking con ty (backend)
make test               # Correr tests con pytest

# Produccion
make prod               # Stack de produccion local
make deploy             # Deploy al servidor
make deploy-status      # Estado del servidor
make deploy-logs        # Logs del servidor
make deploy-ssh         # SSH al servidor
make deploy-rollback    # Rollback
```

### 7.5 Tareas Comunes

**Agregar un nuevo endpoint:**
1. Crear archivo en `backend/app/api/v1/<recurso>/`
2. Registrar en `backend/app/api/v1/router.py`
3. Si necesita logica de negocio, crear/extender dominio en `backend/app/domains/`

**Agregar una nueva pagina:**
1. Crear directorio y `page.tsx` en `frontend/src/app/dashboard/<ruta>/`
2. Crear componentes en `frontend/src/features/<feature>/`
3. Agregar enlace en la navegacion (sidebar)

**Crear una migracion de base de datos:**
```bash
# 1. Modificar/crear modelos SQLModel en backend/app/domains/
# 2. Generar migracion
make migration m='agregar tabla X'
# 3. Revisar migracion en backend/alembic/versions/
# 4. Aplicar
make migrate
```

**Agregar una nueva metrica:** Ver seccion [5.4 Sistema de Metricas](#54-sistema-de-metricas-motor-bi).

**Agregar un nuevo tipo de archivo:** Crear procesador, registrarlo en el registry, agregar deteccion en upload handler. Ver seccion [5.3 Arquitectura de Procesamiento](#53-arquitectura-de-procesamiento-de-datos).

### 7.6 Convenciones

- **Backend:** Python con type hints, formateo con Ruff, type checking con ty
- **Frontend:** TypeScript estricto, ESLint, Tailwind CSS para estilos
- **Idioma del codigo:** Nombres de dominio en espanol, infraestructura en ingles
- **API:** Versionada bajo `/api/v1/`, respuestas JSON con formato consistente de error
- **Git:** Commits en espanol, ramas descriptivas

---

## 8. Produccion y Deploy

**Desarrollo:** Solo la infraestructura (PostgreSQL, Redis, pgweb) corre en Docker. Backend y frontend corren nativamente para hot-reload rapido.

**Produccion:** Todos los servicios corren en contenedores Docker con healthchecks y restart policies.

```bash
make prod    # Produccion local
make deploy  # Deploy al servidor
```

**Docker Compose:**
- `compose.yaml` - Desarrollo (solo infra)
- `compose.prod.yaml` - Produccion (todos los servicios)

En produccion, Swagger UI, ReDoc y el schema OpenAPI estan deshabilitados por seguridad.

# 🦠 EPIDEMIOLOGÍA CHUBUT - Arquitectura de Dominios

## 🎯 **¿Qué es este sistema?**
Sistema de **vigilancia epidemiológica** para la provincia de Chubut. Gestiona eventos epidemiológicos (ENO), clasifica automáticamente casos, y genera reportes para autoridades sanitarias.

## 🏗️ **Arquitectura: Screaming Architecture + Clean Domains**

```
app/
├── domains/          🦠 DOMINIOS DE NEGOCIO (Business Logic)
├── features/         🛠️ CARACTERÍSTICAS TÉCNICAS (Application Services)
├── core/            ⚙️ INFRAESTRUCTURA (Framework & Database)
└── api/             🌐 INTERFACES (REST Endpoints)
```

---

## 🦠 **DOMINIOS DE NEGOCIO**

### 🔥 **epidemiologia/** - CORE DOMAIN
> "El corazón del sistema de vigilancia epidemiológica"

```
epidemiologia/
├── eventos/        📋 Gestión de eventos epidemiológicos (ENO)
├── clasificacion/  🤖 Clasificación automática de eventos
└── seguimiento/    📈 Monitoreo y tracking temporal
```

**¿Qué hace?**
- Registra y gestiona eventos epidemiológicos
- Clasifica automáticamente usando estrategias
- Rastrea evolución temporal de eventos

**Aggregate Roots:** `Evento`, `EventStrategy`, `Timeline`

---

### 👥 **personas/** - Supporting Domain
> "Quién está involucrado en los eventos epidemiológicos"

```
personas/
├── ciudadanos/  👤 Ciudadanos y demografía
└── animales/    🐕 Animales (enfermedades zoonóticas)
```

**¿Qué hace?**
- Gestiona información de ciudadanos
- Maneja datos demográficos y contacto
- Gestiona animales para casos zoonóticos

**Aggregate Roots:** `Ciudadano`, `Animal`

---

### 🗺️ **territorio/** - Supporting Domain
> "Dónde ocurren los eventos epidemiológicos"

```
territorio/
├── geografia/         🌍 Ubicaciones geográficas
└── establecimientos/  🏥 Establecimientos de salud
```

**¿Qué hace?**
- Define contexto geográfico (provincias, localidades)
- Gestiona establecimientos de salud
- Relaciona eventos con ubicaciones

**Aggregate Roots:** `Localidad`, `Establecimiento`

---

### ⚕️ **clinica/** - Supporting Domain
> "Contexto médico de los eventos epidemiológicos"

```
clinica/
├── diagnosticos/     🔬 Diagnósticos médicos
├── salud/           💊 Datos de salud (síntomas, muestras, vacunas)
└── investigaciones/ 🔍 Investigaciones epidemiológicas
```

**¿Qué hace?**
- Gestiona diagnósticos médicos
- Registra síntomas, muestras, vacunas
- Coordina investigaciones epidemiológicas

**Aggregate Roots:** `Diagnostico`, `Muestra`, `Investigacion`

---

### 🔐 **autenticacion/** - Supporting Domain
> "Quién puede usar el sistema"

**¿Qué hace?**
- Autenticación y autorización
- Gestión de usuarios y roles
- Sesiones y seguridad

**Aggregate Root:** `User`

---

## 🛠️ **FEATURES TÉCNICAS**

### 📁 **procesamiento_archivos/**
> "Procesa archivos CSV/Excel con datos epidemiológicos"

**¿Qué hace?**
- Upload y validación de archivos
- Procesamiento asíncrono con Celery
- Bulk insert de datos epidemiológicos

---

### 📊 **dashboard/**
> "Visualizaciones dinámicas del estado epidemiológico"

**¿Qué hace?**
- Genera charts dinámicos
- Procesa datos para visualización
- Configuración de dashboards

---

### 📋 **reporteria/**
> "Genera reportes para autoridades sanitarias"

**¿Qué hace?**
- Genera PDFs con Playwright
- Exporta a Excel/CSV
- Templates de reportes

---

### 📈 **analitica/**
> "Análisis e insights epidemiológicos"

**¿Qué hace?**
- Análisis estadístico
- Detección de patrones
- Métricas e insights

---

## 🎯 **Para Developers Nuevos**

### 📝 **¿Dónde encuentro...?**

| Busco... | Lo encuentro en... |
|---|---|
| **Lógica de eventos epidemiológicos** | `domains/epidemiologia/eventos/` |
| **Algoritmos de clasificación** | `domains/epidemiologia/clasificacion/` |
| **Datos de pacientes** | `domains/personas/ciudadanos/` |
| **Ubicaciones geográficas** | `domains/territorio/geografia/` |
| **Diagnósticos médicos** | `domains/clinica/diagnosticos/` |
| **Upload de archivos** | `features/procesamiento_archivos/` |
| **Charts del dashboard** | `features/dashboard/` |
| **Generación de reportes** | `features/reporteria/` |

### 🔗 **Reglas de Dependencias**

```
✅ PERMITIDO:
features/ → domains/     (Features usan dominios)
domains/ → core/         (Dominios usan infraestructura)

❌ PROHIBIDO:
domains/ → features/     (Dominios NO usan features)
domains/ → domains/      (Dominios NO se conocen entre sí)
```

### 🚀 **Flujo Típico**

1. **API Endpoint** recibe request
2. **Feature Service** coordina la operación
3. **Domain Service** aplica reglas de negocio
4. **Repository** persiste datos
5. **Response** vuelve al cliente

---

## 🧪 **Testing Strategy**

- **Unit Tests:** Cada domain por separado
- **Integration Tests:** Features + domains
- **E2E Tests:** API endpoints completos

---

Esta arquitectura **GRITA EPIDEMIOLOGÍA** - cualquier developer nuevo sabe inmediatamente qué hace el sistema y dónde encontrar cada cosa. 🎯
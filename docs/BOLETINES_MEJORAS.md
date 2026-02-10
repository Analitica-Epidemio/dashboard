# Sistema de Boletines: Propuestas de Mejora

> Rediseño completo del flujo de creación, edición y exportación de boletines epidemiológicos.

---

## Principios de Diseño

Todas las mejoras siguen estos principios:

| Principio | Aplicación |
|-----------|------------|
| **Progressive Disclosure** | Mostrar solo lo necesario en cada paso, revelar complejidad gradualmente |
| **Overview First** | Siempre mostrar el contexto general antes del detalle |
| **Feedback Inmediato** | Cada acción tiene respuesta visual instantánea |
| **Prevención de Errores** | Validar antes de permitir avanzar, confirmaciones en acciones destructivas |
| **Reconocimiento > Memoria** | Opciones visibles, no escondidas en menús |

---

## 1. El Problema Actual

### Pain Points Identificados

```
FLUJO ACTUAL (confuso):

  /nuevo → Formulario simple → [Generar] → Esperar... → Editor
                   ↓
           "¿Qué eventos elijo?"
           "¿Cómo va a quedar?"
           "¿Qué secciones incluye?"
```

**Problemas concretos:**
1. El usuario genera "a ciegas" sin ver preview
2. La configuración de templates requiere conocimiento técnico
3. Los gráficos no se exportan correctamente a PDF
4. No hay forma fácil de reusar boletines anteriores
5. La estructura del documento no es visible mientras se edita

---

## 2. Nuevo Flujo: Wizard Fullscreen

### Concepto: Experiencia Inmersiva de Creación

El nuevo generador es una **experiencia fullscreen** que guía paso a paso con preview en tiempo real.

### Por qué Fullscreen?

- Elimina distracciones
- Enfoca al usuario en la tarea
- Permite layout split (config + preview)
- Sensación de "modo de creación" dedicado

### Layout Principal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [✕ Cancelar]           Crear Boletín            Paso 2 de 4    [Siguiente →]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐   ┌───────────────────────────────────┐   │
│  │                             │   │                                   │   │
│  │      PANEL IZQUIERDO        │   │        PANEL DERECHO              │   │
│  │      ═══════════════        │   │        ═════════════              │   │
│  │                             │   │                                   │   │
│  │      Configuración del      │   │        Preview en vivo            │   │
│  │      paso actual            │   │        del boletín                │   │
│  │                             │   │                                   │   │
│  │      (formularios,          │   │        (se actualiza              │   │
│  │       selectores,           │   │         mientras el usuario       │   │
│  │       opciones)             │   │         configura)                │   │
│  │                             │   │                                   │   │
│  │                             │   │                                   │   │
│  └─────────────────────────────┘   └───────────────────────────────────┘   │
│                                                                             │
│  ──────────────────────────────────────────────────────────────────────────│
│  [○ Período]  [● Eventos]  [○ Contenido]  [○ Revisar]                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Los 4 Pasos

---

#### PASO 1: Período

**Objetivo:** Definir el alcance temporal del boletín.

**Panel Izquierdo:**
```
┌─────────────────────────────────────────┐
│  PERÍODO DEL BOLETÍN                    │
│                                         │
│  Semana Epidemiológica                  │
│  ┌─────────────────────────────────┐    │
│  │  SE 42                      [▼] │    │
│  └─────────────────────────────────┘    │
│  ↳ Semana actual (recomendado)          │
│                                         │
│  Año                                    │
│  ┌─────────────────────────────────┐    │
│  │  2024                       [▼] │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ─────────────────────────────────────  │
│                                         │
│  Semanas de análisis                    │
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │  4   │  │● 8   │  │  12  │          │
│  │ sem  │  │ sem  │  │ sem  │          │
│  └──────┘  └──────┘  └──────┘          │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ ℹ️ Analizarás: SE 35 a SE 42     │    │
│  │    (26/08/2024 - 20/10/2024)    │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

**Panel Derecho (Preview):** Muestra la portada con el período seleccionado.

---

#### PASO 2: Eventos

**Objetivo:** Seleccionar qué enfermedades/eventos incluir.

**UX Clave:** Cada evento muestra su estado epidemiológico actual para ayudar a decidir.

**Panel Izquierdo:**
```
┌─────────────────────────────────────────────────────────────┐
│  EVENTOS A INCLUIR                                          │
│                                                             │
│  🔍 Buscar evento...                                        │
│                                                             │
│  ┌─ RESPIRATORIOS ────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │ [✓] Influenza                                     │ │ │
│  │  │                                                   │ │ │
│  │  │     🟡 ALERTA    ↑ +23% vs semana anterior        │ │ │
│  │  │     142 casos    12.3% positividad                │ │ │
│  │  │                                                   │ │ │
│  │  │     ┌─────────────────────────────────────────┐   │ │ │
│  │  │     │ ▁▂▃▄▅▆▇█▇▅  Mini corredor endémico      │   │ │ │
│  │  │     └─────────────────────────────────────────┘   │ │ │
│  │  │                                                   │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │ [✓] RSV                                           │ │ │
│  │  │                                                   │ │ │
│  │  │     🔴 BROTE     ↑ +67% vs semana anterior        │ │ │
│  │  │     89 casos     18.7% positividad                │ │ │
│  │  │                                                   │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │  [ ] COVID-19              🟢 Normal    → estable      │ │
│  │  [ ] Parainfluenza         🟢 Normal    ↓ -5%         │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ ENTÉRICOS ────────────────────────────────────────────┐ │
│  │  [ ] Rotavirus             🟡 Alerta    ↑ +15%        │ │
│  │  [ ] Norovirus             🟢 Normal    → estable     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  📊 2 eventos seleccionados (1 alerta, 1 brote)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Interacción:** Al hacer click en un evento, se expande mostrando más detalles (corredor, tendencia, etc.)

**Panel Derecho (Preview):** Se actualiza mostrando las secciones que tendrá el boletín según los eventos seleccionados.

---

#### PASO 3: Contenido

**Objetivo:** Configurar qué secciones y gráficos incluir.

**UX Clave:** Drag & drop para reordenar, checkboxes para incluir/excluir.

```
┌─────────────────────────────────────────────────────────────┐
│  ESTRUCTURA DEL BOLETÍN                                     │
│                                                             │
│  Arrastra para reordenar · Click en ⚙️ para configurar      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ≡  ✓ Portada                                   [⚙️]  │   │
│  │    Logo, título, período, autoridades                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ≡  ✓ Resumen Ejecutivo                         [⚙️]  │   │
│  │    KPIs, alertas activas, highlights                 │   │
│  │    ┌───────────────────────────────────────────┐    │   │
│  │    │ Incluye:                                  │    │   │
│  │    │ ✓ Tabla de KPIs        ✓ Alertas         │    │   │
│  │    │ ✓ Mapa resumen         ○ Comparación YoY │    │   │
│  │    └───────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ── SECCIONES POR EVENTO ─────────────────────────────────  │
│  (Se generan automáticamente para cada evento seleccionado) │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ≡  ✓ Influenza                                 [⚙️]  │   │
│  │    ┌───────────────────────────────────────────┐    │   │
│  │    │ ✓ Corredor endémico                       │    │   │
│  │    │ ✓ Curva epidemiológica                    │    │   │
│  │    │ ✓ Distribución por edad                   │    │   │
│  │    │ ○ Distribución geográfica                 │    │   │
│  │    │ ○ Tabla detallada                         │    │   │
│  │    └───────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ≡  ✓ RSV                                       [⚙️]  │   │
│  │    [Misma estructura, configurable]                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ≡  ✓ Metodología                               [⚙️]  │   │
│  │    Fuentes de datos, definiciones                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Panel Derecho (Preview):** Muestra el documento completo con todas las secciones, scrolleable.

---

#### PASO 4: Revisar y Generar

**Objetivo:** Confirmar todo antes de generar.

```
┌─────────────────────────────────────────────────────────────┐
│  RESUMEN FINAL                                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  📅 Período        SE 42 - 2024 (8 semanas)         │   │
│  │  🦠 Eventos        Influenza, RSV                   │   │
│  │  📑 Secciones      5 secciones                      │   │
│  │  📊 Gráficos       12 visualizaciones               │   │
│  │  📄 Páginas est.   ~8 páginas                       │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Título del boletín                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Boletín Epidemiológico SE 42 - 2024                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ Guardar esta configuración como plantilla         │   │
│  │   para reusar en futuros boletines                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│       ┌─────────────────────────────────────────┐          │
│       │                                         │          │
│       │          [Generar Boletín]              │          │
│       │                                         │          │
│       │      Tiempo estimado: ~15 segundos      │          │
│       │                                         │          │
│       └─────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Panel Derecho (Preview):** Preview completo navegable del documento final.

---

## 3. Editor Mejorado

### Layout de 3 Paneles

```
┌────────────┬──────────────────────────────────────────┬─────────────┐
│            │                                          │             │
│ ESTRUCTURA │              EDITOR                      │ PROPIEDADES │
│            │                                          │             │
│  Árbol     │   Área de edición                        │  Contexto   │
│  del       │   (TipTap)                               │  del        │
│  documento │                                          │  elemento   │
│            │   [Contenido A4]                         │  actual     │
│            │                                          │             │
└────────────┴──────────────────────────────────────────┴─────────────┘
```

### Panel Izquierdo: Estructura

Muestra el árbol del documento. Click navega a la sección.

```
┌─────────────────────────┐
│ ESTRUCTURA              │
├─────────────────────────┤
│                         │
│ ▼ Portada          [✓]  │
│   ├─ Título             │
│   ├─ Logo               │
│   └─ Autoridades        │
│                         │
│ ▼ Resumen          [✓]  │
│   ├─ Alertas            │
│   ├─ KPIs               │
│   └─ Highlights         │
│                         │
│ ▶ Influenza        [✓]  │
│ ▶ RSV              [✓]  │
│ ▶ Metodología      [✓]  │
│                         │
│ ─────────────────────── │
│ [+ Agregar sección]     │
│                         │
└─────────────────────────┘
```

### Panel Derecho: Propiedades

Cambia según lo que esté seleccionado.

**Si está seleccionado un gráfico:**
```
┌─────────────────────────┐
│ GRÁFICO                 │
├─────────────────────────┤
│                         │
│ Tipo                    │
│ [Corredor Endémico  ▼]  │
│                         │
│ Evento                  │
│ [RSV               ▼]   │
│                         │
│ Período                 │
│ [SE 35 - SE 42     ▼]   │
│                         │
│ ─────────────────────── │
│                         │
│ Altura                  │
│ [250px             ▼]   │
│                         │
│ Mostrar leyenda         │
│ [✓]                     │
│                         │
│ ─────────────────────── │
│                         │
│ [Actualizar gráfico]    │
│                         │
└─────────────────────────┘
```

**Si está seleccionado texto:**
```
┌─────────────────────────┐
│ TEXTO                   │
├─────────────────────────┤
│                         │
│ Estilo                  │
│ [Párrafo           ▼]   │
│                         │
│ Alineación              │
│ [←] [↔] [→]             │
│                         │
│ Formato                 │
│ [B] [I] [U] [S]         │
│                         │
└─────────────────────────┘
```

---

## 4. Inserción de Gráficos

### Flujo con Slash Command

```
Usuario escribe "/" → Aparece menú → Selecciona "Gráfico" → Se abre configurador
```

### Configurador de Gráfico (Sheet lateral)

```
┌──────────────────────────────────────────────────────────────────┐
│  Insertar Gráfico                                          [✕]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIPO DE GRÁFICO                                                 │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ ▁▂▃▅▇█▇▅│  │ ████████ │  │  ╱╲ ╱╲  │  │ ◀████▶  │        │
│  │          │  │ ████████ │  │ ╱  ╲╱   │  │          │        │
│  │ Corredor │  │ Barras   │  │ Línea   │  │ Pirámide │        │
│  │ [●]      │  │ [ ]      │  │ [ ]     │  │ [ ]      │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  DATOS                                                           │
│                                                                  │
│  Evento                                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  RSV (Virus Sincitial Respiratorio)                    [▼] │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Período                                                         │
│  ┌───────────────────┐    ┌───────────────────┐                 │
│  │ SE 35         [▼] │    │ SE 42         [▼] │                 │
│  │ Desde             │    │ Hasta             │                 │
│  └───────────────────┘    └───────────────────┘                 │
│                                                                  │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  PREVIEW                                                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                            │ │
│  │              Corredor Endémico - RSV                       │ │
│  │                                                            │ │
│  │      ████████████  Brote                                   │ │
│  │     ╱────────────╲                                         │ │
│  │    ╱   Alerta     ╲    ●───●                               │ │
│  │   ╱────────────────╲  ●                                    │ │
│  │  ╱    Seguridad     ╲●                                     │ │
│  │ ────────────────────────────                               │ │
│  │       Éxito                                                │ │
│  │                                                            │ │
│  │  SE35  SE36  SE37  SE38  SE39  SE40  SE41  SE42           │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  [Cancelar]                                        [Insertar]   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Sistema de Templates

### Concepto

Los usuarios pueden guardar configuraciones de boletines como plantillas reutilizables.

### Flujo: Crear desde Template

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Nuevo Boletín                                                        [✕]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ¿Cómo quieres empezar?                                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  [+] Desde cero                                                     │   │
│  │      Configura todo paso a paso                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  [📋] Duplicar boletín anterior                                     │   │
│  │      Usa la configuración del último boletín                        │   │
│  │                                                                     │   │
│  │      Último: SE 41 - 2024 (hace 7 días)                             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  [📁] Usar plantilla guardada                                       │   │
│  │                                                                     │   │
│  │      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │      │ Semanal      │  │ Mensual      │  │ Alerta       │          │   │
│  │      │ Estándar     │  │ Resumen      │  │ de Brote     │          │   │
│  │      └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Exportación Mejorada

### Progress Feedback

```
┌─────────────────────────────────────────────────────────────┐
│  Exportando a PDF...                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ████████████████████████░░░░░░░░░░░░░░  62%               │
│                                                             │
│  ✓ Preparando documento                                     │
│  ✓ Renderizando gráficos (8/12)                            │
│  ◌ Generando páginas                                        │
│  ◌ Optimizando PDF                                          │
│                                                             │
│  Tiempo restante: ~8 segundos                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Quick Wins (1-2 días cada uno)

Mejoras pequeñas con alto impacto:

| # | Mejora | Impacto |
|---|--------|---------|
| 1 | **Botón "Duplicar"** en lista de boletines | Reusar config anterior |
| 2 | **Preview expandido** de evento al seleccionar | Mejor decisión |
| 3 | **Barra de progreso real** en exportación | Menos ansiedad |
| 4 | **Panel de estructura** en editor | Navegación clara |
| 5 | **Atajos de teclado** (Cmd+S, Cmd+E) | Productividad |

---

## 8. Roadmap

```
FASE 1 (2-3 semanas): Fundamentos
────────────────────────────────
☐ Wizard fullscreen con preview en vivo
☐ Fix: Gráficos en exportación PDF
☐ Preview de datos en selección de eventos

FASE 2 (2-3 semanas): Editor
────────────────────────────
☐ Panel de estructura (árbol)
☐ Panel de propiedades contextual
☐ Configurador de gráficos mejorado

FASE 3 (2 semanas): Templates
─────────────────────────────
☐ Duplicar boletín anterior
☐ Guardar/cargar plantillas
☐ Catálogo de gráficos

FASE 4 (2 semanas): Configuración
─────────────────────────────────
☐ UI para gestionar secciones
☐ UI para gestionar bloques
☐ Editor de template de evento
```

---

## 9. Principios de Interacción

### Feedback en cada acción

| Acción | Feedback |
|--------|----------|
| Guardar | Toast "Guardado" + timestamp |
| Generar | Loading con progreso |
| Error | Toast rojo + mensaje claro |
| Éxito | Toast verde + siguiente paso |

### Prevención de errores

| Situación | Prevención |
|-----------|------------|
| Salir sin guardar | Dialog de confirmación |
| Eliminar sección | Dialog "¿Estás seguro?" |
| Generar sin eventos | Botón deshabilitado + tooltip explicativo |
| Periodo inválido | Validación inline + mensaje |

### Estados visuales claros

```
Boletín:
  [Borrador] → Gris, editable
  [En revisión] → Amarillo, comentarios habilitados
  [Publicado] → Verde, solo lectura
```

---

*Documento actualizado: Enero 2026*

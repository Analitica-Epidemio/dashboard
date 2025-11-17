// Types para Boletín Semanal - Versión Simplificada

export interface PortadaConfig {
  titulo: string;
  subtitulo?: string;
  incluir_logo: boolean;
  logo_url?: string;
  incluir_texto_estandar?: boolean; // Legacy field
}

// Legacy types - to be refactored
export type TipoSeccion =
  | "tabla_enos"
  | "vigilancia_ira"
  | "vigilancia_virus"
  | "capacidad_hospitalaria"
  | "intoxicacion_co"
  | "diarreas"
  | "suh"
  | "enfermedad_especifica"
  | "texto_libre";

export interface SeccionConfig {
  id: string;
  orden: number;
  titulo: string;
  contenido_html: string; // Rich text editable content
  enabled?: boolean; // Legacy field
  tipo?: TipoSeccion; // Legacy field
  params?: Record<string, unknown>; // Legacy field
}

export interface BoletinSemanalTemplate {
  id?: number;
  nombre: string;
  tipo: "boletin_semanal";
  portada: PortadaConfig;
  secciones: SeccionConfig[];
  created_at?: string;
  updated_at?: string;
}

// Variables disponibles para insertar en el contenido
export const VARIABLES_DISPONIBLES = [
  {
    variable: "{{semana_epidemiologica}}",
    descripcion: "Número de semana epidemiológica",
    ejemplo: "SE 40",
  },
  {
    variable: "{{año}}",
    descripcion: "Año actual",
    ejemplo: "2025",
  },
  {
    variable: "{{periodo}}",
    descripcion: "Período del reporte",
    ejemplo: "SE 36 a SE 40",
  },
  {
    variable: "{{tabla_top_5_enos}}",
    descripcion: "Tabla con los 5 eventos más frecuentes",
    ejemplo: "[Tabla generada]",
  },
  {
    variable: "{{grafico_ira}}",
    descripcion: "Gráfico de corredor IRA",
    ejemplo: "[Gráfico generado]",
  },
  {
    variable: "{{tabla_casos_ira}}",
    descripcion: "Tabla de casos IRA",
    ejemplo: "[Tabla generada]",
  },
  {
    variable: "{{grafico_virus_respiratorios}}",
    descripcion: "Gráfico de detección viral",
    ejemplo: "[Gráfico generado]",
  },
  {
    variable: "{{capacidad_hospitalaria}}",
    descripcion: "Tabla de capacidad hospitalaria",
    ejemplo: "[Tabla generada]",
  },
];

// Legacy constants - to be refactored or removed
export const SECCIONES_METADATA = [
  {
    tipo: "tabla_enos" as TipoSeccion,
    nombre: "Tabla de ENOs",
    descripcion: "Eventos de Notificación Obligatoria más frecuentes",
    emoji: "📊",
    icono: "📊",
    categoria: "Datos",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "vigilancia_ira" as TipoSeccion,
    nombre: "Vigilancia IRA",
    descripcion: "Infecciones Respiratorias Agudas",
    emoji: "🫁",
    icono: "🫁",
    categoria: "Vigilancia",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "vigilancia_virus" as TipoSeccion,
    nombre: "Vigilancia de Virus",
    descripcion: "Detección viral respiratoria",
    emoji: "🦠",
    icono: "🦠",
    categoria: "Vigilancia",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "capacidad_hospitalaria" as TipoSeccion,
    nombre: "Capacidad Hospitalaria",
    descripcion: "Disponibilidad de camas",
    emoji: "🏥",
    icono: "🏥",
    categoria: "Datos",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "intoxicacion_co" as TipoSeccion,
    nombre: "Intoxicación por CO",
    descripcion: "Casos de intoxicación por monóxido de carbono",
    emoji: "⚠️",
    icono: "⚠️",
    categoria: "Vigilancia",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "diarreas" as TipoSeccion,
    nombre: "Diarreas",
    descripcion: "Casos de enfermedades diarreicas",
    emoji: "💧",
    icono: "💧",
    categoria: "Vigilancia",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "suh" as TipoSeccion,
    nombre: "SUH",
    descripcion: "Síndrome Urémico Hemolítico",
    emoji: "🩸",
    icono: "🩸",
    categoria: "Vigilancia",
    requiere_backend: true,
    configurable: true,
  },
  {
    tipo: "enfermedad_especifica" as TipoSeccion,
    nombre: "Enfermedad Específica",
    descripcion: "Sección personalizada para una enfermedad específica",
    emoji: "🔬",
    icono: "🔬",
    categoria: "Personalizado",
    requiere_backend: false,
    configurable: false,
  },
  {
    tipo: "texto_libre" as TipoSeccion,
    nombre: "Texto Libre",
    descripcion: "Sección de texto libre editable",
    emoji: "📝",
    icono: "📝",
    categoria: "Personalizado",
    requiere_backend: false,
    configurable: false,
  },
];

// Legacy param types for backwards compatibility
export interface TablaEnosParams {
  top_n?: number;
  ultimas_n_semanas?: number;
  excluir_respiratorios?: boolean;
  solo_confirmados?: boolean;
  incluir_nota_pie?: boolean;
}

export interface VigilanciaIRAParams {
  incluir_grafico?: boolean;
  incluir_eti?: boolean;
  incluir_neumonia?: boolean;
  incluir_bronquiolitis?: boolean;
  incluir_grafico_edad?: boolean;
  periodo_desde_se?: number;
  periodo_hasta_se?: number;
}

export interface VigilanciaVirusParams {
  virus_tipos?: string[];
  incluir_grafico_temporal?: boolean;
  incluir_grafico_edad?: boolean;
  incluir_tabla_influenza?: boolean;
  periodo_desde_se?: number;
  periodo_hasta_se?: number;
}

export interface CapacidadHospitalariaParams {
  hospitales?: string[];
  ultimas_n_semanas?: number;
  mostrar_dotacion?: boolean;
}

export interface IntoxicacionCOParams {
  incluir_mapa?: boolean;
  incluir_grafico_ugd?: boolean;
  comparar_con_año_anterior?: boolean;
  año_comparacion?: number;
}

export interface DiarreasParams {
  incluir_tendencia?: boolean;
  incluir_corredor?: boolean;
  incluir_tabla_agentes?: boolean;
  incluir_grafico_distribucion?: boolean;
  periodo_desde_se?: number;
  periodo_hasta_se?: number;
}

export interface SUHParams {
  incluir_detalles?: boolean;
  incluir_grafico_historico?: boolean;
  año_inicio_historico?: number;
  incluir_tabla_casos?: boolean;
  periodo_desde_se?: number;
  periodo_hasta_se?: number;
}

export const DEFAULT_SECCION_PARAMS: Record<TipoSeccion, Record<string, unknown>> = {
  tabla_enos: {},
  vigilancia_ira: {},
  vigilancia_virus: {},
  capacidad_hospitalaria: {},
  intoxicacion_co: {},
  diarreas: {},
  suh: {},
  enfermedad_especifica: {},
  texto_libre: {},
};

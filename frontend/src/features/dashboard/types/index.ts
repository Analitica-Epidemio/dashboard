// Tipos existentes
export interface Group {
  id: string
  name: string
  description?: string | null
}

export interface Event {
  id: string
  name: string
  groupId: string
  description?: string | null
  groupName?: string | null
}

export interface ChartDataPoint {
  date: string
  value: number
  category?: string
}

export interface DashboardFilters {
  selectedGroupId: string | null
  selectedEventId: string | null
}

// KPI Types
export interface KPIData {
  totalCases: number;
  newCases7Days: number;
  incidenceRate: number;
  mortalityRate: number;
  affectedAreas: number;
  totalAreas: number;
  averageResponseTime: number;
  previousPeriod: {
    totalCases: number;
    newCases7Days: number;
    incidenceRate: number;
    mortalityRate: number;
    affectedAreas: number;
    averageResponseTime: number;
  };
  trends: {
    totalCases: 'up' | 'down' | 'stable';
    newCases7Days: 'up' | 'down' | 'stable';
    incidenceRate: 'up' | 'down' | 'stable';
    mortalityRate: 'up' | 'down' | 'stable';
    affectedAreas: 'up' | 'down' | 'stable';
    averageResponseTime: 'up' | 'down' | 'stable';
  };
  lastUpdated: string;
  weekNumber: number;
}

export interface ChartData {
  title: string
  data: ChartDataPoint[]
  type: 'line' | 'bar' | 'area' | 'pie'
  color?: string
}

// ===== NUEVOS TIPOS EPIDEMIOLÓGICOS =====

// Tipos base epidemiológicos
export interface EpidemiologicalWeek {
  year: number;
  week: number;
}

export interface GeographicArea {
  id: string;
  name: string;
  code: string;
}

// Datos para Corredor Endémico
export interface EndemicCorridorZone {
  week: number;
  successZone: number;    // zona_exito
  securityZone: number;   // zona_seguridad  
  alertZone: number;      // zona_alerta
}

export interface EndemicCorridorData {
  zones: EndemicCorridorZone[];
  currentYear: {
    week: number;
    cases: number;
  }[];
  statistics: {
    historicalYears: number;
    tValue: number;
    currentYear: number;
  };
}

export interface EndemicCorridorConfig {
  calculation: 'media' | 'media_movil_casos' | 'media_movil_incidencia';
  cumulative?: boolean;
  logarithmic?: boolean;
  movingWindow?: number;
  lastWeek?: number;
}

// Datos para Curva Epidemiológica
export interface ViralAgent {
  id: string;
  name: string;
  color: string;
}

export interface EpidemiologicalCurvePoint {
  week: number;
  year: number;
  cases: Record<string, number>; // viralAgentId -> cases
  deaths: number;
  mortalityRate: number;
  cumulativeMortality: number;
}

export interface EpidemiologicalCurveData {
  points: EpidemiologicalCurvePoint[];
  viralAgents: ViralAgent[];
  statistics: {
    totalCases: number;
    totalDeaths: number;
    overallMortalityRate: number;
  };
}

// Datos para Totales Históricos
export interface HistoricalTotalsPoint {
  year: number;
  areas: Record<string, number>; // areaId -> cases
  total: number;
  mortalityRate?: number;
}

export interface HistoricalTotalsData {
  points: HistoricalTotalsPoint[];
  areas: GeographicArea[];
  statistics: {
    yearsRange: [number, number];
    totalCases: number;
    averageMortalityRate?: number;
  };
}

// Datos para Casos por Edad
export interface AgeCasesPoint {
  ageGroup: string;
  male: number;
  female: number;
  total: number;
}

export interface AgeCasesData {
  points: AgeCasesPoint[];
  statistics: {
    totalCases: number;
    mostAffectedAgeGroup: string;
    genderDistribution: {
      male: number;
      female: number;
    };
  };
}

// Datos para Casos por UGD
export interface UGDCasesPoint {
  ugdId: string;
  ugdName: string;
  cases: number;
  percentage: number;
  mortalityRate?: number;
}

export interface UGDCasesData {
  points: UGDCasesPoint[];
  statistics: {
    totalCases: number;
    mostAffectedUGD: string;
  };
}

// Datos especializados
export interface SuicideAttemptData {
  points: {
    week: number;
    year: number;
    attempts: number;
    deaths: number;
    mortalityRate: number;
  }[];
  demographics: {
    ageGroups: Record<string, number>;
    genderDistribution: Record<string, number>;
    methodsUsed: Record<string, number>;
  };
}

export interface AnimalRabiesData {
  points: {
    date: string;
    species: string;
    location: string;
    cases: number;
    tested: number;
    positive: number;
  }[];
  statistics: {
    speciesDistribution: Record<string, number>;
    locationDistribution: Record<string, number>;
    positivityRate: number;
  };
}

// Configuración común de charts
export interface ChartConfig {
  width?: number;
  height?: number;
  colors?: Record<string, string>;
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  responsive?: boolean;
}

// Estados de carga para hooks
export interface ChartState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

// Filtros epidemiológicos extendidos
export interface EpidemiologicalFilters extends DashboardFilters {
  dateRange?: {
    startDate: string;
    endDate: string;
  };
  geographicAreas?: string[];
  ageGroups?: string[];
  eventTypes?: string[];
  includeDeaths?: boolean;
}

// Respuesta del API
export interface ApiResponse<T> {
  data: T;
  metadata: {
    totalRecords: number;
    lastUpdated: string;
    source: string;
    filters?: EpidemiologicalFilters;
  };
}
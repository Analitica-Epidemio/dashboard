/**
 * Universal Chart Specification
 * Especificación compartida entre frontend y backend para generación de charts
 */

// ============================================================================
// Tipos Base
// ============================================================================

export type ChartType = 'line' | 'bar' | 'area' | 'pie' | 'd3_pyramid' | 'mapa';

export interface WeekMetadata {
  year: number;
  week: number;
  start_date: string;
  end_date: string;
}

export interface Dataset {
  label?: string | null;
  data: number[];
  color?: string | null;
  type?: 'area' | 'line' | null; // Para area charts con líneas superpuestas
}

// ============================================================================
// Datos por Tipo de Chart
// ============================================================================

export interface BaseChartData {
  labels: string[];
  datasets: Dataset[];
  metadata?: WeekMetadata[] | null;
}

export interface PyramidDataPoint {
  age_group: string;
  male: number;
  female: number;
  [key: string]: unknown;
}

export interface MapDepartmentData {
  codigo_indec: number;
  nombre: string;
  zona_ugd: string;
  poblacion: number;
  casos: number;
  tasa_incidencia: number;
}

export interface MapChartData {
  departamentos: MapDepartmentData[];
  total_casos: number;
}

// ============================================================================
// Configuración de Charts
// ============================================================================

export interface BaseChartConfig {
  height?: number | null;
  width?: number | null;
  showLegend?: boolean | null;
  showGrid?: boolean | null;
  colors?: string[] | null;
}

export interface LineChartConfig extends BaseChartConfig {
  showPoints?: boolean | null;
  curved?: boolean | null;
}

export interface BarChartConfig extends BaseChartConfig {
  stacked?: boolean | null;
  horizontal?: boolean | null;
}

export interface AreaChartConfig extends BaseChartConfig {
  stacked?: boolean | null;
  fillOpacity?: number | null;
}

export interface PieChartConfig extends BaseChartConfig {
  showPercentages?: boolean | null;
  innerRadius?: number | null; // For donut charts
}

export interface PyramidChartConfig extends BaseChartConfig {
  showAxisLabels?: boolean | null;
}

export interface MapChartConfig extends BaseChartConfig {
  colorScale?: 'sequential' | 'diverging' | null;
  province?: 'chubut' | null; // Expandible a otras provincias
}

// ============================================================================
// Filtros (para reproducibilidad)
// ============================================================================

export interface ChartFilters {
  grupo_eno_ids?: number[] | null;
  tipo_eno_ids?: number[] | null;
  clasificacion?: string[] | null;
  provincia_id?: number[] | null;
  fecha_desde?: string | null;
  fecha_hasta?: string | null;
  edad_min?: number | null;
  edad_max?: number | null;
  tipo_sujeto?: 'humano' | 'animal' | null;
  [key: string]: unknown; // Filtros adicionales
}

// ============================================================================
// Especificación Universal
// ============================================================================

export interface UniversalChartSpec {
  // Metadata
  id: string;
  title: string;
  description?: string | null;
  codigo?: string | null; // Código del chart en el backend

  // Tipo y datos (discriminated union)
  type: ChartType;
  data: ChartData;
  config: ChartConfig;

  // Filtros aplicados (para reproducibilidad)
  filters?: ChartFilters | null;

  // Timestamp de generación
  generated_at?: string | null;
}

// Discriminated union para data
export type ChartData =
  | { type: 'line' | 'bar' | 'area' | 'pie'; data: BaseChartData }
  | { type: 'd3_pyramid'; data: PyramidDataPoint[] }
  | { type: 'mapa'; data: MapChartData };

// Discriminated union para config
export type ChartConfig =
  | { type: 'line'; config: LineChartConfig }
  | { type: 'bar'; config: BarChartConfig }
  | { type: 'area'; config: AreaChartConfig }
  | { type: 'pie'; config: PieChartConfig }
  | { type: 'd3_pyramid'; config: PyramidChartConfig }
  | { type: 'mapa'; config: MapChartConfig };

// ============================================================================
// Request/Response para API
// ============================================================================

export interface ChartSpecRequest {
  chart_code: string;
  filters: ChartFilters;
  config?: Partial<ChartConfig>;
}

export interface ChartSpecResponse {
  spec: UniversalChartSpec;
  generated_at: string;
}

// ============================================================================
// Utilidades de Validación
// ============================================================================

export function isValidChartType(type: string): type is ChartType {
  return ['line', 'bar', 'area', 'pie', 'd3_pyramid', 'mapa'].includes(type);
}

export function validateChartSpec(spec: unknown): spec is UniversalChartSpec {
  if (typeof spec !== 'object' || spec === null) return false;

  const s = spec as Partial<UniversalChartSpec>;

  return !!(
    s.id &&
    s.title &&
    s.type &&
    isValidChartType(s.type) &&
    s.data &&
    s.config
  );
}

// ============================================================================
// Helpers para crear specs
// ============================================================================

export function createLineChartSpec(
  id: string,
  title: string,
  data: BaseChartData,
  config?: Partial<LineChartConfig>
): UniversalChartSpec {
  return {
    id,
    title,
    type: 'line',
    data: { type: 'line', data },
    config: { type: 'line', config: { ...config } },
  };
}

export function createBarChartSpec(
  id: string,
  title: string,
  data: BaseChartData,
  config?: Partial<BarChartConfig>
): UniversalChartSpec {
  return {
    id,
    title,
    type: 'bar',
    data: { type: 'bar', data },
    config: { type: 'bar', config: { ...config } },
  };
}

export function createAreaChartSpec(
  id: string,
  title: string,
  data: BaseChartData,
  config?: Partial<AreaChartConfig>
): UniversalChartSpec {
  return {
    id,
    title,
    type: 'area',
    data: { type: 'area', data },
    config: { type: 'area', config: { ...config } },
  };
}

export function createPieChartSpec(
  id: string,
  title: string,
  data: BaseChartData,
  config?: Partial<PieChartConfig>
): UniversalChartSpec {
  return {
    id,
    title,
    type: 'pie',
    data: { type: 'pie', data },
    config: { type: 'pie', config: { ...config } },
  };
}

export function createPyramidChartSpec(
  id: string,
  title: string,
  data: PyramidDataPoint[],
  config?: Partial<PyramidChartConfig>
): UniversalChartSpec {
  return {
    id,
    title,
    type: 'd3_pyramid',
    data: { type: 'd3_pyramid', data },
    config: { type: 'd3_pyramid', config: { ...config } },
  };
}

export function createMapChartSpec(
  id: string,
  title: string,
  data: MapChartData,
  config?: Partial<MapChartConfig>
): UniversalChartSpec {
  return {
    id,
    title,
    type: 'mapa',
    data: { type: 'mapa', data },
    config: { type: 'mapa', config: { ...config } },
  };
}

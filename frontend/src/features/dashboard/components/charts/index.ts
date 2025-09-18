/**
 * Exportación centralizada de todos los componentes de charts epidemiológicos
 */

// Chart infrastructure components
export { DynamicChart } from './DynamicChart';
export { ChartGrid } from './ChartGrid';
export { ChartComponents } from './ChartComponents';
export { EpidemiologicalChartsSection } from './EpidemiologicalChartsSection';

// Specific chart types
export { EpidemiologicalCurveChart } from './EpidemiologicalCurveChart';
export { EndemicCorridorChart } from './EndemicCorridorChart';
export { HistoricalTotalsChart } from './HistoricalTotalsChart';
export { AgePyramidChart } from './AgePyramidChart';
export { UGDPieChart } from './UGDPieChart';
export { SuicideAttemptChart } from './SuicideAttemptChart';
export { AnimalRabiesChart } from './AnimalRabiesChart';
export { ChubutMapChart } from './ChubutMapChart';

// Re-export types for convenience
export type {
  EpidemiologicalFilters,
  ChartConfig,
  EndemicCorridorConfig,
} from '../../types';
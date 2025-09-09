/**
 * Exportación centralizada de todos los componentes de charts epidemiológicos
 */

export { EpidemiologicalCurveChart } from './EpidemiologicalCurveChart';
export { EndemicCorridorChart } from './EndemicCorridorChart';
export { HistoricalTotalsChart } from './HistoricalTotalsChart';
export { AgePyramidChart } from './AgePyramidChart';
export { UGDPieChart } from './UGDPieChart';
export { SuicideAttemptChart } from './SuicideAttemptChart';
export { AnimalRabiesChart } from './AnimalRabiesChart';

// Re-export types for convenience
export type {
  EpidemiologicalFilters,
  ChartConfig,
  EndemicCorridorConfig,
} from '../../types';